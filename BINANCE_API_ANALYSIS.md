# Binance Chain API Analysis

## Summary

After testing multiple API options for Binance Smart Chain (BSC), here are the findings:

### Test Results

1. **BSCScan V1 API** (`api.bscscan.com/api`)
   - Status: **DEPRECATED** (as of December 2025)
   - Message: "You are using a deprecated V1 endpoint, switch to Etherscan API V2"
   - **Not available**

2. **Etherscan API V2 with chainid=56**
   - Status: **REQUIRES PAID PLAN**
   - Message: "Free API access is not supported for this chain. Please upgrade your api plan"
   - **Not available on free tier**

3. **NodeReal/MegaNode** (currently in use)
   - Status: **FREE TIER AVAILABLE**
   - Limitation: **Only returns ~2 days of historical data**
   - Current coverage: Only 9 out of 88 trades (10.2%)
   - Missing: 79 trades (89.8%)

## Comparison: Koinly vs NodeReal API

- **Koinly**: 88 trades from Sept 19 - Oct 23 (35 days)
- **NodeReal API**: 14 transactions from Sept 19-20 (2 days)
- **Matching**: Only 9 transaction hashes match
- **Missing**: 79 trades spanning Sept 20 - Oct 23

## Root Cause

The NodeReal free tier API appears to have severe limitations on historical data access. It only returns the most recent transactions (approximately 2 days), not the full transaction history.

## Recommendations

### Option 1: Upgrade to Paid Etherscan Plan
- Use Etherscan API V2 with `chainid=56`
- Provides full historical data access
- Update `chains_config.py` to use:
  ```python
  'api_base': 'https://api.etherscan.io/v2/api',
  'chain_id': '56',
  'api_type': 'etherscan',
  ```

### Option 2: Use Direct BSC RPC Calls
- Query BSC nodes directly using JSON-RPC
- Slower but provides complete historical data
- No API key required (public RPC endpoints)
- Example endpoint: `https://bsc-dataseed.binance.org/`

### Option 3: Check NodeReal Paid Tier
- Verify if NodeReal paid tier provides better historical data access
- May be more cost-effective than Etherscan paid plan

### Option 4: Hybrid Approach
- Use NodeReal for recent transactions (last 2 days)
- Use Koinly export or manual data for historical transactions
- Combine both sources in the processing pipeline

## Current Configuration

The system is currently configured to use NodeReal/MegaNode free tier:
- Endpoint: `https://bsc-mainnet.nodereal.io/v1/{API-key}`
- API Type: JSON-RPC (NodeReal)
- Limitation: ~2 days of historical data

## Next Steps

1. If you have a paid Etherscan API plan, update `chains_config.py` to use Etherscan V2
2. If not, consider implementing direct BSC RPC calls for historical data
3. Alternatively, use Koinly export as the primary data source for Binance Chain

