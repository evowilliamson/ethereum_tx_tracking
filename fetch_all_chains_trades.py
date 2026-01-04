#!/usr/bin/env python3
"""
Generate trades for all configured blockchains
Runs fetch_all_trades.py for each supported chain
"""

import os
import sys
from chains_config import SUPPORTED_CHAINS
from fetch_all_trades import main as fetch_trades_main

def main():
    """Generate trades for all configured blockchains"""
    # Load settings
    try:
        from blockchain_settings import ETHERSCAN_API_KEY, WALLET_ADDRESSES
    except ImportError:
        print("Error: blockchain_settings.py not found!")
        print("Please copy blockchain_settings.py.example to blockchain_settings.py and configure it.")
        sys.exit(1)
    
    if ETHERSCAN_API_KEY == "YOUR_API_KEY_HERE" or not ETHERSCAN_API_KEY:
        print("Error: ETHERSCAN_API_KEY not set")
        sys.exit(1)
    
    if not WALLET_ADDRESSES or len(WALLET_ADDRESSES) == 0:
        print("Error: WALLET_ADDRESSES not set")
        sys.exit(1)
    
    print("=" * 80)
    print("Multi-Chain DEX Trade Extractor")
    print("=" * 80)
    print(f"Addresses ({len(WALLET_ADDRESSES)}):")
    for addr in WALLET_ADDRESSES:
        print(f"  - {addr}")
    print(f"Chains to process: {', '.join(SUPPORTED_CHAINS)}")
    print(f"Output CSV: evm_trades.csv")
    print("=" * 80)
    print()
    
    # Remove existing evm_trades.csv to start fresh
    output_csv = "evm_trades.csv"
    if os.path.exists(output_csv):
        print(f"Removing existing {output_csv} to start fresh...")
        os.remove(output_csv)
        print(f"✓ Removed {output_csv}\n")
    
    results = {}
    first_run = True
    
    # Loop through all addresses and chains
    for address in WALLET_ADDRESSES:
        print("\n" + "=" * 80)
        print(f"Processing Address: {address}")
        print("=" * 80)
        
        for chain in SUPPORTED_CHAINS:
            print("\n" + "=" * 80)
            print(f"Processing {chain.upper()} for {address[:10]}...")
            print("=" * 80)
            
            try:
                # Run fetch_all_trades with chain parameter, address, and append mode
                fetch_trades_main(
                    chain_name=chain,
                    address=address,
                    output_csv=output_csv,
                    append_mode=not first_run
                )
                
                results[f"{chain}-{address[:10]}"] = "success"
                print(f"\n✓ {chain.upper()} for {address[:10]} completed successfully")
                first_run = False
                
            except KeyboardInterrupt:
                print(f"\n⚠ Interrupted by user")
                results[f"{chain}-{address[:10]}"] = "interrupted"
                break
            except Exception as e:
                print(f"\n✗ {chain.upper()} for {address[:10]} failed: {e}")
                import traceback
                traceback.print_exc()
                results[f"{chain}-{address[:10]}"] = f"error: {str(e)}"
    
    # Sort the final CSV by date_time (descending)
    if os.path.exists(output_csv):
        print("\n" + "=" * 80)
        print("Sorting trades by date_time (descending)...")
        print("=" * 80)
        try:
            import csv
            from datetime import datetime
            
            # Read all rows
            with open(output_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                header = reader.fieldnames
                rows = list(reader)
            
            # Sort by date_time (descending - most recent first)
            def parse_date(date_str):
                try:
                    # Format: 2025/07/29 18:32:35
                    return datetime.strptime(date_str, '%Y/%m/%d %H:%M:%S')
                except:
                    return datetime.min
            
            rows.sort(key=lambda x: parse_date(x.get('date_time', '')), reverse=True)
            
            # Write sorted rows back
            with open(output_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=header, delimiter='\t')
                writer.writeheader()
                writer.writerows(rows)
            
            print(f"✓ Sorted {len(rows)} trades by date_time (descending)")
        except Exception as e:
            print(f"⚠ Warning: Could not sort CSV: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for chain, status in results.items():
        status_symbol = "✓" if status == "success" else "✗"
        print(f"  {status_symbol} {chain.upper()}: {status}")
    print("=" * 80)


if __name__ == "__main__":
    main()

