#!/usr/bin/env python3
"""
Rebuild coingecko_symbol_mapping.json ordered by market cap.
Top coins by market cap will appear first in the mapping.
"""

import json
import requests
import time
import os

MAPPING_FILE = 'coingecko_symbol_mapping.json'

def rebuild_mapping_by_marketcap():
    """Rebuild symbol mapping ordered by market cap"""
    print("="*60)
    print("Rebuilding CoinGecko Symbol Mapping (Ordered by Market Cap)")
    print("="*60)
    
    # Step 1: Get top coins by market cap (we'll use top 200 for canonical IDs)
    print("\nStep 1: Fetching top 200 coins by market cap...")
    canonical_ids = {}
    top_coins_ordered = []
    
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {'vs_currency': 'usd', 'per_page': 200, 'order': 'market_cap_desc', 'page': 1}
        time.sleep(0.5)
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            top200 = response.json()
            for coin in top200:
                symbol = coin.get('symbol', '').upper()
                coin_id = coin.get('id', '')
                market_cap = coin.get('market_cap', 0) or 0
                
                if symbol and coin_id:
                    # Store canonical ID (first entry with this symbol = highest market cap)
                    if symbol not in canonical_ids:
                        canonical_ids[symbol] = coin_id
                        top_coins_ordered.append((symbol, coin_id, market_cap))
            
            print(f"  ✓ Got {len(canonical_ids)} canonical IDs from top 200")
            print(f"  ✓ Top 10 by market cap: {[coin[1] for coin in top_coins_ordered[:10]]}")
        else:
            print(f"  ⚠ Error getting top 200: {response.status_code}")
            return
    except Exception as e:
        print(f"  ⚠ Error getting top 200: {e}")
        return
    
    # Step 2: Get all coins from /coins/list
    print("\nStep 2: Fetching all coins from /coins/list...")
    all_coins = []
    try:
        url = "https://api.coingecko.com/api/v3/coins/list"
        time.sleep(0.5)
        response = requests.get(url, timeout=60)
        
        if response.status_code == 200:
            all_coins = response.json()
            print(f"  ✓ Got {len(all_coins)} coins from /coins/list")
        else:
            print(f"  ⚠ Error getting /coins/list: {response.status_code}")
            return
    except Exception as e:
        print(f"  ⚠ Error getting /coins/list: {e}")
        return
    
    # Step 3: Build mapping ordered by market cap
    print("\nStep 3: Building symbol mapping ordered by market cap...")
    symbol_mapping = {}
    processed_symbols = set()
    
    # Sort top coins by market cap (descending)
    top_coins_ordered.sort(key=lambda x: x[2], reverse=True)
    
    # First, add all top coins (ordered by market cap, highest first)
    for symbol, coin_id, market_cap in top_coins_ordered:
        if symbol and symbol not in processed_symbols:
            symbol_mapping[symbol] = coin_id
            processed_symbols.add(symbol)
    
    # Then, add remaining coins from /coins/list (not in top 200)
    for coin in all_coins:
        symbol = coin.get('symbol', '').upper()
        coin_id = coin.get('id', '')
        
        if symbol and coin_id and symbol not in processed_symbols:
            # Use canonical ID if available, otherwise use this one
            if symbol in canonical_ids:
                symbol_mapping[symbol] = canonical_ids[symbol]
            else:
                symbol_mapping[symbol] = coin_id
            processed_symbols.add(symbol)
    
    print(f"  ✓ Built mapping with {len(symbol_mapping)} unique symbols")
    
    # Step 4: Save to file
    print(f"\nStep 4: Saving to {MAPPING_FILE}...")
    try:
        with open(MAPPING_FILE, 'w') as f:
            json.dump(symbol_mapping, f, indent=2)
        print(f"  ✓ Saved {len(symbol_mapping)} symbol mappings")
        print(f"\n  Top 10 coin IDs in mapping (by market cap):")
        top10_ids = list(symbol_mapping.values())[:10]
        for i, coin_id in enumerate(top10_ids, 1):
            print(f"    {i}. {coin_id}")
    except Exception as e:
        print(f"  ✗ Error saving mapping file: {e}")


if __name__ == "__main__":
    rebuild_mapping_by_marketcap()

