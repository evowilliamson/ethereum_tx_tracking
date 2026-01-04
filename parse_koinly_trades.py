#!/usr/bin/env python3
"""
Parse Koinly JSON export and extract exchange trades
Formats trades as: From coin | From amount | To coin | To amount

https://github.com/jackmatt2/koinly-csv-exporter

"""

import json
import sys
from decimal import Decimal

def format_amount(amount_str):
    """Format amount to 2 decimal places with comma separators"""
    try:
        amount = float(amount_str)
        return f"{amount:,.2f}"
    except (ValueError, TypeError):
        return amount_str

def parse_koinly_trades(json_file):
    """Parse Koinly JSON and extract exchange trades"""
    
    print(f"Reading JSON file: {json_file}")
    print("This may take a moment for large files...\n")
    
    try:
        # Try to load the file
        with open(json_file, 'r', encoding='utf-8') as f:
            print("Loading JSON into memory...")
            data = json.load(f)
            print("✓ JSON loaded successfully\n")
    except MemoryError:
        print("Error: File is too large to load into memory.")
        print("Trying streaming approach...")
        return parse_koinly_trades_streaming(json_file)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Error at position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []
    
    # Handle both array and single object
    if isinstance(data, dict):
        transactions = [data]
    elif isinstance(data, list):
        transactions = data
    else:
        print("Unexpected data format")
        return []
    
    print(f"Found {len(transactions)} total transactions")
    print("Extracting exchange trades...\n")
    
    trades = []
    binance_tx_hashes = set()  # Collect Binance transaction hashes
    
    for i, tx in enumerate(transactions):
        if (i + 1) % 1000 == 0:
            print(f"  Processed {i + 1:,} transactions, found {len(trades)} exchange trades...")
        
        if not isinstance(tx, dict):
            continue
        
        # Check if this is a Binance transaction
        wallet_from = tx.get('from', {}).get('wallet', {}) if tx.get('from') else {}
        wallet_to = tx.get('to', {}).get('wallet', {}) if tx.get('to') else {}
        
        wallet_service_from = wallet_from.get('wallet_service', {}) if wallet_from else {}
        wallet_service_to = wallet_to.get('wallet_service', {}) if wallet_to else {}
        
        service_name = (wallet_service_from.get('name', '') or wallet_service_to.get('name', '')).upper()
        service_tag = (wallet_service_from.get('tag', '') or wallet_service_to.get('tag', '')).upper()
        
        is_binance = 'BINANCE' in service_name or 'BSC' in service_name or 'binance' in service_tag or 'bsc' in service_tag
        
        # Collect Binance transaction hashes
        if is_binance:
            tx_hash = tx.get('txhash', '') or tx.get('tx_hash', '') or tx.get('hash', '')
            if tx_hash and tx_hash.startswith('0x'):
                binance_tx_hashes.add(tx_hash)
            
        # Only process exchange transactions
        if tx.get('type') != 'exchange':
            continue
        
        from_data = tx.get('from', {})
        to_data = tx.get('to', {})
        
        if not from_data or not to_data:
            continue
        
        from_amount = from_data.get('amount', '0')
        from_currency = from_data.get('currency', {})
        from_symbol = from_currency.get('symbol', 'UNKNOWN') if isinstance(from_currency, dict) else 'UNKNOWN'
        
        to_amount = to_data.get('amount', '0')
        to_currency = to_data.get('currency', {})
        to_symbol = to_currency.get('symbol', 'UNKNOWN') if isinstance(to_currency, dict) else 'UNKNOWN'
        
        # Format the trade
        trade = {
            'from_coin': from_symbol,
            'from_amount': format_amount(from_amount),
            'to_coin': to_symbol,
            'to_amount': format_amount(to_amount),
            'raw_from_amount': from_amount,
            'raw_to_amount': to_amount,
            'date': tx.get('date', 'N/A'),
            'txhash': tx.get('txhash', 'N/A')
        }
        
        trades.append(trade)
    
    print(f"\n✓ Processing complete: Found {len(trades)} exchange trades")
    print(f"✓ Found {len(binance_tx_hashes)} unique Binance transaction hashes\n")
    
    # Save Binance transaction hashes to a file
    if binance_tx_hashes:
        with open('binance_tx_hashes.txt', 'w') as f:
            for tx_hash in sorted(binance_tx_hashes):
                f.write(f"{tx_hash}\n")
        print(f"✓ Saved Binance transaction hashes to binance_tx_hashes.txt")
    
    return trades

def parse_koinly_trades_streaming(json_file):
    """Streaming parser for very large files (fallback)"""
    print("Streaming parser not yet implemented. File may be too large.")
    return []

def print_trades_table(trades):
    """Print trades in table format"""
    if not trades:
        print("No exchange trades found.")
        return
    
    print("=" * 80)
    print(f"{'From coin':<15} {'From amount':<20} {'To coin':<15} {'To amount':<20}")
    print("=" * 80)
    
    for trade in trades:
        print(f"{trade['from_coin']:<15} {trade['from_amount']:<20} {trade['to_coin']:<15} {trade['to_amount']:<20}")
    
    print("=" * 80)
    print(f"\nTotal trades: {len(trades)}")

def save_to_csv(trades, output_file='koinly_trades.csv'):
    """Save trades to CSV file"""
    import csv
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['From coin', 'From amount', 'To coin', 'To amount', 'Date', 'Transaction Hash'])
        
        for trade in trades:
            writer.writerow([
                trade['from_coin'],
                trade['raw_from_amount'],
                trade['to_coin'],
                trade['raw_to_amount'],
                trade['date'],
                trade['txhash']
            ])
    
    print(f"\nSaved {len(trades)} trades to {output_file}")

def main():
    input_file = 'dump.txt'
    output_file = 'koinly_trades.csv'
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    print("=" * 80)
    print("Koinly Trade Parser")
    print("=" * 80)
    print(f"Input file:  {input_file}")
    print(f"Output file: {output_file}")
    print("=" * 80 + "\n")
    
    # Verify input file exists
    import os
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found!")
        return
    
    trades = parse_koinly_trades(input_file)
    
    if trades:
        print_trades_table(trades)
        save_to_csv(trades, output_file)
        
        # Show the specific trade mentioned by user
        print("\n" + "=" * 80)
        print("Looking for trade: 31,356.779802 USDC -> 31,383.338735 USDT")
        print("=" * 80)
        found = False
        for trade in trades:
            try:
                if (trade['from_coin'] == 'USDC' and 
                    abs(float(trade['raw_from_amount']) - 31356.779802) < 0.01 and
                    trade['to_coin'] == 'USDT' and
                    abs(float(trade['raw_to_amount']) - 31383.338735) < 0.01):
                    print(f"\n✓ Found matching trade:")
                    print(f"  From coin:   {trade['from_coin']}")
                    print(f"  From amount: {trade['from_amount']}")
                    print(f"  To coin:     {trade['to_coin']}")
                    print(f"  To amount:   {trade['to_amount']}")
                    print(f"  Date:        {trade['date']}")
                    print(f"  TX Hash:     {trade['txhash']}")
                    found = True
                    break
            except (ValueError, KeyError):
                continue
        
        if not found:
            print("  Trade not found in results (may have different precision)")
    else:
        print("No exchange trades found. Make sure the file contains exchange transactions.")
        print("\nNote: The script only extracts transactions with type='exchange'")

if __name__ == '__main__':
    main()

