#!/usr/bin/env python3
"""
Download all available hourly historical data from CryptoCompare API.
Uses /data/v2/histohour endpoint and paginates to get all historical data.
"""

import requests
import csv
import time
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# QuestDB integration
from questdb import (
    get_questdb_connection,
    create_questdb_table,
    load_existing_questdb,
    check_existing_keys_questdb,
    insert_batch_to_questdb
)


def load_existing_csv(output_file: str, symbol: str) -> dict:
    """
    Load existing CSV file into a dictionary keyed by (coin, timestamp).
    
    Args:
        output_file: Path to CSV file
        symbol: Cryptocurrency symbol (e.g., 'BTC')
    
    Returns:
        Dictionary mapping (coin, timestamp) -> {'coin': coin, 'timestamp': ts, 'datetime': dt, 'open': price}
    """
    data_dict = {}
    if not os.path.exists(output_file):
        return data_dict
    
    try:
        with open(output_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                timestamp = int(row['timestamp'])
                key = (symbol.upper(), timestamp)
                data_dict[key] = {
                    'coin': symbol.upper(),
                    'timestamp': timestamp,
                    'datetime': row['datetime'],
                    'open': row['open']
                }
        print(f"  → Loaded {len(data_dict)} existing rows from CSV", flush=True)
    except Exception as e:
        print(f"  ⚠ Error loading existing CSV: {e}", flush=True)
        print(f"  → Starting with empty data", flush=True)
    
    return data_dict


def save_data_to_csv(data_dict: dict, output_file: str, symbol: str):
    """
    Save data dictionary to CSV file, sorted by timestamp.
    Uses a temporary file first to avoid corrupting the original file on failure.
    CSV only contains timestamp, datetime, open (coin is in filename).
    
    Args:
        data_dict: Dictionary mapping (coin, timestamp) -> row data
        output_file: Path to CSV file
        symbol: Cryptocurrency symbol (filter data for this symbol)
    """
    if not data_dict:
        print(f"  ⚠ No data to save", flush=True)
        return
    
    try:
        # Filter data for the specified symbol
        symbol_data = {k: v for k, v in data_dict.items() if k[0].upper() == symbol.upper()}
        if not symbol_data:
            print(f"  ⚠ No data to save to CSV for {symbol}", flush=True)
            return
        
        # Sort by timestamp
        sorted_data = sorted(symbol_data.values(), key=lambda x: x['timestamp'])
        
        # Write to temporary file first
        temp_file = output_file + '.tmp'
        with open(temp_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'datetime', 'open'])
            writer.writeheader()
            # Write only timestamp, datetime, open (exclude coin for CSV)
            for row in sorted_data:
                writer.writerow({
                    'timestamp': row['timestamp'],
                    'datetime': row['datetime'],
                    'open': row['open']
                })
        
        # Only replace the original file after successful write
        # This is atomic on most filesystems
        if os.path.exists(output_file):
            os.replace(temp_file, output_file)
        else:
            os.rename(temp_file, output_file)
        
        file_size = os.path.getsize(output_file)
        print(f"  ✓ Saved {len(sorted_data)} rows to CSV file", flush=True)
        print(f"     File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)", flush=True)
    except Exception as e:
        # Clean up temp file if it exists
        temp_file = output_file + '.tmp'
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
        print(f"  ✗ Error saving file: {type(e).__name__}: {e}", flush=True)
        print(f"  → Original file preserved", flush=True)
        import traceback
        traceback.print_exc()
        raise


