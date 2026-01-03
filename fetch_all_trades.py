#!/usr/bin/env python3
"""
Single script to fetch, parse, enrich, and export all Ethereum DEX trades
Reads configuration from ethereum_settings.py and generates a CSV file
"""

import sys
import os
import json
import csv
import time
from datetime import datetime
from fetch_ethereum_transactions import EthereumTransactionFetcher
from parse_ethereum_trades import EthereumTradeParser
from enrich_trades_with_tokens import enrich_trades
from calculate_prices import add_prices_to_trades


def format_date_for_csv(timestamp):
    """Convert Unix timestamp to format: 2020/09/20 21:36:04"""
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime('%Y/%m/%d %H:%M:%S')
    except:
        return ''


def export_to_csv(enriched_json_file: str, output_csv: str, blockchain: str, address: str):
    """
    Export enriched trades to CSV format with USD intermediary step.
    Each swap is split into two transactions:
    1. source_currency -> USD (disposition)
    2. USD -> target_currency (acquisition)
    """
    print(f"\nExporting trades to CSV: {output_csv}")
    print("-" * 60)
    
    # Load enriched trades (should have prices if calculate_prices was run)
    with open(enriched_json_file, 'r') as f:
        data = json.load(f)
    
    trades = data.get('trades', [])
    if not trades:
        print("No trades to export")
        return
    
    # Write CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')  # Tab-separated
        
        # Write header - simplified for USD intermediary format
        writer.writerow([
            'date_time',
            'source_currency',
            'source_amount',
            'target_currency',
            'target_amount',
            'platform',
            'address'
        ])
        
        total_rows = 0
        trades_with_na = 0
        
        for trade in trades:
            # Get token symbols
            token_in_meta = trade.get('token_in_metadata', {})
            token_out_meta = trade.get('token_out_metadata', {})
            
            source_currency = token_in_meta.get('symbol', 'UNKNOWN')
            target_currency = token_out_meta.get('symbol', 'UNKNOWN')
            
            # Get amounts
            source_amount = float(trade.get('amount_in_formatted', '0'))
            target_amount = float(trade.get('amount_out_formatted', '0'))
            
            # Get prices
            source_price = trade.get('source_price_usd')
            target_price = trade.get('target_price_usd')
            
            # Calculate USD value using source side (leading side)
            source_value = source_price * source_amount if source_price else None
            
            # Format date: 2020/09/20 21:36:04
            date_str = format_date_for_csv(trade.get('timestamp', 0))
            
            # Format USD amount - use "N/A" if source price is missing
            if source_value:
                usd_amount = f"{source_value:.2f}"
            else:
                usd_amount = "N/A"
                trades_with_na += 1
            
            # Row 1: source_currency -> USD (disposition/sale)
            writer.writerow([
                date_str,
                source_currency,
                source_amount,
                'USD',
                usd_amount,
                blockchain,
                address
            ])
            total_rows += 1
            
            # Row 2: USD -> target_currency (acquisition/purchase)
            # If target price is missing, set target_amount to "N/A"
            if target_price:
                target_amount_str = str(target_amount)
            else:
                target_amount_str = "N/A"
                if usd_amount != "N/A":
                    trades_with_na += 1
            
            writer.writerow([
                date_str,
                'USD',
                usd_amount,
                target_currency,
                target_amount_str,
                blockchain,
                address
            ])
            total_rows += 1
    
    exported_swaps = len(trades)
    print(f"✓ Exported {exported_swaps} swaps as {total_rows} transactions")
    if trades_with_na > 0:
        print(f"  ⚠ {trades_with_na} trades have N/A values (missing prices)")


