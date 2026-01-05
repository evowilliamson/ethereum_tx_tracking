# Project Context - Ethereum Transaction Tracking

**Last Updated:** 2026-01-05  
**Project Location:** `/home/ivo/code/ethereum_tx_tracking`

---

## Project Overview

A comprehensive tool to extract **ALL** DEX (Decentralized Exchange) trades from wallet addresses across multiple blockchains. The system identifies and extracts swap transactions from all major DEX protocols using pattern matching and transaction analysis.

### Key Features
- **Multi-Chain Support**: EVM chains (Ethereum, Base, Arbitrum, Optimism, Polygon, Linea, Katana, Binance, Monad, Avalanche) and non-EVM chains (Solana, Sui)
- **Comprehensive DEX Detection**: Detects trades from all major DEXes via pattern matching (Uniswap, SushiSwap, Curve, 1inch, Balancer, 0x, etc.)
- **Price Data Collection**: Top 1000 cryptocurrency hourly price data extraction from CryptoCompare API
- **QuestDB Integration**: Stores price data in QuestDB time-series database

---

## Current Deployment State

### Railway Host
- **Service Name**: `just-shell`
- **Status**: Running
- **Current Process**: Top 1000 cryptocurrency data extraction (resume mode)
- **Volume**: `/data/questdb` (50GB, persistent, confirmed working)
- **QuestDB**: Running on port 80 (Railway requirement)

### Usage & Costs
- **Current Usage**: $0.19 (actual)
- **Estimated Usage**: $47.36 (projection if current rate continues)
- **Pro Plan**: $20/month credit
- **Volume Usage**: $0.21 (confirms volume is configured)

### Data Status
- **QuestDB Data Location**: `/data/questdb/db/` (824MB used, 2% of 50GB)
- **Volume Mount**: Confirmed persistent at `/data/questdb`
- **Last Processed Coin**: DASH (index 150/1000)
- **Coins Processed**: 110 coins with data
- **Remaining**: 849 coins to process (starting from DASH)

---

## Key Components

### 1. DEX Trade Extraction
- **Main Scripts**:
  - `fetch_all_trades.py` - Main orchestrator for single chain
  - `fetch_all_chains_trades.py` - Processes all configured chains
  - `fetch_ethereum_transactions.py` - Ethereum transaction fetcher
  - `fetch_solana_transactions.py` - Solana transaction fetcher
  - `fetch_sui_transactions.py` - Sui transaction fetcher
  - `parse_ethereum_trades.py` - Ethereum trade parser
  - `parse_solana_trades.py` - Solana trade parser
  - `parse_sui_trades.py` - Sui trade parser

- **Configuration**:
  - `chains_config.py` - Chain configurations (API endpoints, chain IDs, native tokens)
  - `ethereum_config.py` - DEX router addresses and function signatures
  - `blockchain_settings.py` - User configuration (API keys, wallet addresses)

### 2. Price Data Collection
- **Main Script**: `download_cryptocompare_hourly.py`
  - Downloads hourly price data from CryptoCompare API
  - Stores data in QuestDB
  - Supports top 1000 coins extraction
  - **Resume Command**: `python3 download_cryptocompare_hourly.py resume [--dry-run]`
  - **Resume Logic**: Automatically finds last processed coin and continues from there
  - **Exclude Coins**: MON (excluded by default, done separately)

- **Key Functions**:
  - `download_top_1000_all_data()` - Full top 1000 download
  - `download_top_1000_all_data_resume()` - Resume from last processed coin
  - `get_top_1000_by_marketcap()` - Fetches top 1000 from CoinGecko

### 3. QuestDB Integration
- **Connection Module**: `questdb.py`
  - PostgreSQL wire protocol connection (port 8812)
  - Table: `crypto_hourly` (coin, timestamp, datetime, open)
  - Functions: `get_questdb_connection()`, `create_questdb_table()`, `load_existing_questdb()`, `insert_batch_to_questdb()`

- **Environment Variables** (from `env.example`):
  - `QUESTDB_HOST` (default: localhost)
  - `QUESTDB_PORT` (default: 8812)
  - `QUESTDB_USER` (default: admin)
  - `QUESTDB_PASSWORD` (default: quest)
  - `QUESTDB_DATABASE` (default: qdb)

### 4. QuestDB Docker Setup
- **Location**: `questdb/` directory
- **Files**:
  - `Dockerfile` - QuestDB Docker image (403MB, tested and working)
  - `entrypoint.sh` - Startup script (creates symlink, copies config, starts QuestDB)
  - `conf/server.conf` - QuestDB configuration (port 80 for Railway)
  - `docker-compose.yml` - Local testing setup
  - `.dockerignore` - Excludes unnecessary files

