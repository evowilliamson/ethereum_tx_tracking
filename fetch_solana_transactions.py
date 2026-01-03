"""
Fetch Solana transactions for a given address
Uses Solana RPC API to fetch transactions and token transfers
"""

import requests
import time
import json
import sys
from typing import List, Dict, Optional
from blockchain_interface import BlockchainTransactionFetcher
from chains_config import get_chain_config


class SolanaTransactionFetcher(BlockchainTransactionFetcher):
    """Fetches all transaction data from Solana RPC"""
    
    def __init__(self, api_key: str, address: str, chain_name: str = 'solana'):
        """
        Initialize transaction fetcher for Solana
        
        Args:
            api_key: RPC endpoint URL (or API key for premium RPC services)
            address: Solana wallet address (base58 encoded)
            chain_name: Chain name (should be 'solana')
        """
        self.address = address
        self.chain_name = chain_name.lower()
        
        # Load chain configuration
        try:
            chain_config = get_chain_config(self.chain_name)
            # Use provided RPC endpoint or default from config
            if api_key and api_key != "YOUR_API_KEY_HERE":
                self.rpc_endpoint = api_key
            else:
                self.rpc_endpoint = chain_config.get('rpc_endpoint', 'https://api.mainnet-beta.solana.com')
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    def validate_address(self, address: str) -> bool:
        """Validate Solana address format (base58, 32-44 chars)"""
        # Basic validation - Solana addresses are base58 encoded, typically 32-44 characters
        if not address or len(address) < 32 or len(address) > 44:
            return False
        # Check for valid base58 characters (no 0, O, I, l)
        invalid_chars = {'0', 'O', 'I', 'l'}
        if any(c in invalid_chars for c in address):
            return False
        return True
    
    def _make_rpc_request(self, method: str, params: List) -> Optional[Dict]:
        """Make a JSON-RPC request to Solana RPC endpoint"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        try:
            response = requests.post(self.rpc_endpoint, json=payload, timeout=30)
            time.sleep(0.25)  # Rate limiting
            
            if response.status_code != 200:
                print(f"HTTP Error {response.status_code}: {response.text}")
                return None
            
            data = response.json()
            
            if 'error' in data:
                error_msg = data['error'].get('message', 'Unknown error')
                print(f"RPC Error: {error_msg}")
                return None
            
            return data.get('result')
            
        except Exception as e:
            print(f"Request error: {e}")
            return None
    
    def fetch_signatures(self, limit: int = 1000) -> List[str]:
        """Fetch transaction signatures for the address"""
        params = [
            self.address,
            {
                "limit": limit
            }
        ]
        
        result = self._make_rpc_request("getSignaturesForAddress", params)
        if result:
            return [sig['signature'] for sig in result]
        return []
    
    def fetch_transaction(self, signature: str) -> Optional[Dict]:
        """Fetch full transaction details by signature"""
        params = [
            signature,
            {
                "encoding": "jsonParsed",
                "maxSupportedTransactionVersion": 0
            }
        ]
        
        result = self._make_rpc_request("getTransaction", params)
        return result
    
    def fetch_token_accounts(self) -> List[Dict]:
        """Fetch all token accounts for the address"""
        params = [
            self.address,
            {
                "programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"  # SPL Token program
            },
            {
                "encoding": "jsonParsed"
            }
        ]
        
        result = self._make_rpc_request("getTokenAccountsByOwner", params)
        if result and 'value' in result:
            return result['value']
        return []
    
    def parse_transaction(self, tx_data: Dict, signature: str) -> Optional[Dict]:
        """Parse a Solana transaction into standardized format"""
        if not tx_data:
            return None
        
        # Extract transaction metadata
        meta = tx_data.get('meta', {})
        block_time = tx_data.get('blockTime')
        slot = tx_data.get('slot', 0)
        
        # Parse token transfers from pre/post token balances
        pre_balances = meta.get('preTokenBalances', [])
        post_balances = meta.get('postTokenBalances', [])
        
        # Build balance map: account -> token -> balance
        pre_balance_map = {}
        post_balance_map = {}
        
        for balance in pre_balances:
            account = balance.get('owner', '')
            mint = balance.get('mint', '')
            amount = int(balance.get('uiTokenAmount', {}).get('uiAmount', 0) * 1e9)  # Convert to lamports
            if account and mint:
                if account not in pre_balance_map:
                    pre_balance_map[account] = {}
                pre_balance_map[account][mint] = amount
        
        for balance in post_balances:
            account = balance.get('owner', '')
            mint = balance.get('mint', '')
            amount = int(balance.get('uiTokenAmount', {}).get('uiAmount', 0) * 1e9)
            if account and mint:
                if account not in post_balance_map:
                    post_balance_map[account] = {}
                post_balance_map[account][mint] = amount
        
        # Calculate token transfers (difference in balances)
        token_transfers = []
        all_accounts = set(pre_balance_map.keys()) | set(post_balance_map.keys())
        
        for account in all_accounts:
            pre_balances_account = pre_balance_map.get(account, {})
            post_balances_account = post_balance_map.get(account, {})
            
            all_mints = set(pre_balances_account.keys()) | set(post_balances_account.keys())
            
            for mint in all_mints:
                pre_amt = pre_balances_account.get(mint, 0)
                post_amt = post_balances_account.get(mint, 0)
                diff = post_amt - pre_amt
                
                if diff != 0:
                    token_transfers.append({
                        'from': account if diff < 0 else None,
                        'to': account if diff > 0 else None,
                        'mint': mint,
                        'amount': str(abs(diff)),
                        'signature': signature
                    })
        
        # Check for SOL transfers (native token)
        account_keys = tx_data.get('transaction', {}).get('message', {}).get('accountKeys', [])
        pre_balances_sol = meta.get('preBalances', [])
        post_balances_sol = meta.get('postBalances', [])
        
        sol_transfers = []
        for i, account_key in enumerate(account_keys):
            if i < len(pre_balances_sol) and i < len(post_balances_sol):
                pre_bal = pre_balances_sol[i]
                post_bal = post_balances_sol[i]
                diff = post_bal - pre_bal
                
                if diff != 0:
                    sol_transfers.append({
                        'from': account_key.get('pubkey', '') if diff < 0 else None,
                        'to': account_key.get('pubkey', '') if diff > 0 else None,
                        'mint': 'So11111111111111111111111111111111111111112',  # Wrapped SOL mint
                        'amount': str(abs(diff)),
                        'signature': signature
                    })
        
        return {
            'hash': signature,
            'block_number': slot,  # Use slot as block number equivalent
            'timestamp': block_time or 0,
            'token_transfers': token_transfers + sol_transfers,
            'success': meta.get('err') is None
        }
    
    def fetch_all_data(self) -> Dict:
        """Fetch all transaction data for the address"""
        print(f"Fetching all transactions for Solana address: {self.address}")
        print("=" * 60)
        
        # Fetch transaction signatures
        print("\nFetching transaction signatures...")
        signatures = self.fetch_signatures(limit=1000)
        print(f"✓ Found {len(signatures)} transaction signatures")
        
        # Fetch full transaction details
        print(f"\nFetching transaction details...")
        transactions = []
        token_transfers_all = []
        
        for i, sig in enumerate(signatures, 1):
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(signatures)}...", end='\r', flush=True)
            
            tx_data = self.fetch_transaction(sig)
            if tx_data:
                parsed = self.parse_transaction(tx_data, sig)
                if parsed:
                    transactions.append({
                        'hash': parsed['hash'],
                        'blockNumber': parsed['block_number'],
                        'timeStamp': parsed['timestamp'],
                        'success': parsed['success']
                    })
                    
                    # Add token transfers
                    for transfer in parsed.get('token_transfers', []):
                        token_transfers_all.append({
                            'hash': transfer['signature'],
                            'from': transfer.get('from', ''),
                            'to': transfer.get('to', ''),
                            'contractAddress': transfer['mint'],  # Use mint as contract address
                            'value': transfer['amount'],
                            'blockNumber': parsed['block_number'],
                            'timeStamp': parsed['timestamp']
                        })
        
        print(f"\n✓ Retrieved {len(transactions)} transactions")
        print(f"✓ Found {len(token_transfers_all)} token transfers")
        
        return {
            "address": self.address,
            "normal_transactions": transactions,
            "erc20_token_transfers": token_transfers_all,  # Use same key for compatibility
            "internal_transactions": [],  # Solana doesn't have internal transactions
            "metadata": {
                "total_normal": len(transactions),
                "total_erc20": len(token_transfers_all),
                "total_internal": 0,
                "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            }
        }


def main():
    """Main function to fetch Solana transactions"""
    if len(sys.argv) < 3:
        print("Usage: python fetch_solana_transactions.py <RPC_ENDPOINT> <ADDRESS> [OUTPUT_FILE]")
        print("\nExample:")
        print("  python fetch_solana_transactions.py https://api.mainnet-beta.solana.com YourAddress wallet_trades.json")
        sys.exit(1)
    
    rpc_endpoint = sys.argv[1]
    address = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else "wallet_trades_solana.json"
    
    fetcher = SolanaTransactionFetcher(rpc_endpoint, address)
    
    if not fetcher.validate_address(address):
        print("Error: Invalid Solana address format")
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

