"""
Fetch Sui transactions for a given address
Uses Sui GraphQL API for reliable pagination and filtering
"""

import requests
import time
import json
import sys
from typing import List, Dict, Optional
from blockchain_interface import BlockchainTransactionFetcher
from chains_config import get_chain_config


class SuiTransactionFetcher(BlockchainTransactionFetcher):
    """Fetches all transaction data from Sui GraphQL API"""
    
    GRAPHQL_ENDPOINT = "https://graphql.mainnet.sui.io/graphql"
    RPC_ENDPOINT = "https://fullnode.mainnet.sui.io:443"
    
    def __init__(self, api_key: str, address: str, chain_name: str = 'sui'):
        """
        Initialize transaction fetcher for Sui
        
        Args:
            api_key: Optional API key (not needed for public GraphQL)
            address: Sui wallet address (0x prefix, 66 chars)
            chain_name: Chain name (should be 'sui')
        """
        self.address = address
        self.chain_name = chain_name.lower()
        self.api_key = api_key
        
        # Use Tatum RPC for transaction details if API key provided
        if api_key and api_key.startswith('t-'):
            self.rpc_endpoint = 'https://sui-mainnet.gateway.tatum.io/'
            self.tatum_api_key = api_key
            print(f"Using Tatum RPC for transaction details")
        else:
            self.rpc_endpoint = self.RPC_ENDPOINT
            self.tatum_api_key = None
    
    def validate_address(self, address: str) -> bool:
        """Validate Sui address format (0x prefix, 66 chars total)"""
        if not address:
            return False
        if not address.startswith('0x'):
            return False
        if len(address) != 66:
            return False
        try:
            int(address, 16)
            return True
        except ValueError:
            return False
    
    def _make_graphql_request(self, query: str, retries: int = 3) -> Optional[Dict]:
        """Make a GraphQL request to Sui GraphQL endpoint"""
        headers = {'Content-Type': 'application/json'}
        
        for attempt in range(retries):
            try:
                response = requests.post(
                    self.GRAPHQL_ENDPOINT,
                    json={'query': query},
                    headers=headers,
                    timeout=60
                )
                time.sleep(0.2)  # Rate limiting
                
                if response.status_code != 200:
                    print(f"HTTP Error {response.status_code}: {response.text[:200]}")
                    if attempt < retries - 1:
                        time.sleep(2)
                        continue
                    return None
                
                data = response.json()
                
                if 'errors' in data:
                    print(f"GraphQL Error: {data['errors']}")
                    return None
                
                return data.get('data')
                
            except requests.exceptions.Timeout:
                print(f"Timeout on attempt {attempt + 1}/{retries}, retrying...")
                time.sleep(3)
            except Exception as e:
                print(f"Request error: {e}")
                if attempt < retries - 1:
                    time.sleep(2)
        
        return None
    
    def _make_rpc_request(self, method: str, params: List, retries: int = 3) -> Optional[Dict]:
        """Make a JSON-RPC request to Sui RPC endpoint (for transaction details)"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        headers = {
            'accept': 'application/json',
            'content-type': 'application/json'
        }
        
        if self.tatum_api_key:
            headers['x-api-key'] = self.tatum_api_key
        
        for attempt in range(retries):
            try:
                response = requests.post(self.rpc_endpoint, json=payload, headers=headers, timeout=60)
                time.sleep(0.3)
                
                if response.status_code != 200:
                    if attempt < retries - 1:
                        time.sleep(2)
                        continue
                    return None
                
                data = response.json()
                
                if 'error' in data:
                    return None
                
                return data.get('result')
                
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(2)
        
        return None
    
    def fetch_all_transaction_digests(self) -> List[str]:
        """Fetch all transaction digests for the address using GraphQL"""
        all_digests = []
        cursor = None
        page = 0
        
        print("Fetching transaction digests via GraphQL...")
        
        while True:
            page += 1
            
            if cursor:
                query = '''
                {
                  address(address: "%s") {
                    transactions(first: 50, after: "%s") {
                      nodes { digest }
                      pageInfo { hasNextPage endCursor }
                    }
                  }
                }
                ''' % (self.address, cursor)
            else:
                query = '''
                {
                  address(address: "%s") {
                    transactions(first: 50) {
                      nodes { digest }
                      pageInfo { hasNextPage endCursor }
                    }
                  }
                }
                ''' % self.address
            
            data = self._make_graphql_request(query)
            
            if not data or not data.get('address'):
                print(f"  Page {page}: Error fetching data")
                break
            
            txs = data['address']['transactions']['nodes']
            page_info = data['address']['transactions']['pageInfo']
            
            for tx in txs:
                all_digests.append(tx['digest'])
            
            print(f"  Page {page}: +{len(txs)} txs (total: {len(all_digests)})")
            
            if not page_info['hasNextPage']:
                break
            
            cursor = page_info['endCursor']
        
        return all_digests
    
    def fetch_transaction_details_batch(self, digests: List[str]) -> List[Dict]:
        """Fetch full transaction details for a batch of digests via RPC"""
        params = [
            digests,
            {
                'showBalanceChanges': True,
                'showEffects': True,
                'showInput': True
            }
        ]
        
        result = self._make_rpc_request("sui_multiGetTransactionBlocks", params)
        return result if result else []
    
    def parse_transaction(self, tx_item: Dict) -> Optional[Dict]:
        """Parse a Sui transaction into standardized format"""
        if not tx_item:
            return None
        
        tx_digest = tx_item.get('digest', '')
        timestamp_ms = tx_item.get('timestampMs')
        timestamp = int(timestamp_ms) // 1000 if timestamp_ms else 0
        checkpoint = tx_item.get('checkpoint', 0)
        
        balance_changes = tx_item.get('balanceChanges', [])
        effects = tx_item.get('effects', {})
        status = effects.get('status', {})
        success = status.get('status') == 'success' if isinstance(status, dict) else True
        
        token_transfers = []
        our_address_lower = self.address.lower()
        
        for change in balance_changes:
            owner = change.get('owner', {})
            if isinstance(owner, dict):
                owner_address = owner.get('AddressOwner', '')
            else:
                owner_address = str(owner) if owner else ''
            
            coin_type = change.get('coinType', '')
            amount = int(change.get('amount', '0'))
            
            if owner_address.lower() == our_address_lower and coin_type and amount != 0:
                is_send = amount < 0
                is_receive = amount > 0
                
                token_transfers.append({
                    'from': owner_address if is_send else None,
                    'to': owner_address if is_receive else None,
                    'coin_type': coin_type,
                    'amount': str(abs(amount)),
                    'signature': tx_digest
                })
        
        return {
            'hash': tx_digest,
            'block_number': checkpoint,
            'timestamp': timestamp,
            'token_transfers': token_transfers,
            'success': success
        }
    
    def fetch_all_data(self) -> Dict:
        """Fetch all transaction data for the address"""
        print(f"Fetching all transactions for Sui address: {self.address}")
        print("=" * 60)
        
        # Step 1: Get all transaction digests via GraphQL (correct filtering + pagination)
        all_digests = self.fetch_all_transaction_digests()
        
        if not all_digests:
            print("No transactions found")
            return {
                "address": self.address,
                "normal_transactions": [],
                "erc20_token_transfers": [],
                "internal_transactions": [],
                "metadata": {
                    "total_normal": 0,
                    "total_erc20": 0,
                    "total_internal": 0,
                    "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
                }
            }
        
        print(f"\n✓ Found {len(all_digests)} total transaction digests")
        
        # Step 2: Fetch full transaction details via RPC (in batches)
        print(f"\nFetching transaction details...")
        transactions = []
        token_transfers_all = []
        
        batch_size = 50
        for batch_start in range(0, len(all_digests), batch_size):
            batch_digests = all_digests[batch_start:batch_start + batch_size]
            batch_num = batch_start // batch_size + 1
            total_batches = (len(all_digests) + batch_size - 1) // batch_size
            
            print(f"  Batch {batch_num}/{total_batches}: {len(batch_digests)} transactions...", end='\r', flush=True)
            
            tx_items = self.fetch_transaction_details_batch(batch_digests)
            
            for tx_item in tx_items:
                parsed = self.parse_transaction(tx_item)
                if parsed:
                    transactions.append({
                        'hash': parsed['hash'],
                        'blockNumber': parsed['block_number'],
                        'timeStamp': parsed['timestamp'],
                        'success': parsed['success']
                    })
                    
                    for transfer in parsed.get('token_transfers', []):
                        token_transfers_all.append({
                            'hash': transfer['signature'],
                            'from': transfer.get('from', ''),
                            'to': transfer.get('to', ''),
                            'contractAddress': transfer.get('coin_type', ''),
                            'value': transfer['amount'],
                            'blockNumber': parsed['block_number'],
                            'timeStamp': parsed['timestamp']
                        })
        
        print(f"\n✓ Retrieved {len(transactions)} transactions")
        print(f"✓ Found {len(token_transfers_all)} token transfers")
        
        return {
            "address": self.address,
            "normal_transactions": transactions,
            "erc20_token_transfers": token_transfers_all,
            "internal_transactions": [],
            "metadata": {
                "total_normal": len(transactions),
                "total_erc20": len(token_transfers_all),
                "total_internal": 0,
                "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            }
        }


def main():
    """Main function to fetch Sui transactions"""
    if len(sys.argv) < 2:
        print("Usage: python fetch_sui_transactions.py <ADDRESS> [OUTPUT_FILE] [API_KEY]")
        print("\nExamples:")
        print("  # Basic usage (uses public GraphQL + RPC):")
        print("  python fetch_sui_transactions.py 0xYourAddress")
        print("")
        print("  # With output file:")
        print("  python fetch_sui_transactions.py 0xYourAddress wallet_trades_sui.json")
        print("")
        print("  # With Tatum API key for better RPC reliability:")
        print("  python fetch_sui_transactions.py 0xYourAddress wallet_trades_sui.json t-YOUR-TATUM-KEY")
        sys.exit(1)
    
    address = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "wallet_trades_sui.json"
    api_key = sys.argv[3] if len(sys.argv) > 3 else ""
    
    fetcher = SuiTransactionFetcher(api_key, address)
    
    if not fetcher.validate_address(address):
        print("Error: Invalid Sui address format (should start with 0x and be 66 characters)")
        sys.exit(1)
    
    data = fetcher.fetch_all_data()
    
    # Save to file
    print(f"\nSaving data to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✓ Data saved successfully!")
    print(f"\nSummary:")
    print(f"  Normal transactions: {data['metadata']['total_normal']}")
    print(f"  Token transfers: {data['metadata']['total_erc20']}")


if __name__ == "__main__":
    main()
