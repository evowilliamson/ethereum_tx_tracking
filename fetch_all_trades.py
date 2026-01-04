#!/usr/bin/env python3
"""
Multi-chain DEX trade extractor - fetches, parses, enriches, and exports trades
Reads configuration from blockchain_settings.py and generates CSV files

Usage:
    python fetch_all_trades.py           # Process all chains (EVM + non-EVM) → trades.csv
    python fetch_all_trades.py evm       # Process all EVM chains → evm_trades.csv
    python fetch_all_trades.py binance   # Process binance only → binance_trades.csv
    python fetch_all_trades.py sui       # Process sui only → sui_trades.csv

Debug Mode (SUI only - speeds up testing):
    SUI_DEBUG_MODE=true python fetch_all_trades.py sui  # Only fetch first 50 transactions

Always processes ALL configured addresses for the relevant chain type.
Supports: ethereum, monad, avax, base, arbitrum, binance, linea, katana, polygon, optimism, solana, sui
"""

import sys
import os
import json
import csv
import time
from datetime import datetime
from blockchain_interface import get_fetcher_class, get_parser_class
from enrich_trades_with_tokens import enrich_trades
from calculate_prices import add_prices_to_trades
from chains_config import is_evm_chain


def format_date_for_csv(timestamp):
    """Convert Unix timestamp to format: 2020/09/20 21:36:04"""
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime('%Y/%m/%d %H:%M:%S')
    except:
        return ''


