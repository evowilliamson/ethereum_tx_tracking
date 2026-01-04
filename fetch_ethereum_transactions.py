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
from blockchain_interface import BlockchainTransactionFetcher


class EthereumTransactionFetcher(BlockchainTransactionFetcher):
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
            # Check if this is a NodeReal endpoint (uses JSON-RPC instead of REST)
            self.is_nodereal = 'nodereal.io' in self.base_url or chain_config.get('api_type') == 'nodereal'
            # Check if this is a direct RPC endpoint
            self.is_rpc = chain_config.get('api_type') == 'rpc' or ('dataseed' in self.base_url or 'rpc' in self.base_url.lower())
            # Check if this is a GoldRush/CovalentHQ endpoint
            self.is_goldrush = 'covalenthq.com' in self.base_url or chain_config.get('api_type') == 'goldrush'
            # For NodeReal, append API key to endpoint: https://bsc-mainnet.nodereal.io/v1/{API-key}
            if self.is_nodereal:
                self.base_url = f"{self.base_url}/{self.api_key}"
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    def validate_address(self, address: str) -> bool:
        """Validate EVM address format (0x prefix, 42 chars)"""
        return address.startswith('0x') and len(address) == 42
        
    def _get_transaction_input(self, tx_hash: str) -> str:
        """Get transaction input data from NodeReal"""
        payload = {
            'jsonrpc': '2.0',
            'method': 'eth_getTransactionByHash',
            'params': [tx_hash],
            'id': 1
        }
        try:
            response = requests.post(self.base_url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'result' in data and data['result']:
                    return data['result'].get('input', '0x')
        except:
            pass
        return '0x'
    
    def _get_transfers_from_receipt(self, tx_hash: str) -> List[Dict]:
        """Get token transfers from transaction receipt logs"""
        payload = {
            'jsonrpc': '2.0',
            'method': 'eth_getTransactionReceipt',
            'params': [tx_hash],
            'id': 1
        }
        transfers = []
        try:
            response = requests.post(self.base_url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'result' in data and data['result']:
                    receipt = data['result']
                    logs = receipt.get('logs', [])
                    
                    # ERC-20 Transfer event signature: Transfer(address,address,uint256)
                    # Topics: [0] = event signature, [1] = from, [2] = to
                    # Data: amount
                    transfer_event_sig = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
                    
                    for log in logs:
                        topics = log.get('topics', [])
                        if len(topics) >= 3 and topics[0].lower() == transfer_event_sig:
                            # This is a Transfer event
                            from_addr = '0x' + topics[1][-40:] if len(topics[1]) >= 42 else topics[1]
                            to_addr = '0x' + topics[2][-40:] if len(topics[2]) >= 42 else topics[2]
                            amount_hex = log.get('data', '0x0')
                            amount = int(amount_hex, 16) if amount_hex != '0x' else 0
                            token_addr = log.get('address', '').lower()
                            
                            # Only include if it involves our address
                            if from_addr.lower() == self.address.lower() or to_addr.lower() == self.address.lower():
                                transfers.append({
                                    'hash': tx_hash,
                                    'blockNumber': str(int(receipt.get('blockNumber', '0x0'), 16)) if receipt.get('blockNumber') else '0',
                                    'timeStamp': '0',  # Will be filled from normal tx if available
                                    'from': from_addr,
                                    'to': to_addr,
                                    'value': str(amount),
                                    'contractAddress': token_addr,
                                    'tokenSymbol': '',  # Will be enriched later
                                    'tokenName': '',
                                    'tokenDecimal': '18',
                                    'gas': '0',
                                    'gasPrice': '0',
                                    'gasUsed': '0',
                                    'isError': '0',
                                    'txreceipt_status': '1',
                                    'input': '0x',
                                    'cumulativeGasUsed': '0',
                                    'confirmations': '0',
                                })
        except Exception as e:
            pass  # Silently fail, we'll use what we have
        return transfers
    
    def _make_nodereal_request(self, method: str, params: Dict) -> Optional[List[Dict]]:
        """Make a JSON-RPC request to NodeReal API"""
        payload = {
            'jsonrpc': '2.0',
            'method': method,
            'params': [params],
            'id': 1
        }
        
        try:
            response = requests.post(self.base_url, json=payload, timeout=30)
            time.sleep(RATE_LIMIT_DELAY)  # Respect rate limit
            
            if response.status_code != 200:
                print(f"HTTP Error {response.status_code}: {response.text}")
                return None
            
            data = response.json()
            
            if 'error' in data:
                error = data['error']
                print(f"NodeReal API Error: {error.get('message', 'Unknown error')}")
                return None
            
            result = data.get('result', {})
            transfers = result.get('transfers', [])
            
            # Check for pagination info
            total = result.get('total', len(transfers))
            has_more = result.get('hasMore', False)
            
            # Store pagination info for debugging
            if hasattr(self, '_last_pagination_info'):
                self._last_pagination_info = {
                    'total': total,
                    'has_more': has_more,
                    'returned': len(transfers)
                }
            
            # Convert NodeReal format to Etherscan format
            converted = []
            seen_hashes = set()  # Track hashes to fetch input data once per transaction
            
            for transfer in transfers:
                tx_hash = transfer.get('hash', '')
                tx_hash_lower = tx_hash.lower()
                
                # Map NodeReal transfer to Etherscan transaction format
                tx = {
                    'hash': tx_hash,
                    'blockNumber': str(int(transfer.get('blockNum', '0x0'), 16)) if transfer.get('blockNum') else '0',
                    'timeStamp': str(transfer.get('blockTimeStamp', 0)),
                    'from': transfer.get('from', ''),
                    'to': transfer.get('to', ''),
                    'value': str(int(transfer.get('value', '0x0'), 16)) if transfer.get('value') else '0',
                    'gas': '0',
                    'gasPrice': '0',
                    'gasUsed': '0',
                    'isError': '0',
                    'txreceipt_status': '1',
                    'input': '0x',  # Will be fetched if needed
                    'contractAddress': transfer.get('contractAddress', ''),
                    'cumulativeGasUsed': '0',
                    'confirmations': '0',
                    'tokenName': transfer.get('name', ''),
                    'tokenSymbol': transfer.get('asset', ''),
                    'tokenDecimal': '18',
                }
                
                # For token transfers, add token-specific fields
                if transfer.get('category') in ['20', '721', '1155']:
                    tx['tokenSymbol'] = transfer.get('asset', '')
                    tx['tokenName'] = transfer.get('name', '')
                
                # For normal transactions (external/internal), fetch input data
                if transfer.get('category') in ['external', 'internal'] and tx_hash_lower not in seen_hashes:
                    tx['input'] = self._get_transaction_input(tx_hash)
                    seen_hashes.add(tx_hash_lower)
                
                converted.append(tx)
            
            return converted
            
        except Exception as e:
            print(f"NodeReal request error: {e}")
            return None
    
    def _make_rpc_call(self, method: str, params: list, retries: int = 3) -> Optional[Dict]:
        """Make a direct RPC call to blockchain node with retry logic"""
        payload = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'id': 1
        }
        
        # Try multiple RPC endpoints if first one fails
        rpc_endpoints = [
            self.base_url,
            'https://bsc-dataseed1.binance.org',
            'https://bsc-dataseed2.binance.org',
            'https://bsc-dataseed3.binance.org',
            'https://bsc-dataseed4.binance.org',
        ]
        
        for attempt in range(retries):
            for endpoint in rpc_endpoints:
                try:
                    response = requests.post(endpoint, json=payload, timeout=30)
                    time.sleep(1.0)  # Rate limit for public RPC (be conservative)
                    
                    if response.status_code != 200:
                        continue  # Try next endpoint
                    
                    data = response.json()
                    if 'error' in data:
                        error = data['error']
                        error_msg = error.get('message', 'Unknown error').lower()
                        if 'limit' in error_msg or 'rate' in error_msg:
                            # Rate limited, wait longer and try next endpoint
                            time.sleep(2.0)
                            continue
                        print(f"RPC Error: {error.get('message', 'Unknown error')}")
                        return None
                    
                    return data.get('result')
                except Exception as e:
                    continue  # Try next endpoint
            
            # All endpoints failed, wait and retry
            if attempt < retries - 1:
                wait_time = (attempt + 1) * 5  # Exponential backoff: 5s, 10s, 15s
                print(f"  Rate limited, waiting {wait_time}s before retry...")
                time.sleep(wait_time)
        
        print(f"RPC call failed after {retries} retries")
        return None
    
    def _get_latest_block(self) -> Optional[int]:
        """Get latest block number"""
        result = self._make_rpc_call('eth_blockNumber', [])
        if result:
            return int(result, 16)
        return None
    
    def _get_block_timestamp(self, block_number: int) -> Optional[int]:
        """Get block timestamp"""
        block_hex = hex(block_number)
        result = self._make_rpc_call('eth_getBlockByNumber', [block_hex, False])
        if result and 'timestamp' in result:
            return int(result['timestamp'], 16)
        return None
    
    def _fetch_token_transfers_via_rpc(self, from_block: int = 0, to_block: int = None) -> List[Dict]:
        """Fetch all ERC-20 token transfers for address using eth_getLogs"""
        if to_block is None:
            to_block = self._get_latest_block()
            if to_block is None:
                return []
        
        # ERC-20 Transfer event signature: Transfer(address,address,uint256)
        transfer_event_sig = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
        
        # Address needs to be padded to 32 bytes (64 hex chars)
        address_padded = '0x' + '0' * 24 + self.address[2:].lower()
        
        transfers = []
        
        # Query in smaller chunks to avoid rate limits (1000 blocks at a time)
        chunk_size = 1000
        current_from = from_block
        
        print(f"  Querying blocks {from_block:,} to {to_block:,} in chunks of {chunk_size:,}...")
        
        while current_from <= to_block:
            current_to = min(current_from + chunk_size - 1, to_block)
            
            # Query transfers FROM address
            from_filter = {
                'fromBlock': hex(current_from),
                'toBlock': hex(current_to),
                'topics': [transfer_event_sig, address_padded]
            }
            
            logs_from = self._make_rpc_call('eth_getLogs', [from_filter])
            if logs_from:
                for log in logs_from:
                    tx_hash = log.get('transactionHash', '')
                    block_num = int(log['blockNumber'], 16)
                    token_addr = log.get('address', '').lower()
                    topics = log.get('topics', [])
                    data = log.get('data', '0x0')
                    
                    if len(topics) >= 3:
                        from_addr = '0x' + topics[1][-40:]
                        to_addr = '0x' + topics[2][-40:]
                        amount = int(data, 16) if data != '0x' else 0
                        
                        block_ts = self._get_block_timestamp(block_num) or 0
                        
                        transfers.append({
                            'hash': tx_hash,
                            'blockNumber': str(block_num),
                            'timeStamp': str(block_ts),
                            'from': from_addr,
                            'to': to_addr,
                            'value': str(amount),
                            'contractAddress': token_addr,
                            'tokenSymbol': '',
                            'tokenName': '',
                            'tokenDecimal': '18',
                            'gas': '0',
                            'gasPrice': '0',
                            'gasUsed': '0',
                            'isError': '0',
                            'txreceipt_status': '1',
                            'input': '0x',
                            'cumulativeGasUsed': '0',
                            'confirmations': '0',
                        })
            
            # Query transfers TO address for this chunk
            to_filter = {
                'fromBlock': hex(current_from),
                'toBlock': hex(current_to),
                'topics': [transfer_event_sig, None, address_padded]  # None means any value for 'from'
            }
            
            logs_to = self._make_rpc_call('eth_getLogs', [to_filter])
            if logs_to:
                for log in logs_to:
                    tx_hash = log.get('transactionHash', '')
                    block_num = int(log['blockNumber'], 16)
                    token_addr = log.get('address', '').lower()
                    topics = log.get('topics', [])
                    data = log.get('data', '0x0')
                    
                    if len(topics) >= 3:
                        from_addr = '0x' + topics[1][-40:]
                        to_addr = '0x' + topics[2][-40:]
                        amount = int(data, 16) if data != '0x' else 0
                        
                        # Skip if we already have this transfer (from FROM query)
                        if any(t.get('hash', '').lower() == tx_hash.lower() and 
                               t.get('contractAddress', '').lower() == token_addr for t in transfers):
                            continue
                        
                        block_ts = self._get_block_timestamp(block_num) or 0
                        
                        transfers.append({
                            'hash': tx_hash,
                            'blockNumber': str(block_num),
                            'timeStamp': str(block_ts),
                            'from': from_addr,
                            'to': to_addr,
                            'value': str(amount),
                            'contractAddress': token_addr,
                            'tokenSymbol': '',
                            'tokenName': '',
                            'tokenDecimal': '18',
                            'gas': '0',
                            'gasPrice': '0',
                            'gasUsed': '0',
                            'isError': '0',
                            'txreceipt_status': '1',
                            'input': '0x',
                            'cumulativeGasUsed': '0',
                            'confirmations': '0',
                        })
            
            # Move to next chunk
            current_from = current_to + 1
            if (current_from - from_block) % 10000 == 0:
                print(f"    Progress: {current_from - from_block:,} blocks processed, found {len(transfers)} transfers...")
            time.sleep(0.5)  # Additional delay between chunks
        
        print(f"  ✓ Completed: Found {len(transfers)} token transfers total")
        return transfers
    
    def _fetch_normal_transactions_via_rpc(self, from_block: int = 0, to_block: int = None) -> List[Dict]:
        """Fetch normal transactions for address using eth_getTransactionByHash"""
        # First, get all unique transaction hashes from token transfers
        # Then fetch full transaction details
        token_transfers = self._fetch_token_transfers_via_rpc(from_block, to_block)
        tx_hashes = set(t.get('hash', '') for t in token_transfers)
        
        # Also need to get transactions where address is sender/receiver
        # This is more complex with RPC - we'd need to scan blocks
        # For now, we'll get transactions from receipts of token transfers
        normal_txs = []
        
        for tx_hash in list(tx_hashes)[:1000]:  # Limit to avoid too many calls
            tx_data = self._make_rpc_call('eth_getTransactionByHash', [tx_hash])
            if tx_data:
                block_num = int(tx_data.get('blockNumber', '0x0'), 16) if tx_data.get('blockNumber') else 0
                block_ts = self._get_block_timestamp(block_num) if block_num else 0
                
                # Only include if address is sender or receiver
                from_addr = tx_data.get('from', '').lower()
                to_addr = tx_data.get('to', '').lower()
                if from_addr == self.address.lower() or to_addr == self.address.lower():
                    normal_txs.append({
                        'hash': tx_hash,
                        'blockNumber': str(block_num),
                        'timeStamp': str(block_ts),
                        'from': tx_data.get('from', ''),
                        'to': tx_data.get('to', ''),
                        'value': str(int(tx_data.get('value', '0x0'), 16)) if tx_data.get('value') else '0',
                        'gas': str(int(tx_data.get('gas', '0x0'), 16)) if tx_data.get('gas') else '0',
                        'gasPrice': str(int(tx_data.get('gasPrice', '0x0'), 16)) if tx_data.get('gasPrice') else '0',
                        'gasUsed': '0',
                        'isError': '0',
                        'txreceipt_status': '1',
                        'input': tx_data.get('input', '0x'),
                        'contractAddress': '',
                        'cumulativeGasUsed': '0',
                        'confirmations': '0',
                    })
        
        return normal_txs
    
    def _fetch_goldrush_transactions(self, page: int = 0, page_size: int = 1000) -> Optional[List[Dict]]:
        """Fetch transactions using GoldRush/CovalentHQ API"""
        # GoldRush API endpoint: /v1/{chain}/address/{address}/transactions_v2/
        chain_name = 'bsc-mainnet'  # BSC on GoldRush
        url = f"{self.base_url}/{chain_name}/address/{self.address}/transactions_v2/"
        
        params = {
            'key': self.api_key,
            'page-number': page,
            'page-size': min(page_size, 10000),  # Max 10k per page
            'no-logs': 'false'  # Include logs for token transfers
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            time.sleep(0.2)  # Rate limit
            
            if response.status_code != 200:
                print(f"GoldRush HTTP Error {response.status_code}: {response.text[:200]}")
                return None
            
            data = response.json()
            # Check for error (but False is not an error)
            if 'error' in data and data['error'] is not False and data['error']:
                print(f"GoldRush API Error: {data['error']}")
                return None
            
            result = data.get('data', {})
            if not result:
                print(f"GoldRush API: No data in response. Full response: {data}")
                return None
            
            items = result.get('items', [])
            if not items:
                # No items, but might be valid (empty result)
                return []
            
            # Convert GoldRush format to Etherscan format
            converted = []
            for item in items:
                if not item:
                    continue
                tx_hash = item.get('tx_hash', '')
                block_num = item.get('block_height', 0)
                block_ts = item.get('block_signed_at', '')
                # Convert ISO timestamp to Unix timestamp
                if block_ts:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(block_ts.replace('Z', '+00:00'))
                        block_ts = str(int(dt.timestamp()))
                    except:
                        block_ts = '0'
                
                # Normal transaction
                converted.append({
                    'hash': tx_hash,
                    'blockNumber': str(block_num),
                    'timeStamp': block_ts or '0',
                    'from': item.get('from_address', ''),
                    'to': item.get('to_address', ''),
                    'value': str(item.get('value', 0)),
                    'gas': str(item.get('gas_offered', 0)),
                    'gasPrice': str(item.get('gas_price', 0)),
                    'gasUsed': str(item.get('gas_spent', 0)),
                    'isError': '0',
                    'txreceipt_status': '1',
                    'input': item.get('input', '0x'),
                    'contractAddress': '',
                    'cumulativeGasUsed': '0',
                    'confirmations': '0',
                })
                
                # Also extract token transfers from logs
                log_events = item.get('log_events', []) or []
                for log in log_events:
                    if not log:
                        continue
                    decoded = log.get('decoded', {}) or {}
                    if decoded and decoded.get('name') == 'Transfer':
                        params_list = decoded.get('params', [])
                        if len(params_list) >= 3:
                            from_addr = params_list[0].get('value', '')
                            to_addr = params_list[1].get('value', '')
                            amount = params_list[2].get('value', '0')
                            token_addr = log.get('sender_address', '').lower()
                            
                            # Only include if it involves our address
                            if from_addr.lower() == self.address.lower() or to_addr.lower() == self.address.lower():
                                converted.append({
                                    'hash': tx_hash,
                                    'blockNumber': str(block_num),
                                    'timeStamp': block_ts or '0',
                                    'from': from_addr,
                                    'to': to_addr,
                                    'value': str(amount),
                                    'contractAddress': token_addr,
                                    'tokenSymbol': '',
                                    'tokenName': '',
                                    'tokenDecimal': '18',
                                    'gas': '0',
                                    'gasPrice': '0',
                                    'gasUsed': '0',
                                    'isError': '0',
                                    'txreceipt_status': '1',
                                    'input': '0x',
                                    'cumulativeGasUsed': '0',
                                    'confirmations': '0',
                                })
            
            return converted
            
        except Exception as e:
            print(f"GoldRush request error: {e}")
            return None
    
    def _make_request(self, params: Dict) -> Optional[List[Dict]]:
        """Make a request to explorer API V2 with rate limiting"""
        # Use GoldRush API if configured
        if self.is_goldrush:
            action = params.get('action', 'txlist')
            page = params.get('page', 1) - 1  # GoldRush uses 0-based pagination
            page_size = params.get('offset', 10000)
            
            if action in ['txlist', 'tokentx']:
                return self._fetch_goldrush_transactions(page, page_size)
            else:
                return []
        
        # Use direct RPC if configured
        if self.is_rpc:
            action = params.get('action', 'txlist')
            if action == 'tokentx':
                print(f"  Fetching token transfers via RPC (this may take a while)...")
                return self._fetch_token_transfers_via_rpc()
            elif action == 'txlist':
                print(f"  Fetching normal transactions via RPC (this may take a while)...")
                return self._fetch_normal_transactions_via_rpc()
            else:
                return []
        
        # Use NodeReal JSON-RPC if this is a NodeReal endpoint
        if self.is_nodereal:
            action = params.get('action', 'txlist')
            # Map Etherscan actions to NodeReal methods
            if action == 'txlist':
                # Get external transactions
                nodereal_params = {
                    'fromAddress': self.address,
                    'category': ['external', 'internal'],
                    'page': params.get('page', 1),
                    'limit': min(params.get('offset', 10000), 1000)  # NodeReal limit is 1000
                }
                return self._make_nodereal_request('nr_getAssetTransfers', nodereal_params)
            elif action == 'tokentx':
                # Get token transfers (ERC-20, ERC-721, ERC-1155)
                # Need to get both FROM and TO transfers to detect swaps
                # NodeReal API returns limited results per page, so we need to paginate
                page = params.get('page', 1)
                limit = min(params.get('offset', 10000), 1000)
                
                from_params = {
                    'fromAddress': self.address,
                    'category': ['20', '721', '1155'],
                    'page': page,
                    'limit': limit
                }
                to_params = {
                    'toAddress': self.address,
                    'category': ['20', '721', '1155'],
                    'page': page,
                    'limit': limit
                }
                
                # Fetch transfers with pagination support
                from_transfers = []
                to_transfers = []
                
                # Fetch FROM transfers (paginate if needed)
                from_page = page
                while True:
                    from_params['page'] = from_page
                    from_result = self._make_nodereal_request('nr_getAssetTransfers', from_params)
                    if not from_result:
                        break
                    from_transfers.extend(from_result)
                    # Check if there are more pages (NodeReal might not return hasMore, so check if we got full page)
                    if len(from_result) < limit:
                        break
                    from_page += 1
                    if from_page > 100:  # Safety limit
                        break
                
                # Fetch TO transfers (paginate if needed)
                to_page = page
                while True:
                    to_params['page'] = to_page
                    to_result = self._make_nodereal_request('nr_getAssetTransfers', to_params)
                    if not to_result:
                        break
                    to_transfers.extend(to_result)
                    if len(to_result) < limit:
                        break
                    to_page += 1
                    if to_page > 100:  # Safety limit
                        break
                
                # Also get transfers by transaction hash for swaps
                # For each transaction hash we have, get all transfers from receipt logs
                all_hashes = set()
                for tx in from_transfers + to_transfers:
                    all_hashes.add(tx.get('hash', '').lower())
                
                # Get additional transfers from transaction receipts
                receipt_transfers = []
                for tx_hash in list(all_hashes)[:50]:  # Limit to avoid too many API calls
                    receipt_txs = self._get_transfers_from_receipt(tx_hash)
                    receipt_transfers.extend(receipt_txs)
                
                # Combine all transfers and deduplicate by hash+token+from+to
                all_transfers = {}
                transfer_key = lambda t: f"{t.get('hash', '').lower()}_{t.get('contractAddress', '').lower()}_{t.get('from', '').lower()}_{t.get('to', '').lower()}"
                
                for tx in from_transfers + to_transfers + receipt_transfers:
                    key = transfer_key(tx)
                    if key not in all_transfers:
                        all_transfers[key] = tx
                
                return list(all_transfers.values())
            elif action == 'txlistinternal':
                # Internal transactions are included in 'internal' category
                nodereal_params = {
                    'fromAddress': self.address,
                    'category': ['internal'],
                    'page': params.get('page', 1),
                    'limit': min(params.get('offset', 10000), 1000)
                }
                return self._make_nodereal_request('nr_getAssetTransfers', nodereal_params)
            else:
                return []
        
        # Standard Etherscan REST API
        params['apikey'] = self.api_key
        params['address'] = self.address
        # Only add chainid for V2 API (BSCTrace and old BSCScan V1 don't use chainid)
        if '/v2/api' in self.base_url and self.chain_id:
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
                    # BSC via Etherscan requires paid plan - but we now use BSCTrace (free)
                    # Check if result has data anyway (user might have paid Etherscan plan)
                    if isinstance(result, list) and len(result) > 0:
                        return result
                    # If no results and using Etherscan, it's likely the API key doesn't have BSC access
                    if 'etherscan.io' in self.base_url:
                        print(f"  Note: BSC requires paid Etherscan API plan. Consider using BSCTrace API (free) instead.")
                    return []
                elif 'deprecated' in message.lower() or (self.chain_name == 'binance' and message == 'NOTOK'):
                    # BSCTrace API - "NOTOK" might just mean no results
                    # Check if we got results despite the NOTOK message
                    if isinstance(result, list) and len(result) > 0:
                        return result
                    # If no results, treat as empty
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

