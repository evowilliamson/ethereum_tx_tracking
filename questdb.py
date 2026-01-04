"""
QuestDB integration for cryptocurrency hourly data storage.
Handles connection, table creation, loading, and saving data to QuestDB.
"""

import os
from datetime import datetime, timedelta

# QuestDB connection (using PostgreSQL wire protocol)
try:
    import psycopg2
    from psycopg2.extras import execute_values
    from psycopg2 import errors
    QUESTDB_AVAILABLE = True
except ImportError:
    QUESTDB_AVAILABLE = False
    errors = None
    print("Warning: psycopg2 not installed. QuestDB functionality will be disabled.", flush=True)
    print("  Install with: pip install psycopg2-binary", flush=True)


def get_questdb_connection():
    """
    Get QuestDB connection using PostgreSQL wire protocol.
    Default: localhost:8812 (QuestDB default port)
    """
    if not QUESTDB_AVAILABLE:
        return None
    
    # QuestDB connection settings (can be overridden with environment variables)
    host = os.getenv('QUESTDB_HOST', 'localhost')
    port = os.getenv('QUESTDB_PORT', '8812')
    user = os.getenv('QUESTDB_USER', 'admin')
    password = os.getenv('QUESTDB_PASSWORD', 'quest')
    database = os.getenv('QUESTDB_DATABASE', 'qdb')
    
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        # QuestDB requires autocommit mode for PostgreSQL wire protocol
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"  ⚠ Could not connect to QuestDB: {e}", flush=True)
        print(f"  → Continuing without database functionality", flush=True)
        return None


def create_questdb_table(conn):
    """
    Create the crypto_hourly table if it doesn't exist.
    QuestDB uses designated timestamp and doesn't support PRIMARY KEY constraints.
    We'll use (coin, timestamp) as a logical composite key for upserts.
    """
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            # Check if table exists by trying to query it
            table_exists = False
            try:
                cur.execute("SELECT 1 FROM crypto_hourly LIMIT 1")
                table_exists = True
            except (psycopg2.errors.UndefinedTable, psycopg2.DatabaseError) as e:
                # Table doesn't exist, check error message
                error_msg = str(e).lower()
                if 'table does not exist' in error_msg or 'undefined' in error_msg:
                    table_exists = False
                else:
                    # Some other error, re-raise
                    raise
            
            # Create table if it doesn't exist
            if not table_exists:
                create_table_sql = """
                CREATE TABLE crypto_hourly (
                    coin SYMBOL CAPACITY 50 CACHE,
                    timestamp TIMESTAMP,
                    datetime STRING,
                    open DOUBLE
                ) TIMESTAMP(timestamp) PARTITION BY DAY;
                """
                cur.execute(create_table_sql)
                # No commit needed with autocommit=True
            
            # Create index on coin for better query performance
            try:
                cur.execute("CREATE INDEX IF NOT EXISTS idx_coin ON crypto_hourly (coin);")
                # No commit needed with autocommit=True
            except:
                pass  # Index might already exist or not supported
            
            return True
    except Exception as e:
        print(f"  ⚠ Error creating QuestDB table: {e}", flush=True)
        # No rollback needed with autocommit=True
        return False


def load_existing_questdb(conn, symbol: str) -> dict:
    """
    Load existing data from QuestDB for a given symbol.
    
    Args:
        conn: QuestDB connection
        symbol: Cryptocurrency symbol (e.g., 'BTC')
    
    Returns:
        Dictionary mapping (coin, timestamp) -> {'coin': coin, 'timestamp': ts, 'datetime': dt, 'open': price}
    """
    data_dict = {}
    if not conn:
        return data_dict
    
    try:
        with conn.cursor() as cur:
            select_sql = "SELECT coin, timestamp, datetime, open FROM crypto_hourly WHERE coin = %s"
            cur.execute(select_sql, (symbol.upper(),))
            rows = cur.fetchall()
            
            for row in rows:
                coin, ts, dt, open_price = row
                # Convert timestamp to Unix timestamp (int)
                if isinstance(ts, datetime):
                    timestamp = int(ts.timestamp())
                else:
                    timestamp = int(ts)
                
                key = (coin, timestamp)
                data_dict[key] = {
                    'coin': coin,
                    'timestamp': timestamp,
                    'datetime': dt,
                    'open': str(open_price)
                }
            
            if rows:
                print(f"  → Loaded {len(data_dict)} existing rows from QuestDB", flush=True)
    except Exception as e:
        print(f"  ⚠ Error loading from QuestDB: {e}", flush=True)
        print(f"  → Starting with empty data from database", flush=True)
    
    return data_dict


