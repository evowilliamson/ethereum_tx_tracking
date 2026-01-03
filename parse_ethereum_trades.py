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
        self.erc20_by_hash = defaultdict(list)
        for tx in self.data.get('erc20_token_transfers', []):
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
        
        # Check if transaction involves ETH (value sent)
        eth_value = int(tx.get('value', '0'))
        is_eth_in = eth_value > 0
        
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
        
        # Find all transfers involving our address
        our_transfers = []
        for transfer in erc20_transfers:
            from_addr = transfer.get('from', '').lower()
            to_addr = transfer.get('to', '').lower()
            if from_addr == our_address_lower or to_addr == our_address_lower:
                our_transfers.append(transfer)
        
        # If we have 2+ transfers involving us, it's likely a swap
        if len(our_transfers) >= 2:
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
            # This filters out simple transfers (same token or one-way transfers)
            if token_in and token_out and token_in != token_out and amount_in > 0 and amount_out > 0:
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