def fetch_all_hourly_data(symbol: str, currency: str = 'USD', api_key: str = None, output_file: str = None, start_ts: int = None, end_ts: int = None, data_dict: dict = None, questdb_conn = None):
    """
    Fetch all hourly historical data for a cryptocurrency.
    
    Args:
        symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH', 'USDT')
        currency: Target currency (default: 'USD')
        api_key: Optional API key (not required for free tier, but helps with rate limits)
    
    Returns:
        Dictionary mapping timestamp -> {'timestamp': ts, 'datetime': dt, 'open': price}
    """
    base_url = 'https://min-api.cryptocompare.com/data/v2/histohour'
    limit = 2000  # Maximum data points per request
    
    # Determine starting timestamp
    if end_ts is not None:
        to_ts = end_ts  # Start from end timestamp
    else:
        to_ts = int(time.time())  # Start with current timestamp
    
    # Initialize data dictionary if not provided
    if data_dict is None:
        data_dict = {}
    
    print(f"\nFetching hourly data for {symbol}/{currency}...", flush=True)
    if start_ts is not None and end_ts is not None:
        start_date = datetime.fromtimestamp(start_ts).strftime('%Y-%m-%d %H:%M:%S')
        end_date = datetime.fromtimestamp(end_ts).strftime('%Y-%m-%d %H:%M:%S')
        print(f"Date range: {start_date} to {end_date} (exclusive)", flush=True)
    else:
        print(f"Starting from current time, going backwards in time (all available data)...", flush=True)
    print(f"API endpoint: {base_url}", flush=True)
    print(f"Max data points per request: {limit}", flush=True)
    
    request_count = 0
    start_time = time.time()
    
    while True:
        params = {
            'fsym': symbol.upper(),
            'tsym': currency.upper(),
            'limit': limit,
            'toTs': to_ts
        }
        
        if api_key:
            params['api_key'] = api_key
        
        current_date = datetime.fromtimestamp(to_ts).strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n[Request {request_count + 1}] Fetching data up to: {current_date} (timestamp: {to_ts})", flush=True)
        print(f"  URL: {base_url}", flush=True)
        print(f"  Parameters: fsym={params['fsym']}, tsym={params['tsym']}, limit={params['limit']}, toTs={params['toTs']}", flush=True)
        
        try:
            print(f"  → Sending request...", flush=True)
            print(f"  → Request URL: {base_url}?fsym={params['fsym']}&tsym={params['tsym']}&limit={params['limit']}&toTs={params['toTs']}", flush=True)
            
            try:
                response = requests.get(base_url, params=params, timeout=30)
                print(f"  → Response status: {response.status_code}", flush=True)
            except requests.exceptions.Timeout:
                print(f"  ✗ Request timed out after 30 seconds", flush=True)
                break
            except requests.exceptions.ConnectionError as e:
                print(f"  ✗ Connection error: {e}", flush=True)
                break
            
            response.raise_for_status()
            data = response.json()
            
            print(f"  → Response type: {data.get('Response')}", flush=True)
            
            if data.get('Response') != 'Success':
                error_message = data.get('Message', 'Unknown error')
                print(f"  ✗ API error: {error_message}", flush=True)
                print(f"  Response data: {data}", flush=True)
                break
            
            if 'Data' not in data:
                print(f"  ✗ No 'Data' key in response", flush=True)
                print(f"  Response keys: {list(data.keys())}", flush=True)
                break
                
            if 'Data' not in data['Data']:
                print(f"  ✗ No 'Data.Data' key in response", flush=True)
                print(f"  Data keys: {list(data['Data'].keys())}", flush=True)
                break
            
            batch = data['Data']['Data']
            print(f"  → Got {len(batch)} data points in this batch", flush=True)
            
            if not batch:
                print(f"  ✓ No more data available (empty batch)", flush=True)
                break
            
            # Filter data points to be within the date range if specified
            if start_ts is not None:
                # Filter out data points before start_ts
                batch = [point for point in batch if point['time'] >= start_ts]
                if not batch:
                    print(f"  ✓ Reached start date, no more data in range", flush=True)
                    break
            
            if end_ts is not None:
                # Filter out data points at or after end_ts (end is exclusive)
                batch = [point for point in batch if point['time'] < end_ts]
                if not batch:
                    print(f"  ✓ All data points are after end date, no more data in range", flush=True)
                    # Check if we should continue - if earliest point is before end_ts, we might have more
                    earliest_time = data['Data']['Data'][0]['time']
                    if earliest_time >= end_ts:
                        break
            
            if not batch:
                print(f"  ✓ No data points in the specified range", flush=True)
                break
            
            # Prepare batch data
            batch_rows = []
            batch_timestamps = []
            for point in batch:
                timestamp = point['time']
                # Format datetime as YYYY/MM/DD hh:00:00
                dt = datetime.fromtimestamp(timestamp)
                datetime_str = dt.strftime('%Y/%m/%d %H:00:00')
                
                batch_rows.append({
                    'coin': symbol.upper(),
                    'timestamp': timestamp,
                    'datetime': datetime_str,
                    'open': str(point['open'])
                })
                batch_timestamps.append(timestamp)
            
            # Check which rows already exist in QuestDB (batch check)
            existing_keys = set()
            if questdb_conn:
                existing_keys = check_existing_keys_questdb(questdb_conn, symbol, batch_timestamps)
            
            # Filter out existing rows and prepare new rows for QuestDB
            new_rows_for_db = []
            updated_count = 0
            new_count = 0
            
            for row in batch_rows:
                key = (row['coin'], row['timestamp'])
                
                # Check if key already exists in data_dict (from CSV/previous loads)
                if key in data_dict:
                    updated_count += 1
                else:
                    new_count += 1
                
                # Update dictionary (overwrites if exists, adds if new)
                data_dict[key] = row
                
                # If this row doesn't exist in QuestDB, add it to new_rows_for_db
                if key not in existing_keys:
                    new_rows_for_db.append(row)
            
            # Insert new rows to QuestDB in batch
            if questdb_conn and new_rows_for_db:
                insert_batch_to_questdb(questdb_conn, symbol, new_rows_for_db)
            
            if updated_count > 0:
                print(f"  → Updated {updated_count} existing rows in data_dict, added {new_count} new rows", flush=True)
            else:
                print(f"  → Added {new_count} new rows to data dictionary", flush=True)
            
            request_count += 1
            
            # Get earliest and latest timestamps from this batch
            earliest_time = batch[0]['time']
            latest_time = batch[-1]['time']
            earliest_date = datetime.fromtimestamp(earliest_time).strftime('%Y-%m-%d %H:%M:%S')
            latest_date = datetime.fromtimestamp(latest_time).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"  ✓ Request {request_count} successful!", flush=True)
            print(f"     Batch range: {earliest_date} to {latest_date}", flush=True)
            print(f"     Total data points in dictionary: {len(data_dict)}", flush=True)
            
            # Set toTs to one second before the earliest timestamp for next request
            to_ts = earliest_time - 1
            print(f"     Next request will go back to: {datetime.fromtimestamp(to_ts).strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
            
            # Rate limiting - be nice to the API
            print(f"  → Waiting 0.2 seconds before next request...", flush=True)
            time.sleep(0.2)
            
            # Check if we've gone back far enough (stop if we get duplicate or very old data)
            original_batch = data['Data']['Data']
            if len(original_batch) < limit:
                # If we got fewer than the limit, we're likely at the end
                print(f"  ✓ Reached end of available data (got {len(original_batch)} < {limit} data points)", flush=True)
                break
            
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Request error: {type(e).__name__}: {e}", flush=True)
            break
        except Exception as e:
            print(f"  ✗ Error: {type(e).__name__}: {e}", flush=True)
            import traceback
            traceback.print_exc()
            break
    
    elapsed_time = time.time() - start_time
    print(f"\n{'='*60}", flush=True)
    print(f"Download Summary", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"Total requests: {request_count}", flush=True)
    print(f"Total data points in dictionary: {len(data_dict)}", flush=True)
    print(f"Time elapsed: {elapsed_time:.1f} seconds", flush=True)
    
    return data_dict


def save_to_csv(data: list, output_file: str, symbol: str):
    """
    Save hourly data to CSV file.
    
    Args:
        data: List of data points
        output_file: Output CSV file path
        symbol: Cryptocurrency symbol (for header)
    """
    if not data:
        print("\n  ⚠ No data to save", flush=True)
        return
    
    print(f"\n{'='*60}", flush=True)
    print(f"Saving data to CSV file...", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"Output file: {output_file}", flush=True)
    print(f"Data points to write: {len(data)}", flush=True)
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            print(f"  → Writing CSV header...", flush=True)
            writer.writerow([
                'timestamp',
                'datetime',
                'open',
                'high',
                'low',
                'close',
                'volumefrom',
                'volumeto'
            ])
            
            # Write data rows
            print(f"  → Writing {len(data)} data rows...", flush=True)
            for i, point in enumerate(data):
                if (i + 1) % 1000 == 0:
                    print(f"     Progress: {i + 1}/{len(data)} rows written...", flush=True)
                
                dt = datetime.fromtimestamp(point['time']).strftime('%Y-%m-%d %H:%M:%S')
                writer.writerow([
                    point['time'],
                    dt,
                    point['open'],
                    point['high'],
                    point['low'],
                    point['close'],
                    point['volumefrom'],
                    point['volumeto']
                ])
        
        file_size = os.path.getsize(output_file)
        print(f"  ✓ Successfully saved {len(data)} data points to {output_file}", flush=True)
        print(f"     File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)", flush=True)
        
    except Exception as e:
        print(f"  ✗ Error saving file: {type(e).__name__}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python3 download_cryptocompare_hourly.py <SYMBOL> [CURRENCY] [START_DATE] [END_DATE]", flush=True)
        print("\nExample (all data):", flush=True)
        print("  python3 download_cryptocompare_hourly.py BTC", flush=True)
        print("  python3 download_cryptocompare_hourly.py BTC USD", flush=True)
        print("\nExample (date range):", flush=True)
        print("  python3 download_cryptocompare_hourly.py BTC USD 2024/01/01 2024/12/31", flush=True)
        print("  python3 download_cryptocompare_hourly.py ETH 2024/06/01 2024/06/30", flush=True)
        print("\nDate format: YYYY/MM/DD", flush=True)
        print("Start date: YYYY/MM/DD 00:00:00 (inclusive)", flush=True)
        print("End date: (YYYY/MM/DD + 1 day) 00:00:00 (exclusive)", flush=True)
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    
    # Parse arguments - detect if they are currency or dates
    start_ts = None
    end_ts = None
    currency = 'USD'
    
    if len(sys.argv) > 2:
        arg2 = sys.argv[2]
        # Check if arg2 is a date (YYYY/MM/DD format)
        if '/' in arg2 and len(arg2.split('/')) == 3:
            # arg2 is start date
            start_date_str = arg2
            if len(sys.argv) > 3:
                end_date_str = sys.argv[3]
            else:
                print("Error: End date required when start date is provided", flush=True)
                sys.exit(1)
        else:
            # arg2 is currency
            currency = arg2.upper()
            if len(sys.argv) > 3:
                arg3 = sys.argv[3]
                if '/' in arg3 and len(arg3.split('/')) == 3:
                    # arg3 is start date
                    start_date_str = arg3
                    if len(sys.argv) > 4:
                        end_date_str = sys.argv[4]
                    else:
                        print("Error: End date required when start date is provided", flush=True)
                        sys.exit(1)
                else:
                    # No dates provided
                    pass
    
    # Parse dates if provided
    if 'start_date_str' in locals():
        try:
            # Parse start date: YYYY/MM/DD -> YYYY-MM-DD 00:00:00
            start_dt = datetime.strptime(start_date_str, '%Y/%m/%d')
            start_ts = int(start_dt.timestamp())
            
            # Parse end date: YYYY/MM/DD -> (YYYY-MM-DD + 1 day) 00:00:00
            end_dt = datetime.strptime(end_date_str, '%Y/%m/%d')
            end_dt = end_dt + timedelta(days=1)  # Add 1 day
            end_ts = int(end_dt.timestamp())
            
            if start_ts >= end_ts:
                print("Error: Start date must be before end date", flush=True)
                sys.exit(1)
        except ValueError as e:
            print(f"Error: Invalid date format. Use YYYY/MM/DD. Error: {e}", flush=True)
            sys.exit(1)
    
    # Create output directory in home directory
    home_dir = Path.home()
    base_data_dir = home_dir / ".dex_trades_extractor" / ".files" / "price" / "cryptocompare"
    base_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Set output file path (always use default)
    output_file = str(base_data_dir / f"{symbol.lower()}.csv")
    
    # Optional: API key from environment variable
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    
    print("="*60, flush=True)
    print(f"Downloading Hourly Historical Data from CryptoCompare", flush=True)
    print("="*60, flush=True)
    print(f"Symbol: {symbol}", flush=True)
    print(f"Currency: {currency}", flush=True)
    print(f"Output file: {output_file}", flush=True)
    if api_key:
        print(f"API key: {api_key[:10]}... (provided)", flush=True)
    else:
        print(f"API key: Not provided (using free tier)", flush=True)
    print("="*60, flush=True)
    
    # Load existing data from CSV and QuestDB
    print(f"\n{'='*60}", flush=True)
    print(f"Loading existing data from CSV and QuestDB", flush=True)
    print(f"{'='*60}", flush=True)
    
    data_dict = {}
    
    # Load from CSV
    csv_data = load_existing_csv(output_file, symbol)
    data_dict.update(csv_data)
    
    # Load from QuestDB
    questdb_conn = get_questdb_connection()
    if questdb_conn:
        # Create table if it doesn't exist
        create_questdb_table(questdb_conn)
        
        # Load existing data from QuestDB
        questdb_data = load_existing_questdb(questdb_conn, symbol)
        # Merge with CSV data (QuestDB data takes precedence if there's a conflict)
        data_dict.update(questdb_data)
    else:
        questdb_conn = None
    
    # Fetch all data and update dictionary
    print(f"\n{'='*60}", flush=True)
    print(f"Fetching data from API and updating data dictionary", flush=True)
    print(f"{'='*60}", flush=True)
    data_dict = fetch_all_hourly_data(symbol, currency, api_key, output_file, start_ts, end_ts, data_dict, questdb_conn)
    
    if not data_dict:
        print(f"\n{'='*60}", flush=True)
        print(f"ERROR: No data retrieved", flush=True)
        print(f"{'='*60}", flush=True)
        print(f"Possible reasons:", flush=True)
        print(f"  - Invalid symbol: {symbol}", flush=True)
        print(f"  - API rate limit exceeded", flush=True)
        print(f"  - Network error", flush=True)
        if questdb_conn:
            questdb_conn.close()
        sys.exit(1)
    
    # Save data to CSV at the end (QuestDB data was inserted during pagination)
    print(f"\n{'='*60}", flush=True)
    print(f"Saving data to CSV file", flush=True)
    print(f"{'='*60}", flush=True)
    
    # Save to CSV
    save_data_to_csv(data_dict, output_file, symbol)
    
    # Close QuestDB connection (data was inserted during pagination)
    if questdb_conn:
        questdb_conn.close()
    
    print(f"\n{'='*60}", flush=True)
    print(f"SUCCESS: Complete!", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"Data saved to: {output_file}", flush=True)
    if questdb_conn:
        print(f"Data saved to: QuestDB table 'crypto_hourly' (inserted during pagination)", flush=True)
    
    # Calculate stats for this symbol only
    symbol_data = {k: v for k, v in data_dict.items() if k[0].upper() == symbol.upper()}
    print(f"Total data points for {symbol}: {len(symbol_data)}", flush=True)
    if symbol_data:
        sorted_timestamps = sorted([row['timestamp'] for row in symbol_data.values()])
        first_date = datetime.fromtimestamp(sorted_timestamps[0]).strftime('%Y-%m-%d %H:%M:%S')
        last_date = datetime.fromtimestamp(sorted_timestamps[-1]).strftime('%Y-%m-%d %H:%M:%S')
        
        # Show requested date range if dates were provided, otherwise show full range
        if 'start_date_str' in locals() and 'end_date_str' in locals():
            print(f"Requested date range: {start_date_str} 00:00:00 to {end_date_str} 23:59:59", flush=True)
            print(f"Total data in file: {first_date} to {last_date}", flush=True)
        else:
            print(f"Date range: {first_date} to {last_date}", flush=True)


if __name__ == "__main__":
    main()

