# QuestDB Price Lookup Integration Plan

## Overview
Integrate QuestDB as the primary price source for trade pricing, with CoinGecko as fallback. Implement weighted interpolation for timestamp-based price lookup and on-demand data fetching for missing coins.

## Files That Need Changes

### 1. `questdb.py` (MAJOR CHANGES)
**Purpose**: Add QuestDB-specific functions for price lookup, interpolation, and on-demand data fetching.

#### Functions to ADD:

1. **`get_hourly_prices_for_timestamp(conn, symbol: str, trade_timestamp: int) -> Tuple[Optional[Dict], Optional[Dict]]`**
   - Query QuestDB for the two hourly rows that bracket a trade timestamp
   - Returns: (hour_before_row, hour_after_row) or (None, None) if not found
   - Uses TIMESTAMP column for efficient querying (not datetime STRING)
   - Logic:
     - Calculate hour_before: floor trade_timestamp to the hour
     - Calculate hour_after: hour_before + 3600 seconds
     - Query: `WHERE coin = %s AND timestamp IN (%s, %s) ORDER BY timestamp`

2. **`interpolate_price(hour_before: Dict, hour_after: Dict, trade_timestamp: int) -> float`**
   - Calculate weighted average price between two hourly data points
   - Pure function (no DB access needed)
   - Formula:
     - Distance to hour_before: `dist_before = trade_timestamp - hour_before['timestamp']`
     - Distance to hour_after: `dist_after = hour_after['timestamp'] - trade_timestamp`
     - Weight for hour_before: `weight_before = dist_after / 3600`
     - Weight for hour_after: `weight_after = dist_before / 3600`
     - Interpolated price: `(hour_before['open'] * weight_before) + (hour_after['open'] * weight_after)`

3. **`get_questdb_price(conn, symbol: str, trade_timestamp: int) -> Optional[float]`**
   - Main function to get price from QuestDB with interpolation
   - Calls `get_hourly_prices_for_timestamp()` to get the two rows
   - If both rows exist: calls `interpolate_price()` and returns result
   - If missing: returns None (caller should fetch on-demand)

4. **`fetch_and_insert_coin_data_from_cryptocompare(conn, symbol: str, api_key: str = None) -> bool`**
   - On-demand fetch of ALL historical data for a coin from CryptoCompare API
   - Reuses logic from `download_cryptocompare_hourly.py` (can extract or import)
   - Fetches all available data (no date range limit)
   - Inserts all data into QuestDB using `insert_batch_to_questdb()`
   - Returns: True if successful, False otherwise
   - Note: This function will reuse the `fetch_all_hourly_data()` function from `download_cryptocompare_hourly.py`

#### Functions to KEEP (already in questdb.py):
- `get_questdb_connection()` ✓
- `create_questdb_table()` ✓
- `load_existing_questdb()` ✓ (might not be needed for price lookup)
- `check_existing_keys_questdb()` ✓ (used by fetch function)
- `insert_batch_to_questdb()` ✓ (used by fetch function)
- `get_crypto_data()` ✓ (might not be needed, but keep for compatibility)

---

### 2. `calculate_prices.py` (MAJOR CHANGES)
**Purpose**: Modify price calculation logic to use QuestDB as primary source.

#### Changes to `PriceFeedBuilder` class:

1. **Add QuestDB connection to `__init__()`**
   - Import `get_questdb_connection` from `questdb`
   - Store connection: `self.questdb_conn = get_questdb_connection()`
   - Optionally create table if connection exists: `create_questdb_table(self.questdb_conn)`

2. **RENAME/MODIFY: `get_coingecko_price()` → `get_price()` (or keep both)**
   - **Option A (Recommended)**: Rename to `get_price()` and make it QuestDB-first
     - Strategy:
       1. Try QuestDB first: `get_questdb_price(self.questdb_conn, symbol, timestamp)`
       2. If QuestDB returns None (missing data):
          - Fetch on-demand: `fetch_and_insert_coin_data_from_cryptocompare()`
          - Retry QuestDB: `get_questdb_price()` again
       3. If still None, fallback to CoinGecko: `get_historical_price()` (current logic)
     - Update `price_source` to track: "questdb", "questdb_on_demand", "coingecko", etc.
   
   - **Option B**: Keep `get_coingecko_price()` for fallback, add new `get_questdb_price()` method
     - Call QuestDB first in `calculate_prices_for_trade()`, then fallback to CoinGecko

3. **MODIFY: `calculate_prices_for_trade()`**
   - Change Strategy 1 (line ~177) to use QuestDB instead of CoinGecko
   - Update price_source values:
     - "questdb" - Found in QuestDB (primary)
     - "questdb_on_demand" - Fetched on-demand from CryptoCompare, then found in QuestDB
     - "coingecko" - Fallback to CoinGecko
     - "coingecko_with_ratio" - CoinGecko + swap ratio (keep existing)
     - "stablecoin_ratio" - Stablecoin fallback (keep existing)
     - "unavailable" - No price available (keep existing)

4. **ADD: Helper method for on-demand fetching**
   - `_fetch_missing_coin_data(self, symbol: str) -> bool`
   - Wraps `fetch_and_insert_coin_data_from_cryptocompare()`
   - Handles API key retrieval (from environment or config)
   - Returns True if data was fetched and inserted successfully

