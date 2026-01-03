#!/usr/bin/env python3
"""
Calculate USD prices for all trades
Uses multiple strategies to ensure tax services have USD valuations
"""

import json
import requests
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

# Stablecoins that should be priced at $1
STABLECOINS = {'USDC', 'USDT', 'DAI', 'BUSD', 'USDP', 'TUSD', 'USDD', 'FRAX', 'LUSD', 'USD3', 'NUSD', 'AUSD', 'USN'}

# Protocol stablecoin derivatives (approximate $1, but may vary)
PROTOCOL_STABLECOINS = {
    'aEthUSDC', 'aUSDC', 'reUSDC', 'fUSDC', 'csUSDC', 'hyperUSDC', 'syrupUSDC',
    'aEthUSDT', 'syrupUSDT', 'stcUSD', 'siUSD', 'cUSD', 'reUSDe', 'iUSD'
}


class PriceFeedBuilder:
    """Builds a price feed from trades and external APIs"""
    
    def __init__(self):
        self.price_feed = {}  # token_address -> list of (timestamp, price) tuples
        self.symbol_to_addresses = {}  # symbol -> set of addresses (for lookup)
        self.coingecko_cache = {}  # symbol -> CoinGecko ID mapping
        
    def is_stablecoin(self, symbol: str) -> bool:
        """Check if token is a stablecoin"""
        return symbol.upper() in STABLECOINS
    
    def is_protocol_stablecoin(self, symbol: str) -> bool:
        """Check if token is a protocol stablecoin derivative"""
        return symbol in PROTOCOL_STABLECOINS
    
    def calculate_price_from_trade(self, trade: Dict) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculate USD prices from trade if one side is a stablecoin
        Returns: (source_price_usd, target_price_usd)
        """
        token_in_meta = trade.get('token_in_metadata', {})
        token_out_meta = trade.get('token_out_metadata', {})
        
        source_symbol = token_in_meta.get('symbol', '').upper()
        target_symbol = token_out_meta.get('symbol', '').upper()
        
        source_amount = float(trade.get('amount_in_formatted', '0'))
        target_amount = float(trade.get('amount_out_formatted', '0'))
        
        if source_amount == 0 or target_amount == 0:
            return None, None
        
        source_price = None
        target_price = None
        
        # If source is stablecoin
        if self.is_stablecoin(source_symbol):
            source_price = 1.0
            target_price = source_amount / target_amount if target_amount > 0 else None
        
        # If target is stablecoin
        elif self.is_stablecoin(target_symbol):
            target_price = 1.0
            source_price = target_amount / source_amount if source_amount > 0 else None
        
        # If source is protocol stablecoin (approximate $1)
        elif self.is_protocol_stablecoin(source_symbol):
            source_price = 1.0  # Approximate
            target_price = source_amount / target_amount if target_amount > 0 else None
        
        # If target is protocol stablecoin
        elif self.is_protocol_stablecoin(target_symbol):
            target_price = 1.0  # Approximate
            source_price = target_amount / source_amount if source_amount > 0 else None
        
        return source_price, target_price
    
    def get_coingecko_price(self, symbol: str, timestamp: int) -> Optional[float]:
        """Get historical price from CoinGecko (free API, no key needed)"""
        # Map common symbols to CoinGecko IDs
        symbol_to_id = {
            'ETH': 'ethereum',
            'WETH': 'ethereum',  # WETH price = ETH price
            'WBTC': 'wrapped-bitcoin',
            'BTC': 'wrapped-bitcoin',
            'COMP': 'compound-governance-token',
            'AAVE': 'aave',
            'UNI': 'uniswap',
            'LINK': 'chainlink',
            'CRV': 'curve-dao-token',
            'SUSHI': 'sushi',
            'MKR': 'maker',
            'SNX': 'synthetix-network-token',
            'YFI': 'yearn-finance',
        }
        
        coingecko_id = symbol_to_id.get(symbol.upper())
        if not coingecko_id:
            return None
        
        # CoinGecko free API allows historical price queries
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
        except Exception as e:
            pass  # API failed, return None
        
        return None
    
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
    
    def find_price_in_feed(self, token_address: Optional[str], token_symbol: str, 
                          target_timestamp: int, max_hours: int = 720) -> Optional[float]:
        """
        Find price from price feed, looking for prices within max_hours of target timestamp
        Can search by address or symbol
        Default max_hours is 720 (30 days) to use prices from earlier trades
        If no price within window, uses closest available price (for protocol tokens)
        """
        # Try by address first
        if token_address and token_address in self.price_feed:
            prices = self.price_feed[token_address]
            if prices:
                best_price = None
                min_diff = float('inf')
                best_price_within_window = None
                min_diff_within_window = float('inf')
                
                for price_timestamp, price in prices:
                    time_diff = abs(price_timestamp - target_timestamp)
                    hours_diff = time_diff / 3600
                    
                    # Track best price within window
                    if hours_diff <= max_hours and time_diff < min_diff_within_window:
                        min_diff_within_window = time_diff
                        best_price_within_window = price
                    
                    # Also track closest price overall (for protocol tokens that rarely trade)
                    if time_diff < min_diff:
                        min_diff = time_diff
                        best_price = price
                
                # Prefer price within window, but fall back to closest if available
                # For protocol tokens, use closest price even if older (better than nothing)
                if best_price_within_window:
                    return best_price_within_window
                elif best_price:
                    # Use closest price even if outside window (for rare tokens)
                    return best_price
        
        # Try by symbol if address not found
        if token_symbol:
            symbol_upper = token_symbol.upper()
            if symbol_upper in self.symbol_to_addresses:
                best_price = None
                min_diff = float('inf')
                best_price_within_window = None
                min_diff_within_window = float('inf')
                
                for addr in self.symbol_to_addresses[symbol_upper]:
                    if addr in self.price_feed:
                        prices = self.price_feed[addr]
                        for price_timestamp, price in prices:
                            time_diff = abs(price_timestamp - target_timestamp)
                            hours_diff = time_diff / 3600
                            
                            if hours_diff <= max_hours and time_diff < min_diff_within_window:
                                min_diff_within_window = time_diff
                                best_price_within_window = price
                            
                            if time_diff < min_diff:
                                min_diff = time_diff
                                best_price = price
                
                if best_price_within_window:
                    return best_price_within_window
                elif best_price:
                    return best_price
        
        return None
    
    def build_price_feed(self, trades: List[Dict]):
        """
        Build price feed from all trades that have USD pairs
        Stores prices by token address and timestamp
        Also builds symbol -> address mapping for lookup
        Processes trades in chronological order to build feed progressively
        """
        print("\nBuilding price feed from trades...")
        
        # Sort trades by timestamp to process chronologically
        sorted_trades = sorted(trades, key=lambda t: t.get('timestamp', 0))
        
        for trade in sorted_trades:
            source_price, target_price = self.calculate_price_from_trade(trade)
            
            token_in_meta = trade.get('token_in_metadata', {})
            token_out_meta = trade.get('token_out_metadata', {})
            timestamp = trade.get('timestamp', 0)
            
            token_in_addr = token_in_meta.get('address', '').lower()
            token_out_addr = token_out_meta.get('address', '').lower()
            token_in_symbol = token_in_meta.get('symbol', '').upper()
            token_out_symbol = token_out_meta.get('symbol', '').upper()
            
            # Store prices in feed
            if source_price:
                if token_in_addr not in self.price_feed:
                    self.price_feed[token_in_addr] = []
                self.price_feed[token_in_addr].append((timestamp, source_price))
                
                # Map symbol to address
                if token_in_symbol:
                    if token_in_symbol not in self.symbol_to_addresses:
                        self.symbol_to_addresses[token_in_symbol] = set()
                    self.symbol_to_addresses[token_in_symbol].add(token_in_addr)
            
            if target_price:
                if token_out_addr not in self.price_feed:
                    self.price_feed[token_out_addr] = []
                self.price_feed[token_out_addr].append((timestamp, target_price))
                
                # Map symbol to address
                if token_out_symbol:
                    if token_out_symbol not in self.symbol_to_addresses:
                        self.symbol_to_addresses[token_out_symbol] = set()
                    self.symbol_to_addresses[token_out_symbol].add(token_out_addr)
        
        print(f"  ✓ Built price feed with {len(self.price_feed)} tokens")
    
    def calculate_prices_for_trade(self, trade: Dict) -> Tuple[Optional[float], Optional[float], str]:
        """
        Calculate USD prices for a trade using multiple strategies
        Returns: (source_price_usd, target_price_usd, price_source)
        price_source: "stablecoin", "feed", "coingecko", "derived", "unavailable"
        """
        # Strategy 1: Direct calculation from stablecoin trade
        source_price, target_price = self.calculate_price_from_trade(trade)
        if source_price and target_price:
            return source_price, target_price, "stablecoin"
        
        token_in_meta = trade.get('token_in_metadata', {})
        token_out_meta = trade.get('token_out_metadata', {})
        
        source_symbol = token_in_meta.get('symbol', '')
        target_symbol = token_out_meta.get('symbol', '')
        
        source_amount = float(trade.get('amount_in_formatted', '0'))
        target_amount = float(trade.get('amount_out_formatted', '0'))
        timestamp = trade.get('timestamp', 0)
        
        token_in_addr = token_in_meta.get('address', '').lower()
        token_out_addr = token_out_meta.get('address', '').lower()
        
        # Strategy 2: Try price feed with extended time window (30 days, or closest available)
        if not source_price:
            source_price = self.find_price_in_feed(token_in_addr, source_symbol, timestamp, max_hours=720)
        
        if not target_price:
            target_price = self.find_price_in_feed(token_out_addr, target_symbol, timestamp, max_hours=720)
        
        # If we have both prices, return immediately
        if source_price and target_price:
            return source_price, target_price, "feed"
        
        # Strategy 2b: If we have one price, calculate the other from exchange ratio
        if source_price and not target_price and source_amount > 0 and target_amount > 0:
            total_value_usd = source_price * source_amount
            target_price = total_value_usd / target_amount
            return source_price, target_price, "calculated_from_feed"
        
        if target_price and not source_price and source_amount > 0 and target_amount > 0:
            total_value_usd = target_price * target_amount
            source_price = total_value_usd / source_amount
            return source_price, target_price, "calculated_from_feed"
        
        # Strategy 3: Try CoinGecko for missing prices
        if not source_price:
            source_price = self.get_coingecko_price(source_symbol, timestamp)
        
        if not target_price:
            target_price = self.get_coingecko_price(target_symbol, timestamp)
        
        # If CoinGecko gave us both, return
        if source_price and target_price:
            return source_price, target_price, "coingecko"
        
        # Strategy 3b: If CoinGecko gave us one price, calculate the other
        if source_price and not target_price and source_amount > 0 and target_amount > 0:
            total_value_usd = source_price * source_amount
            target_price = total_value_usd / target_amount
            return source_price, target_price, "calculated_from_coingecko"
        
        if target_price and not source_price and source_amount > 0 and target_amount > 0:
            total_value_usd = target_price * target_amount
            source_price = total_value_usd / source_amount
            return source_price, target_price, "calculated_from_coingecko"
        
        # Strategy 4: Protocol token - try underlying asset from price feed
        if not source_price:
            underlying_source = self.extract_underlying_asset(source_symbol)
            if underlying_source:
                underlying_price = self.find_price_in_feed(None, underlying_source, timestamp)
                if underlying_price and source_amount > 0 and target_amount > 0:
                    # Calculate protocol token price from exchange ratio
                    exchange_ratio = target_amount / source_amount
                    if target_price:
                        source_price = target_price * exchange_ratio
                        return source_price, target_price, "derived"
                    else:
                        # Use underlying price as base
                        source_price = underlying_price * exchange_ratio
                        target_price = underlying_price
                        return source_price, target_price, "derived"
        
        if not target_price:
            underlying_target = self.extract_underlying_asset(target_symbol)
            if underlying_target:
                underlying_price = self.find_price_in_feed(None, underlying_target, timestamp)
                if underlying_price and source_amount > 0 and target_amount > 0:
                    exchange_ratio = source_amount / target_amount
                    if source_price:
                        target_price = source_price * exchange_ratio
                        return source_price, target_price, "derived"
                    else:
                        target_price = underlying_price * exchange_ratio
                        source_price = underlying_price
                        return source_price, target_price, "derived"
        
        # Strategy 5: If one price is known, calculate the other from ratio
        if source_price and source_amount > 0 and target_amount > 0:
            total_value_usd = source_price * source_amount
            target_price = total_value_usd / target_amount
            return source_price, target_price, "calculated"
        
        if target_price and source_amount > 0 and target_amount > 0:
            total_value_usd = target_price * target_amount
            source_price = total_value_usd / source_amount
            return source_price, target_price, "calculated"
        
        # No price available
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
    
    # Build initial price feed from trades with stablecoin pairs
    price_builder.build_price_feed(trades)
    
    # Sort trades chronologically to use earlier prices for later trades
    sorted_trades = sorted(trades, key=lambda t: t.get('timestamp', 0))
    
    # Calculate prices for each trade in chronological order
    priced_count = 0
    unavailable_count = 0
    price_sources = defaultdict(int)
    
    for trade in sorted_trades:
        source_price, target_price, price_source = price_builder.calculate_prices_for_trade(trade)
        
        # Store newly calculated prices in feed for future trades
        if source_price or target_price:
            token_in_meta = trade.get('token_in_metadata', {})
            token_out_meta = trade.get('token_out_metadata', {})
            timestamp = trade.get('timestamp', 0)
            
            token_in_addr = token_in_meta.get('address', '').lower()
            token_out_addr = token_out_meta.get('address', '').lower()
            token_in_symbol = token_in_meta.get('symbol', '').upper()
            token_out_symbol = token_out_meta.get('symbol', '').upper()
            
            if source_price and token_in_addr:
                if token_in_addr not in price_builder.price_feed:
                    price_builder.price_feed[token_in_addr] = []
                price_builder.price_feed[token_in_addr].append((timestamp, source_price))
                
                # Update symbol mapping
                if token_in_symbol:
                    if token_in_symbol not in price_builder.symbol_to_addresses:
                        price_builder.symbol_to_addresses[token_in_symbol] = set()
                    price_builder.symbol_to_addresses[token_in_symbol].add(token_in_addr)
            
            if target_price and token_out_addr:
                if token_out_addr not in price_builder.price_feed:
                    price_builder.price_feed[token_out_addr] = []
                price_builder.price_feed[token_out_addr].append((timestamp, target_price))
                
                # Update symbol mapping
                if token_out_symbol:
                    if token_out_symbol not in price_builder.symbol_to_addresses:
                        price_builder.symbol_to_addresses[token_out_symbol] = set()
                    price_builder.symbol_to_addresses[token_out_symbol].add(token_out_addr)
        
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

