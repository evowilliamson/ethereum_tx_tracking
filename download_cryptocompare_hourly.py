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

# CoinGecko integration
from coingecko import get_top_1000_by_marketcap


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
    limit = 1999  # Request 1999 hours to get exactly 2000 rows per batch (API returns limit+1 points with inclusive boundaries)
    
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
            print(f"  → Got {len(batch)} data points in this batch for {symbol}", flush=True)
            
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
            
            # Prepare batch data (filter out exactly 0.0 prices - indicates pre-launch period)
            batch_rows = []
            batch_timestamps = []
            filtered_zero_count = 0
            
            for point in batch:
                price = point['open']
                
                # Skip exactly 0.0 prices (coin didn't exist yet)
                # Keep all non-zero prices, no matter how small (e.g., 0.0000000000555 is valid)
                if price == 0.0:
                    filtered_zero_count += 1
                    continue
                
                timestamp = point['time']
                # Format datetime as YYYY/MM/DD hh:00:00
                dt = datetime.fromtimestamp(timestamp)
                datetime_str = dt.strftime('%Y/%m/%d %H:00:00')
                
                batch_rows.append({
                    'coin': symbol.upper(),
                    'timestamp': timestamp,
                    'datetime': datetime_str,
                    'open': str(price)
                })
                batch_timestamps.append(timestamp)
            
            # Early stop: If all prices in batch were 0.0, we've hit the pre-launch period
            # CryptoCompare has no data for this coin before this point
            if len(batch_rows) == 0:
                print(f"  ✓ All prices in batch were 0.0 for {symbol} (pre-launch period)", flush=True)
                print(f"  ✓ Reached end of available data for {symbol} - stopping early", flush=True)
                break
            
            if filtered_zero_count > 0:
                print(f"  → Filtered out {filtered_zero_count} rows with 0.0 prices for {symbol} (pre-launch data)", flush=True)
            
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
                print(f"  → Updated {updated_count} existing rows in data_dict, added {new_count} new rows for {symbol}", flush=True)
            else:
                print(f"  → Added {new_count} new rows to data dictionary for {symbol}", flush=True)
            
            request_count += 1
            
            # Get earliest and latest timestamps from filtered batch_rows (not original batch)
            # Note: batch_rows only contains valid (non-zero) prices after filtering
            if batch_rows:
                earliest_time = batch_rows[0]['timestamp']
                latest_time = batch_rows[-1]['timestamp']
                earliest_date = datetime.fromtimestamp(earliest_time).strftime('%Y-%m-%d %H:%M:%S')
                latest_date = datetime.fromtimestamp(latest_time).strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"  ✓ Request {request_count} successful for {symbol}!", flush=True)
                print(f"     Batch range: {earliest_date} to {latest_date}", flush=True)
                print(f"     Total data points in dictionary for {symbol}: {len(data_dict)}", flush=True)
                
                # Set toTs to one hour before the earliest timestamp for next request
                # This ensures no overlap (API returns limit+1 points with inclusive boundaries)
                to_ts = earliest_time - 3600
                print(f"     Next request will go back to: {datetime.fromtimestamp(to_ts).strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
            else:
                # This shouldn't happen due to early stop check above, but handle it just in case
                print(f"  ✓ Request {request_count} successful (all prices filtered out)", flush=True)
            
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




def _process_coins_batch(coins_to_process, base_data_dir, questdb_conn, api_key, currency='USD', show_original_position=False, total_coins=None):
    """
    Shared function to process a batch of coins.
    
    Args:
        coins_to_process: List of (index, symbol) tuples or list of symbols
        base_data_dir: Path to base data directory
        questdb_conn: QuestDB connection
        api_key: Optional API key
        currency: Currency pair (default USD)
        show_original_position: If True, show original position in output
        total_coins: Total coins count (for position display)
    
    Returns:
        coin_stats: Dictionary mapping symbol -> {'rows': int, 'error': str or None, 'success': bool}
        errors: List of (symbol, error_message) tuples
    """
    coin_stats = {}
    errors = []
    
    # Normalize input: handle both (index, symbol) tuples and just symbols
    normalized_coins = []
    for item in coins_to_process:
        if isinstance(item, tuple):
            normalized_coins.append(item)
        else:
            # Just a symbol, create tuple with index
            normalized_coins.append((coins_to_process.index(item), item))
    
    for idx_offset, coin_info in enumerate(normalized_coins, 1):
        if isinstance(coin_info, tuple):
            original_idx, symbol = coin_info
        else:
            original_idx = idx_offset - 1
            symbol = coin_info
        
        print(f"\n{'='*60}", flush=True)
        if show_original_position and total_coins:
            print(f"Processing {idx_offset}/{len(normalized_coins)}: {symbol} (original position: {original_idx + 1}/{total_coins})", flush=True)
        else:
            print(f"Processing {idx_offset}/{len(normalized_coins)}: {symbol}", flush=True)
        print(f"{'='*60}", flush=True)
        
        coin_start_time = time.time()
        rows_inserted = 0
        error_message = None
        
        try:
            # Set output file path
            output_file = str(base_data_dir / f"{symbol.lower()}.csv")
            
            # Load existing data from CSV and QuestDB
            data_dict = {}
            
            # Load from CSV
            csv_data = load_existing_csv(output_file, symbol)
            data_dict.update(csv_data)
            
            # Load from QuestDB (if available)
            if questdb_conn:
                questdb_data = load_existing_questdb(questdb_conn, symbol)
                data_dict.update(questdb_data)
            
            # Fetch all data (no date ranges - get ALL historical data)
            data_dict = fetch_all_hourly_data(
                symbol=symbol,
                currency=currency,
                api_key=api_key,
                output_file=output_file,
                start_ts=None,  # No start date
                end_ts=None,    # No end date
                data_dict=data_dict,
                questdb_conn=questdb_conn
            )
            
            if data_dict:
                # Filter for this symbol
                symbol_data = {k: v for k, v in data_dict.items() if k[0].upper() == symbol.upper()}
                rows_inserted = len(symbol_data)
                
                # Save to CSV
                save_data_to_csv(data_dict, output_file, symbol)
                
                coin_stats[symbol] = {
                    'rows': rows_inserted,
                    'error': None,
                    'success': True
                }
                
                coin_elapsed = time.time() - coin_start_time
                print(f"  ✓ {symbol}: {rows_inserted} rows inserted in {coin_elapsed:.1f}s", flush=True)
            else:
                error_message = "No data retrieved from API"
                coin_stats[symbol] = {
                    'rows': 0,
                    'error': error_message,
                    'success': False
                }
                errors.append((symbol, error_message))
                print(f"  ✗ {symbol}: {error_message}", flush=True)
        
        except Exception as e:
            error_message = f"{type(e).__name__}: {str(e)}"
            coin_stats[symbol] = {
                'rows': 0,
                'error': error_message,
                'success': False
            }
            errors.append((symbol, error_message))
            print(f"  ✗ {symbol}: Error - {error_message}", flush=True)
            import traceback
            traceback.print_exc()
        
        # Rate limiting between coins
        if idx_offset < len(normalized_coins):  # Don't sleep after last coin
            print(f"  → Waiting 2.0 seconds before next coin...", flush=True)
            time.sleep(2.0)
    
    return coin_stats, errors


def _generate_final_report(coin_stats, total_coins_processed, total_elapsed, report_title="Download Report", starting_coin=None):
    """
    Generate final report for coin processing.
    
    Args:
        coin_stats: Dictionary mapping symbol -> {'rows': int, 'error': str or None, 'success': bool}
        total_coins_processed: Total number of coins processed
        total_elapsed: Total time elapsed in seconds
        report_title: Title for the report
        starting_coin: Optional starting coin name for resume reports
    """
    successful_coins = [s for s, stats in coin_stats.items() if stats['success']]
    failed_coins = [s for s, stats in coin_stats.items() if not stats['success']]
    total_rows = sum(stats['rows'] for stats in coin_stats.values())
    
    print(f"\n{'='*80}", flush=True)
    print(f"FINAL REPORT: {report_title}", flush=True)
    print(f"{'='*80}", flush=True)
    if starting_coin:
        print(f"Starting coin: {starting_coin}", flush=True)
    print(f"Total coins processed: {total_coins_processed}", flush=True)
    print(f"Successful: {len(successful_coins)}", flush=True)
    print(f"Failed: {len(failed_coins)}", flush=True)
    print(f"Total rows inserted: {total_rows:,}", flush=True)
    print(f"Total time elapsed: {total_elapsed/60:.1f} minutes ({total_elapsed:.1f} seconds)", flush=True)
    
    if successful_coins:
        print(f"\n{'='*80}", flush=True)
        print(f"SUCCESSFUL COINS ({len(successful_coins)}):", flush=True)
        print(f"{'='*80}", flush=True)
        sorted_successful = sorted(
            [(s, coin_stats[s]['rows']) for s in successful_coins],
            key=lambda x: x[1],
            reverse=True
        )
        for symbol, rows in sorted_successful:
            print(f"  {symbol:10} : {rows:>8,} rows", flush=True)
    
    if failed_coins:
        print(f"\n{'='*80}", flush=True)
        print(f"FAILED COINS ({len(failed_coins)}):", flush=True)
        print(f"{'='*80}", flush=True)
        for symbol in failed_coins:
            error_msg = coin_stats[symbol]['error']
            print(f"  {symbol:10} : {error_msg}", flush=True)
    
    print(f"\n{'='*80}", flush=True)
    print(f"Report complete", flush=True)
    print(f"{'='*80}", flush=True)


def download_top_1000_all_data(api_key: str = None):
    """
    Download all hourly historical data for top 1000 cryptocurrencies by market cap.
    
    This function:
    1. Gets top 1000 coins by market cap
    2. Iterates through each coin
    3. Downloads all available hourly data (no date ranges)
    4. Saves to CSV and QuestDB
    5. Generates a final report with stats per coin
    
    Args:
        api_key: Optional API key for CryptoCompare (helps with rate limits)
    """
    # Get top 1000 coins
    coins = get_top_1000_by_marketcap(api_key)
    
    if not coins:
        print("Error: No coins retrieved from API", flush=True)
        return
    
    print(f"\n{'='*60}", flush=True)
    print(f"Starting download of all hourly data for {len(coins)} coins", flush=True)
    print(f"{'='*60}", flush=True)
    
    # Setup output directory
    home_dir = Path.home()
    base_data_dir = home_dir / ".dex_trades_extractor" / ".files" / "price" / "cryptocompare"
    base_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup QuestDB connection (reused for all coins)
    questdb_conn = get_questdb_connection()
    if questdb_conn:
        create_questdb_table(questdb_conn)
        print("  ✓ Connected to QuestDB", flush=True)
    else:
        print("  ⚠ QuestDB not available, using CSV only", flush=True)
    
    currency = 'USD'
    total_start_time = time.time()
    
    # Process all coins using shared function
    coin_stats, errors = _process_coins_batch(
        coins_to_process=coins,
        base_data_dir=base_data_dir,
        questdb_conn=questdb_conn,
        api_key=api_key,
        currency=currency,
        show_original_position=False,
        total_coins=len(coins)
    )
    
    # Close QuestDB connection
    if questdb_conn:
        questdb_conn.close()
    
    # Generate final report
    total_elapsed = time.time() - total_start_time
    _generate_final_report(
        coin_stats=coin_stats,
        total_coins_processed=len(coins),
        total_elapsed=total_elapsed,
        report_title=f"Top {len(coins)} Cryptocurrencies Download"
    )


def download_top_1000_all_data_resume(dry_run=False, exclude_coins=None, api_key: str = None):
    """
    Resume download of top 1000 cryptocurrencies by market cap from the last processed coin.
    
    This function:
    1. Gets top 1000 coins by market cap (ordered list)
    2. Queries QuestDB to find which coins have data
    3. Finds the last coin in the ordered list that has data (excluding exclude_coins)
    4. Determines which coins to process (from last_coin onwards, skipping exclude_coins)
    5. If dry_run=False, executes extraction starting from last_coin
    6. If dry_run=True, only shows what would be done (no extraction)
    
    Args:
        dry_run: If True, only show determination logic, don't execute extraction
        exclude_coins: List of coin symbols to exclude when finding last coin (e.g., ['MON'])
                       These coins will also be skipped during processing
        api_key: Optional API key for CryptoCompare (helps with rate limits)
    """
    if exclude_coins is None:
        exclude_coins = ['MON']
    
    # Convert exclude_coins to uppercase for comparison
    exclude_coins_upper = [coin.upper() for coin in exclude_coins]
    
    print(f"\n{'='*80}", flush=True)
    print(f"Resuming Top 1000 Download - Determination Logic", flush=True)
    print(f"{'='*80}", flush=True)
    
    # Get top 1000 coins (ordered by market cap)
    coins = get_top_1000_by_marketcap(api_key)
    
    if not coins:
        print("Error: No coins retrieved from API", flush=True)
        return
    
    # Log the complete list of coins for verification
    print(f"\n[DEBUG] Top 1000 coins list (total: {len(coins)}):", flush=True)
    print(f"  First 50 coins:", flush=True)
    for i, coin in enumerate(coins[:50]):
        print(f"    {i:3}: {coin}", flush=True)
    print(f"  ... (middle {len(coins) - 100} coins omitted) ...", flush=True)
    print(f"  Last 50 coins:", flush=True)
    for i, coin in enumerate(coins[-50:], start=len(coins) - 50):
        print(f"    {i:3}: {coin}", flush=True)
    
    # Check for duplicates in the list
    coin_counts = {}
    for coin in coins:
        coin_counts[coin] = coin_counts.get(coin, 0) + 1
    duplicates = {coin: count for coin, count in coin_counts.items() if count > 1}
    if duplicates:
        print(f"\n[DEBUG] Duplicate coins found in list:", flush=True)
        for coin, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True):
            indices = [i for i, c in enumerate(coins) if c == coin]
            print(f"  {coin}: appears {count} times at indices {indices[:5]}{'...' if len(indices) > 5 else ''}", flush=True)
    
    # Setup QuestDB connection for checking existing data
    questdb_conn = get_questdb_connection()
    if not questdb_conn:
        print("Error: QuestDB not available - cannot determine resume point", flush=True)
        return
    
    # Ensure table exists before querying
    create_questdb_table(questdb_conn)
    
    try:
        # Query QuestDB to find which coins have data
        with questdb_conn.cursor() as cur:
            cur.execute("SELECT DISTINCT coin FROM crypto_hourly")
            coins_in_db = set([row[0] for row in cur.fetchall()])
        
        print(f"\nDetermination Logic:", flush=True)
        print(f"  Total coins in top 1000 list: {len(coins)}", flush=True)
        print(f"  Coins with data in QuestDB: {len(coins_in_db)}", flush=True)
        if exclude_coins_upper:
            print(f"  Excluding from 'last coin' search: {', '.join(exclude_coins_upper)}", flush=True)
        
        # Create a mapping of coin -> index in the ordered list
        # Use FIRST occurrence to handle duplicates (CoinGecko API may return duplicates)
        coin_to_index = {}
        for i, coin in enumerate(coins):
            if coin not in coin_to_index:  # Only store first occurrence
                coin_to_index[coin] = i
        print(f"\n[DEBUG] Creating coin_to_index mapping for {len(coins)} coins", flush=True)
        
        # Log all coins in DB and their indices
        print(f"\n[DEBUG] Coins in QuestDB and their indices:", flush=True)
        db_coin_indices = {}
        for coin in sorted(coins_in_db):
            if coin in coin_to_index:
                idx = coin_to_index[coin]
                db_coin_indices[coin] = idx
                excluded = " (EXCLUDED)" if coin in exclude_coins_upper else ""
                print(f"  {coin}: index {idx} (position {idx + 1}){excluded}", flush=True)
            else:
                excluded = " (EXCLUDED)" if coin in exclude_coins_upper else ""
                print(f"  {coin}: NOT FOUND in ordered list{excluded}", flush=True)
        
        # Find the coin with the LOWEST ranking (HIGHEST index) in the ordered list that has data in DB
        # This is the LAST coin processed in the aborted run
        last_coin_idx = -1
        last_coin = None
        
        print(f"\n[DEBUG] Finding coin with highest index (excluding: {', '.join(exclude_coins_upper)}):", flush=True)
        # For each coin in DB (excluding exclude_coins), find its index
        # Find the one with the highest index (lowest ranking)
        for coin in coins_in_db:
            if coin not in exclude_coins_upper:
                if coin in coin_to_index:
                    coin_idx = coin_to_index[coin]
                    print(f"  Checking {coin}: index {coin_idx}, current last_coin_idx = {last_coin_idx}", flush=True)
                    if coin_idx > last_coin_idx:
                        print(f"    → {coin} has higher index ({coin_idx} > {last_coin_idx}), updating last_coin", flush=True)
                        last_coin_idx = coin_idx
                        last_coin = coin
                    else:
                        print(f"    → {coin} has lower index ({coin_idx} <= {last_coin_idx}), skipping", flush=True)
                else:
                    print(f"  Checking {coin}: NOT FOUND in coin_to_index mapping, skipping", flush=True)
            else:
                print(f"  Checking {coin}: EXCLUDED, skipping", flush=True)
        
        if last_coin_idx < 0:
            print(f"\n  ⚠ No coins found in QuestDB (excluding {', '.join(exclude_coins_upper)})", flush=True)
            print(f"  → Will start from first coin: {coins[0] if coins else 'N/A'}", flush=True)
            last_coin_idx = -1  # Start from beginning
            last_coin = None
        else:
            print(f"\n  ✓ Last coin in batch: {last_coin} (index {last_coin_idx + 1}/{len(coins)})", flush=True)
            
            # Get row count for last coin
            with questdb_conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM crypto_hourly WHERE coin = %s", (last_coin,))
                row_count = cur.fetchone()[0]
                print(f"  ✓ {last_coin} has {row_count:,} rows in QuestDB (may be partial - aborted run)", flush=True)
        
        # Determine coins to process
        print(f"\n[DEBUG] Determining coins to process:", flush=True)
        if last_coin_idx >= 0:
            print(f"  last_coin_idx = {last_coin_idx}, last_coin = {last_coin}", flush=True)
            print(f"  Will process coins from index {last_coin_idx} to {len(coins) - 1} (total {len(coins) - last_coin_idx} positions)", flush=True)
            coins_to_process = []
            for i in range(last_coin_idx, len(coins)):
                coin = coins[i]
                if coin not in exclude_coins_upper:
                    coins_to_process.append((i, coin))
                    if len(coins_to_process) <= 5:  # Log first 5
                        print(f"    Added: {coin} at index {i} (position {i + 1})", flush=True)
                else:
                    if i < last_coin_idx + 10:  # Log first 10 excluded
                        print(f"    Skipped (excluded): {coin} at index {i} (position {i + 1})", flush=True)
            
            print(f"  Total coins_to_process: {len(coins_to_process)}", flush=True)
            if len(coins_to_process) > 5:
                print(f"    ... and {len(coins_to_process) - 5} more", flush=True)
            
            coins_before_last = last_coin_idx
            coins_after_last = len(coins_to_process)
            next_coin_after_last = coins_to_process[1][1] if len(coins_to_process) > 1 else None
            
            print(f"\n[DEBUG] Calculation results:", flush=True)
            print(f"  coins_before_last = {coins_before_last} (indices 0-{coins_before_last - 1})", flush=True)
            print(f"  coins_after_last = {coins_after_last} (indices {last_coin_idx}-{len(coins) - 1}, excluding exclude_coins)", flush=True)
            if next_coin_after_last:
                # Find the index in the original coins list
                if next_coin_after_last in coin_to_index:
                    next_idx = coin_to_index[next_coin_after_last]
                    print(f"  next_coin_after_last = {next_coin_after_last} at index {next_idx} (position {next_idx + 1}) in ordered list", flush=True)
                else:
                    print(f"  next_coin_after_last = {next_coin_after_last} (NOT FOUND in coin_to_index)", flush=True)
            else:
                print(f"  next_coin_after_last = None (no coins after last_coin)", flush=True)
        else:
            # No coins found, start from beginning
            print(f"  No coins found in DB (excluding exclude_coins), starting from beginning", flush=True)
            coins_to_process = []
            for i, coin in enumerate(coins):
                if coin not in exclude_coins_upper:
                    coins_to_process.append((i, coin))
            coins_before_last = 0
            coins_after_last = len(coins_to_process)
            next_coin_after_last = coins_to_process[1][1] if len(coins_to_process) > 1 else None
            print(f"  coins_before_last = 0, coins_after_last = {coins_after_last}", flush=True)
            if next_coin_after_last:
                print(f"  next_coin_after_last = {next_coin_after_last}", flush=True)
        
        # Show determination results
        print(f"\n  Processing Plan:", flush=True)
        if last_coin_idx >= 0:
            print(f"  - Will redo: {last_coin} (in case partial)", flush=True)
            if next_coin_after_last:
                print(f"  - Will continue with: {next_coin_after_last} (next after {last_coin})", flush=True)
            print(f"  - Total coins to process: {coins_after_last} (starting from {last_coin})", flush=True)
            print(f"  - Will skip: {coins_before_last} coins before {last_coin} (already fully processed)", flush=True)
        else:
            print(f"  - Will start from: {coins[0]} (first coin)", flush=True)
            if next_coin_after_last:
                print(f"  - Will continue with: {next_coin_after_last} (next after {coins[0]})", flush=True)
            print(f"  - Total coins to process: {coins_after_last}", flush=True)
        
        # Show sample of skipped coins (for reference only)
        skipped_coins = []
        if last_coin_idx >= 0:
            for i in range(last_coin_idx):
                if coins[i] not in exclude_coins_upper:
                    skipped_coins.append(coins[i])
        
        if skipped_coins:
            if len(skipped_coins) <= 10:
                print(f"    (Skipped coins: {', '.join(skipped_coins)})", flush=True)
            else:
                print(f"    (Sample skipped coins: {', '.join(skipped_coins[:5])} ... {', '.join(skipped_coins[-3:])})", flush=True)
        
        if exclude_coins_upper:
            print(f"  - Will skip: {', '.join(exclude_coins_upper)} (will be done separately)", flush=True)
        
        # Show dry run status
        if dry_run:
            print(f"\n{'='*80}", flush=True)
            print(f"[DRY RUN - No extraction will be performed]", flush=True)
            print(f"{'='*80}", flush=True)
            questdb_conn.close()
            return
        
        # Execute extraction
        print(f"\n{'='*80}", flush=True)
        print(f"Starting extraction from {last_coin if last_coin else coins[0]} onwards", flush=True)
        print(f"{'='*80}", flush=True)
        
        # Setup output directory
        home_dir = Path.home()
        base_data_dir = home_dir / ".dex_trades_extractor" / ".files" / "price" / "cryptocompare"
        base_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure table exists
        create_questdb_table(questdb_conn)
        
        currency = 'USD'
        total_start_time = time.time()
        
        # Process coins using shared function
        coin_stats, errors = _process_coins_batch(
            coins_to_process=coins_to_process,
            base_data_dir=base_data_dir,
            questdb_conn=questdb_conn,
            api_key=api_key,
            currency=currency,
            show_original_position=True,
            total_coins=len(coins)
        )
        
        # Generate final report
        total_elapsed = time.time() - total_start_time
        _generate_final_report(
            coin_stats=coin_stats,
            total_coins_processed=len(coins_to_process),
            total_elapsed=total_elapsed,
            report_title="Resume Download",
            starting_coin=last_coin if last_coin else coins[0]
        )
    
    finally:
        questdb_conn.close()


