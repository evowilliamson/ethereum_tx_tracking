# QuestDB Setup Guide

This project uses QuestDB to store cryptocurrency hourly price data.

## Data Directory Structure

All data is stored in `~/.dex_trades_extractor/`:
- **QuestDB database**: `~/.dex_trades_extractor/.questdb/`
- **CSV files**: `~/.dex_trades_extractor/.files/price/cryptocompare/`

## Quick Start

### Step 1: Install QuestDB

**Using the installation script (Recommended for Ubuntu):**
```bash
./install_questdb.sh
```

This script will:
- Download the latest QuestDB binary for your architecture
- Install it to `/opt/questdb`
- Create a symlink in `/usr/local/bin` so you can use `questdb` command
- Verify the installation

**Manual installation:**
- Visit: https://questdb.io/get-questdb/
- Follow the installation instructions for your operating system

### Step 2: Start QuestDB

**Using the helper script:**
```bash
./start_questdb.sh
```

**Or manually:**
```bash
mkdir -p ~/.dex_trades_extractor/.questdb
questdb start -d ~/.dex_trades_extractor/.questdb
```

### Step 3: Stop QuestDB (when needed)

**Using the helper script:**
```bash
./stop_questdb.sh
```

**Or manually:**
```bash
questdb stop
```

## Verify QuestDB is Running

1. **Web Console**: Open http://localhost:9000 in your browser
2. **Check status**: 
   ```bash
   questdb status
   ```

## Python Dependencies

Install the required Python package:

```bash
pip install psycopg2-binary
```

Or use the setup script:

```bash
./setup.sh
```

## Connection Configuration

The Python scripts connect to QuestDB using these default settings (can be overridden with environment variables):

- **Host**: `localhost` (set `QUESTDB_HOST` env var to change)
- **Port**: `8812` (set `QUESTDB_PORT` env var to change)
- **User**: `admin` (set `QUESTDB_USER` env var to change)
- **Password**: `quest` (set `QUESTDB_PASSWORD` env var to change)
- **Database**: `qdb` (set `QUESTDB_DATABASE` env var to change)

## Database Schema

The `crypto_hourly` table is created automatically with the following structure:

- `coin` (SYMBOL): Cryptocurrency symbol (e.g., 'BTC')
- `timestamp` (TIMESTAMP): Hourly timestamp (designated timestamp)
- `datetime` (STRING): Human-readable datetime (YYYY/MM/DD HH:00:00)
- `open` (DOUBLE): Opening price for the hour

Composite key: `(coin, timestamp)`

## Managing QuestDB

### View Status

```bash
questdb status
```

### Stop QuestDB

**Using the helper script (recommended):**
```bash
./stop_questdb.sh
```

**Manual command:**
```bash
questdb stop
```

### Start QuestDB (if stopped)

**Using the helper script (recommended):**
```bash
./start_questdb.sh
```

**Manual command:**
```bash
questdb start -d ~/.dex_trades_extractor/.questdb
```

### Backup Data

The QuestDB data directory can be backed up directly:

```bash
# Backup
tar -czf questdb-backup-$(date +%Y%m%d).tar.gz ~/.dex_trades_extractor/.questdb/

# Restore
tar -xzf questdb-backup-YYYYMMDD.tar.gz -C ~/
```

## Troubleshooting

### Port Already in Use

If you get a "port already in use" error:

1. Check if QuestDB is already running:
   ```bash
   questdb status
   ```

2. Stop the existing instance and restart

### Cannot Connect from Python

1. Verify QuestDB is running: `questdb status`
2. Check that `psycopg2-binary` is installed: `pip list | grep psycopg2`
3. Test connection:
   ```python
   import psycopg2
   conn = psycopg2.connect(host='localhost', port='8812', user='admin', password='quest', database='qdb')
   print("Connected successfully!")
   conn.close()
   ```

### Data Not Persisting

- Make sure the data directory exists and is writable
- Verify permissions on `~/.dex_trades_extractor/.questdb/`
- Check QuestDB logs for errors

### QuestDB Not Found

If the `questdb` command is not found:

1. Verify QuestDB is installed: Check installation directory
2. Ensure QuestDB is in your PATH
3. Reinstall QuestDB if needed: https://questdb.io/get-questdb/
