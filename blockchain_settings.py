"""
Multi-Blockchain Trade Extractor Settings
Loads credentials from environment variables or .env file
Supports EVM chains (Ethereum, Base, Arbitrum, etc.) and non-EVM chains (Solana, Sui)
"""

import os

# Try to load from python-dotenv if available (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, that's okay

# Your Etherscan API Key (default for Ethereum and fallback)
# Get one for free at: https://etherscan.io/apis
# Set via environment variable: ETHERSCAN_API_KEY
# Or create a .env file with: ETHERSCAN_API_KEY=your_key_here
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "2DEMFWZT3QKJPI6FVFIBRA5RMVFYFY8RP5")

# Chain-specific API keys (optional - will fallback to ETHERSCAN_API_KEY if not set)
# Set environment variables like: BASE_API_KEY=xxx, ARBITRUM_API_KEY=xxx, etc.
API_KEYS = {
    'ethereum': os.getenv("ETHEREUM_API_KEY", ETHERSCAN_API_KEY),
    'base': os.getenv("BASE_API_KEY", ETHERSCAN_API_KEY),
    'arbitrum': os.getenv("ARBITRUM_API_KEY", ETHERSCAN_API_KEY),
    'optimism': os.getenv("OPTIMISM_API_KEY", ETHERSCAN_API_KEY),
    'polygon': os.getenv("POLYGON_API_KEY", ETHERSCAN_API_KEY),
    'avax': os.getenv("AVAX_API_KEY", ETHERSCAN_API_KEY),
    'binance': os.getenv("BINANCE_API_KEY", os.getenv("GOLDRUSH_API_KEY", "cqt_rQgw87kqPqPRVyHrjjwxGDJXF3dQ")),
    'linea': os.getenv("LINEA_API_KEY", ETHERSCAN_API_KEY),
    'katana': os.getenv("KATANA_API_KEY", ETHERSCAN_API_KEY),
    'monad': os.getenv("MONAD_API_KEY", ETHERSCAN_API_KEY),
}

# Your Ethereum wallet address(es)
# Set via environment variable: WALLET_ADDRESS (single address) or WALLET_ADDRESSES (comma-separated)
# Or create a .env file with: WALLET_ADDRESS=0xYourAddressHere or WALLET_ADDRESSES=0xAddr1,0xAddr2
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "0xb77Cb8F81A0f704E1E858EBa57C67c072ABBFCAD")

# List of wallet addresses to process
# If WALLET_ADDRESSES env var is set, use that; otherwise use WALLET_ADDRESS as a single-item list
_WALLET_ADDRESSES_ENV = os.getenv("WALLET_ADDRESSES", "")
if _WALLET_ADDRESSES_ENV:
    # Parse comma-separated addresses
    WALLET_ADDRESSES = [addr.strip() for addr in _WALLET_ADDRESSES_ENV.split(',') if addr.strip()]
else:
    # Use single address as list, or add additional addresses here
    WALLET_ADDRESSES = [
        "0xb77Cb8F81A0f704E1E858EBa57C67c072ABBFCAD",
        "0x302d129011fB164D8D5FE93cD1E8795D61C4f76F"
    ]

# Optional: Output file name (default: ethereum_trades.json)
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "ethereum_trades.json")

# Blockchain name for CSV export (default: "ethereum")
BLOCKCHAIN = os.getenv("BLOCKCHAIN", "ethereum")

# Non-EVM chain addresses (Solana, Sui)
# These use different address formats than EVM chains
NON_EVM_ADDRESSES = {
    'solana': os.getenv("SOLANA_ADDRESS", ""),  # Solana address format
    'sui': os.getenv("SUI_ADDRESS", "0x6525b9a3a48a54e518cf57618c68621074be2ffd724f8a51e7b3048682acf572"),  # Sui address (66 chars)
}