def main():
    """Main function"""
    # Optional: API key from environment variable
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    
    # Debug: Print arguments for troubleshooting
    if len(sys.argv) > 1:
        print(f"[DEBUG] sys.argv: {sys.argv}", flush=True)
        print(f"[DEBUG] sys.argv[1].lower(): '{sys.argv[1].lower()}'", flush=True)
    
    # Check for special "top1000" command
    if len(sys.argv) >= 2 and sys.argv[1].lower() == 'top1000':
        print("="*80, flush=True)
        print("Downloading all hourly data for top 1000 cryptocurrencies", flush=True)
        print("="*80, flush=True)
        download_top_1000_all_data(api_key)
        return
    
    # Check for special "resume" command (case-insensitive)
    if len(sys.argv) >= 2:
        first_arg = sys.argv[1].lower().strip()
        if first_arg == 'resume':
            dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
            exclude_coins = ['MON']  # Default exclude list
            # Check for custom exclude coins
            if '--exclude' in sys.argv:
                idx = sys.argv.index('--exclude')
                if idx + 1 < len(sys.argv):
                    exclude_coins = [coin.strip().upper() for coin in sys.argv[idx + 1].split(',')]
            download_top_1000_all_data_resume(dry_run=dry_run, exclude_coins=exclude_coins, api_key=api_key)
            return
    
    if len(sys.argv) < 2:
        print("Usage: python3 download_cryptocompare_hourly.py <SYMBOL> [CURRENCY] [START_DATE] [END_DATE]", flush=True)
        print("   OR: python3 download_cryptocompare_hourly.py top1000", flush=True)
        print("   OR: python3 download_cryptocompare_hourly.py resume [--dry-run] [--exclude COIN1,COIN2]", flush=True)
        print("\nExample (all data for single coin):", flush=True)
        print("  python3 download_cryptocompare_hourly.py BTC", flush=True)
        print("  python3 download_cryptocompare_hourly.py BTC USD", flush=True)
        print("\nExample (date range for single coin):", flush=True)
        print("  python3 download_cryptocompare_hourly.py BTC USD 2024/01/01 2024/12/31", flush=True)
        print("  python3 download_cryptocompare_hourly.py ETH 2024/06/01 2024/06/30", flush=True)
        print("\nExample (top 1000 coins - all historical data):", flush=True)
        print("  python3 download_cryptocompare_hourly.py top1000", flush=True)
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

