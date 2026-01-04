# Multi-Chain EVM DEX Trade Extractor

A comprehensive tool to extract **ALL** DEX trades from your wallet addresses across **multiple EVM-compatible blockchains**. Perfect for tax reporting, trading analysis, and portfolio tracking.

## Features

- 🔗 **Multi-Chain Support**: Extracts trades from 9+ EVM-compatible blockchains
- 👛 **Multiple Addresses**: Process multiple wallet addresses in one run
- 💰 **USD Pricing**: Automatically calculates USD values for all trades using historical price data
- 📊 **Tax-Ready CSV**: Exports trades in a format optimized for tax software (Koinly, CoinTracker, etc.)
- 🔍 **Comprehensive DEX Detection**: Identifies trades from all major DEX protocols via pattern matching
- ⚡ **Smart Price Calculation**: Handles complex tokens (Pendle PTs, protocol stablecoins, etc.)
- 📅 **Chronological Processing**: Trades sorted by date/time for accurate tax reporting

## Supported Blockchains

- **Ethereum** (Mainnet)
- **Monad**
- **Arbitrum**
- **Base**
- **Linea**
- **Optimism**
- **Polygon**
- **Katana (Ronin)**
- **Binance Smart Chain (BSC)**

## Supported DEX Protocols

The tool automatically detects trades from all major DEXes via pattern matching:

- Uniswap V2 & V3
- SushiSwap
- Curve Finance
- 1inch (V4 & V5)
- Balancer V2
- 0x Protocol
- KyberSwap
- DODO
- Paraswap
- CowSwap (CoW Protocol)
- Bancor Network
- And more (any swap detected via transfer pattern analysis)

## Installation

### Prerequisites

