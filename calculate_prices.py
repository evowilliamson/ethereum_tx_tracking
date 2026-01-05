#!/usr/bin/env python3
"""
Calculate USD prices for all trades
Uses multiple strategies to ensure tax services have USD valuations
"""

import json
import requests
import time
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict

# CoinGecko integration
from coingecko import (
    refresh_symbol_mapping,
    load_symbol_mapping,
    get_historical_price,
    get_cache_key,
    DEFAULT_MAPPING_FILE,
    DEFAULT_CACHE_FILE
)

# Stablecoins - extended list for cache window optimization and fallback pricing
# We get actual prices from CoinGecko, but use this list to:
# 1. Apply longer cache window (5 min vs 1 min) for stablecoins
# 2. Fallback to $1.00 if CoinGecko fails for a stablecoin
STABLECOINS = {
    # Major USD stablecoins
    'USDC', 'USDT', 'DAI', 'BUSD', 'USDP', 'TUSD', 'USDD', 'FRAX', 'LUSD', 
    'GUSD', 'HUSD', 'SUSD', 'MIM', 'OUSD', 'FEI', 'USD3', 'NUSD', 'AUSD', 'USN',
    # Additional USD stablecoins
    'USDE',      # Ethena USDe
    'PYUSD',     # PayPal USD
    'CRVUSD',    # Curve USD
    'DOLA',      # Inverse Finance DOLA
    'USDX',      # dForce USDx
    'USX',       # Tokenized USD
    'USDR',      # Real USD
    'CUSD',      # Celo Dollar
    'CEUR',      # Celo Euro
    'EURS',      # STASIS Euro
    'EURT',      # Tether Euro
    'AGEUR',     # Angle Protocol agEUR
    'IDRT',      # Rupiah Token
    'BIDR',      # Binance IDR
    'TRYB',      # BiLira
    'XAUT',      # Tether Gold
    'PAXG',      # PAX Gold
    # Algorithmic stablecoins
    'UST',       # TerraUSD (historical)
    'KUSD',      # Kolibri USD
    # Regional stablecoins
    'BRLT',      # Tether Brazilian Real
    'CNHT',      # Tether Chinese Yuan Offshore
    'XAUD',      # Australian Dollar Token
    'XCAD',      # Canadian Dollar Token
    'XCHF',      # Swiss Franc Token
    'XCNY',      # Chinese Yuan Token
    'XEUR',      # Euro Token
    'XGBP',      # British Pound Token
    'XJPY',      # Japanese Yen Token
    'XKRW',      # South Korean Won Token
    'XPLN',      # Polish Zloty Token
    'XSEK',      # Swedish Krona Token
    'XSGD',      # Singapore Dollar Token
}


