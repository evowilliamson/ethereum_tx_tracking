"""
Parse Sui transactions to identify DEX trades
Analyzes token transfers and DEX package interactions
"""

import json
import sys
from typing import List, Dict, Optional
from collections import defaultdict
from blockchain_interface import BlockchainTradeParser

# Known Sui DEX package IDs (these are examples, actual IDs need to be verified)
SUI_DEX_PACKAGES = {
    'Cetus': '0x1eabed72c53feb3805120a081dc15963c204dc8d091542592abaf7a35689b2fb',
    'Turbos': '0x5c45d10c26c5fb53bfaff819666da6bc729b3a57215a66f0f2fc20ff3d6d2a4c',
    'Kriya': '0xa0eba10b173538c8fecca1dff298e488402c9ad3d3743c3f12c2a9c3b4a4c4e4',
    'DeepBook': '0x000000000000000000000000000000000000dee9',  # DeepBook is a core protocol
}


class SuiTradeParser(BlockchainTradeParser):
    """Parses Sui transactions to identify DEX trades"""
    
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
        """Check if transaction interacts with a known DEX package"""
        # For Sui, we need to check package IDs in the transaction
        # This is simplified - in practice, we'd parse the transaction data
        # For now, we'll rely on transfer pattern analysis
        return None  # Will be enhanced with actual package ID checking
    
    def _normalize_coin_type(self, coin_type: str) -> str:
        """Normalize Sui coin type to a consistent format"""
        # Sui coin types can be in different formats
        # 0x2::coin::Coin<0x...::TOKEN::TOKEN>
        # We'll extract the token identifier
        if '::' in coin_type:
            parts = coin_type.split('::')
            if len(parts) >= 3:
                # Extract the token identifier (last part before closing bracket)
                token_part = parts[-1].rstrip('>')
                return token_part
        return coin_type
    
    def _parse_swap_from_transfers(self, tx_hash: str, transfers: List[Dict]) -> Optional[Dict]:
        """Parse a swap from token transfers"""
        our_address_lower = self.address.lower()
        
        # Find transfers involving our address
        our_transfers = []
        for transfer in transfers:
            from_addr = (transfer.get('from') or '').lower()
            to_addr = (transfer.get('to') or '').lower()
            
            if from_addr == our_address_lower or to_addr == our_address_lower:
                our_transfers.append(transfer)
        
        if len(our_transfers) < 2:
            return None
        
        # Aggregate amounts by coin type
        coins_sent = {}  # coin_type -> total_amount
        coins_received = {}  # coin_type -> total_amount
        
        for transfer in our_transfers:
            from_addr = (transfer.get('from') or '').lower()
            to_addr = (transfer.get('to') or '').lower()
            value = int(transfer.get('value', '0'))
            coin_type = transfer.get('contractAddress', '')  # Coin type stored here
            
            # Normalize coin type
            coin_type_normalized = self._normalize_coin_type(coin_type)
            
            if from_addr == our_address_lower:
                coins_sent[coin_type_normalized] = coins_sent.get(coin_type_normalized, 0) + value
            elif to_addr == our_address_lower:
                coins_received[coin_type_normalized] = coins_received.get(coin_type_normalized, 0) + value
        
        # Find the coin we sent most (coin in) and received most (coin out)
        coin_in = max(coins_sent.items(), key=lambda x: x[1])[0] if coins_sent else None
        coin_out = max(coins_received.items(), key=lambda x: x[1])[0] if coins_received else None
        amount_in = coins_sent.get(coin_in, 0) if coin_in else 0
        amount_out = coins_received.get(coin_out, 0) if coin_out else 0
        
        # Only return if it's a real swap: different coins, both amounts > 0
        if coin_in and coin_out and coin_in != coin_out and amount_in > 0 and amount_out > 0:
            tx = self.normal_txs_by_hash.get(tx_hash)
            block_number = tx.get('blockNumber', 0) if tx else 0
            timestamp = tx.get('timeStamp', 0) if tx else 0
            
            return {
                'tx_hash': tx_hash,
                'block_number': block_number,
                'timestamp': timestamp,
                'dex': 'Unknown DEX',  # Will try to identify from package ID later
                'token_in': coin_in,
                'token_out': coin_out,
                'amount_in': str(amount_in),
                'amount_out': str(amount_out),
                'type': 'swap'
            }
        
        return None
    
    def parse_all_trades(self) -> List[Dict]:
        """
        Parse all DEX trades from Sui transaction data
        
        Uses transfer pattern analysis to identify swaps:
        - Sending one coin type AND receiving a different coin type = swap
        """
        print("Analyzing Sui transactions to identify DEX trades (swaps only, not transfers)...")
        print("=" * 60)
        
        processed_hashes = set()
        
        # Process transactions with token transfers
        for tx_hash, transfers in self.token_transfers_by_hash.items():
            if tx_hash in processed_hashes:
                continue
            
            # Check if this transaction involves our address
            our_address_lower = self.address.lower()
            involves_us = any(
                (t.get('from') or '').lower() == our_address_lower or 
                (t.get('to') or '').lower() == our_address_lower 
                for t in transfers
            )
            
            if involves_us and len(transfers) >= 2:
                swap = self._parse_swap_from_transfers(tx_hash, transfers)
                if swap:
                    self.trades.append(swap)
                    processed_hashes.add(tx_hash)
                    print(f"  Found swap: {swap['dex']} - Checkpoint {swap['block_number']}")
        
        # Sort by block number (checkpoint)
        self.trades.sort(key=lambda x: x['block_number'])
        
        print(f"\n✓ Identified {len(self.trades)} DEX trades")
        return self.trades


def main():
    """Main function to parse Sui trades"""
    if len(sys.argv) < 2:
        print("Usage: python parse_sui_trades.py <INPUT_FILE> [OUTPUT_FILE]")
        print("\nExample:")
        print("  python parse_sui_trades.py wallet_trades_sui.json sui_trades.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "sui_trades.json"
    
    print(f"Loading transaction data from {input_file}...")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    parser = SuiTradeParser(data)
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

