#!/usr/bin/env python3
"""
CoinGecko API integration
Provides functions for fetching cryptocurrency data from CoinGecko API
"""

import requests
import time
import json
import os
from typing import Dict, Optional
from datetime import datetime


# Default file paths
DEFAULT_MAPPING_FILE = 'coingecko_symbol_mapping.json'
DEFAULT_CACHE_FILE = 'coingecko_cache.json'


def get_top_1000_by_marketcap(api_key: str = None) -> list:
    """
    Get top 1000 cryptocurrencies by market cap from CoinGecko API.
    
    Args:
        api_key: Optional API key (not used for CoinGecko, kept for compatibility)
    
    Returns:
        List of cryptocurrency symbols ordered by market cap (highest first)
    """
    base_url = 'https://api.coingecko.com/api/v3/coins/markets'
    per_page = 250  # Maximum per request (CoinGecko API limit)
    total_needed = 1000
    all_coins = []
    
    print(f"\n{'='*60}", flush=True)
    print(f"Fetching top {total_needed} cryptocurrencies by market cap from CoinGecko", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"API endpoint: {base_url}", flush=True)
    print(f"Max coins per request: {per_page}", flush=True)
    
    # CoinGecko API returns max 250 coins per request
    # We need 4 requests to get 1000 coins
    num_pages = (total_needed + per_page - 1) // per_page  # Ceiling division
    
    for page_num in range(1, num_pages + 1):
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': per_page,
            'page': page_num
        }
        
        start_idx = (page_num - 1) * per_page + 1
        end_idx = min(page_num * per_page, total_needed)
        
        print(f"\n[Page {page_num}/{num_pages}] Fetching coins {start_idx} to {end_idx}...", flush=True)
        
        try:
            # CoinGecko free tier rate limit: ~10-50 calls/minute
            # Using 3 second delay to avoid rate limiting
            if page_num > 1:
                time.sleep(3.0)
            
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            coins = response.json()
            
            if not coins:
                print(f"  ✓ No more coins available (got {len(all_coins)} total)", flush=True)
                break
            
            # Extract symbols from coin data
            page_symbols = []
            for coin in coins:
                symbol = coin.get('symbol', '').upper()
                if symbol:
                    page_symbols.append(symbol)
            
            all_coins.extend(page_symbols)
            print(f"  ✓ Got {len(page_symbols)} coins (total: {len(all_coins)})", flush=True)
            
            # If we got fewer coins than requested, we've reached the end
            if len(coins) < per_page:
                print(f"  ✓ Reached end of available coins", flush=True)
                break
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print(f"  ✗ Rate limited - waiting 5 seconds before retry...", flush=True)
                time.sleep(5.0)
                continue  # Retry this page
            else:
                print(f"  ✗ HTTP error: {e.response.status_code} - {e}", flush=True)
                break
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Request error: {type(e).__name__}: {e}", flush=True)
            break
        except Exception as e:
            print(f"  ✗ Error: {type(e).__name__}: {e}", flush=True)
            import traceback
            traceback.print_exc()
            break
    
    # Limit to exactly 1000 (or whatever we got if less)
    if len(all_coins) > total_needed:
        all_coins = all_coins[:total_needed]
    
    print(f"\n{'='*60}", flush=True)
    print(f"Successfully fetched {len(all_coins)} cryptocurrencies", flush=True)
    print(f"{'='*60}", flush=True)
    
    return all_coins