class PriceFeedBuilder:
    """Builds a price feed from trades and external APIs"""
    
    CACHE_FILE = DEFAULT_CACHE_FILE
    MAPPING_FILE = DEFAULT_MAPPING_FILE
    
    def __init__(self):
        self.symbol_mapping = refresh_symbol_mapping(self.MAPPING_FILE)  # {symbol: coin_id} - refreshed on every flow start
        self.price_cache = self._load_price_cache()  # {symbol: {'price': float, 'timestamp': int}}
        
    def is_stablecoin(self, symbol: str) -> bool:
        """Check if token is a stablecoin"""
        return symbol.upper() in STABLECOINS
    
    def _load_price_cache(self) -> Dict:
        """Load price cache from file"""
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_price_cache(self):
        """Save price cache to file"""
        try:
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(self.price_cache, f, indent=2)
        except Exception:
            pass  # Silently fail if can't save cache
    
    def _get_cache_key(self, symbol: str, timestamp: int) -> str:
        """Generate cache key for historical price: symbol_date"""
        return get_cache_key(symbol, timestamp)
    
    def get_coingecko_price(self, symbol: str, timestamp: int) -> Optional[float]:
        """Get historical price from CoinGecko with file-based caching by date"""
        symbol_upper = symbol.upper()
        cache_key = self._get_cache_key(symbol_upper, timestamp)
        
        # Check cache first - same date = same price (no time window needed)
        if cache_key in self.price_cache:
            cached_price = self.price_cache[cache_key]
            if cached_price is not None:
                return float(cached_price)
        
        # Cache miss, query CoinGecko
        price = get_historical_price(symbol_upper, timestamp, self.symbol_mapping)
        
        # Update cache if we got a price (cache by date, not timestamp)
        if price is not None:
            self.price_cache[cache_key] = price
            self._save_price_cache()
        
        return price
    
    def extract_underlying_asset(self, protocol_token: str) -> Optional[str]:
        """
        Extract underlying asset from protocol token symbol
        Examples:
        - PT-nBASIS-26MAR2026 -> nBASIS
        - PT-iUSD-4DEC2025 -> iUSD
        - aEthUSDC -> USDC
        - fGHO -> GHO
        """
        # Pendle PT tokens: PT-ASSET-DATE -> ASSET
        if protocol_token.startswith('PT-'):
            parts = protocol_token.split('-')
            if len(parts) >= 2:
                return parts[1]  # Return the asset part
        
        # Aave tokens: aEthASSET -> ASSET, aASSET -> ASSET
        if protocol_token.startswith('aEth'):
            return protocol_token[4:]  # Remove 'aEth' prefix
        if protocol_token.startswith('a') and len(protocol_token) > 1:
            return protocol_token[1:]  # Remove 'a' prefix
        
        # Other patterns
        if protocol_token.startswith('f'):  # fUSDC, fGHO
            return protocol_token[1:]
        
        return None
    
    def calculate_prices_for_trade(self, trade: Dict) -> Tuple[Optional[float], Optional[float], str]:
        """
        Calculate USD prices for a trade using CoinGecko as primary source
        Returns: (source_price_usd, target_price_usd, price_source)
        price_source: "coingecko", "coingecko_with_ratio", "stablecoin_ratio", "unavailable"
        
        Strategy priority:
        1. CoinGecko for both tokens (primary)
        2. CoinGecko for one token + swap ratio for other (fallback)
        3. Stablecoin = $1.00 + swap ratio (last resort if CoinGecko fails for stablecoin)
        4. Unavailable (if no options)
        """
        token_in_meta = trade.get('token_in_metadata', {})
        token_out_meta = trade.get('token_out_metadata', {})
        
        source_symbol = token_in_meta.get('symbol', '')
        target_symbol = token_out_meta.get('symbol', '')
        
        source_amount = float(trade.get('amount_in_formatted', '0'))
        target_amount = float(trade.get('amount_out_formatted', '0'))
        timestamp = trade.get('timestamp', 0)
        
        # Strategy 1: Try CoinGecko for both tokens (primary)
        source_price = self.get_coingecko_price(source_symbol, timestamp)
        target_price = self.get_coingecko_price(target_symbol, timestamp)
        
        # Case 1: Both found in CoinGecko
        if source_price and target_price:
            return source_price, target_price, "coingecko"
        
        # Case 2: Source found, target not found - calculate target from swap ratio
        if source_price and not target_price:
            if source_amount > 0 and target_amount > 0:
                target_price = (source_amount / target_amount) * source_price
                return source_price, target_price, "coingecko_with_ratio"
        
        # Case 3: Target found, source not found - calculate source from swap ratio
        if target_price and not source_price:
            if source_amount > 0 and target_amount > 0:
                source_price = (target_amount / source_amount) * target_price
                return source_price, target_price, "coingecko_with_ratio"
        
        # Case 4: Both not found - check if one is stablecoin
        if not source_price and not target_price:
            # Check if source is stablecoin - try CoinGecko specifically for it
            if self.is_stablecoin(source_symbol):
                source_price = self.get_coingecko_price(source_symbol, timestamp)
                if source_price:
                    # Got stablecoin price from CoinGecko, calculate target
                    if source_amount > 0 and target_amount > 0:
                        target_price = (source_amount / target_amount) * source_price
                        return source_price, target_price, "coingecko_with_ratio"
                else:
                    # CoinGecko failed for stablecoin, assume $1.00
                    source_price = 1.0
                    if source_amount > 0 and target_amount > 0:
                        target_price = source_amount / target_amount
                        return source_price, target_price, "stablecoin_ratio"
            
            # Check if target is stablecoin - try CoinGecko specifically for it
            elif self.is_stablecoin(target_symbol):
                target_price = self.get_coingecko_price(target_symbol, timestamp)
                if target_price:
                    # Got stablecoin price from CoinGecko, calculate source
                    if source_amount > 0 and target_amount > 0:
                        source_price = (target_amount / source_amount) * target_price
                        return source_price, target_price, "coingecko_with_ratio"
                else:
                    # CoinGecko failed for stablecoin, assume $1.00
                    target_price = 1.0
                    if source_amount > 0 and target_amount > 0:
                        source_price = target_amount / source_amount
                        return source_price, target_price, "stablecoin_ratio"
            
            # Neither is stablecoin, no prices available
            return None, None, "unavailable"
        
        # Should not reach here, but return unavailable as fallback
        return None, None, "unavailable"


def add_prices_to_trades(enriched_json_file: str, output_json_file: str):
    """Add USD prices to enriched trades"""
    print("\nCalculating USD prices for all trades...")
    print("-" * 60)
    
    # Load enriched trades
    with open(enriched_json_file, 'r') as f:
        data = json.load(f)
    
    trades = data.get('trades', [])
    if not trades:
        print("No trades to price")
        return
    
    price_builder = PriceFeedBuilder()
    
    # Calculate prices for each trade
    priced_count = 0
    unavailable_count = 0
    price_sources = defaultdict(int)
    
    for trade in trades:
        source_price, target_price, price_source = price_builder.calculate_prices_for_trade(trade)
        
        trade['source_price_usd'] = source_price
        trade['target_price_usd'] = target_price
        trade['price_source'] = price_source
        
        if source_price and target_price:
            priced_count += 1
        else:
            unavailable_count += 1
        
        price_sources[price_source] += 1
    
    # Save updated trades
    with open(output_json_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\nPrice calculation summary:")
    print(f"  ✓ Priced: {priced_count} trades")
    print(f"  ⚠ Unavailable: {unavailable_count} trades")
    print(f"\nPrice sources:")
    for source, count in sorted(price_sources.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python calculate_prices.py <enriched_json_file> [output_json_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.json', '_priced.json')
    
    add_prices_to_trades(input_file, output_file)

