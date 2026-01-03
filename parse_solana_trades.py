"""
Parse Solana transactions to identify DEX trades
Analyzes token transfers and DEX program interactions
"""

import json
import sys
from typing import List, Dict, Optional
from collections import defaultdict
from blockchain_interface import BlockchainTradeParser

# Known Solana DEX program IDs
SOLANA_DEX_PROGRAMS = {
    'Raydium': '675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8',
    'Orca': 'whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc',
    'Jupiter': 'JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4',
    'Serum': '9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin',
    'Meteora': 'Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB',
    'Lifinity': 'EewxydAPCCVuNEyrVN68PuSYdQ7wKn27V9Gjeoi8dy3S',
    'Phoenix': 'PhoeNiXZ8ByJGLkxNfZRnkUfjvmuYqL89QTT47NR3MZ8',
}

# Common DEX instruction discriminators (first byte of instruction data)
SWAP_INSTRUCTION_PATTERNS = [
    'swap',  # Generic swap
    'exchange',  # Generic exchange
]


class SolanaTradeParser(BlockchainTradeParser):
    """Parses Solana transactions to identify DEX trades"""
    
    def __init__(self, transaction_data: Dict):
        self.data = transaction_data
        self.address = transaction_data['address']
        self.trades = []
        
        # Build lookup structures
        self._build_lookups()
    
    def _build_lookups(self):
        """Build lookup structures for efficient processing"""
        # Group token transfers by transaction hash
        self.token_transfers_by_hash = defaultdict(list)
        for tx in self.data.get('erc20_token_transfers', []):  # Using same key for compatibility
            tx_hash = tx.get('hash', '').lower()
            self.token_transfers_by_hash[tx_hash].append(tx)
        
        # Index normal transactions by hash
        self.normal_txs_by_hash = {}
        for tx in self.data.get('normal_transactions', []):
            tx_hash = tx.get('hash', '').lower()
            self.normal_txs_by_hash[tx_hash] = tx
    
    def _is_dex_interaction(self, tx: Dict) -> Optional[str]:
        """Check if transaction interacts with a known DEX program"""
        # For Solana, we need to check program IDs in the transaction
        # This is simplified - in practice, we'd parse the transaction message
        # For now, we'll rely on transfer pattern analysis
        return None  # Will be enhanced with actual program ID checking
    
    def _parse_swap_from_transfers(self, tx_hash: str, transfers: List[Dict]) -> Optional[Dict]:
        """Parse a swap from token transfers"""
        our_address_lower = self.address.lower()
        
        # Find transfers involving our address
        our_transfers = []
        for transfer in transfers:
            from_addr = transfer.get('from', '').lower()
            to_addr = transfer.get('to', '').lower()
            
            if from_addr == our_address_lower or to_addr == our_address_lower:
                our_transfers.append(transfer)
        
        if len(our_transfers) < 2:
            return None
        
        # Aggregate amounts by token (mint address)
        tokens_sent = {}  # mint -> total_amount
        tokens_received = {}  # mint -> total_amount
        
        for transfer in our_transfers:
            from_addr = transfer.get('from', '').lower()
            to_addr = transfer.get('to', '').lower()
            value = int(transfer.get('value', '0'))
            mint_addr = transfer.get('contractAddress', '').lower()  # Mint address
            
            if from_addr == our_address_lower:
                tokens_sent[mint_addr] = tokens_sent.get(mint_addr, 0) + value
            elif to_addr == our_address_lower:
                tokens_received[mint_addr] = tokens_received.get(mint_addr, 0) + value
        
        # Find the token we sent most (token in) and received most (token out)
        token_in = max(tokens_sent.items(), key=lambda x: x[1])[0] if tokens_sent else None
        token_out = max(tokens_received.items(), key=lambda x: x[1])[0] if tokens_received else None
        amount_in = tokens_sent.get(token_in, 0) if token_in else 0
        amount_out = tokens_received.get(token_out, 0) if token_out else 0
        
        # Only return if it's a real swap: different tokens, both amounts > 0
        if token_in and token_out and token_in != token_out and amount_in > 0 and amount_out > 0:
            tx = self.normal_txs_by_hash.get(tx_hash)
            block_number = tx.get('blockNumber', 0) if tx else 0
            timestamp = tx.get('timeStamp', 0) if tx else 0
            
            return {
                'tx_hash': tx_hash,
                'block_number': block_number,
                'timestamp': timestamp,
                'dex': 'Unknown DEX',  # Will try to identify from program ID later
                'token_in': token_in,
                'token_out': token_out,
                'amount_in': str(amount_in),
                'amount_out': str(amount_out),
                'type': 'swap'
            }
        
        return None
    
    def parse_all_trades(self) -> List[Dict]:
        """
        Parse all DEX trades from Solana transaction data
        
        Uses transfer pattern analysis to identify swaps:
        - Sending one token AND receiving a different token = swap
        """
        print("Analyzing Solana transactions to identify DEX trades (swaps only, not transfers)...")
        print("=" * 60)
        
        processed_hashes = set()
        
        # Process transactions with token transfers
        for tx_hash, transfers in self.token_transfers_by_hash.items():
            if tx_hash in processed_hashes:
                continue
            
            # Check if this transaction involves our address
            our_address_lower = self.address.lower()
            involves_us = any(
                t.get('from', '').lower() == our_address_lower or 
                t.get('to', '').lower() == our_address_lower 
                for t in transfers
            )
            
            if involves_us and len(transfers) >= 2:
                swap = self._parse_swap_from_transfers(tx_hash, transfers)
                if swap:
                    self.trades.append(swap)
                    processed_hashes.add(tx_hash)
                    print(f"  Found swap: {swap['dex']} - Slot {swap['block_number']}")
        
        # Sort by block number (slot)
        self.trades.sort(key=lambda x: x['block_number'])
        
        print(f"\n✓ Identified {len(self.trades)} DEX trades")
        return self.trades


def main():
    """Main function to parse Solana trades"""
    if len(sys.argv) < 2:
        print("Usage: python parse_solana_trades.py <INPUT_FILE> [OUTPUT_FILE]")
        print("\nExample:")
        print("  python parse_solana_trades.py wallet_trades_solana.json solana_trades.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "solana_trades.json"
    
    print(f"Loading transaction data from {input_file}...")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    parser = SolanaTradeParser(data)
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

