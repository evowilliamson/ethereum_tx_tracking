"""
Fetch all EVM transactions for a given address using Etherscan-compatible API
Works with Ethereum, Base, Arbitrum, Optimism, Polygon, Avalanche, BSC, Linea, Katana, Monad
Fetches: normal transactions, ERC-20 transfers, and internal transactions
"""

import requests
import time
import json
import sys
from typing import List, Dict, Optional
from ethereum_config import RATE_LIMIT_DELAY
from chains_config import get_chain_config


class EthereumTransactionFetcher:
    """Fetches all transaction data from Etherscan-compatible API (supports all EVM chains)"""
    
    def __init__(self, api_key: str, address: str, chain_name: str = 'ethereum'):
        """
        Initialize transaction fetcher for a specific chain
        
        Args:
            api_key: API key for the explorer (Etherscan, Basescan, etc.)
                     Can be a dict with chain-specific keys, or a single key (fallback)
            address: Wallet address to fetch transactions for
            chain_name: Chain name (e.g., 'ethereum', 'base', 'arbitrum')
        """
        self.address = address
        self.chain_name = chain_name.lower()
        
        # Get chain-specific API key if api_key is a dict, otherwise use provided key
        if isinstance(api_key, dict):
            self.api_key = api_key.get(self.chain_name, api_key.get('ethereum', 'YOUR_API_KEY_HERE'))
        else:
            self.api_key = api_key
        
        # Load chain configuration
        try:
            chain_config = get_chain_config(self.chain_name)
            self.base_url = chain_config['api_base']
            self.chain_id = chain_config['chain_id']
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        
    def _make_request(self, params: Dict) -> Optional[List[Dict]]:
        """Make a request to explorer API V2 with rate limiting"""
        params['apikey'] = self.api_key
        params['address'] = self.address
        # Only add chainid for V2 API (BSCScan uses V1 API without chainid)
        if '/v2/api' in self.base_url:
            params['chainid'] = self.chain_id
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            time.sleep(RATE_LIMIT_DELAY)  # Respect rate limit
            
            if response.status_code != 200:
                print(f"HTTP Error {response.status_code}: {response.text}")
                return None
            
            data = response.json()
            
            result = data.get('result', [])
            message = data.get('message', '')
            status = data.get('status')
            
            # Check if we got results despite status 0 (some APIs return data with status 0)
            if isinstance(result, list) and len(result) > 0:
                # We have data, return it even if status is 0
                return result
            
            if status == '0':
                if 'rate limit' in message.lower():
                    print("Rate limit hit, waiting 5 seconds...")
                    time.sleep(5)
                    return self._make_request(params)  # Retry
                elif 'No transactions found' in message or 'No records found' in message:
                    return []  # Empty result, not an error
                elif 'Invalid API Key' in message:
                    print(f"ERROR: Invalid API Key! Please check your Etherscan API key.")
                    return None
                elif 'Max rate limit reached' in message:
                    print(f"ERROR: Rate limit exceeded. Please wait and try again later.")
                    return None
                elif 'free api access is not supported' in message.lower() or 'upgrade your api plan' in message.lower():
                    # BSC requires paid plan - check if result has data anyway (user might have paid plan)
                    if isinstance(result, list) and len(result) > 0:
                        return result
                    # If no results, it's likely the API key doesn't have BSC access
                    print(f"  Note: BSC requires paid Etherscan API plan. Your key may not have BSC access.")
                    return []
                elif 'deprecated' in message.lower() or (self.chain_name == 'binance' and message == 'NOTOK'):
                    # BSCScan V1 API is deprecated but still works - ignore the warning
                    # For BSCScan, "NOTOK" might just mean no results (need separate API key)
                    # Check if we got results despite the deprecation/NOTOK message
                    if isinstance(result, list) and len(result) > 0:
                        return result
                    # If no results, treat as empty (might need separate BSCScan API key)
                    return []
                else:
                    # Check if we still got results despite status 0
                    if isinstance(result, list) and len(result) > 0:
                        return result
                    print(f"API Error: {message}")
                    return None
            
            # Handle case where result is a string (error message)
            if isinstance(result, str):
                if 'rate limit' in result.lower():
                    print("Rate limit in result, waiting...")
                    time.sleep(5)
                    return self._make_request(params)
                if 'deprecated' in result.lower():
                    print(f"  Warning: API returned deprecation message")
                    return []
                # For paid plan required messages, the API might still return data
                # Check if there's actual error content or just a warning
                if 'free api access is not supported' in result.lower() or 'upgrade your api plan' in result.lower():
                    # This is just an informational message - return empty, data would be in result list if available
                    # The actual transactions would be in a list format, not a string
                    return []
                return []
            
            return result if isinstance(result, list) else []
            
        except Exception as e:
            print(f"Request error: {e}")
            return None
    
    def fetch_transactions(self, action: str, startblock: int = 0, 
                          endblock: int = 99999999, page: int = 1, 
                          offset: int = 10000, sort: str = 'asc') -> List[Dict]:
        """
        Fetch transactions with pagination
        
        Args:
            action: 'txlist' (normal), 'tokentx' (ERC-20), 'txlistinternal' (internal)
            startblock: Starting block number
            endblock: Ending block number
            page: Page number
            offset: Number of results per page (max 10000)
            sort: 'asc' or 'desc'
        """
        params = {
            'module': 'account',
            'action': action,
            'startblock': startblock,
            'endblock': endblock,
            'page': page,
            'offset': offset,
            'sort': sort
        }
        
        return self._make_request(params) or []
    
    def fetch_all_transactions(self, action: str) -> List[Dict]:
        """Fetch all transactions with automatic pagination"""
        all_txs = []
        page = 1
        
        print(f"\nFetching {action} transactions...")
        
        while True:
            print(f"  Page {page}...", end=' ', flush=True)
            txs = self.fetch_transactions(action, page=page)
            
            if txs is None:
                print("\nERROR: Failed to fetch transactions. Check API key and network connection.")
                break
            
            if len(txs) == 0:
                if page == 1:
                    print("No transactions found for this address.")
                else:
                    print("No more transactions.")
                break
            
            all_txs.extend(txs)
            print(f"Got {len(txs)} transactions (total: {len(all_txs)})")
            
            # If we got less than the max, we're done
            if len(txs) < 10000:
                break
            
            page += 1
        
        print(f"✓ Retrieved {len(all_txs)} {action} transactions total\n")
        return all_txs
    
    def fetch_all_data(self) -> Dict:
        """Fetch all transaction types for the address"""
        print(f"Fetching all transactions for address: {self.address}")
        print("=" * 60)
        
        # Fetch normal transactions
        normal_txs = self.fetch_all_transactions('txlist')
        
        # Fetch ERC-20 token transfers
        erc20_txs = self.fetch_all_transactions('tokentx')
        
        # Fetch internal transactions
        internal_txs = self.fetch_all_transactions('txlistinternal')
        
        return {
            "address": self.address,
            "normal_transactions": normal_txs,
            "erc20_token_transfers": erc20_txs,
            "internal_transactions": internal_txs,
            "metadata": {
                "total_normal": len(normal_txs),
                "total_erc20": len(erc20_txs),
                "total_internal": len(internal_txs),
                "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            }
        }


def main():
    """Main function to fetch transactions"""
    if len(sys.argv) < 3:
        print("Usage: python fetch_ethereum_transactions.py <API_KEY> <ADDRESS> [OUTPUT_FILE]")
        print("\nExample:")
        print("  python fetch_ethereum_transactions.py YOUR_API_KEY 0xYourAddress wallet_trades.json")
        sys.exit(1)
    
    api_key = sys.argv[1]
    address = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else "wallet_trades.json"
    
    if not address.startswith('0x') or len(address) != 42:
        print("Error: Invalid Ethereum address format")
        sys.exit(1)
    
    fetcher = EthereumTransactionFetcher(api_key, address)
    data = fetcher.fetch_all_data()
    
    # Save to file
    print(f"\nSaving data to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✓ Data saved successfully!")
    print(f"\nSummary:")
    print(f"  Normal transactions: {data['metadata']['total_normal']}")
    print(f"  ERC-20 transfers: {data['metadata']['total_erc20']}")
    print(f"  Internal transactions: {data['metadata']['total_internal']}")
    print(f"\nNext step: Run extract_ethereum_trades.py to identify DEX swaps")


if __name__ == "__main__":
    main()