def export_to_csv(enriched_json_file: str, output_csv: str, blockchain: str, address: str, append_mode: bool = False):
    """
    Export enriched trades to CSV format with USD intermediary step.
    Each swap is split into two transactions:
    1. source_currency -> USD (disposition)
    2. USD -> target_currency (acquisition)
    
    Args:
        enriched_json_file: Path to enriched trades JSON
        output_csv: Path to output CSV file (always evm_trades.csv)
        blockchain: Chain name (ethereum, monad, etc.) - used for platform column
        address: Wallet address
        append_mode: If True, append to existing file (skip header). If False, create new file.
    """
    print(f"\nExporting trades to CSV: {output_csv}")
    print("-" * 60)
    
    # Load enriched trades (should have prices if calculate_prices was run)
    with open(enriched_json_file, 'r') as f:
        data = json.load(f)
    
    trades = data.get('trades', [])
    if not trades:
        print("No trades to export")
        return
    
    # Open file in append mode if appending, write mode if creating new
    file_mode = 'a' if append_mode else 'w'
    with open(output_csv, file_mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')  # Tab-separated
        
        # Write header only if creating new file
        if not append_mode:
            writer.writerow([
                'date_time',
                'source_currency',
                'source_amount',
                'target_currency',
                'target_amount',
                'platform',
                'address'
            ])
        
        total_rows = 0
        trades_with_na = 0
        filtered_fees = 0
        
        for trade in trades:
            # Get token symbols and amounts first
            token_in_meta = trade.get('token_in_metadata', {})
            token_out_meta = trade.get('token_out_metadata', {})
            
            token_in_symbol = token_in_meta.get('symbol', 'UNKNOWN')
            token_out_symbol = token_out_meta.get('symbol', 'UNKNOWN')
            
            amount_in = float(trade.get('amount_in_formatted', '0'))
            amount_out = float(trade.get('amount_out_formatted', '0'))
            
            # Filter out small swaps with UNKNOWN tokens (likely fees)
            has_unknown = token_in_symbol == 'UNKNOWN' or token_out_symbol == 'UNKNOWN'
            
            if has_unknown:
                # Get USD value to check if it's a small fee
                source_price = trade.get('source_price_usd', 0)
                target_price = trade.get('target_price_usd', 0)
                
                # Calculate USD value
                if source_price:
                    usd_value = source_price * amount_in
                elif target_price:
                    usd_value = target_price * amount_out
                else:
                    usd_value = 0
                
                # Filter out small swaps with UNKNOWN tokens (likely fees)
                # If USD value is < $10, it's likely a fee payment
                if usd_value > 0 and usd_value < 10:
                    filtered_fees += 1
                    continue  # Skip this trade (likely a fee)
                
                # Also check BNB/ETH amounts directly
                if token_in_symbol == 'BNB' or token_in_symbol == 'ETH':
                    if amount_in < 0.1:  # < 0.1 BNB
                        filtered_fees += 1
                        continue  # Skip this trade (likely a fee)
                elif token_out_symbol == 'BNB' or token_out_symbol == 'ETH':
                    if amount_out < 0.1:  # < 0.1 BNB
                        filtered_fees += 1
                        continue  # Skip this trade (likely a fee)
                # For other tokens, if amount is very small (< 10 units), likely a fee
                elif amount_in < 10 and amount_out < 10:
                    filtered_fees += 1
                    continue  # Skip this trade (likely a fee)
            
            # Use the extracted values
            source_currency = token_in_symbol
            target_currency = token_out_symbol
            source_amount = amount_in
            target_amount = amount_out
            
            # Get prices
            source_price = trade.get('source_price_usd')
            target_price = trade.get('target_price_usd')
            
            # Calculate USD value using source side (leading side)
            source_value = source_price * source_amount if source_price else None
            
            # Format date: 2020/09/20 21:36:04
            date_str = format_date_for_csv(trade.get('timestamp', 0))
            
            # Format USD amount - use "N/A" if source price is missing
            if source_value:
                usd_amount = f"{source_value:.2f}"
            else:
                usd_amount = "N/A"
                trades_with_na += 1
            
            # Row 1: source_currency -> USD (disposition/sale)
            writer.writerow([
                date_str,
                source_currency,
                source_amount,
                'USD',
                usd_amount,
                blockchain,
                address
            ])
            total_rows += 1
            
            # Row 2: USD -> target_currency (acquisition/purchase)
            # Always write the actual target_amount (even if we don't know USD value)
            # Only set target_amount to "N/A" if the actual amount is missing
            if target_amount and target_amount > 0:
                target_amount_str = str(target_amount)
            else:
                target_amount_str = "N/A"
            
            # If usd_amount is "N/A", we still write the row but mark USD as "N/A"
            # This indicates we don't know the USD value, but we know the actual token amounts
            writer.writerow([
                date_str,
                'USD',
                usd_amount,
                target_currency,
                target_amount_str,
                blockchain,
                address
            ])
            total_rows += 1
    
    exported_swaps = len(trades) - filtered_fees
    print(f"✓ Exported {exported_swaps} swaps as {total_rows} transactions")
    if filtered_fees > 0:
        print(f"  ⚠ Filtered out {filtered_fees} small fee payments (UNKNOWN tokens with small amounts)")
    if trades_with_na > 0:
        print(f"  ⚠ {trades_with_na} trades have N/A values (missing prices)")


def process_single_chain_address(chain_name, address, output_csv, append_mode=False):
    """
    Process a single chain for a single address - does everything in one go
    
    Args:
        chain_name: Chain name (e.g., 'base', 'arbitrum', 'sui')
        address: Wallet address
        output_csv: Output CSV file path
        append_mode: If True, append to CSV instead of overwriting (default: False)
    """
    # Load settings from blockchain_settings.py
    try:
        from blockchain_settings import ETHERSCAN_API_KEY
    except ImportError:
        print("Error: blockchain_settings.py not found!")
        print("Please copy blockchain_settings.py.example to blockchain_settings.py and configure it.")
        print("Note: This settings file works for all EVM and non-EVM chains.")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading settings: {e}")
        sys.exit(1)
    
    # Check if settings are configured
    if ETHERSCAN_API_KEY == "YOUR_API_KEY_HERE" or not ETHERSCAN_API_KEY:
        print("Error: ETHERSCAN_API_KEY not set in blockchain_settings.py")
        print("Please edit blockchain_settings.py and set your API key.")
        print("You may also need chain-specific API keys in the API_KEYS dictionary.")
        sys.exit(1)
    
    # Validate blockchain name
    from chains_config import SUPPORTED_CHAINS, get_chain_config
    blockchain = chain_name.lower()
    if blockchain not in SUPPORTED_CHAINS:
        print(f"Error: Blockchain '{blockchain}' not supported.")
        print(f"Supported chains: {', '.join(SUPPORTED_CHAINS)}")
        sys.exit(1)
    
    chain_config = get_chain_config(blockchain)
    
    # Validate address
    if not address:
        chain_type = "EVM" if is_evm_chain(blockchain) else "non-EVM"
        print(f"Error: Address not provided for {blockchain} ({chain_type} chain)")
        sys.exit(1)
    
    # Get chain-specific API key/RPC endpoint
    try:
        from blockchain_settings import API_KEYS
        # For EVM chains, use API keys
        if is_evm_chain(blockchain):
            api_key = API_KEYS.get(blockchain, ETHERSCAN_API_KEY) if 'API_KEYS' in dir() else ETHERSCAN_API_KEY
        else:
            # For Solana/Sui, use RPC endpoint from chain config (no API key needed for public RPCs)
            api_key = chain_config.get('rpc_endpoint', '')
    except ImportError:
        if is_evm_chain(blockchain):
            api_key = ETHERSCAN_API_KEY
        else:
            api_key = chain_config.get('rpc_endpoint', '')
    
    # Output file names (chain-specific JSON files, but single CSV for all chains)
    # Use address suffix to differentiate between multiple addresses
    address_suffix = address[-8:] if len(address) >= 8 else address  # Last 8 chars of address for file naming
    intermediate_json = f"wallet_trades_{blockchain}_{address_suffix}.json"
    parsed_json = f"{blockchain}_trades_{address_suffix}.json"
    enriched_json = f"{blockchain}_trades_enriched_{address_suffix}.json"
    priced_json = f"{blockchain}_trades_enriched_priced_{address_suffix}.json"
    # output_csv is already set from parameter or default above
    
    print("=" * 60)
    print(f"{chain_config['name']} DEX Trade Extractor - All-in-One")
    print("=" * 60)
    print(f"Chain: {chain_config['name']} ({blockchain})")
    print(f"Address: {address}")
    print(f"Output CSV: {output_csv}")
    # Reminder for Sui debug mode
    if blockchain.lower() == 'sui':
        import os
        if os.getenv('SUI_DEBUG_MODE', 'false').lower() != 'true':
            print("💡 TIP: Sui can be slow. Set SUI_DEBUG_MODE=true for faster testing (first page only)")
    print("=" * 60)
    
    # Step 1: Fetch transactions
    print(f"\n[Step 1/5] Fetching transactions from {chain_config['name']} explorer...")
    print("-" * 60)
    
    # Get appropriate fetcher class
    FetcherClass = get_fetcher_class(blockchain)
    fetcher = FetcherClass(api_key, address, blockchain)
    
    # Validate address format
    if not fetcher.validate_address(address):
        print(f"Error: Invalid {blockchain} address format")
        sys.exit(1)
    data = fetcher.fetch_all_data()
    
    print(f"Saving transaction data to {intermediate_json}...")
    with open(intermediate_json, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✓ Transaction data saved")
    
    # Step 2: Parse trades
    print("\n[Step 2/5] Parsing DEX trades...")
    print("-" * 60)
    
    # Get appropriate parser class
    ParserClass = get_parser_class(blockchain)
    parser = ParserClass(data)
    trades = parser.parse_all_trades()
    
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
    
    print(f"Saving parsed trades to {parsed_json}...")
    with open(parsed_json, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"✓ Parsed {len(trades)} trades")
    
    # Step 3: Enrich with token metadata
    print(f"\n[Step 3/5] Enriching trades with token metadata...")
    print("-" * 60)
    
    if len(trades) > 0:
        enrich_trades(parsed_json, enriched_json, api_key, transaction_data_file=intermediate_json, chain_name=blockchain)
    else:
        # No trades to enrich, create empty enriched file
        print("No trades to enrich, creating empty enriched file...")
        empty_data = {
            "address": address,
            "total_trades": 0,
            "trades": []
        }
        with open(enriched_json, 'w') as f:
            json.dump(empty_data, f, indent=2)
        print(f"✓ Created {enriched_json}")
    
    # Step 4: Calculate USD prices (only if we have trades)
    print("\n[Step 4/5] Calculating USD prices...")
    if len(trades) > 0:
        add_prices_to_trades(enriched_json, priced_json)
    else:
        # No trades, use enriched file directly
        priced_json = enriched_json
    
    # Step 5: Export to CSV
    print("\n[Step 5/5] Exporting to CSV...")
    # append_mode is now passed as parameter
    export_to_csv(priced_json, output_csv, blockchain, address, append_mode=append_mode)
    
    # Final summary
    print("\n" + "=" * 60)
    print("Complete!")
    print("=" * 60)
    print(f"✓ Fetched transactions")
    print(f"✓ Parsed {len(trades)} DEX trades")
    print(f"✓ Enriched with token metadata")
    print(f"✓ Calculated USD prices")
    print(f"✓ Exported to CSV: {output_csv}")
    print("=" * 60)
    
    # Show summary stats
    if trades:
        dex_counts = {}
        for trade in trades:
            dex = trade.get('dex', 'Unknown')
            dex_counts[dex] = dex_counts.get(dex, 0) + 1
        
        print("\nTrades by DEX:")
        for dex, count in sorted(dex_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {dex}: {count}")
        
        timestamps = [t['timestamp'] for t in trades if t.get('timestamp')]
        if timestamps:
            min_time = min(timestamps)
            max_time = max(timestamps)
            min_date = datetime.fromtimestamp(min_time).strftime("%Y-%m-%d")
            max_date = datetime.fromtimestamp(max_time).strftime("%Y-%m-%d")
            print(f"\nDate range: {min_date} to {max_date}")
    
    print("\n" + "=" * 60)


def main(mode=None):
    """
    Main entry point that handles different processing modes:
    - None or "all": Process all chains (EVM + non-EVM) → trades.csv
    - "evm": Process all EVM chains → evm_trades.csv
    - Specific chain name: Process that chain only → {chain}_trades.csv
    
    Always processes ALL addresses for the relevant chain type.
    
    Args:
        mode: Processing mode - None/"all", "evm", or specific chain name
    """
    # Load settings
    try:
        from blockchain_settings import ETHERSCAN_API_KEY, WALLET_ADDRESSES, NON_EVM_ADDRESSES
        from chains_config import SUPPORTED_CHAINS, is_evm_chain
    except ImportError as e:
        print(f"Error: blockchain_settings.py not found! {e}")
        print("Please copy blockchain_settings.py.example to blockchain_settings.py and configure it.")
        sys.exit(1)
    
    # Check if settings are configured
    if ETHERSCAN_API_KEY == "YOUR_API_KEY_HERE" or not ETHERSCAN_API_KEY:
        print("Error: ETHERSCAN_API_KEY not set in blockchain_settings.py")
        print("Please edit blockchain_settings.py and set your API key.")
        sys.exit(1)
    
    # Determine which chains to process
    if mode is None or mode.lower() == "all":
        # Process all chains (EVM + non-EVM)
        chains_to_process = SUPPORTED_CHAINS
        output_csv = "trades.csv"
        mode_name = "All Chains"
    elif mode.lower() == "evm":
        # Process all EVM chains only
        chains_to_process = [chain for chain in SUPPORTED_CHAINS if is_evm_chain(chain)]
        output_csv = "evm_trades.csv"
        mode_name = "All EVM Chains"
    else:
        # Process specific chain
        chain_name = mode.lower()
        if chain_name not in SUPPORTED_CHAINS:
            print(f"Error: Chain '{chain_name}' not supported.")
            print(f"Supported chains: {', '.join(SUPPORTED_CHAINS)}")
            print("Use 'evm' to process all EVM chains, or no parameter to process all chains.")
            sys.exit(1)
        chains_to_process = [chain_name]
        output_csv = f"{chain_name}_trades.csv"
        mode_name = f"{chain_name.upper()} Chain"
    
    # Remove existing output CSV to start fresh
    if os.path.exists(output_csv):
        print(f"Removing existing {output_csv} to start fresh...")
        os.remove(output_csv)
        print(f"✓ Removed {output_csv}\n")
    
    print("=" * 80)
    print(f"Multi-Chain DEX Trade Extractor - {mode_name}")
    print("=" * 80)
    print(f"Chains to process: {', '.join(chains_to_process)}")
    print(f"Output CSV: {output_csv}")
    print("=" * 80)
    print()
    
    results = {}
    first_run = True
    
    # Process each chain
    for chain in chains_to_process:
        print("\n" + "=" * 80)
        print(f"Processing {chain.upper()}")
        print("=" * 80)
        
        # Get addresses for this chain type
        if is_evm_chain(chain):
            addresses = WALLET_ADDRESSES
            if not addresses or len(addresses) == 0:
                print(f"⚠ Warning: No EVM addresses configured. Skipping {chain}.")
                results[chain] = "skipped: no addresses"
                continue
        else:
            # For non-EVM chains, get address(es) from NON_EVM_ADDRESSES
            chain_address_data = NON_EVM_ADDRESSES.get(chain, '')
            if not chain_address_data:
                print(f"⚠ Warning: No address configured for {chain}. Skipping.")
                results[chain] = "skipped: no address"
                continue
            # Handle both single address (string) and list of addresses
            if isinstance(chain_address_data, list):
                addresses = chain_address_data
            else:
                addresses = [chain_address_data] if chain_address_data else []
            if not addresses:
                print(f"⚠ Warning: No valid address(es) for {chain}. Skipping.")
                results[chain] = "skipped: no address"
                continue
        
        # Process each address for this chain
        for address in addresses:
            print(f"\nProcessing address: {address[:10]}...")
            
            try:
                process_single_chain_address(
                    chain_name=chain,
                    address=address,
                    output_csv=output_csv,
                    append_mode=not first_run
                )
                
                results[f"{chain}-{address[:10]}"] = "success"
                first_run = False
                
            except KeyboardInterrupt:
                print(f"\n⚠ Interrupted by user")
                results[f"{chain}-{address[:10]}"] = "interrupted"
                break
            except Exception as e:
                print(f"\n✗ {chain.upper()} for {address[:10]} failed: {e}")
                import traceback
                traceback.print_exc()
                results[f"{chain}-{address[:10]}"] = f"error: {str(e)}"
    
    # Sort the final CSV by date_time (descending) if file exists and has data
    if os.path.exists(output_csv):
        try:
            import csv
            from datetime import datetime
            
            # Read all rows
            with open(output_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                header = reader.fieldnames
                rows = list(reader)
            
            if rows:
                # Sort by date_time (descending - most recent first)
                def parse_date(date_str):
                    try:
                        # Format: 2025/07/29 18:32:35
                        return datetime.strptime(date_str, '%Y/%m/%d %H:%M:%S')
                    except:
                        return datetime.min
                
                rows.sort(key=lambda x: parse_date(x.get('date_time', '')), reverse=True)
                
                # Write sorted rows back
                with open(output_csv, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=header, delimiter='\t')
                    writer.writeheader()
                    writer.writerows(rows)
                
                print(f"\n✓ Sorted {len(rows)} trades by date_time (descending)")
        except Exception as e:
            print(f"⚠ Warning: Could not sort CSV: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for key, status in results.items():
        status_symbol = "✓" if status == "success" else "✗"
        print(f"  {status_symbol} {key.upper()}: {status}")
    print("=" * 80)


if __name__ == "__main__":
    # Parse command-line arguments
    # Usage:
    #   python fetch_all_trades.py           → all chains → trades.csv
    #   python fetch_all_trades.py evm        → all EVM chains → evm_trades.csv
    #   python fetch_all_trades.py binance    → binance only → binance_trades.csv
    #   python fetch_all_trades.py sui       → sui only → sui_trades.csv
    
    mode = None
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    
    main(mode=mode)

