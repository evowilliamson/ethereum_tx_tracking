"""
Enrich trade data with token metadata (names, symbols, decimals)
Uses Etherscan API to fetch token information
"""

import json
import sys
import requests
import time
from typing import Dict, Optional
from collections import defaultdict
from ethereum_config import ETHERSCAN_API_BASE, RATE_LIMIT_DELAY, ETH_ADDRESS, WETH_ADDRESS
from known_tokens import KNOWN_TOKENS
from chains_config import is_evm_chain


class TokenMetadataFetcher:
    """Fetches token metadata from Etherscan API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = ETHERSCAN_API_BASE
        self.cache = {}
        
        # Common tokens cache
        self.cache[ETH_ADDRESS.lower()] = {
            'name': 'Ethereum',
            'symbol': 'ETH',
            'decimals': 18
        }
        self.cache[WETH_ADDRESS.lower()] = {
            'name': 'Wrapped Ether',
            'symbol': 'WETH',
            'decimals': 18
        }
    
    def fetch_token_info(self, token_address: str) -> Optional[Dict]:
        """Fetch token name, symbol, and decimals from Etherscan"""
        token_address = token_address.lower()
        
        # Check cache
        if token_address in self.cache:
            return self.cache[token_address]
        
        # Check known tokens first (fallback)
        if token_address in KNOWN_TOKENS:
            token_info = KNOWN_TOKENS[token_address].copy()
            self.cache[token_address] = token_info
            return token_info
        
        # Skip zero address (native token)
        eth_address = '0x0000000000000000000000000000000000000000'
        if token_address == eth_address.lower():
            return self.cache[eth_address.lower()]
        
        try:
            params = {
                'module': 'token',
                'action': 'tokeninfo',
                'contractaddress': token_address,
                'apikey': self.api_key
            }
            
            # Add chainid for V2 API if available
            if hasattr(self, 'chain_id') and self.chain_id:
                params['chainid'] = self.chain_id
            
            response = requests.get(self.base_url, params=params, timeout=30)
            time.sleep(RATE_LIMIT_DELAY)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == '1' and data.get('result'):
                    result = data['result'][0] if isinstance(data['result'], list) else data['result']
                    
                    # Try to get decimals from multiple fields
                    decimals = 18  # default
                    if 'divisor' in result:
                        decimals = int(result.get('divisor', 18))
                    elif 'decimals' in result:
                        decimals = int(result.get('decimals', 18))
                    elif 'tokenDecimal' in result:
                        decimals = int(result.get('tokenDecimal', 18))
                    
                    token_info = {
                        'name': result.get('tokenName', 'Unknown'),
                        'symbol': result.get('symbol', 'UNKNOWN'),
                        'decimals': decimals
                    }
                    
                    self.cache[token_address] = token_info
                    return token_info
        except Exception as e:
            print(f"  Warning: Could not fetch info for {token_address}: {e}")
        
        # Return default if fetch fails
        default = {
            'name': 'Unknown Token',
            'symbol': 'UNKNOWN',
            'decimals': 18
        }
        self.cache[token_address] = default
        return default
    
    def format_amount(self, amount_str: str, decimals: int) -> str:
        """Format token amount from wei to human-readable"""
        try:
            amount = int(amount_str)
            divisor = 10 ** decimals
            formatted = amount / divisor
            return f"{formatted:.{min(decimals, 8)}f}".rstrip('0').rstrip('.')
        except:
            return amount_str


def get_token_metadata_fetcher(chain_name: str, api_key: str):
    """
    Get appropriate token metadata fetcher for the chain
    
    Args:
        chain_name: Chain name
        api_key: API key or RPC endpoint
    
    Returns:
        TokenMetadataFetcher instance
    """
    if is_evm_chain(chain_name):
        return TokenMetadataFetcher(api_key)
    elif chain_name == 'solana':
        return SolanaTokenMetadataFetcher(api_key)
    elif chain_name == 'sui':
        return SuiTokenMetadataFetcher(api_key)
    else:
        # Default to EVM fetcher
        return TokenMetadataFetcher(api_key)


class SolanaTokenMetadataFetcher:
    """Fetches token metadata from Solana RPC"""
    
    def __init__(self, rpc_endpoint: str):
        self.rpc_endpoint = rpc_endpoint
        self.cache = {}
        
        # Common tokens cache
        sol_mint = 'So11111111111111111111111111111111111111112'  # Wrapped SOL
        self.cache[sol_mint.lower()] = {
            'name': 'Solana',
            'symbol': 'SOL',
            'decimals': 9
        }
    
    def fetch_token_info(self, mint_address: str) -> Optional[Dict]:
        """Fetch token metadata from Solana RPC"""
        mint_address_lower = mint_address.lower()
        
        # Check cache
        if mint_address_lower in self.cache:
            return self.cache[mint_address_lower]
        
        # For Solana, we can query the mint account for decimals
        # Name and symbol typically come from token lists or metadata
        try:
            import requests
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getAccountInfo",
                "params": [
                    mint_address,  # Use original case for RPC call
                    {
                        "encoding": "jsonParsed"
                    }
                ]
            }
            
            response = requests.post(self.rpc_endpoint, json=payload, timeout=10)
            time.sleep(0.25)
            
            if response.status_code == 200:
                data = response.json()
                if 'result' in data and data['result']:
                    account_data = data['result'].get('value', {})
                    parsed = account_data.get('data', {}).get('parsed', {})
                    info = parsed.get('info', {})
                    
                    decimals = info.get('decimals', 9)
                    
                    token_info = {
                        'name': f"Token {mint_address[:8]}",
                        'symbol': f"TOKEN{mint_address[:4].upper()}",
                        'decimals': decimals
                    }
                    
                    self.cache[mint_address_lower] = token_info
                    return token_info
        except Exception as e:
            pass
        
        # Return default
        default = {
            'name': 'Unknown Token',
            'symbol': 'UNKNOWN',
            'decimals': 9  # Solana default
        }
        self.cache[mint_address_lower] = default
        return default
    
    def format_amount(self, amount_str: str, decimals: int) -> str:
        """Format token amount from lamports to human-readable"""
        try:
            amount = int(amount_str)
            divisor = 10 ** decimals
            formatted = amount / divisor
            return f"{formatted:.{min(decimals, 8)}f}".rstrip('0').rstrip('.')
        except:
            return amount_str


class SuiTokenMetadataFetcher:
    """Fetches token metadata from Sui RPC"""
    
    def __init__(self, rpc_endpoint: str):
        self.rpc_endpoint = rpc_endpoint
        self.cache = {}
        
        # Common tokens cache
        sui_coin_type = '0x2::sui::SUI'
        self.cache[sui_coin_type.lower()] = {
            'name': 'Sui',
            'symbol': 'SUI',
            'decimals': 9
        }
    
    def fetch_token_info(self, coin_type: str) -> Optional[Dict]:
        """Fetch token metadata from Sui RPC"""
        coin_type = coin_type.lower()
        
        # Check cache
        if coin_type in self.cache:
            return self.cache[coin_type]
        
        # For Sui, coin types are in format: 0x...::TOKEN::TOKEN
        # We can extract symbol from the coin type
        try:
            if '::' in coin_type:
                parts = coin_type.split('::')
                if len(parts) >= 3:
                    symbol = parts[-1].rstrip('>').upper()
                    name = f"{symbol} Token"
                    
                    # Default decimals for Sui coins
                    decimals = 9
                    
                    token_info = {
                        'name': name,
                        'symbol': symbol,
                        'decimals': decimals
                    }
                    
                    self.cache[coin_type] = token_info
                    return token_info
        except Exception as e:
            pass
        
        # Return default
        default = {
            'name': 'Unknown Token',
            'symbol': 'UNKNOWN',
            'decimals': 9  # Sui default
        }
        self.cache[coin_type] = default
        return default
    
    def format_amount(self, amount_str: str, decimals: int) -> str:
        """Format token amount to human-readable"""
        try:
            amount = int(amount_str)
            divisor = 10 ** decimals
            formatted = amount / divisor
            return f"{formatted:.{min(decimals, 8)}f}".rstrip('0').rstrip('.')
        except:
            return amount_str


def enrich_trades(input_file: str, output_file: str, api_key: str, transaction_data_file: str = None, chain_name: str = 'ethereum'):
    """Enrich trades with token metadata
    
    Args:
        input_file: Parsed trades JSON file
        output_file: Output enriched trades JSON file
        api_key: API key for token metadata (optional, used as fallback)
        transaction_data_file: Optional path to raw transaction data (wallet_trades_*.json)
                              If provided, token metadata will be extracted from ERC20 transfers
        chain_name: Chain name (for chain-specific config)
    """
    print("Loading trades...")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    trades = data.get('trades', [])
    if not trades:
        print("No trades found to enrich")
        return
    
    print(f"Enriching {len(trades)} trades with token metadata...")
    print("=" * 60)
    
    # First, try to extract token metadata from transaction data (if available)
    token_metadata = {}
    if transaction_data_file:
        try:
            print("Extracting token metadata from transaction data...")
            with open(transaction_data_file, 'r') as f:
                tx_data = json.load(f)
            
            # Extract from ERC20 token transfers (they contain tokenName, tokenSymbol, tokenDecimal)
            erc20_transfers = tx_data.get('erc20_token_transfers', [])
            for tx in erc20_transfers:
                addr = tx.get('contractAddress', '').lower()
                if addr and addr not in token_metadata:
                    # Check if token info exists in transfer
                    if tx.get('tokenName') or tx.get('tokenSymbol'):
                        token_metadata[addr] = {
                            'name': tx.get('tokenName', 'Unknown'),
                            'symbol': tx.get('tokenSymbol', 'UNKNOWN'),
                            'decimals': int(tx.get('tokenDecimal', 18))
                        }
            
            if token_metadata:
                print(f"✓ Extracted metadata for {len(token_metadata)} tokens from transaction data")
        except Exception as e:
            print(f"  Warning: Could not extract from transaction data: {e}")
    
    fetcher = get_token_metadata_fetcher(chain_name, api_key)
    
    # Collect unique token addresses from trades
    token_addresses = set()
    for trade in trades:
        token_addresses.add(trade.get('token_in', '').lower())
        token_addresses.add(trade.get('token_out', '').lower())
    
    token_addresses.discard('')  # Remove empty addresses
    print(f"Found {len(token_addresses)} unique tokens")
    
    # Only fetch metadata for tokens we don't already have
    missing_tokens = [addr for addr in token_addresses if addr not in token_metadata]
    if missing_tokens:
        print(f"Fetching metadata for {len(missing_tokens)} remaining tokens...")
        for i, token_addr in enumerate(missing_tokens, 1):
            print(f"  [{i}/{len(missing_tokens)}] Fetching {token_addr[:10]}...", end=' ', flush=True)
            metadata = fetcher.fetch_token_info(token_addr)
            if metadata:
                token_metadata[token_addr] = metadata
                print(f"✓ {metadata['symbol']}")
            else:
                print("✗ Failed")
    else:
        print("✓ All token metadata found in transaction data")
    
    # Enrich trades
    print("\nEnriching trades...")
    enriched_trades = []
    for trade in trades:
        token_in_addr = trade.get('token_in', '').lower()
        token_out_addr = trade.get('token_out', '').lower()
        
        token_in_meta = token_metadata.get(token_in_addr, {})
        token_out_meta = token_metadata.get(token_out_addr, {})
        
        enriched_trade = trade.copy()
        enriched_trade['token_in_metadata'] = {
            'address': token_in_addr,
            'name': token_in_meta.get('name', 'Unknown'),
            'symbol': token_in_meta.get('symbol', 'UNKNOWN'),
            'decimals': token_in_meta.get('decimals', 18)
        }
        enriched_trade['token_out_metadata'] = {
            'address': token_out_addr,
            'name': token_out_meta.get('name', 'Unknown'),
            'symbol': token_out_meta.get('symbol', 'UNKNOWN'),
            'decimals': token_out_meta.get('decimals', 18)
        }
        
        # Add formatted amounts
        decimals_in = token_in_meta.get('decimals', 18)
        decimals_out = token_out_meta.get('decimals', 18)
        enriched_trade['amount_in_formatted'] = fetcher.format_amount(
            trade.get('amount_in', '0'), decimals_in
        )
        enriched_trade['amount_out_formatted'] = fetcher.format_amount(
            trade.get('amount_out', '0'), decimals_out
        )
        
        enriched_trades.append(enriched_trade)
    
    # Update data
    data['trades'] = enriched_trades
    data['metadata']['enriched'] = True
    data['metadata']['tokens_fetched'] = len(token_metadata)
    
    # Save enriched data
    print(f"\nSaving enriched trades to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✓ Enriched {len(enriched_trades)} trades")
    print(f"✓ Fetched metadata for {len(token_metadata)} tokens")


def main():
    """Main function"""
    if len(sys.argv) < 3:
        print("Usage: python enrich_trades_with_tokens.py <API_KEY> <TRADES_FILE> [OUTPUT_FILE]")
        print("\nExample:")
        print("  python enrich_trades_with_tokens.py YOUR_API_KEY ethereum_trades.json enriched_trades.json")
        sys.exit(1)
    
    api_key = sys.argv[1]
    input_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else input_file.replace('.json', '_enriched.json')
    
    enrich_trades(input_file, output_file, api_key)


if __name__ == "__main__":
    main()