#### Functions to KEEP (no changes):
- `is_stablecoin()` ✓
- `_load_price_cache()` ✓ (might not be needed, but keep for CoinGecko fallback)
- `_save_price_cache()` ✓ (might not be needed, but keep for CoinGecko fallback)
- `_get_cache_key()` ✓ (might not be needed, but keep for CoinGecko fallback)
- `extract_underlying_asset()` ✓

#### Functions to KEEP (minor changes):
- `add_prices_to_trades()` ✓ (no changes, just uses updated `PriceFeedBuilder`)

---

### 3. `download_cryptocompare_hourly.py` (MINOR CHANGES - OPTIONAL)
**Purpose**: Extract/reuse the `fetch_all_hourly_data()` function for on-demand fetching.

#### Options:
- **Option A**: Import and reuse `fetch_all_hourly_data()` directly in `questdb.py`
  - Pro: No code duplication
  - Con: Creates dependency between questdb.py and download_cryptocompare_hourly.py
  
- **Option B**: Extract `fetch_all_hourly_data()` to a shared module (e.g., `cryptocompare_api.py`)
  - Pro: Better separation of concerns
  - Con: Requires refactoring

- **Option C (Recommended)**: Keep in `download_cryptocompare_hourly.py`, import it in `questdb.py`
  - Pro: Minimal changes, function already exists and works
  - Con: Slight coupling, but acceptable for now

**Decision**: Use Option C - import `fetch_all_hourly_data()` in `questdb.py` for on-demand fetching.

---

## Functions to Move to `questdb.py`

### Already in questdb.py (no move needed):
- All QuestDB connection and table management functions ✓
- All QuestDB data insertion functions ✓
- All QuestDB query functions ✓

### No functions need to be moved (they're already in the right place)

However, we should ensure that:
- QuestDB-specific logic stays in `questdb.py`
- Price calculation orchestration stays in `calculate_prices.py`
- CryptoCompare API fetching stays in `download_cryptocompare_hourly.py` (but can be imported)

---

## New Dependencies

### Import statements to add:

**In `questdb.py`:**
```python
from download_cryptocompare_hourly import fetch_all_hourly_data  # For on-demand fetching
import os  # For API key from environment
```

**In `calculate_prices.py`:**
```python
from questdb import (
    get_questdb_connection,
    create_questdb_table,
    get_questdb_price,  # NEW
    fetch_and_insert_coin_data_from_cryptocompare  # NEW (optional, might be internal to questdb.py)
)
```

---

## Implementation Order

1. **Step 1**: Add new functions to `questdb.py`
   - `get_hourly_prices_for_timestamp()`
   - `interpolate_price()`
   - `get_questdb_price()`
   - `fetch_and_insert_coin_data_from_cryptocompare()`

2. **Step 2**: Modify `calculate_prices.py`
   - Add QuestDB connection to `PriceFeedBuilder.__init__()`
   - Modify `get_coingecko_price()` or create new `get_price()` method
   - Update `calculate_prices_for_trade()` to use QuestDB first

3. **Step 3**: Test
   - Test with coins that exist in QuestDB
   - Test with coins missing from QuestDB (on-demand fetch)
   - Test interpolation accuracy
   - Test fallback to CoinGecko

---

## API Key Management

The `fetch_and_insert_coin_data_from_cryptocompare()` function needs a CryptoCompare API key.

**Options:**
1. Read from environment variable: `CRYPTOCOMPARE_API_KEY`
2. Read from config file (if exists)
3. Pass as parameter (None = use free tier)

**Decision**: Use environment variable `CRYPTOCOMPARE_API_KEY` (optional, for rate limit benefits).

---

## Error Handling

- QuestDB connection failure → Fallback to CoinGecko (graceful degradation)
- Missing data in QuestDB → Fetch on-demand, then retry QuestDB
- On-demand fetch failure → Fallback to CoinGecko
- Interpolation failure (missing one of two rows) → Fetch on-demand, then retry
- CoinGecko fallback → Keep existing error handling

---

## Testing Considerations

1. **Unit tests** (if test suite exists):
   - Test `interpolate_price()` with various timestamps
   - Test `get_hourly_prices_for_timestamp()` with existing/missing data
   - Test `get_questdb_price()` with various scenarios

2. **Integration tests**:
   - Test full flow: trade timestamp → QuestDB lookup → interpolation → price
   - Test on-demand fetching: missing coin → fetch → insert → lookup → price
   - Test fallback: QuestDB unavailable → CoinGecko

3. **Performance tests**:
   - Compare QuestDB lookup speed vs CoinGecko API calls
   - Verify interpolation adds minimal overhead

---

## Summary of Changes

| File | Change Type | Functions Affected |
|------|-------------|-------------------|
| `questdb.py` | **ADD** | 4 new functions (see above) |
| `calculate_prices.py` | **MODIFY** | `PriceFeedBuilder.__init__()`, `get_coingecko_price()` (or new `get_price()`), `calculate_prices_for_trade()` |
| `download_cryptocompare_hourly.py` | **NO CHANGE** | (function imported, not modified) |
| Other files | **NO CHANGE** | - |

---

## Notes

- QuestDB queries should use `TIMESTAMP` column (not `datetime` STRING) for optimal performance
- Interpolation formula: weighted average based on time distance
- On-demand fetching: fetch ALL historical data (not just the needed hour) for future-proofing
- Price sources: Track "questdb", "questdb_on_demand", "coingecko", etc. for analytics
- Graceful degradation: If QuestDB fails, fallback to CoinGecko (existing behavior)

