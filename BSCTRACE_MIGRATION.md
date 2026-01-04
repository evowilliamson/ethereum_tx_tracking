# BSCTrace API Migration

## Overview

As of December 2025, BSCScan API was deprecated and moved behind a paywall on Etherscan's unified API V2. This project has been updated to use **BSCTrace API** (powered by MegaNode) as a free alternative.

## Changes Made

1. **`chains_config.py`**: Updated Binance Chain configuration to use BSCTrace API endpoint
   - Endpoint: `https://api.bsctrace.com/api`
   - Removed `chain_id` parameter (BSCTrace uses V1-style API format)

2. **`fetch_ethereum_transactions.py`**: Updated to handle BSCTrace API format
   - No `chainid` parameter for BSCTrace (similar to old BSCScan V1)

3. **`ethereum_settings.py.example`**: Updated with BSCTrace API key instructions
   - Environment variable: `BSCTRACE_API_KEY` or `BINANCE_API_KEY`

4. **Documentation**: Updated README.md with BSCTrace setup instructions

## Setup Instructions

1. **Get BSCTrace API Key**:
   - Visit: https://nodereal.io/meganode
   - Sign up for a free account
   - Create a project and get your API key

2. **Configure API Key**:
   ```bash
   export BSCTRACE_API_KEY="your_api_key_here"
   ```
   Or add to `ethereum_settings.py`:
   ```python
   API_KEYS = {
       'binance': 'your_bsctrace_api_key_here',
   }
   ```

3. **Test the Integration**:
   ```bash
   python fetch_all_trades.py binance YOUR_ADDRESS
   ```

## API Endpoint

- **BSCTrace API**: `https://api.bsctrace.com/api`
- **Explorer**: https://bsctrace.com/
- **Migration Guide**: https://www.bnbchain.org/en/blog/migration-guide-bscscan-api-to-bsctrace-api-via-meganode

## Notes

- BSCTrace API is Etherscan-compatible, so it should work with the existing code
- If you encounter issues with the endpoint, verify the exact URL in your MegaNode dashboard
- The API key format is the same as Etherscan (simple string)

## Troubleshooting

If transactions are not being fetched:
1. Verify your API key is correct
2. Check if the endpoint `https://api.bsctrace.com/api` is correct (may vary)
3. Ensure your API key has BSC mainnet access enabled in MegaNode dashboard
4. Check rate limits - free tier may have restrictions

