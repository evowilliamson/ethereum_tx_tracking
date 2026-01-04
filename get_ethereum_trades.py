"""
Main script to fetch and parse all Ethereum DEX trades
Orchestrates the entire process: fetch transactions -> parse trades -> save results
"""

import sys
import os
from fetch_ethereum_transactions import EthereumTransactionFetcher
from parse_ethereum_trades import EthereumTradeParser


def main():
    """Main orchestrator function"""
    # Try to load from config file first
    api_key = None
    address = None
    output_file = "ethereum_trades.json"
    
    try:
        from blockchain_settings import ETHERSCAN_API_KEY, WALLET_ADDRESS, OUTPUT_FILE as CONFIG_OUTPUT
        if ETHERSCAN_API_KEY != "YOUR_API_KEY_HERE" and WALLET_ADDRESS != "0xYourWalletAddressHere":
            api_key = ETHERSCAN_API_KEY
            address = WALLET_ADDRESS
            if CONFIG_OUTPUT != "ethereum_trades.json":
                output_file = CONFIG_OUTPUT
    except ImportError:
        pass
    except Exception:
        pass
    
    # Override with command line arguments if provided
    if len(sys.argv) >= 3:
        api_key = sys.argv[1]
        address = sys.argv[2]
    
    # If still no credentials, show usage
    if not api_key or not address:
        print("=" * 60)
        print("Ethereum DEX Trade Extractor")
        print("=" * 60)
        print("\nYou can provide credentials in two ways:")
        print("\nOption 1: Edit blockchain_settings.py")
        print("  - Open blockchain_settings.py")
        print("  - Replace YOUR_API_KEY_HERE with your Etherscan API key")
        print("  - Replace 0xYourWalletAddressHere with your wallet address")
        print("  - Then run: python get_ethereum_trades.py")
        print("\nOption 2: Command line arguments")
        print("  python get_ethereum_trades.py <API_KEY> <ADDRESS> [OPTIONS]")
        print("\nArguments:")
        print("  API_KEY    Your Etherscan API key")
        print("  ADDRESS    Your Ethereum wallet address (0x...)")
        print("\nOptions:")
        print("  --skip-fetch    Skip fetching and use existing wallet_trades.json")
        print("  --output FILE   Specify output file (default: ethereum_trades.json)")
        print("\nExample:")
        print("  python get_ethereum_trades.py YOUR_API_KEY 0xYourAddress")
        print("\nGet API key: https://etherscan.io/apis")
        print("\nThis script will:")
        print("  1. Fetch all transactions from Etherscan")
        print("  2. Identify DEX swaps across all protocols")
        print("  3. Save trades to JSON file")
        sys.exit(1)
    
    # Parse options
    skip_fetch = '--skip-fetch' in sys.argv
    if '--output' in sys.argv:
        idx = sys.argv.index('--output')
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]
    
    intermediate_file = "wallet_trades.json"
    
    print("=" * 60)
    print("Ethereum DEX Trade Extractor")
    print("=" * 60)
    print(f"Address: {address}")
    print(f"Output: {output_file}")
    print("=" * 60)
    print("\nNOTE: If you get 'deprecated V1 endpoint' errors,")
    print("Etherscan has migrated to V2. Check API_V2_NOTE.md for solutions.")
    print("=" * 60)
    
    # Step 1: Fetch transactions
    if not skip_fetch:
        print("\n[Step 1/2] Fetching transactions from Etherscan...")
        print("-" * 60)
        
        if not address.startswith('0x') or len(address) != 42:
            print("Error: Invalid Ethereum address format")
            sys.exit(1)
        
        fetcher = EthereumTransactionFetcher(api_key, address)
        data = fetcher.fetch_all_data()
        
        # Save intermediate data
        print(f"\nSaving transaction data to {intermediate_file}...")
        import json
        with open(intermediate_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✓ Transaction data saved")
    else:
        print("\n[Step 1/2] Skipping fetch (using existing data)...")
        if not os.path.exists(intermediate_file):
            print(f"Error: {intermediate_file} not found!")
            sys.exit(1)
        
        import json
        with open(intermediate_file, 'r') as f:
            data = json.load(f)
        print(f"✓ Loaded existing transaction data")
    
    # Step 2: Parse trades
    print("\n[Step 2/2] Parsing DEX trades...")
    print("-" * 60)
    
    parser = EthereumTradeParser(data)
    trades = parser.parse_all_trades()
    
    # Prepare final output
    import json
    import time
    output = {
        "address": address,
        "total_trades": len(trades),
        "trades": trades,
        "metadata": {
            "parsed_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "total_transactions": data.get('metadata', {}).get('total_normal', 0),
            "total_erc20_transfers": data.get('metadata', {}).get('total_erc20', 0)
        }
    }
    
    # Save results
    print(f"\nSaving trades to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ Saved {len(trades)} trades to {output_file}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total DEX trades found: {len(trades)}")
    print("(Only swaps/trades, not simple transfers)")
    
    if trades:
        # Group by DEX
        dex_counts = {}
        for trade in trades:
            dex = trade.get('dex', 'Unknown')
            dex_counts[dex] = dex_counts.get(dex, 0) + 1
        
        print("\nTrades by DEX:")
        for dex, count in sorted(dex_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {dex}: {count}")
        
        # Show date range
        timestamps = [t['timestamp'] for t in trades if t.get('timestamp')]
        if timestamps:
            import datetime
            min_time = min(timestamps)
            max_time = max(timestamps)
            min_date = datetime.datetime.fromtimestamp(min_time).strftime("%Y-%m-%d")
            max_date = datetime.datetime.fromtimestamp(max_time).strftime("%Y-%m-%d")
            print(f"\nDate range: {min_date} to {max_date}")
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()