def refresh_symbol_mapping(mapping_file: str = DEFAULT_MAPPING_FILE) -> Dict[str, str]:
    """
    Refresh symbol → CoinGecko ID mapping
    Queries top 200 for canonical IDs, then /coins/list for all tokens
    
    Args:
        mapping_file: Path to save the mapping file
    
    Returns:
        {symbol: coin_id} mapping
    """
    print("Refreshing CoinGecko symbol mapping...")
    
    # Step 1: Get canonical IDs from top 200 (for conflict resolution)
    canonical_ids = {}
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
                # First entry with this symbol = canonical (highest market cap)
                if symbol and symbol not in canonical_ids:
                    canonical_ids[symbol] = coin_id
            print(f"  ✓ Got {len(canonical_ids)} canonical IDs from top 200")
    except Exception as e:
        print(f"  ⚠ Error getting top 200: {e}")
    
    # Step 2: Get all coins from /coins/list
    symbol_mapping = {}
    try:
        url = "https://api.coingecko.com/api/v3/coins/list"
        time.sleep(0.5)
        response = requests.get(url, timeout=60)
        
        if response.status_code == 200:
            all_coins = response.json()
            print(f"  ✓ Got {len(all_coins)} coins from /coins/list")
            
            # Step 3: Build mapping (use canonical when available, otherwise first or heuristic)
            for coin in all_coins:
                symbol = coin.get('symbol', '').upper()
                coin_id = coin.get('id', '')
                
                if symbol and coin_id:
                    if symbol in canonical_ids:
                        # Use canonical ID (from top 200, highest market cap)
                        symbol_mapping[symbol] = canonical_ids[symbol]
                    elif symbol not in symbol_mapping:
                        # First time seeing this symbol
                        symbol_mapping[symbol] = coin_id
                    else:
                        # Conflict - use heuristic: prefer non-bridged, shorter ID
                        current_id = symbol_mapping[symbol]
                        if ('bridged' not in coin_id.lower() and 'peg' not in coin_id.lower() and 
                            len(coin_id) < len(current_id)):
                            symbol_mapping[symbol] = coin_id
            
            print(f"  ✓ Built mapping with {len(symbol_mapping)} unique symbols")
            
            # Save to file
            try:
                with open(mapping_file, 'w') as f:
                    json.dump(symbol_mapping, f, indent=2)
                print(f"  ✓ Saved to {mapping_file}")
            except Exception as e:
                print(f"  ⚠ Could not save mapping file: {e}")
            
        else:
            print(f"  ⚠ Error getting /coins/list: {response.status_code}")
            # Try to load from file if exists
            symbol_mapping = load_symbol_mapping(mapping_file)
    except Exception as e:
        print(f"  ⚠ Error refreshing mapping: {e}")
        # Try to load from file if exists
        symbol_mapping = load_symbol_mapping(mapping_file)
    
    return symbol_mapping


def load_symbol_mapping(mapping_file: str = DEFAULT_MAPPING_FILE) -> Dict[str, str]:
    """
    Load symbol mapping from file if refresh fails
    
    Args:
        mapping_file: Path to the mapping file
    
    Returns:
        {symbol: coin_id} mapping
    """
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r') as f:
                mapping = json.load(f)
                print(f"  ✓ Loaded {len(mapping)} mappings from file")
                return mapping
        except Exception:
            pass
    return {}


def get_historical_price(symbol: str, timestamp: int, symbol_mapping: Dict[str, str]) -> Optional[float]:
    """
    Get historical price from CoinGecko with caching
    
    Args:
        symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
        timestamp: Unix timestamp
        symbol_mapping: {symbol: coin_id} mapping
    
    Returns:
        Price in USD or None if not found
    """
    symbol_upper = symbol.upper()
    coingecko_id = symbol_mapping.get(symbol_upper)
    if not coingecko_id:
        return None
    
    return query_coingecko_price(coingecko_id, timestamp)


def query_coingecko_price(coingecko_id: str, timestamp: int) -> Optional[float]:
    """
    Query CoinGecko API for historical price
    
    Args:
        coingecko_id: CoinGecko coin ID (e.g., 'bitcoin', 'ethereum')
        timestamp: Unix timestamp
    
    Returns:
        Price in USD or None if not found
    """
    try:
        date_str = datetime.fromtimestamp(timestamp).strftime('%d-%m-%Y')
        url = f"https://api.coingecko.com/api/v3/coins/{coingecko_id}/history"
        params = {'date': date_str}
        
        time.sleep(0.5)  # Rate limit for free API
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'market_data' in data and 'current_price' in data['market_data']:
                return float(data['market_data']['current_price']['usd'])
        elif response.status_code == 429:
            # Rate limited - can't use cache from different date (would be wrong price)
            print(f"  ⚠ Rate limited for {coingecko_id} on {date_str} - will retry or mark unavailable")
            # Don't use cached price from different date - better to mark as unavailable
            # than use wrong price
        else:
            print(f"  ⚠ CoinGecko API error for {coingecko_id}: {response.status_code}")
    except Exception as e:
        print(f"  ⚠ Exception querying CoinGecko for {coingecko_id}: {e}")
    
    return None


def get_cache_key(symbol: str, timestamp: int) -> str:
    """
    Generate cache key for historical price: symbol_date
    
    Args:
        symbol: Cryptocurrency symbol
        timestamp: Unix timestamp
    
    Returns:
        Cache key string
    """
    date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
    return f"{symbol.upper()}_{date_str}"