def main():
    """Main function - does everything in one go"""
    # Load settings from ethereum_settings.py
    try:
        from ethereum_settings import ETHERSCAN_API_KEY, WALLET_ADDRESS, OUTPUT_FILE
        # Try to get BLOCKCHAIN, default to "ethereum" if not set
        try:
            from ethereum_settings import BLOCKCHAIN
            blockchain = BLOCKCHAIN if BLOCKCHAIN else 'ethereum'
        except ImportError:
            blockchain = 'ethereum'
    except ImportError:
        print("Error: ethereum_settings.py not found!")
        print("Please copy ethereum_settings.py.example to ethereum_settings.py and configure it.")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading settings: {e}")
        sys.exit(1)
    
    # Check if settings are configured
    if ETHERSCAN_API_KEY == "YOUR_API_KEY_HERE" or not ETHERSCAN_API_KEY:
        print("Error: ETHERSCAN_API_KEY not set in ethereum_settings.py")
        print("Please edit ethereum_settings.py and set your API key.")
        sys.exit(1)
    
    if WALLET_ADDRESS == "0xYourWalletAddressHere" or not WALLET_ADDRESS:
        print("Error: WALLET_ADDRESS not set in ethereum_settings.py")
        print("Please edit ethereum_settings.py and set your wallet address.")
        sys.exit(1)
    
    address = WALLET_ADDRESS
    api_key = ETHERSCAN_API_KEY
    
    # Output file names
    intermediate_json = "wallet_trades.json"
    parsed_json = OUTPUT_FILE if OUTPUT_FILE else "ethereum_trades.json"
    enriched_json = parsed_json.replace('.json', '_enriched.json')
    output_csv = parsed_json.replace('.json', '.csv')
    
    print("=" * 60)
    print("Ethereum DEX Trade Extractor - All-in-One")
    print("=" * 60)
    print(f"Address: {address}")
    print(f"Blockchain: {blockchain}")
    print(f"Output CSV: {output_csv}")
    print("=" * 60)
    
    # Step 1: Fetch transactions
    print("\n[Step 1/4] Fetching transactions from Etherscan...")
    print("-" * 60)
    
    if not address.startswith('0x') or len(address) != 42:
        print("Error: Invalid Ethereum address format")
        sys.exit(1)
    
    fetcher = EthereumTransactionFetcher(api_key, address)
    data = fetcher.fetch_all_data()
    
    print(f"Saving transaction data to {intermediate_json}...")
    with open(intermediate_json, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✓ Transaction data saved")
    
    # Step 2: Parse trades
    print("\n[Step 2/4] Parsing DEX trades...")
    print("-" * 60)
    
    parser = EthereumTradeParser(data)
    trades = parser.parse_all_trades()
    
    output = {
        "address": address,
        "total_trades": len(trades),
        "trades": trades,
        "metadata": {
            "parsed_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "total_transactions": data.get('metadata', {}).get('total_normal', 0),
            "total_erc20_transfers": data.get('metadata', {}).get('total_erc20', 0)
        }
    }
    
    print(f"Saving parsed trades to {parsed_json}...")
    with open(parsed_json, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"✓ Parsed {len(trades)} trades")
    
    # Step 3: Enrich with token metadata
    print("\n[Step 3/5] Enriching trades with token metadata...")
    print("-" * 60)
    
    enrich_trades(parsed_json, enriched_json, api_key)
    
    # Step 4: Calculate USD prices
    print("\n[Step 4/5] Calculating USD prices...")
    priced_json = enriched_json.replace('.json', '_priced.json')
    add_prices_to_trades(enriched_json, priced_json)
    
    # Step 5: Export to CSV
    print("\n[Step 5/5] Exporting to CSV...")
    export_to_csv(priced_json, output_csv, blockchain, address)
    
    # Final summary
    print("\n" + "=" * 60)
    print("Complete!")
    print("=" * 60)
    print(f"✓ Fetched transactions")
    print(f"✓ Parsed {len(trades)} DEX trades")
    print(f"✓ Enriched with token metadata")
    print(f"✓ Calculated USD prices")
    print(f"✓ Exported to CSV: {output_csv}")
    print("=" * 60)
    
    # Show summary stats
    if trades:
        dex_counts = {}
        for trade in trades:
            dex = trade.get('dex', 'Unknown')
            dex_counts[dex] = dex_counts.get(dex, 0) + 1
        
        print("\nTrades by DEX:")
        for dex, count in sorted(dex_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {dex}: {count}")
        
        timestamps = [t['timestamp'] for t in trades if t.get('timestamp')]
        if timestamps:
            min_time = min(timestamps)
            max_time = max(timestamps)
            min_date = datetime.fromtimestamp(min_time).strftime("%Y-%m-%d")
            max_date = datetime.fromtimestamp(max_time).strftime("%Y-%m-%d")
            print(f"\nDate range: {min_date} to {max_date}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

