"""
Parse Ethereum transactions to identify DEX trades across all protocols
Analyzes transaction logs, function calls, and ERC-20 transfers
"""

import json
import sys
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from ethereum_config import (
    DEX_ROUTERS, SWAP_FUNCTION_SIGNATURES, SWAP_EVENT_SIGNATURES,
    ETH_ADDRESS, WETH_ADDRESS
)
from blockchain_interface import BlockchainTradeParser

# Protocol token patterns that indicate deposits/withdrawals, not DEX swaps
PROTOCOL_TOKEN_PATTERNS = [
    'aeth',  # Aave tokens (aEthWETH, aEthUSDC, etc.)
    'csusdc',  # Coinshift USDC
    'reusdc',  # Relend USDC
    'fusdc',  # Fluid USDC
    'syrup',  # Syrup tokens
    'pt-',  # Pendle PT tokens
    'variabledebt',  # Aave variable debt tokens
    'staked',  # Staked tokens (sUSN, stcUSD, etc.)
    'siusd',  # Staked infiniFi USD
    'hyperusdc',  # Hyperithm USDC
]


class EthereumTradeParser(BlockchainTradeParser):
    """Parses transactions to identify DEX trades"""
    
    def __init__(self, transaction_data: Dict):
        self.data = transaction_data
        self.address = transaction_data['address']
        self.trades = []
        
        # Build lookup structures
        self._build_lookups()
    
    def _build_lookups(self):
        """Build lookup structures for efficient processing"""
        # Group ERC-20 transfers by transaction hash
        # Filter out entries without contractAddress (these are BNB transfers, not ERC-20)
        self.erc20_by_hash = defaultdict(list)
        for tx in self.data.get('erc20_token_transfers', []):
            # Only include actual ERC-20 transfers (must have contractAddress)
            if tx.get('contractAddress'):
                tx_hash = tx.get('hash', '').lower()
                self.erc20_by_hash[tx_hash].append(tx)
        
        # Index normal transactions by hash
        self.normal_txs_by_hash = {}
        for tx in self.data.get('normal_transactions', []):
            tx_hash = tx.get('hash', '').lower()
            self.normal_txs_by_hash[tx_hash] = tx
        
        # Create reverse lookup: router address -> DEX name
        self.router_to_dex = {addr.lower(): name for name, addr in DEX_ROUTERS.items()}
    
    def _is_dex_interaction(self, tx: Dict) -> Optional[str]:
        """Check if transaction interacts with a known DEX router"""
        to_address = tx.get('to', '').lower()
        
        # Check if 'to' address is a known DEX router
        if to_address in self.router_to_dex:
            return self.router_to_dex[to_address]
        
        # Check function signature (first 4 bytes of input data)
        input_data = tx.get('input', '')
        if len(input_data) >= 10:  # 0x + 8 hex chars
            func_sig = input_data[:10].lower()
            if func_sig in SWAP_FUNCTION_SIGNATURES:
                # Try to identify DEX from contract address
                return self.router_to_dex.get(to_address, "Unknown DEX")
        
        return None
    
    def _parse_uniswap_v2_swap(self, tx: Dict, erc20_transfers: List[Dict]) -> Optional[Dict]:
        """Parse Uniswap V2 style swap (also works for SushiSwap)"""
        if len(erc20_transfers) < 2:
            return None
        
        # Find transfers involving our address
        our_transfers = []
        for transfer in erc20_transfers:
            from_addr = transfer.get('from', '').lower()
            to_addr = transfer.get('to', '').lower()
            our_addr = self.address.lower()
            
            if from_addr == our_addr or to_addr == our_addr:
                our_transfers.append(transfer)
        
        if len(our_transfers) < 2:
            return None
        
        # Aggregate amounts by token (sum all transfers of same token)
        tokens_sent = {}
        tokens_received = {}
        
        for transfer in our_transfers:
            from_addr = transfer.get('from', '').lower()
            to_addr = transfer.get('to', '').lower()
            value = int(transfer.get('value', '0'))
            token_addr = transfer.get('contractAddress', '').lower()
            
            if from_addr == our_addr:
                tokens_sent[token_addr] = tokens_sent.get(token_addr, 0) + value
            elif to_addr == our_addr:
                tokens_received[token_addr] = tokens_received.get(token_addr, 0) + value
        
        token_in = max(tokens_sent.items(), key=lambda x: x[1])[0] if tokens_sent else None
        token_out = max(tokens_received.items(), key=lambda x: x[1])[0] if tokens_received else None
        amount_in = tokens_sent.get(token_in, 0) if token_in else 0
        amount_out = tokens_received.get(token_out, 0) if token_out else 0
        
        if token_in and token_out and token_in != token_out and amount_in > 0 and amount_out > 0:
            return {
                'tx_hash': tx.get('hash', ''),
                'block_number': int(tx.get('blockNumber', 0)),
                'timestamp': int(tx.get('timeStamp', 0)),
                'dex': self._is_dex_interaction(tx) or "Uniswap V2",
                'token_in': token_in,
                'token_out': token_out,
                'amount_in': str(amount_in),
                'amount_out': str(amount_out),
                'type': 'swap'
            }
        
        return None
    
    def _parse_uniswap_v3_swap(self, tx: Dict, erc20_transfers: List[Dict]) -> Optional[Dict]:
        """Parse Uniswap V3 swap from logs"""
        # Uniswap V3 emits Swap events in logs
        # We need to check if there's a Swap event in the transaction
        
        # For now, use similar logic to V2 but mark as V3
        swap = self._parse_uniswap_v2_swap(tx, erc20_transfers)
        if swap:
            swap['dex'] = 'Uniswap V3'
            return swap
        return None
    
    def _parse_eth_swap(self, tx: Dict, erc20_transfers: List[Dict]) -> Optional[Dict]:
        """Parse swap involving ETH (native token)"""
        our_addr = self.address.lower()
        tx_hash = tx.get('hash', '').lower()
        tx_from = tx.get('from', '').lower()
        
        # Check if transaction involves ETH (value sent)
        # IMPORTANT: Only count as swap if WE sent the ETH (tx.from == our_address)
        # If we only received ETH, it's not a swap - it's an airdrop/reward/refund
        eth_value = int(tx.get('value', '0'))
        is_eth_in = eth_value > 0 and tx_from == our_addr  # Must be from us
        
        # Filter out simple BNB transfers (not swaps)
        # These are typically gas refunds, dust, or simple transfers
        tx_from = tx.get('from', '').lower()
        tx_to = tx.get('to', '').lower()
        input_data = tx.get('input', '0x')
        has_swap_function = len(input_data) >= 10 and input_data[:10].lower() in SWAP_FUNCTION_SIGNATURES
        is_dex_router = tx_to in self.router_to_dex
        
        # If this is a simple BNB transfer TO our address (we're receiving, not sending)
        # and it's a small amount without swap function or DEX router, it's likely not a swap
        if tx_to == our_addr and tx_from != our_addr:
            # We're receiving BNB - check if it's a swap or just a transfer
            if eth_value > 0 and eth_value < 100000000000000000:  # < 0.1 BNB
                if not has_swap_function and not is_dex_router and len(erc20_transfers) == 0:
                    # Small BNB transfer to us without swap function or token transfers - likely gas refund or dust
                    return None
        
        # Aggregate ERC-20 transfers (token out when ETH in)
        tokens_received = {}  # token -> total_amount
        for transfer in erc20_transfers:
            to_addr = transfer.get('to', '').lower()
            if to_addr == our_addr:
                token_addr = transfer.get('contractAddress', '').lower()
                value = int(transfer.get('value', '0'))
                tokens_received[token_addr] = tokens_received.get(token_addr, 0) + value
        
        # ETH -> Token swap
        if is_eth_in and tokens_received:
            token_out = max(tokens_received.items(), key=lambda x: x[1])[0]
            amount_out = tokens_received[token_out]
            
            # Filter out very small BNB swaps that are likely fees/dust
            # If BNB amount is very small (< 0.1 BNB), it's likely a fee payment, not a real swap
            if eth_value < 100000000000000000:  # < 0.1 BNB
                # Very small amount - likely fee or dust, not a real swap
                return None
            
            return {
                'tx_hash': tx.get('hash', ''),
                'block_number': int(tx.get('blockNumber', 0)),
                'timestamp': int(tx.get('timeStamp', 0)),
                'dex': self._is_dex_interaction(tx) or "Unknown DEX",
                'token_in': ETH_ADDRESS,  # ETH
                'token_out': token_out,
                'amount_in': str(eth_value),
                'amount_out': str(amount_out),
                'type': 'swap'
            }
        
        # Token -> ETH swap
        # Aggregate ERC-20 transfers we sent
        tokens_sent = {}
        for transfer in erc20_transfers:
            from_addr = transfer.get('from', '').lower()
            if from_addr == our_addr:
                token_addr = transfer.get('contractAddress', '').lower()
                value = int(transfer.get('value', '0'))
                tokens_sent[token_addr] = tokens_sent.get(token_addr, 0) + value
        
        # Check internal transactions for ETH received
        eth_received = 0
        internal_txs = self.data.get('internal_transactions', [])
        for internal in internal_txs:
            if internal.get('hash', '').lower() == tx_hash:
                if internal.get('to', '').lower() == our_addr:
                    eth_received += int(internal.get('value', '0'))
        
        if tokens_sent and eth_received > 0:
            token_in = max(tokens_sent.items(), key=lambda x: x[1])[0]
            amount_in = tokens_sent[token_in]
            return {
                'tx_hash': tx.get('hash', ''),
                'block_number': int(tx.get('blockNumber', 0)),
                'timestamp': int(tx.get('timeStamp', 0)),
                'dex': self._is_dex_interaction(tx) or "Unknown DEX",
                'token_in': token_in,
                'token_out': ETH_ADDRESS,  # ETH
                'amount_in': str(amount_in),
                'amount_out': str(eth_received),
                'type': 'swap'
            }
        
        return None
    
    def _is_protocol_interaction(self, token_in: str, token_out: str) -> bool:
        """
        Check if this looks like a protocol deposit/withdrawal rather than a DEX swap.
        
        Args:
            token_in: Token address (will check against known tokens for symbol)
            token_out: Token address (will check against known tokens for symbol)
        
        Returns:
            True if this appears to be a protocol interaction, False if it's a DEX swap
        """
        # Try to get token symbols from known tokens or metadata
        # For now, check addresses against known protocol token addresses
        # This will be more accurate after enrichment, but we can filter here too
        
        token_in_lower = token_in.lower()
        token_out_lower = token_out.lower()
        
        # Check if either token address matches protocol patterns
        # (Some protocol tokens have patterns in their addresses or we can check known tokens)
        for pattern in PROTOCOL_TOKEN_PATTERNS:
            if pattern in token_in_lower or pattern in token_out_lower:
                return True
        
        # Also check against known protocol token addresses from known_tokens
        # Import here to avoid circular dependency
        try:
            from known_tokens import KNOWN_TOKENS
            token_in_info = KNOWN_TOKENS.get(token_in_lower, {})
            token_out_info = KNOWN_TOKENS.get(token_out_lower, {})
            
            token_in_symbol = token_in_info.get('symbol', '').lower()
            token_out_symbol = token_out_info.get('symbol', '').lower()
            
            # Check if either symbol matches protocol patterns
            for pattern in PROTOCOL_TOKEN_PATTERNS:
                if pattern in token_in_symbol or pattern in token_out_symbol:
                    return True
        except ImportError:
            pass  # known_tokens might not be available
        
        return False
    
    def _parse_generic_swap(self, tx: Dict) -> Optional[Dict]:
        """Parse generic swap by analyzing ERC-20 transfers and transaction patterns"""
        tx_hash = tx.get('hash', '').lower()
        erc20_transfers = self.erc20_by_hash.get(tx_hash, [])
        our_address_lower = self.address.lower()
        
        # Filter out simple BNB transfers (gas fees, dust, refunds)
        tx_from = tx.get('from', '').lower()
        tx_to = tx.get('to', '').lower()
        tx_value = int(tx.get('value', '0'))
        input_data = tx.get('input', '0x')
        has_input_data = input_data != '0x' and len(input_data) > 10
        has_swap_function = len(input_data) >= 10 and input_data[:10].lower() in SWAP_FUNCTION_SIGNATURES
        is_dex_router = tx_to in self.router_to_dex
        
        # If this is a simple BNB transfer TO our address (we're receiving, not sending)
        # with no contract interaction, no swap function, and small amount, it's not a swap
        if tx_to == our_address_lower and tx_from != our_address_lower:
            # We're receiving BNB
            if tx_value > 0:
                # Check if it's a small amount without swap indicators
                if tx_value < 100000000000000000:  # < 0.1 BNB
                    if not has_swap_function and not is_dex_router and len(erc20_transfers) == 0:
                        # Small BNB transfer to us without swap function or token transfers - likely gas refund or dust
                        return None
                # Also check if it's just a simple transfer (no input data, standard gas)
                gas_used = int(tx.get('gasUsed', '0'))
                if gas_used == 21000 and not has_input_data and len(erc20_transfers) == 0:
                    # Standard gas for simple transfer, no input data, no token transfers - not a swap
                    return None
        
        # Find all transfers involving our address
        our_transfers = []
        for transfer in erc20_transfers:
            from_addr = transfer.get('from', '').lower()
            to_addr = transfer.get('to', '').lower()
            if from_addr == our_address_lower or to_addr == our_address_lower:
                our_transfers.append(transfer)
        
        # Enhanced: Also check if transaction is to a contract (likely DEX/protocol)
        # and has token transfers - this indicates a swap even with single transfer
        is_contract_interaction = tx_to and tx_to != our_address_lower and tx_to != '0x'
        
        # If we have 2+ transfers involving us, it's likely a swap
        # OR if we have 1 transfer + contract interaction with input data (swap function call)
        if len(our_transfers) >= 2 or (len(our_transfers) >= 1 and is_contract_interaction and has_input_data):
            # Aggregate amounts by token (sum all transfers of same token)
            # In swaps, there can be multiple transfers of the same token
            tokens_sent = {}  # token_address -> total_amount
            tokens_received = {}  # token_address -> total_amount
            
            for transfer in our_transfers:
                from_addr = transfer.get('from', '').lower()
                to_addr = transfer.get('to', '').lower()
                value = int(transfer.get('value', '0'))
                token_addr = transfer.get('contractAddress', '').lower()
                
                if from_addr == our_address_lower:
                    # We're sending this token (token in)
                    tokens_sent[token_addr] = tokens_sent.get(token_addr, 0) + value
                elif to_addr == our_address_lower:
                    # We're receiving this token (token out)
                    tokens_received[token_addr] = tokens_received.get(token_addr, 0) + value
            
            # Find the token we sent most (token in) and received most (token out)
            token_in = max(tokens_sent.items(), key=lambda x: x[1])[0] if tokens_sent else None
            token_out = max(tokens_received.items(), key=lambda x: x[1])[0] if tokens_received else None
            amount_in = tokens_sent.get(token_in, 0) if token_in else 0
            amount_out = tokens_received.get(token_out, 0) if token_out else 0
            
            # Only return if it's a real swap: different tokens, both amounts > 0
            # AND we must have sent something (tokens_sent must not be empty)
            # This filters out airdrops, rewards, refunds where we only receive tokens
            is_swap = False
            if token_in and token_out and token_in != token_out and amount_in > 0 and amount_out > 0:
                # Must have sent something (tokens_sent not empty) to be a swap
                # If we only received tokens without sending anything, it's not a swap
                if tokens_sent and len(tokens_sent) > 0:
                    is_swap = True
            elif len(our_transfers) >= 1 and is_contract_interaction and has_input_data:
                # Single transfer to contract with function call - likely a swap
                # We might only see one side if the other token is native (BNB) or not captured
                # Check if input data looks like a swap function
                input_data = tx.get('input', '0x')
                func_sig = input_data[:10].lower() if len(input_data) >= 10 else ''
                if func_sig in SWAP_FUNCTION_SIGNATURES:
                    # It's a swap function call - treat as swap even if we only see one token
                    if token_in and amount_in > 0:
                        # We sent a token, assume we received something (BNB or another token)
                        token_out = ETH_ADDRESS  # Assume BNB/ETH received
                        amount_out = tx.get('value', '0')  # Use transaction value as amount out
                        if amount_out == '0' or int(amount_out) == 0:
                            # No BNB value, might have received another token we didn't capture
                            # Still count it as a swap since it's a swap function call
                            amount_out = '1'  # Placeholder, will be enriched later
                        is_swap = True
                    elif token_out and amount_out > 0:
                        # We received a token, assume we sent something
                        token_in = ETH_ADDRESS  # Assume BNB/ETH sent
                        amount_in = tx.get('value', '0')
                        if amount_in == '0' or int(amount_in) == 0:
                            amount_in = '1'  # Placeholder
                        is_swap = True
            
            if is_swap:
                # Filter out very small swaps that are likely fees/dust
                # If amount is very small (< 0.01 BNB equivalent) and token_out is empty/zero,
                # it's likely a fee payment, not a real swap
                amount_in_wei = int(amount_in) if isinstance(amount_in, str) else amount_in
                amount_out_wei = int(amount_out) if isinstance(amount_out, str) else amount_out
                
                # If token_in is BNB and amount is very small, likely a fee
                if token_in == ETH_ADDRESS.lower() and amount_in_wei < 10000000000000000:  # < 0.01 BNB
                    if not token_out or token_out == '' or token_out == ETH_ADDRESS.lower():
                        # Very small BNB amount with no clear token_out - likely fee
                        return None
                
                # Don't filter protocol interactions - Koinly counts them as trades
                # (e.g., USDC -> SYRUPUSDC, AETHUSDC -> USDC are counted as trades by Koinly)
                # These are token exchanges even if they're protocol deposits/withdrawals
                
                return {
                    'tx_hash': tx.get('hash', ''),
                    'block_number': int(tx.get('blockNumber', 0)),
                    'timestamp': int(tx.get('timeStamp', 0)),
                    'dex': self._is_dex_interaction(tx) or "Unknown DEX",
                    'token_in': token_in,
                    'token_out': token_out,
                    'amount_in': str(amount_in),
                    'amount_out': str(amount_out),
                    'type': 'swap'
                }
        
        # Filter out simple BNB transfers (not swaps)
        # These are typically gas refunds, dust, or simple transfers
        tx_value = int(tx.get('value', '0'))
        gas_used = int(tx.get('gasUsed', '0'))
        gas_price = int(tx.get('gasPrice', '0'))
        
        # Calculate gas fee
        gas_fee = gas_used * gas_price if gas_used > 0 and gas_price > 0 else 0
        
        # If this is a simple BNB transfer (no ERC-20 transfers, no contract interaction, small amount)
        # and the amount is similar to gas fees or very small, it's likely not a swap
        if len(erc20_transfers) == 0:
            # Simple BNB transfer - check if it's a swap or just a transfer
            tx_to = tx.get('to', '').lower()
            input_data = tx.get('input', '0x')
            has_swap_function = len(input_data) >= 10 and input_data[:10].lower() in SWAP_FUNCTION_SIGNATURES
            is_dex_router = tx_to in self.router_to_dex
            
            # If it's a very small amount (< 0.1 BNB) and not a DEX interaction, likely not a swap
            if tx_value > 0 and tx_value < 100000000000000000:  # < 0.1 BNB
                if not has_swap_function and not is_dex_router:
                    # Small BNB transfer without swap function - likely gas refund or dust
                    return None
        
        # Additional filter: If we have a very small BNB amount and no clear swap indicators,
        # it's likely a fee payment, not a swap
        if tx_value > 0 and tx_value < 100000000000000000:  # < 0.1 BNB
            if not has_swap_function and not is_dex_router and len(erc20_transfers) == 0:
                # Very small BNB amount without swap indicators - likely fee
                return None
        
        # Check for ETH swaps
        if len(erc20_transfers) < 2:
            return self._parse_eth_swap(tx, erc20_transfers)
        
        # Try standard patterns
        swap = self._parse_uniswap_v2_swap(tx, erc20_transfers)
        if swap:
            return swap
        
        swap = self._parse_uniswap_v3_swap(tx, erc20_transfers)
        if swap:
            return swap
        
        swap = self._parse_eth_swap(tx, erc20_transfers)
        if swap:
            return swap
        
        return None
    
    def parse_all_trades(self) -> List[Dict]:
        """
        Parse all DEX trades from transaction data
        
        NOTE: Only identifies actual swaps/trades, NOT simple transfers.
        A trade requires:
        - Sending one token AND receiving a different token
        - Interaction with DEX router OR swap function signature
        - Different token_in and token_out addresses
        """
        print("Analyzing transactions to identify DEX trades (swaps only, not transfers)...")
        print("=" * 60)
        
        processed_hashes = set()
        
        # Process normal transactions
        for tx in self.data.get('normal_transactions', []):
            tx_hash = tx.get('hash', '').lower()
            
            if tx_hash in processed_hashes:
                continue
            
            # Check if this is a DEX interaction
            dex_name = self._is_dex_interaction(tx)
            input_data = tx.get('input', '')
            is_swap_function = len(input_data) >= 10 and input_data[:10].lower() in SWAP_FUNCTION_SIGNATURES
            
            if dex_name or is_swap_function:
                # Try to parse as swap
                swap = self._parse_generic_swap(tx)
                if swap:
                    self.trades.append(swap)
                    processed_hashes.add(tx_hash)
                    print(f"  Found swap: {swap['dex']} - Block {swap['block_number']}")
        
        # Also check transactions with ERC-20 transfers (likely swaps)
        # This catches swaps that might not have been caught by router detection
        for tx_hash, transfers in self.erc20_by_hash.items():
            if tx_hash in processed_hashes:
                continue
            
            # Check transactions with transfers (including single transfer + ETH swaps)
            if len(transfers) >= 1:
                # Check if this transaction involves our address
                our_address_lower = self.address.lower()
                involves_us = any(
                    t.get('from', '').lower() == our_address_lower or 
                    t.get('to', '').lower() == our_address_lower 
                    for t in transfers
                )
                
                if involves_us:
                    tx = self.normal_txs_by_hash.get(tx_hash)
                    if tx:
                        # Try generic swap first
                        swap = self._parse_generic_swap(tx)
                        if swap:
                            self.trades.append(swap)
                            processed_hashes.add(tx_hash)
                            print(f"  Found swap: {swap['dex']} - Block {swap['block_number']}")
                        else:
                            # Try ETH swap if generic didn't work (for Token -> ETH swaps)
                            swap = self._parse_eth_swap(tx, transfers)
                            if swap:
                                self.trades.append(swap)
                                processed_hashes.add(tx_hash)
                                print(f"  Found swap: {swap['dex']} - Block {swap['block_number']}")
                    else:
                        # Transaction might be internal or we don't have it
                        # Try to construct a basic swap from transfers
                        our_transfers = [t for t in transfers 
                                       if t.get('from', '').lower() == our_address_lower or 
                                          t.get('to', '').lower() == our_address_lower]
                        
                        # Check for Token -> ETH swaps (1 transfer + internal ETH)
                        if len(our_transfers) == 1:
                            transfer = our_transfers[0]
                            from_addr = transfer.get('from', '').lower()
                            to_addr = transfer.get('to', '').lower()
                            
                            # If we sent a token, check for ETH received via internal tx
                            if from_addr == our_address_lower:
                                token_in = transfer.get('contractAddress', '').lower()
                                amount_in = int(transfer.get('value', '0'))
                                
                                # Check internal transactions for ETH received
                                internal_txs = self.data.get('internal_transactions', [])
                                eth_received = 0
                                for internal in internal_txs:
                                    if internal.get('hash', '').lower() == tx_hash:
                                        if internal.get('to', '').lower() == our_address_lower:
                                            eth_received += int(internal.get('value', '0'))
                                
                                if token_in and amount_in > 0 and eth_received > 0:
                                    # Don't filter - include all token -> ETH swaps
                                    first_transfer = transfers[0]
                                    swap = {
                                        'tx_hash': tx_hash,
                                        'block_number': int(first_transfer.get('blockNumber', 0)),
                                        'timestamp': int(first_transfer.get('timeStamp', 0)),
                                        'dex': 'Unknown DEX',
                                        'token_in': token_in,
                                        'token_out': ETH_ADDRESS,
                                        'amount_in': str(amount_in),
                                        'amount_out': str(eth_received),
                                        'type': 'swap'
                                    }
                                    self.trades.append(swap)
                                    processed_hashes.add(tx_hash)
                                    print(f"  Found swap: {swap['dex']} - Block {swap['block_number']}")
                                    continue
                        
                        if len(our_transfers) >= 2:
                            # Get block info from first transfer
                            first_transfer = transfers[0]
                            token_in = None
                            token_out = None
                            amount_in = 0
                            amount_out = 0
                            
                            # Aggregate amounts by token (sum all transfers)
                            tokens_sent = {}
                            tokens_received = {}
                            
                            for transfer in our_transfers:
                                from_addr = transfer.get('from', '').lower()
                                to_addr = transfer.get('to', '').lower()
                                value = int(transfer.get('value', '0'))
                                token_addr = transfer.get('contractAddress', '').lower()
                                
                                if from_addr == our_address_lower:
                                    tokens_sent[token_addr] = tokens_sent.get(token_addr, 0) + value
                                elif to_addr == our_address_lower:
                                    tokens_received[token_addr] = tokens_received.get(token_addr, 0) + value
                            
                            token_in = max(tokens_sent.items(), key=lambda x: x[1])[0] if tokens_sent else None
                            token_out = max(tokens_received.items(), key=lambda x: x[1])[0] if tokens_received else None
                            amount_in = tokens_sent.get(token_in, 0) if token_in else 0
                            amount_out = tokens_received.get(token_out, 0) if token_out else 0
                            
                            if token_in and token_out and token_in != token_out and amount_in > 0 and amount_out > 0:
                                # Don't filter protocol interactions - Koinly counts them as trades
                                
                                swap = {
                                    'tx_hash': tx_hash,
                                    'block_number': int(first_transfer.get('blockNumber', 0)),
                                    'timestamp': int(first_transfer.get('timeStamp', 0)),
                                    'dex': 'Unknown DEX',
                                    'token_in': token_in,
                                    'token_out': token_out,
                                    'amount_in': str(amount_in),
                                    'amount_out': str(amount_out),
                                    'type': 'swap'
                                }
                                self.trades.append(swap)
                                processed_hashes.add(tx_hash)
                                print(f"  Found swap: {swap['dex']} - Block {swap['block_number']}")
        
        # Sort by block number
        self.trades.sort(key=lambda x: x['block_number'])
        
        print(f"\n✓ Identified {len(self.trades)} DEX trades")
        return self.trades


def main():
    """Main function to parse trades"""
    if len(sys.argv) < 2:
        print("Usage: python parse_ethereum_trades.py <INPUT_FILE> [OUTPUT_FILE]")
        print("\nExample:")
        print("  python parse_ethereum_trades.py wallet_trades.json ethereum_trades.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "ethereum_trades.json"
    
    print(f"Loading transaction data from {input_file}...")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    parser = EthereumTradeParser(data)
    trades = parser.parse_all_trades()
    
    # Prepare output
    output = {
        "address": data['address'],
        "total_trades": len(trades),
        "trades": trades,
        "metadata": {
            "parsed_at": __import__('time').strftime("%Y-%m-%d %H:%M:%S UTC", __import__('time').gmtime())
        }
    }
    
    # Save results
    print(f"\nSaving trades to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ Saved {len(trades)} trades to {output_file}")
    
    # Print summary by DEX
    if trades:
        dex_counts = {}
        for trade in trades:
            dex = trade.get('dex', 'Unknown')
            dex_counts[dex] = dex_counts.get(dex, 0) + 1
        
        print("\nTrades by DEX:")
        for dex, count in sorted(dex_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {dex}: {count}")


if __name__ == "__main__":
    main()

