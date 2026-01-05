#!/usr/bin/env python3
"""
Filter Sui trades based on Koinly trades CSV
Only keeps trades that have matching transaction hashes in koinly_trades.csv
"""

import json
import csv
import sys
from datetime import datetime

def load_koinly_tx_hashes(koinly_csv):
    """Load transaction hashes from Koinly CSV"""
    tx_hashes = set()
    
    print(f"Loading transaction hashes from {koinly_csv}...")
    with open(koinly_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tx_hash = row.get('Transaction Hash', '').strip()
            if tx_hash:
                # Sui transaction hashes are base58, convert to lowercase for matching
                tx_hashes.add(tx_hash.lower())
    
    print(f"✓ Loaded {len(tx_hashes)} transaction hashes from Koinly")
    return tx_hashes

def filter_sui_trades(enriched_json, koinly_tx_hashes, output_json):
    """Filter Sui trades to only include those with matching Koinly transaction hashes"""
    
    print(f"\nLoading Sui trades from {enriched_json}...")
    with open(enriched_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    original_count = len(data.get('trades', []))
    print(f"✓ Loaded {original_count} trades")
    
    # Filter trades
    filtered_trades = []
    matched_hashes = set()
    unmatched_trades = []
    
    for trade in data.get('trades', []):
        tx_hash = trade.get('tx_hash', '').lower()
        
        if tx_hash in koinly_tx_hashes:
            filtered_trades.append(trade)
            matched_hashes.add(tx_hash)
        else:
            unmatched_trades.append(trade)
    
    print(f"\n✓ Matched {len(filtered_trades)} trades with Koinly")
    print(f"✗ Filtered out {len(unmatched_trades)} trades not in Koinly")
    
    # Show some examples of filtered trades
    if unmatched_trades:
        print(f"\nExamples of filtered trades (first 5):")
        for i, trade in enumerate(unmatched_trades[:5]):
            token_in = trade.get('token_in_metadata', {}).get('symbol', 'UNKNOWN')
            token_out = trade.get('token_out_metadata', {}).get('symbol', 'UNKNOWN')
            amount_in = trade.get('amount_in_formatted', '0')
            amount_out = trade.get('amount_out_formatted', '0')
            source_price = trade.get('source_price_usd', 0)
            usd_value = float(amount_in) * source_price if source_price else 0
            print(f"  {i+1}. {token_in} {amount_in} -> {token_out} {amount_out} (USD: ${usd_value:.2f}) - {trade.get('tx_hash', 'N/A')[:20]}...")
    
    # Update data
    data['trades'] = filtered_trades
    data['total_trades'] = len(filtered_trades)
    data['metadata'] = data.get('metadata', {})
    data['metadata']['filtered_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    data['metadata']['original_trade_count'] = original_count
    data['metadata']['filtered_trade_count'] = len(filtered_trades)
    data['metadata']['koinly_matched_hashes'] = len(matched_hashes)
    
    # Save filtered JSON
    print(f"\nSaving filtered trades to {output_json}...")
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"✓ Saved {len(filtered_trades)} filtered trades")
    
    return filtered_trades, unmatched_trades

def main():
    enriched_json = 'sui_trades_enriched_priced_82acf572.json'
    koinly_csv = 'koinly_trades.csv'
    output_json = 'sui_trades_enriched_priced_82acf572.json'  # Overwrite original
    
    if len(sys.argv) > 1:
        enriched_json = sys.argv[1]
    if len(sys.argv) > 2:
        koinly_csv = sys.argv[2]
    if len(sys.argv) > 3:
        output_json = sys.argv[3]
    
    print("=" * 80)
    print("Filter Sui Trades by Koinly Transaction Hashes")
    print("=" * 80)
    print(f"Enriched JSON: {enriched_json}")
    print(f"Koinly CSV:    {koinly_csv}")
    print(f"Output JSON:   {output_json}")
    print("=" * 80)
    
    # Load Koinly transaction hashes
    koinly_tx_hashes = load_koinly_tx_hashes(koinly_csv)
    
    if not koinly_tx_hashes:
        print("\n⚠ Warning: No transaction hashes found in Koinly CSV!")
        print("Make sure the CSV has a 'Transaction Hash' column.")
        return
    
    # Filter trades
    filtered_trades, unmatched_trades = filter_sui_trades(enriched_json, koinly_tx_hashes, output_json)
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Original trades:  {len(filtered_trades) + len(unmatched_trades)}")
    print(f"Matched trades:   {len(filtered_trades)}")
    print(f"Filtered trades:  {len(unmatched_trades)}")
    print("=" * 80)
    
    print("\n✓ Filtering complete!")
    print(f"Next step: Re-run the Sui flow to regenerate sui_trades.csv with filtered trades")

if __name__ == '__main__':
    main()







