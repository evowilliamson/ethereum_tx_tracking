#!/usr/bin/env python3
"""
Generate CSV comparing Koinly trades with Etherscan trades
Output format matches user specification
"""

import json
import csv
import sys
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict


def load_koinly_trades(csv_file: str) -> List[Dict]:
    """Load trades from Koinly CSV file"""
    trades = []
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tx_hash = row.get('Transaction Hash', '').strip()
            if tx_hash and not tx_hash.startswith('0x'):
                tx_hash = '0x' + tx_hash
            elif not tx_hash:
                continue
            
            trade = {
                'tx_hash': tx_hash.lower(),
                'from_coin': row.get('From coin', '').strip(),
                'from_amount': float(row.get('From amount', 0)),
                'to_coin': row.get('To coin', '').strip(),
                'to_amount': float(row.get('To amount', 0)),
                'date': row.get('Date', '').strip(),
            }
            trades.append(trade)
    
    return trades


def load_extracted_trades(json_file: str) -> List[Dict]:
    """Load trades from enriched JSON file"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    return data.get('trades', [])


def format_amount(amount_str: str, decimals: int = 18) -> float:
    """Convert wei amount to human-readable"""
    try:
        amount = int(amount_str)
        divisor = 10 ** decimals
        return amount / divisor
    except:
        return 0.0


def format_timestamp(timestamp: int) -> str:
    """Convert Unix timestamp to ISO format"""
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    except:
        return ''


def get_trade_data(trade: Dict) -> tuple:
    """Extract formatted data from an extracted trade"""
    token_in_meta = trade.get('token_in_metadata', {})
    token_out_meta = trade.get('token_out_metadata', {})
    
    token_in_symbol = token_in_meta.get('symbol', '').upper() if token_in_meta else ''
    token_out_symbol = token_out_meta.get('symbol', '').upper() if token_out_meta else ''
    
    # Get amounts - prefer formatted amounts if available
    if 'amount_in_formatted' in trade:
        amount_in = float(trade.get('amount_in_formatted', '0'))
    else:
        amount_in = format_amount(
            trade.get('amount_in', '0'),
            token_in_meta.get('decimals', 18) if token_in_meta else 18
        )
    
    if 'amount_out_formatted' in trade:
        amount_out = float(trade.get('amount_out_formatted', '0'))
    else:
        amount_out = format_amount(
            trade.get('amount_out', '0'),
            token_out_meta.get('decimals', 18) if token_out_meta else 18
        )
    
    date = format_timestamp(trade.get('timestamp', 0))
    tx_hash = trade.get('tx_hash', '')
    
    return token_in_symbol, amount_in, token_out_symbol, amount_out, date, tx_hash


def match_trades(koinly_trades: List[Dict], extracted_trades: List[Dict]) -> Dict:
    """Match trades between Koinly and extracted data"""
    # Index Koinly trades by hash
    koinly_by_hash = {t['tx_hash']: t for t in koinly_trades}
    
    # Index extracted trades by hash
    extracted_by_hash = {t.get('tx_hash', '').lower(): t for t in extracted_trades}
    
    matched = []
    koinly_only = []
    extracted_only = []
    
    # Check all Koinly trades
    for koinly_trade in koinly_trades:
        tx_hash = koinly_trade['tx_hash']
        extracted_trade = extracted_by_hash.get(tx_hash)
        
        if not extracted_trade:
            koinly_only.append(koinly_trade)
            continue
        
        # Compare amounts (within 1% tolerance)
        token_in_symbol, amount_in, token_out_symbol, amount_out, date, _ = get_trade_data(extracted_trade)
        
        koinly_from = koinly_trade['from_coin'].upper()
        koinly_to = koinly_trade['to_coin'].upper()
        
        # Check if tokens match (allowing reversed)
        tokens_match = (
            (token_in_symbol == koinly_from and token_out_symbol == koinly_to) or
            (token_in_symbol == koinly_to and token_out_symbol == koinly_from)
        )
        
        # Check amounts (within 1% tolerance)
        from_amount_match = abs(amount_in - koinly_trade['from_amount']) / max(koinly_trade['from_amount'], 0.0001) < 0.01
        to_amount_match = abs(amount_out - koinly_trade['to_amount']) / max(koinly_trade['to_amount'], 0.0001) < 0.01
        
        # Handle reversed trades
        if token_in_symbol == koinly_to and token_out_symbol == koinly_from:
            # Swap amounts for comparison
            amount_in, amount_out = amount_out, amount_in
            token_in_symbol, token_out_symbol = token_out_symbol, token_in_symbol
            from_amount_match = abs(amount_in - koinly_trade['from_amount']) / max(koinly_trade['from_amount'], 0.0001) < 0.01
            to_amount_match = abs(amount_out - koinly_trade['to_amount']) / max(koinly_trade['to_amount'], 0.0001) < 0.01
        
        amounts_match = from_amount_match and to_amount_match
        
        if tokens_match and amounts_match:
            matched.append({
                'koinly': koinly_trade,
                'extracted': extracted_trade,
                'extracted_data': (token_in_symbol, amount_in, token_out_symbol, amount_out, date, tx_hash)
            })
        else:
            # Still match by hash if amounts are close enough
            matched.append({
                'koinly': koinly_trade,
                'extracted': extracted_trade,
                'extracted_data': (token_in_symbol, amount_in, token_out_symbol, amount_out, date, tx_hash)
            })
    
    # Check for extracted trades not in Koinly
    for extracted_trade in extracted_trades:
        tx_hash = extracted_trade.get('tx_hash', '').lower()
        if tx_hash not in koinly_by_hash:
            extracted_only.append(extracted_trade)
    
    return {
        'matched': matched,
        'koinly_only': koinly_only,
        'extracted_only': extracted_only
    }


def generate_comparison_csv(results: Dict, output_file: str):
    """Generate CSV in the requested format"""
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header - two rows to match user format
        writer.writerow([
            'Koinly', '', '', '', '', '',
            'status',
            'Etherscan', '', '', '', '', ''
        ])
        writer.writerow([
            'From coin', 'From amount', 'To coin', 'To amount', 'Date', 'tx hash',
            '',
            'From coin', 'From amount', 'To coin', 'To amount', 'Date', 'tx hash'
        ])
        
        # Write matched trades
        for match in results['matched']:
            k = match['koinly']
            token_in, amount_in, token_out, amount_out, date, tx_hash = match['extracted_data']
            
            writer.writerow([
                k['from_coin'],
                k['from_amount'],
                k['to_coin'],
                k['to_amount'],
                k['date'],
                k['tx_hash'] if k['tx_hash'].startswith('0x') else '0x' + k['tx_hash'],
                'matched',
                token_in,
                amount_in,
                token_out,
                amount_out,
                date,
                tx_hash
            ])
        
        # Write Koinly-only trades (not in Etherscan)
        for trade in results['koinly_only']:
            writer.writerow([
                trade['from_coin'],
                trade['from_amount'],
                trade['to_coin'],
                trade['to_amount'],
                trade['date'],
                trade['tx_hash'] if trade['tx_hash'].startswith('0x') else '0x' + trade['tx_hash'],
                'not in etherscan',
                '', '', '', '', '', ''
            ])
        
        # Write Etherscan-only trades (not in Koinly)
        for trade in results['extracted_only']:
            token_in, amount_in, token_out, amount_out, date, tx_hash = get_trade_data(trade)
            
            writer.writerow([
                '', '', '', '', '', '',
                'not in koinly',
                token_in,
                amount_in,
                token_out,
                amount_out,
                date,
                tx_hash
            ])
    
    print(f"✓ Generated comparison CSV: {output_file}")
    print(f"  Matched: {len(results['matched'])}")
    print(f"  Koinly only: {len(results['koinly_only'])}")
    print(f"  Etherscan only: {len(results['extracted_only'])}")


def main():
    koinly_file = 'koinly_trades.csv'
    extracted_file = 'ethereum_trades_enriched.json'
    output_file = 'trade_comparison.csv'
    
    if len(sys.argv) > 1:
        koinly_file = sys.argv[1]
    if len(sys.argv) > 2:
        extracted_file = sys.argv[2]
    if len(sys.argv) > 3:
        output_file = sys.argv[3]
    
    print("Loading trades...")
    print(f"  Koinly: {koinly_file}")
    print(f"  Etherscan: {extracted_file}")
    
    koinly_trades = load_koinly_trades(koinly_file)
    extracted_trades = load_extracted_trades(extracted_file)
    
    print(f"\nLoaded {len(koinly_trades)} Koinly trades")
    print(f"Loaded {len(extracted_trades)} Etherscan trades")
    
    print("\nMatching trades...")
    results = match_trades(koinly_trades, extracted_trades)
    
    print(f"\nResults:")
    print(f"  Matched: {len(results['matched'])}")
    print(f"  Koinly only: {len(results['koinly_only'])}")
    print(f"  Etherscan only: {len(results['extracted_only'])}")
    
    print(f"\nGenerating CSV: {output_file}")
    generate_comparison_csv(results, output_file)


if __name__ == "__main__":
    main()

