# Architecture Extension for Solana and Sui Support

This document describes the architecture extension that enables support for Solana and Sui blockchains in addition to the existing EVM chains.

## Overview

The extension introduces an abstraction layer that allows the transaction extractor and tax calculator to work with both EVM-compatible chains (Ethereum, Base, Arbitrum, etc.) and non-EVM chains (Solana, Sui).

## Architecture Components

### 1. Blockchain Interface (`blockchain_interface.py`)

The core abstraction layer defines two base classes:

- **`BlockchainTransactionFetcher`**: Abstract base class for fetching transactions
  - `fetch_all_data()`: Returns standardized transaction data format
  - `validate_address()`: Validates address format for the chain

- **`BlockchainTradeParser`**: Abstract base class for parsing trades
  - `parse_all_trades()`: Returns standardized trade format

Factory functions:
- `get_fetcher_class(chain_name)`: Returns appropriate fetcher class
- `get_parser_class(chain_name)`: Returns appropriate parser class

### 2. Chain-Specific Implementations

#### EVM Chains
- **`EthereumTransactionFetcher`**: Extends `BlockchainTransactionFetcher`
  - Uses Etherscan-compatible APIs
  - Fetches normal transactions, ERC-20 transfers, internal transactions

- **`EthereumTradeParser`**: Extends `BlockchainTradeParser`
  - Parses EVM transactions using ERC-20 transfer patterns
  - Detects DEX interactions via router addresses and function signatures

#### Solana
- **`SolanaTransactionFetcher`**: Extends `BlockchainTransactionFetcher`
  - Uses Solana RPC API (`getSignaturesForAddress`, `getTransaction`)
  - Fetches transactions and token transfers (SPL tokens)
  - Parses token balance changes from transaction metadata

- **`SolanaTradeParser`**: Extends `BlockchainTradeParser`
  - Analyzes SPL token transfers to identify swaps
  - Uses transfer pattern analysis (send token A, receive token B)

#### Sui
- **`SuiTransactionFetcher`**: Extends `BlockchainTransactionFetcher`
  - Uses Sui RPC API (`suix_getTransactions`, `sui_getTransactionBlock`)
  - Fetches transactions and coin transfers
  - Parses balance changes and object changes

- **`SuiTradeParser`**: Extends `BlockchainTradeParser`
  - Analyzes coin transfers to identify swaps
  - Uses transfer pattern analysis with coin types

### 3. Token Metadata Enrichment

The `enrich_trades_with_tokens.py` module now supports chain-specific token metadata fetchers:

- **`TokenMetadataFetcher`**: For EVM chains (uses Etherscan API)
- **`SolanaTokenMetadataFetcher`**: For Solana (uses Solana RPC)
- **`SuiTokenMetadataFetcher`**: For Sui (extracts from coin type format)

### 4. Chain Configuration

Updated `chains_config.py`:
- Added `solana` and `sui` to `SUPPORTED_CHAINS`
- Added chain configurations with RPC endpoints
- Added `is_evm_chain()` helper function
- Added `chain_type` field to distinguish EVM vs non-EVM chains

### 5. Main Processing Script

Updated `fetch_all_trades.py`:
- Uses factory functions to get appropriate fetcher/parser classes
- Handles both API keys (EVM) and RPC endpoints (non-EVM)
- Works seamlessly with all chain types

## Standardized Data Formats

### Transaction Data Format

All fetchers return data in this format:
```python
{
    "address": str,
    "normal_transactions": List[Dict],
    "erc20_token_transfers": List[Dict],  # SPL transfers for Solana, coin transfers for Sui
    "internal_transactions": List[Dict],  # Empty for non-EVM chains
    "metadata": {
        "total_normal": int,
        "total_erc20": int,
        "total_internal": int,
        "fetched_at": str
    }
}
```

### Trade Format

All parsers return trades in this format:
```python
{
    'tx_hash': str,
    'block_number': int,  # Slot for Solana, checkpoint for Sui
    'timestamp': int,  # Unix timestamp
    'dex': str,  # DEX name
    'token_in': str,  # Token address/mint/coin type
    'token_out': str,
    'amount_in': str,  # Raw amount
    'amount_out': str,
    'type': 'swap'
}
```

## Usage

### Configuration

Add RPC endpoints to `ethereum_settings.py`:
```python
RPC_ENDPOINTS = {
    'solana': 'https://api.mainnet-beta.solana.com',
    'sui': 'https://fullnode.mainnet.sui.io:443',
}
```

### Running

The same commands work for all chains:
```bash
# Process all chains (including Solana and Sui)
python fetch_all_chains_trades.py

# Process a specific chain
python fetch_all_trades.py solana
python fetch_all_trades.py sui
```

## Price Calculation and Tax Calculator

The existing price calculation (`calculate_prices.py`) and tax calculator (`calculate_fifo_taxes.py`) work with all chains because they operate on the standardized trade format. No changes were needed.

## Future Enhancements

1. **DEX Identification**: Enhance parsers to identify specific DEXes from program/package IDs
2. **Token Metadata**: Integrate with token registries (Solana Token List, Sui token metadata)
3. **Performance**: Add caching and batch RPC requests
4. **Error Handling**: Improve error messages for chain-specific issues

## Testing

To test the new chains:

1. **Solana**:
   ```bash
   python fetch_solana_transactions.py https://api.mainnet-beta.solana.com <SOLANA_ADDRESS>
   python parse_solana_trades.py wallet_trades_solana.json
   ```

2. **Sui**:
   ```bash
   python fetch_sui_transactions.py https://fullnode.mainnet.sui.io:443 <SUI_ADDRESS>
   python parse_sui_trades.py wallet_trades_sui.json
   ```

## Notes

- Solana addresses are base58 encoded (32-44 characters)
- Sui addresses start with `0x` and are 66 characters total
- Both chains use different RPC APIs than EVM chains
- Token transfers are identified through balance changes rather than event logs
- The abstraction layer ensures backward compatibility with all existing EVM chains