- **Key Features**:
  - Port 80 configured (Railway requirement)
  - Symlink: `~/.questdb` → `/data/questdb` (for persistence)
  - Config file copied from image to volume at startup
  - Base image: `eclipse-temurin:17-jre-jammy`
  - QuestDB version: 9.2.3

---

## Recent Work Completed

### QuestDB Docker Setup (2026-01-05)
1. **Created Docker setup**:
   - Dockerfile with QuestDB 9.2.3
   - Entrypoint script for symlink and config setup
   - Configuration file with port 80
   - Docker Compose for local testing
   - Documentation: README.md, TESTING.md, DOCKER_EXPLANATION.md

2. **Fixed Issues**:
   - QuestDB download URL format (`-rt-linux-x86-64` instead of `-linux-x86_64`)
   - Directory structure after extraction
   - QuestDB binary path (`bin/questdb.sh`)
   - Added `.dockerignore` to exclude unnecessary files

3. **Built and Tested**:
   - ✅ Docker image built successfully
   - ✅ Image tested locally with docker-compose
   - ✅ Entrypoint script verified (creates symlink, copies config)
   - ✅ Port 80 configuration confirmed
   - ✅ Volume persistence tested
   - ✅ Ready for Railway deployment

### Resume Command Implementation (2026-01-05)
1. **Added resume command** to `download_cryptocompare_hourly.py`:
   - Command: `python3 download_cryptocompare_hourly.py resume [--dry-run]`
   - Automatically finds last processed coin from QuestDB
   - Continues from last coin (excluding MON by default)
   - Supports `--dry-run` flag for testing

2. **Debug Output**: Added debug logging to help troubleshoot Railway issues

### Volume Configuration Verification (2026-01-05)
1. **Confirmed volume is persistent**:
   - Mount path: `/data/questdb`
   - Size: 50GB
   - Status: Persistent volume (confirmed via `mountpoint` command)
   - Data: 824MB used (2% of capacity)

---

## Important Decisions & Gotchas

### Port Configuration
- **QuestDB HTTP Port**: 80 (not 9000) - Railway requirement
- **PostgreSQL Port**: 8812 (unchanged, used by Python app)
- **ILP Port**: 9009 (unchanged)
- **Configuration**: Set in `questdb/conf/server.conf` as `http.bind.to=0.0.0.0:80`

### Data Persistence Strategy
- **Volume Mount**: `/data/questdb` (Railway persistent volume)
- **Symlink**: `~/.questdb` → `/data/questdb`
- **Why**: QuestDB expects default path `~/.questdb`, but we need data in volume
- **Config File**: Copied from image (`/opt/questdb-config/server.conf`) to volume (`/data/questdb/conf/server.conf`) at startup

### Resume Logic
- **Last Coin Detection**: Finds coin with highest index in ordered top 1000 list that has data in QuestDB
- **Exclude Logic**: MON is excluded from "last coin" search (will be done separately)
- **Resume Point**: Starts from last coin (redoes it in case partial) and continues forward
- **Dry Run**: Use `--dry-run` flag to see what would be processed without executing

### Railway Configuration
- **Service**: `just-shell`
- **Volume**: Configured in Railway Dashboard → Service → Settings → Volumes
- **Mount Path**: `/data/questdb`
- **Volume Size**: 50GB
- **Region**: (check Railway dashboard)

---

## File Structure

```
ethereum_tx_tracking/
├── questdb/                    # QuestDB Docker setup (built and tested)
│   ├── Dockerfile              # QuestDB Docker image definition
│   ├── entrypoint.sh           # Container startup script
│   ├── docker-compose.yml       # Local testing setup
│   ├── conf/
│   │   └── server.conf         # QuestDB config (port 80)
│   ├── .dockerignore          # Excluded files from build
│   ├── README.md               # QuestDB setup docs
│   ├── TESTING.md              # Testing guide
│   └── DOCKER_EXPLANATION.md   # Docker setup explanation
│
├── download_cryptocompare_hourly.py  # Main price data extraction script
├── questdb.py                  # QuestDB connection and operations
├── coingecko.py                # CoinGecko API integration
├── check_top1000_progress.py   # Progress checking script
│
├── fetch_all_trades.py         # Main DEX trade extraction orchestrator
├── fetch_all_chains_trades.py  # Multi-chain processor
├── fetch_ethereum_transactions.py
├── fetch_solana_transactions.py
├── fetch_sui_transactions.py
├── parse_ethereum_trades.py
├── parse_solana_trades.py
├── parse_sui_trades.py
│
├── chains_config.py            # Chain configurations
├── ethereum_config.py          # DEX router addresses
├── blockchain_settings.py      # User config (API keys, addresses)
├── blockchain_settings.py.example
│
├── enrich_trades_with_tokens.py
├── calculate_prices.py
├── calculate_fifo_taxes.py
│
├── DEPLOYMENT.md               # Railway deployment guide
├── README.md                   # Project documentation
└── CONTEXT.md                  # This file
```