def check_existing_keys_questdb(conn, symbol: str, timestamps: list) -> set:
    """
    Check which (coin, timestamp) keys already exist in QuestDB.
    
    Args:
        conn: QuestDB connection
        symbol: Cryptocurrency symbol (e.g., 'BTC')
        timestamps: List of Unix timestamps to check
    
    Returns:
        Set of (coin, timestamp) tuples that exist in QuestDB
    """
    existing_keys = set()
    if not conn or not timestamps:
        return existing_keys
    
    try:
        with conn.cursor() as cur:
            # Convert timestamps to datetime objects for QuestDB
            min_ts = datetime.fromtimestamp(min(timestamps))
            max_ts = datetime.fromtimestamp(max(timestamps))
            
            # Query for existing rows in this timestamp range
            select_sql = """
            SELECT coin, timestamp FROM crypto_hourly 
            WHERE coin = %s AND timestamp >= %s AND timestamp <= %s
            """
            cur.execute(select_sql, (symbol.upper(), min_ts, max_ts))
            rows = cur.fetchall()
            
            for row in rows:
                coin, ts = row
                # Convert timestamp to Unix timestamp (int)
                if isinstance(ts, datetime):
                    timestamp = int(ts.timestamp())
                else:
                    timestamp = int(ts)
                
                key = (coin, timestamp)
                existing_keys.add(key)
    
    except Exception as e:
        print(f"  ⚠ Error checking existing keys in QuestDB: {e}", flush=True)
    
    return existing_keys


def insert_batch_to_questdb(conn, symbol: str, new_rows: list):
    """
    Insert a batch of new rows into QuestDB.
    
    Args:
        conn: QuestDB connection
        symbol: Cryptocurrency symbol (e.g., 'BTC')
        new_rows: List of dictionaries with keys: 'coin', 'timestamp', 'datetime', 'open'
    """
    if not conn or not new_rows:
        return
    
    try:
        with conn.cursor() as cur:
            # Prepare data for insertion
            values = []
            for row in new_rows:
                # Convert timestamp to datetime for QuestDB
                ts = datetime.fromtimestamp(row['timestamp'])
                values.append((
                    row['coin'],
                    ts,
                    row['datetime'],
                    float(row['open'])
                ))
            
            # Insert all rows in batch
            insert_sql = """
            INSERT INTO crypto_hourly (coin, timestamp, datetime, open)
            VALUES %s
            """
            execute_values(cur, insert_sql, values)
            # No commit needed with autocommit=True
            print(f"  ✓ Inserted {len(values)} new rows to QuestDB", flush=True)
    
    except Exception as e:
        print(f"  ✗ Error inserting batch to QuestDB: {type(e).__name__}: {e}", flush=True)
        # No rollback needed with autocommit=True
        import traceback
        traceback.print_exc()


def get_crypto_data(conn, symbol: str, start_date: str, end_date: str) -> list:
    """
    Get all rows from QuestDB for a given coin and date range.
    
    Args:
        conn: QuestDB connection
        symbol: Cryptocurrency symbol (e.g., 'BTC')
        start_date: Start date in format 'YYYY/MM/DD' (inclusive)
        end_date: End date in format 'YYYY/MM/DD' (inclusive, up to end of day)
    
    Returns:
        List of dictionaries with keys: 'coin', 'timestamp', 'datetime', 'open'
        Each row contains:
        - coin (str): Cryptocurrency symbol
        - timestamp (int): Unix timestamp
        - datetime (str): Human-readable datetime (YYYY/MM/DD HH:00:00)
        - open (float): Opening price
    """
    if not conn:
        print("  ⚠ No QuestDB connection available", flush=True)
        return []
    
    try:
        # Parse dates - both dates are inclusive
        start_dt = datetime.strptime(start_date, '%Y/%m/%d')
        # Start date: from 00:00:00 (inclusive)
        start_dt = start_dt.replace(hour=0, minute=0, second=0)
        
        end_dt = datetime.strptime(end_date, '%Y/%m/%d')
        # End date: include the entire day up to 23:59:59 (inclusive)
        end_dt = end_dt.replace(hour=23, minute=59, second=59)
        
        # Convert to timestamps for query
        start_ts = start_dt
        end_ts = end_dt
        
        with conn.cursor() as cur:
            select_sql = """
            SELECT coin, timestamp, datetime, open 
            FROM crypto_hourly 
            WHERE coin = %s 
            AND timestamp >= %s 
            AND timestamp <= %s
            ORDER BY timestamp ASC
            """
            cur.execute(select_sql, (symbol.upper(), start_ts, end_ts))
            rows = cur.fetchall()
            
            # Convert to list of dictionaries
            result = []
            for row in rows:
                coin, ts, dt, open_price = row
                # Convert timestamp to Unix timestamp (int)
                if isinstance(ts, datetime):
                    timestamp = int(ts.timestamp())
                else:
                    timestamp = int(ts)
                
                result.append({
                    'coin': coin,
                    'timestamp': timestamp,
                    'datetime': dt,
                    'open': float(open_price)
                })
            
            return result
            
    except ValueError as e:
        print(f"  ⚠ Error parsing dates: {e}", flush=True)
        print(f"  → Expected format: YYYY/MM/DD", flush=True)
        return []
    except Exception as e:
        print(f"  ⚠ Error querying QuestDB: {type(e).__name__}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return []