- Python 3.7 or higher
- API keys:
  - **Ethereum & most chains**: Etherscan API key (free tier works) - get one at [https://etherscan.io/apis](https://etherscan.io/apis)
  - **BSC (Binance Smart Chain)**: BSCTrace API key (free) - get one at [https://nodereal.io/meganode](https://nodereal.io/meganode)

### Step 1: Clone or Download

```bash
git clone <repository-url>
cd ethereum_tx_tracking
```

### Step 2: Install Dependencies

```bash
pip install requests python-dotenv
```

Optional but recommended:
```bash
pip install python-dotenv  # For .env file support
```

### Step 3: Configure Settings

1. Copy the example settings file:
   ```bash
   cp ethereum_settings.py.example ethereum_settings.py
   ```

2. Edit `ethereum_settings.py` and add:
   - Your Etherscan API key
   - Your wallet address(es)
   - Optional: Chain-specific API keys

   ```python
   # Required: Your Etherscan API key
   ETHERSCAN_API_KEY = "your_etherscan_api_key_here"
   
   # Required: List of wallet addresses to process
   WALLET_ADDRESSES = [
       "0xYourFirstWalletAddress",
       "0xYourSecondWalletAddress",
   ]
   ```

**Important**: `ethereum_settings.py` is gitignored to protect your API keys and addresses. Never commit this file!

### Step 4: (Optional) Environment Variables

Instead of editing the settings file, you can use environment variables:

```bash
export ETHERSCAN_API_KEY="your_api_key"
export WALLET_ADDRESSES="0xAddress1,0xAddress2"
```

Or create a `.env` file:
```
ETHERSCAN_API_KEY=your_api_key
WALLET_ADDRESSES=0xAddress1,0xAddress2
```

## Quick Start

Run the main script to process all configured chains and addresses:

```bash
python3 fetch_all_chains_trades.py
```

This will:
1. Process all supported blockchains
2. Process all wallet addresses in `WALLET_ADDRESSES`
3. Fetch transactions from each chain
4. Parse and identify DEX trades
5. Enrich with token metadata
6. Calculate USD prices
7. Export to `evm_trades.csv`

The output CSV file (`evm_trades.csv`) will contain all trades from all chains and addresses, sorted by date (most recent first).

## Usage Examples

### Process All Chains for All Addresses

```bash
python3 fetch_all_chains_trades.py
```

### Process a Single Chain for One Address

```bash
python3 fetch_all_trades.py --chain-name ethereum
```

Or edit `chains_config.py` to modify `SUPPORTED_CHAINS` and only include the chains you want.

## Output Format

The tool generates `evm_trades.csv` with the following columns:

| Column | Description |
|--------|-------------|
| `date_time` | Transaction timestamp (YYYY/MM/DD HH:MM:SS) |
| `source_currency` | Token symbol you're selling |
| `source_amount` | Amount of source token |
| `target_currency` | Token symbol you're buying (or USD for intermediary step) |
| `target_amount` | Amount of target token (or USD value) |
| `platform` | Blockchain name (ethereum, monad, arbitrum, etc.) |
| `address` | Wallet address that made the trade |

### Tax Reporting Format

For tax reporting, each swap is split into two USD intermediary transactions:
- `TOKEN_A → USD`: Source token to USD conversion
- `USD → TOKEN_B`: USD to target token conversion

This format is required by most tax software and ensures accurate USD valuations.

### Example Output

```csv
date_time	source_currency	source_amount	target_currency	target_amount	platform	address
2026/01/02 22:15:59	USDC	18987.522451	USD	18987.52	monad	0xb77Cb8F81A0f704E1E858EBa57C67c072ABBFCAD
2026/01/02 22:15:59	USD	18987.52	edgeUSDC	18981.235905	monad	0xb77Cb8F81A0f704E1E858EBa57C67c072ABBFCAD
2025/12/29 13:59:23	USDC	31356.7798	USD	31356.78	ethereum	0xb77Cb8F81A0f704E1E858EBa57C67c072ABBFCAD
2025/12/29 13:59:23	USD	31356.78	USDT	31383.33874	ethereum	0xb77Cb8F81A0f704E1E858EBa57C67c072ABBFCAD
```

## How It Works

### 1. Transaction Fetching

For each blockchain and address:
- Fetches all normal transactions
- Fetches all ERC-20 token transfers
- Fetches all internal transactions
- Respects API rate limits automatically

### 2. DEX Trade Identification

Uses multiple strategies to identify swaps:

#### Strategy 1: DEX Router Detection
- Checks if transaction interacts with known DEX router addresses
- Identifies DEX by router contract address

#### Strategy 2: Function Signature Matching
- Analyzes transaction input data
- Matches against 20+ known swap function signatures

#### Strategy 3: Transfer Pattern Analysis
- Groups ERC-20 transfers by transaction hash
- Identifies swaps when your address sends one token and receives another
- Handles multiple transfers of the same token (aggregates amounts)

#### Strategy 4: ETH Swap Detection
- Detects swaps involving native ETH
- Handles WETH wrapping/unwrapping

### 3. Token Metadata Enrichment

- Extracts token metadata (name, symbol, decimals) from transaction data
- Falls back to Etherscan API if needed
- Uses known tokens database for common tokens

### 4. USD Price Calculation

Smart pricing system that handles:

- **Standard Tokens**: Fetches historical prices from CoinGecko
- **Stablecoins**: Uses 1:1 USD ratio
- **Protocol Stablecoins**: Identifies protocol derivatives (e.g., vbUSDC, PT-sUSDE) and uses underlying asset pricing
- **Pendle PTs**: Extracts underlying asset from token name and prices accordingly
- **Missing Prices**: Marks as "N/A" if price cannot be determined

Uses a 30-day lookup window and processes trades chronologically to build an incremental price feed.

### 5. CSV Export

- Splits each swap into two USD intermediary transactions
- Formats dates as `YYYY/MM/DD HH:MM:SS`
- Sorts all trades by date (descending - most recent first)
- Includes platform and address columns for multi-chain/multi-address tracking

## Configuration

### Adding/Removing Chains

Edit `chains_config.py`:

```python
# To process only specific chains:
SUPPORTED_CHAINS = ['ethereum', 'arbitrum', 'base']

# To add a new chain, add it to the CHAINS dictionary:
CHAINS['your_chain'] = {
    'name': 'Your Chain',
    'api_base': 'https://api.yourexplorer.com/api',
    'chain_id': '12345',
    'native_token': 'ETH',
    'weth_address': '0x...',
    'explorer_url': 'https://yourexplorer.com',
}
```

### Adding DEX Routers

Edit `ethereum_config.py` to add new DEX router addresses or swap function signatures.

### Modifying Price Calculation

Edit `calculate_prices.py` to:
- Adjust the price lookup window (default: 30 days)
- Add new protocol stablecoins
- Customize pricing logic

## API Keys

### Required

- **Etherscan API Key**: Get one for free at [https://etherscan.io/apis](https://etherscan.io/apis)
  - Most chains use Etherscan API V2, which supports multiple chains with a single key
  - Free tier allows 5 calls/second (sufficient for most use cases)

### Optional (Chain-Specific)

Some chains may work better with their native explorer API keys:
- Base: [https://basescan.org/apis](https://basescan.org/apis)
- Arbitrum: [https://arbiscan.io/apis](https://arbiscan.io/apis)
- Polygon: [https://polygonscan.com/apis](https://polygonscan.com/apis)
- Optimism: [https://optimistic.etherscan.io/apis](https://optimistic.etherscan.io/apis)

Add chain-specific keys in `ethereum_settings.py`:

```python
API_KEYS = {
    'ethereum': 'your_etherscan_key',
    'base': 'your_basescan_key',  # Optional
    # ... etc
}
```

## Rate Limits

The script automatically handles rate limits:
- **Free Etherscan API**: 5 calls/second
- Automatic delays between requests
- Progress indicators show fetch status

For large wallets or many chains, the script may take several minutes to complete. This is normal.

## Troubleshooting

### No trades found

- **Check your address**: Verify the address format (0x followed by 40 hex characters)
- **Verify transactions exist**: Check the blockchain explorer directly
- **Check chain support**: Ensure the chain is in `SUPPORTED_CHAINS`

### API errors (403, rate limit, etc.)

- **Verify API key**: Check your Etherscan API key is valid
- **Check rate limits**: Wait a few minutes if rate limited
- **Optimism**: May require chain-specific API keys or paid Etherscan plan
- **BSC (Binance Smart Chain)**: Uses BSCTrace API (free) - get API key at [https://nodereal.io/meganode](https://nodereal.io/meganode). Note: BSCScan API was deprecated in Dec 2025.

### Missing USD prices

- **Complex tokens**: Some tokens (like custom Pendle PTs) may show "N/A" if pricing logic can't determine underlying asset
- **Old trades**: Prices older than 30 days may use closest available price
- **Manual review**: Check `evm_trades.csv` and manually price trades marked "N/A"

### Missing trades

- **DEX not recognized**: The tool uses pattern matching, so it should catch most swaps even if DEX is unknown
- **Non-standard swaps**: Some protocols use unique patterns - check transaction on explorer manually
- **Low-value swaps**: All swaps are included regardless of size

## Files Created

### Output Files

- `evm_trades.csv`: **Main output** - All trades from all chains/addresses (use this for tax software)

### Intermediate Files (for debugging)

- `wallet_trades_{chain}_{address_suffix}.json`: Raw transaction data from explorer
- `{chain}_trades_{address_suffix}.json`: Parsed trades (before enrichment)
- `{chain}_trades_enriched_{address_suffix}.json`: Trades with token metadata
- `{chain}_trades_enriched_priced_{address_suffix}.json`: Trades with USD prices

These intermediate files are useful for debugging but can be deleted to save space.

## Importing to Tax Software

### Koinly

1. Export trades: The CSV format is compatible with Koinly
2. Import: Use Koinly's CSV import feature
3. Verify: Check that all trades are recognized correctly

### CoinTracker

1. Export trades: The CSV should work with CoinTracker's generic format
2. Map columns if needed: CoinTracker may require column mapping
3. Verify: Check that USD values are imported correctly

### Generic Tax Software

The CSV format uses tab-separated values with clear column headers. Most tax software can import this format directly or with minor adjustments.

## CryptoCompare Hourly Price Data

This tool includes functionality to download historical hourly cryptocurrency price data from CryptoCompare API.

### Features

- 📊 **Hourly Historical Data**: Downloads hourly price data for any cryptocurrency
- 💾 **Dual Storage**: Saves data to both CSV files and QuestDB database
- 🔄 **Incremental Updates**: Smart deduplication - only inserts new data, updates existing records
- 📅 **Flexible Date Ranges**: Fetch all available data or specify a date range
- ⚡ **Efficient Pagination**: Automatically handles API pagination for large datasets
- 🔒 **Data Integrity**: Atomic file operations prevent data corruption

### Installation

#### 1. Install Python Dependencies

```bash
pip install requests psycopg2-binary
```

#### 2. Install QuestDB (Optional but Recommended)

QuestDB is an open-source time-series database optimized for fast queries. It's optional - the script works with CSV-only mode if QuestDB is not installed.

**Quick Installation (Ubuntu/Debian):**

```bash
./install_questdb.sh
```

This script:
- Downloads and installs QuestDB binary
- Installs Java (OpenJDK 17) if needed
- Installs Python package `psycopg2-binary`
- Sets up QuestDB in `/opt/questdb`

**Manual Installation:**

Follow the instructions at [https://questdb.io/get-questdb/](https://questdb.io/get-questdb/)

**Start QuestDB:**

```bash
./start_questdb.sh
```

This starts QuestDB with data directory: `~/.dex_trades_extractor/.questdb/`

**Stop QuestDB:**

```bash
./stop_questdb.sh
```

**Uninstall QuestDB:**

```bash
./uninstall_questdb.sh
```

For more details, see `QUESTDB_SETUP.md`.

### Usage

#### Basic Usage - Fetch All Available Data

```bash
python3 download_cryptocompare_hourly.py BTC USD
```

This downloads all available hourly data for BTC/USD from the earliest point in time.

#### Fetch Specific Date Range

```bash
python3 download_cryptocompare_hourly.py BTC USD 2025/01/01 2025/09/01
```

This downloads hourly data from `2025/01/01 00:00:00` to `(2025/09/01 + 1 day) 00:00:00` (exclusive).

**Date Format**: `YYYY/MM/DD`

**Examples:**

```bash
# Fetch BTC data for January 2025
python3 download_cryptocompare_hourly.py BTC USD 2025/01/01 2025/01/31

# Fetch ETH data for Q1 2021
python3 download_cryptocompare_hourly.py ETH USD 2021/01/01 2021/03/31

# Fetch all available BTC data
python3 download_cryptocompare_hourly.py BTC USD
```

#### API Key (Optional)

The script works with CryptoCompare's free tier (no API key required). For higher rate limits, you can provide an API key:

```bash
export CRYPTOCOMPARE_API_KEY="your_api_key_here"
python3 download_cryptocompare_hourly.py BTC USD 2025/01/01 2025/09/01
```

Get a free API key at [https://www.cryptocompare.com/cryptopian/api-keys](https://www.cryptocompare.com/cryptopian/api-keys)

### Output

#### CSV Files

CSV files are stored in: `~/.dex_trades_extractor/.files/price/cryptocompare/`

**Filename format**: `<symbol>.csv` (e.g., `btc.csv`, `eth.csv`)

**CSV Format:**

| Column | Description | Format |
|--------|-------------|--------|
| `timestamp` | Unix timestamp | Integer (seconds since epoch) |
| `datetime` | Human-readable datetime | `YYYY/MM/DD HH:00:00` |
| `open` | Opening price for the hour | Decimal number |

**Example:**

```csv
timestamp,datetime,open
1704067200,2024/01/01 00:00:00,42000.5
1704070800,2024/01/01 01:00:00,42100.2
1704074400,2024/01/01 02:00:00,42200.8
```

**Note**: The `coin` column is NOT included in the CSV file since each file is already per-coin.

#### QuestDB Database

If QuestDB is installed and running, data is also saved to the `crypto_hourly` table.

**Table Schema:**

| Column | Type | Description |
|--------|------|-------------|
| `coin` | SYMBOL | Cryptocurrency symbol (e.g., 'BTC') |
| `timestamp` | TIMESTAMP | Hourly timestamp (designated timestamp) |
| `datetime` | STRING | Human-readable datetime (`YYYY/MM/DD HH:00:00`) |
| `open` | DOUBLE | Opening price for the hour |

**Logical Key**: `(coin, timestamp)` - used for deduplication

**Query Example:**

```python
from questdb import get_questdb_connection, get_crypto_data

conn = get_questdb_connection()
data = get_crypto_data(conn, 'BTC', '2025/01/01', '2025/01/31')
# Returns list of dictionaries with 'coin', 'timestamp', 'datetime', 'open'
```

Or via SQL:

```sql
SELECT coin, timestamp, datetime, open 
FROM crypto_hourly 
WHERE coin = 'BTC' 
AND timestamp >= '2025-01-01 00:00:00' 
AND timestamp <= '2025-01-31 23:59:59'
ORDER BY timestamp ASC;
```

### Data Management

#### Incremental Updates

The script automatically handles incremental updates:

1. **Loads existing data** from CSV and QuestDB
2. **Fetches new data** from CryptoCompare API
3. **Deduplicates** - only inserts data that doesn't exist
4. **Updates** existing records with latest data
5. **Saves** updated data back to CSV and QuestDB

**Example:** Running the script twice with the same date range:

```bash
# First run - inserts new data
python3 download_cryptocompare_hourly.py BTC USD 2025/01/01 2025/09/01
# ✓ Inserted 5856 new rows to QuestDB

# Second run - updates existing data, no duplicates
python3 download_cryptocompare_hourly.py BTC USD 2025/01/01 2025/09/01
# → Updated 1488 existing rows in data_dict, added 0 new rows
```

#### Data Merging

The script merges data from multiple sources:

1. **CSV file** - loaded first (if exists)
2. **QuestDB** - loaded second (if available, takes precedence over CSV)
3. **API data** - fetched and merged into existing data
4. **Final save** - writes complete dataset back to CSV and QuestDB

This ensures consistency across both storage formats.

### Supported Cryptocurrencies

The script supports any cryptocurrency available on CryptoCompare. Common examples:

- **BTC** (Bitcoin)
- **ETH** (Ethereum)
- **USDT** (Tether)
- **BNB** (Binance Coin)
- **SOL** (Solana)
- **ADA** (Cardano)
- And hundreds more...

Check [CryptoCompare API](https://min-api.cryptocompare.com/) for full list.

### Data Storage Locations

- **CSV files**: `~/.dex_trades_extractor/.files/price/cryptocompare/`
- **QuestDB data**: `~/.dex_trades_extractor/.questdb/`
- **QuestDB web console**: http://localhost:9000
- **QuestDB PostgreSQL port**: localhost:8812

### Script Options

| Argument | Required | Description | Example |
|----------|----------|-------------|---------|
| `SYMBOL` | Yes | Cryptocurrency symbol | `BTC`, `ETH` |
| `CURRENCY` | Yes | Quote currency | `USD`, `EUR` |
| `START_DATE` | No | Start date (YYYY/MM/DD) | `2025/01/01` |
| `END_DATE` | No | End date (YYYY/MM/DD) | `2025/09/01` |

**Notes:**
- If dates are provided, both `START_DATE` and `END_DATE` must be provided
- Date range is inclusive for start, exclusive for end (end date + 1 day at 00:00:00)
- If no dates provided, fetches all available data from earliest point

### Troubleshooting

#### QuestDB Not Running

If you see "Could not connect to QuestDB" messages:

1. Check if QuestDB is running: `questdb status`
2. Start QuestDB: `./start_questdb.sh`
3. Script will continue in CSV-only mode if QuestDB is unavailable

#### No Data Retrieved

- **Check symbol**: Verify the symbol exists on CryptoCompare
- **Check date range**: Ensure dates are valid (YYYY/MM/DD format)
- **Check API**: Verify CryptoCompare API is accessible
- **Check rate limits**: Free tier has rate limits - wait a few seconds between runs

#### Data Not Appearing in QuestDB

- **Check connection**: Ensure QuestDB is running (`questdb status`)
- **Check autocommit**: QuestDB requires autocommit mode (handled automatically by script)
- **Check web console**: Visit http://localhost:9000 to view data
- **Check logs**: Use `questdb status` to see logs

#### File Corruption

The script uses atomic file operations (writes to temp file, then replaces original). If script fails:

1. Check for `.tmp` files in the output directory
2. Remove `.tmp` files if found
3. Re-run the script - it will rebuild from QuestDB if available

### Advanced Usage

#### Querying QuestDB Data

```python
from questdb import get_questdb_connection, get_crypto_data

# Get connection
conn = get_questdb_connection()

# Query data for date range (inclusive on both ends)
data = get_crypto_data(conn, 'BTC', '2025/01/01', '2025/01/31')

# Process data
for row in data:
    print(f"{row['datetime']}: ${row['open']}")

conn.close()
```

#### Custom Date Range Logic

The script uses the following logic for date ranges:

- **Start date**: `YYYY/MM/DD 00:00:00` (inclusive)
- **End date**: `(YYYY/MM/DD + 1 day) 00:00:00` (exclusive)

Example: `2025/01/01` to `2025/01/31` includes all hours from:
- Start: `2025-01-01 00:00:00` (inclusive)
- End: `2025-02-01 00:00:00` (exclusive, so includes all of Jan 31)

## Advanced Usage

### Processing Specific Chains Only

Edit `chains_config.py`:

```python
SUPPORTED_CHAINS = ['ethereum', 'arbitrum']  # Only these chains
```

### Processing Single Address

Edit `ethereum_settings.py`:

```python
WALLET_ADDRESSES = ["0xYourAddress"]
```

### Custom Date Range

Currently processes all historical transactions. To limit date range, modify `fetch_ethereum_transactions.py` to add `startblock`/`endblock` parameters.

## Project Structure

```
.
├── README.md                          # This file
├── fetch_all_chains_trades.py        # Main script (run this)
├── fetch_all_trades.py                # Single-chain processor
├── fetch_ethereum_transactions.py    # Transaction fetcher
├── parse_trades.py                    # Trade parser
├── enrich_trades_with_tokens.py      # Token metadata enrichment
├── calculate_prices.py                # USD price calculation
├── chains_config.py                   # Chain configurations
├── ethereum_config.py                 # DEX router addresses
├── ethereum_settings.py.example       # Settings template
├── ethereum_settings.py               # Your settings (gitignored)
└── known_tokens.py                    # Known token metadata database
```

## Privacy & Security

- **API Keys**: Never commit `ethereum_settings.py` (it's in `.gitignore`)
- **Wallet Addresses**: Wallet addresses are public on-chain, but be careful with API keys
- **Transaction Data**: All data is fetched from public blockchain explorers

## Limitations

- **Complex DeFi**: Some complex DeFi interactions (liquidity provision, yield farming) may not be detected as simple swaps
- **Cross-Chain**: Does not track cross-chain swaps (bridges)
- **Price Accuracy**: USD prices are estimates based on available historical data
- **API Dependencies**: Requires working explorer APIs (some may have rate limits or downtime)

## Contributing

Feel free to:
- Add support for new chains
- Improve DEX detection patterns
- Enhance price calculation logic
- Add new token metadata sources

## License

[Add your license here]

## Support

For issues:
1. Check the troubleshooting section above
2. Verify your API key is valid
3. Check transaction data in intermediate JSON files
4. Review the explorer directly to verify trades exist

## Changelog

### v2.0 (Current)
- Multi-chain support (9+ EVM chains)
- Multiple address support
- USD pricing with smart token handling
- Tax-optimized CSV export
- Chronological processing

### v1.0
- Ethereum-only support
- Single address processing
- Basic CSV export