---

## Common Commands

### Top 1000 Data Extraction
```bash
# Resume extraction (dry run)
python3 download_cryptocompare_hourly.py resume --dry-run

# Resume extraction (actual)
python3 download_cryptocompare_hourly.py resume

# Check progress
python3 check_top1000_progress.py
```

### QuestDB Management
```bash
# Start QuestDB locally
./start_questdb.sh

# Stop QuestDB locally
./stop_questdb.sh

# Check QuestDB status
questdb status
```

### Docker (Local Testing)
```bash
# Build image
cd questdb
docker build -t questdb:latest .

# Run with docker-compose
docker-compose up -d

# Check logs
docker-compose logs -f questdb
```

### Railway
```bash
# SSH into Railway
railway shell

# Run command on Railway
railway run <command>

# Check logs
railway logs

# Pull latest changes (on Railway host)
git pull origin main
```

---

## Configuration Files

### `blockchain_settings.py`
- Contains API keys and wallet addresses
- Not in git (use `.example` file as template)
- Required for all operations

### `questdb/conf/server.conf`
- QuestDB server configuration
- Port 80 for HTTP (Railway requirement)
- Committed to git (version controlled)

### `chains_config.py`
- Chain-specific configurations
- API endpoints, chain IDs, native tokens
- Supports all EVM and non-EVM chains

### `ethereum_config.py`
- DEX router addresses
- Function signatures
- Swap event signatures

---

## Railway Deployment

### Current Setup
- **Service**: `just-shell`
- **Volume**: `/data/questdb` (50GB, persistent)
- **QuestDB**: Running (not in Docker yet, using installed binary)
- **Port**: 80 (HTTP), 8812 (PostgreSQL), 9009 (ILP)

### Docker Deployment Status
- ✅ **Docker image built and tested locally**
- ✅ Dockerfile complete in `questdb/` directory
- ✅ Entrypoint script tested and verified
- ✅ Configuration file (port 80) confirmed working
- ✅ Ready for Railway deployment
- **Next step**: Deploy to Railway (push to git, Railway will auto-build)
- Will use same volume mount: `/data/questdb` (data persists)

---

## Important Notes

### Data Safety
- ✅ Volume is persistent (confirmed)
- ✅ Data survives container restarts
- ✅ Data survives deployments
- ✅ Current data: 824MB in `/data/questdb/db/`

### Process Status
- Top 1000 extraction running in resume mode
- Last processed: DASH (index 150)
- 110 coins with data
- 849 coins remaining

### Cost Management
- Current usage: $0.19 (low)
- Estimated: $47.36 (if rate continues - just projection)
- Can stop service when not needed to reduce costs
- Volume usage: $0.21 (normal)

### Known Issues/Considerations
- QuestDB port must be 80 for Railway (not configurable to 9000)
- MON coin excluded from top 1000 processing (done separately)
- Resume logic finds last coin by highest index in ordered list
- ✅ Docker image built and tested - ready for Railway deployment

---

## Quick Reference

### Where is data stored?
- **QuestDB data**: `/data/questdb/db/` (persistent volume)
- **QuestDB config**: `/data/questdb/conf/server.conf`
- **Symlink**: `~/.questdb` → `/data/questdb`

### How to resume top 1000?
```bash
python3 download_cryptocompare_hourly.py resume
```

### How to check if volume is persistent?
```bash
mountpoint /data/questdb
# Should return: /data/questdb is a mountpoint
```

### How to verify QuestDB is running?
```bash
curl http://localhost:80/ping
# Should return: OK
```

---

## Next Steps / TODO

1. **Deploy QuestDB Docker to Railway** (ready to deploy)
   - ✅ Docker image built and tested locally
   - Next: Push `questdb/` directory to git
   - Railway will auto-build and deploy
   - Volume will be reused (data persists)

2. **Monitor top 1000 extraction**
   - Check progress periodically
   - Monitor costs
   - Stop when not needed

3. **Optimize if needed**
   - Reduce memory/CPU usage
   - Add rate limiting
   - Process in batches

---

## For New Chat Sessions

When starting a new chat, provide this context:

```
I'm working on an Ethereum transaction tracking project. Current state:

- Top 1000 crypto price extraction running on Railway
- QuestDB Docker setup completed and tested (questdb/ directory)
- Docker image built and verified locally
- Volume: /data/questdb (50GB, persistent, confirmed)
- Last processed coin: DASH (index 150/1000)
- Resume command: python3 download_cryptocompare_hourly.py resume

Key files:
- download_cryptocompare_hourly.py (has resume command)
- questdb/ (Docker setup - built and tested)
- questdb.py (QuestDB integration)

See CONTEXT.md for full details.
```

This gives the AI assistant immediate context without needing to re-read everything.

