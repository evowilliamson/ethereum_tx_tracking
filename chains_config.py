"""
Chain Configuration for Multi-EVM Support
Defines API endpoints, chain IDs, and chain-specific settings
"""

# Supported blockchains
# EVM chains: ethereum, monad, arbitrum, linea, optimism, polygon, katana, binance, base, avax
# Non-EVM chains: solana, sui
SUPPORTED_CHAINS = ['ethereum', 'monad', 'arbitrum', 'linea', 'optimism', 'polygon', 'katana', 'binance', 'base', 'solana', 'sui']
# SUPPORTED_CHAINS = ['ethereum', 'monad', 'avax', 'base', 'arbitrum', 'binance', 'linea', 'katana', 'polygon', 'optimism']

# Chain configurations
CHAINS = {
    'ethereum': {
        'name': 'Ethereum',
        'api_base': 'https://api.etherscan.io/v2/api',
        'chain_id': '1',
        'native_token': 'ETH',
        'weth_address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
        'explorer_url': 'https://etherscan.io',
    },
    'base': {
        'name': 'Base',
        'api_base': 'https://api.etherscan.io/v2/api',  # Use Etherscan API V2 - supports Base via chainid
        'chain_id': '8453',
        'native_token': 'ETH',
        'weth_address': '0x4200000000000000000000000000000000000006',
        'explorer_url': 'https://basescan.org',
    },
    'arbitrum': {
        'name': 'Arbitrum',
        'api_base': 'https://api.etherscan.io/v2/api',  # Use Etherscan API V2 - supports Arbitrum via chainid
        'chain_id': '42161',  # Arbitrum One Mainnet
        'native_token': 'ETH',
        'weth_address': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
        'explorer_url': 'https://arbiscan.io',
    },
    'optimism': {
        'name': 'Optimism',
        'api_base': 'https://api-optimistic.etherscan.io/v2/api',  # Uses own endpoint (not in Etherscan V2 chainlist)
        'chain_id': '10',
        'native_token': 'ETH',
        'weth_address': '0x4200000000000000000000000000000000000006',
        'explorer_url': 'https://optimistic.etherscan.io',
    },
    'polygon': {
        'name': 'Polygon',
        'api_base': 'https://api.etherscan.io/v2/api',  # Use Etherscan API V2 - supports Polygon via chainid
        'chain_id': '137',
        'native_token': 'MATIC',
        'weth_address': '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',  # WMATIC
        'explorer_url': 'https://polygonscan.com',
    },
    'monad': {
        'name': 'Monad',
        'api_base': 'https://api.etherscan.io/v2/api',  # Use Etherscan API V2 - supports Monad via chainid
        'chain_id': '143',  # Monad Mainnet chain ID (via Etherscan API V2)
        'native_token': 'MON',
        'weth_address': '0x0000000000000000000000000000000000000000',  # Verify: WETH/WMON address on Monad
        'explorer_url': 'https://monadscan.com',  # MonadScan explorer
    },
    'avax': {
        'name': 'Avalanche',
        'api_base': 'https://api.snowtrace.io/v2/api',
        'chain_id': '43114',
        'native_token': 'AVAX',
        'weth_address': '0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7',  # WAVAX
        'explorer_url': 'https://snowtrace.io',
    },
    'binance': {
        'name': 'Binance Smart Chain',
        'api_base': 'https://api.etherscan.io/v2/api',  # Use Etherscan API V2 (BSCScan recommends this)
        'chain_id': '56',
        'native_token': 'BNB',
        'weth_address': '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',  # WBNB
        'explorer_url': 'https://bscscan.com',
    },
    'linea': {
        'name': 'Linea',
        'api_base': 'https://api.etherscan.io/v2/api',  # Use Etherscan API V2 - supports Linea via chainid
        'chain_id': '59144',
        'native_token': 'ETH',
        'weth_address': '0xe5D7C2a44FfDDf6b295A15c148167daaAf5Cf34f',
        'explorer_url': 'https://lineascan.build',
    },
    'katana': {
        'name': 'Katana',
        'api_base': 'https://api.etherscan.io/v2/api',  # Use Etherscan API V2 - supports Katana via chainid
        'chain_id': '747474',  # Katana chain ID (via Etherscan API V2)
        'native_token': 'KAT',
        'weth_address': '0xc99a6A985eD2Cac1ef41640596C5A5f9F4E19Ef5',  # Verify: WETH/WKAT address on Katana
        'explorer_url': 'https://katana.roninchain.com',
    },
    'solana': {
        'name': 'Solana',
        'api_base': None,  # Solana uses RPC endpoints, not explorer APIs
        'rpc_endpoint': 'https://api.mainnet-beta.solana.com',  # Default public RPC
        'chain_id': None,  # Solana doesn't use chain IDs
        'native_token': 'SOL',
        'weth_address': None,  # Solana uses wrapped SOL (WSOL) but different address format
        'explorer_url': 'https://solscan.io',
        'chain_type': 'non-evm',  # Mark as non-EVM
    },
    'sui': {
        'name': 'Sui',
        'api_base': None,  # Sui uses RPC endpoints
        'rpc_endpoint': 'https://fullnode.mainnet.sui.io:443',  # Default public RPC
        'chain_id': None,  # Sui doesn't use chain IDs
        'native_token': 'SUI',
        'weth_address': None,  # Sui uses wrapped SUI but different format
        'explorer_url': 'https://suiscan.xyz',
        'chain_type': 'non-evm',  # Mark as non-EVM
    },
}


def get_chain_config(chain_name: str) -> dict:
    """
    Get configuration for a specific chain
    
    Args:
        chain_name: Lowercase chain name (e.g., 'ethereum', 'base', 'solana', 'sui')
    
    Returns:
        Dictionary with chain configuration
    
    Raises:
        ValueError: If chain is not supported
    """
    chain_name = chain_name.lower()
    if chain_name not in CHAINS:
        raise ValueError(
            f"Chain '{chain_name}' not supported. "
            f"Supported chains: {', '.join(SUPPORTED_CHAINS)}"
        )
    return CHAINS[chain_name]


def is_evm_chain(chain_name: str) -> bool:
    """
    Check if a chain is EVM-compatible
    
    Args:
        chain_name: Lowercase chain name
    
    Returns:
        True if EVM-compatible, False otherwise
    """
    chain_name = chain_name.lower()
    chain_config = get_chain_config(chain_name)
    return chain_config.get('chain_type', 'evm') == 'evm'


def get_api_base(chain_name: str) -> str:
    """Get API base URL for a chain"""
    return get_chain_config(chain_name)['api_base']


def get_chain_id(chain_name: str) -> str:
    """Get chain ID for a chain"""
    return get_chain_config(chain_name)['chain_id']


def get_weth_address(chain_name: str) -> str:
    """Get WETH address for a chain"""
    return get_chain_config(chain_name)['weth_address']


def get_native_token(chain_name: str) -> str:
    """Get native token symbol for a chain"""
    return get_chain_config(chain_name)['native_token']


# DEX Router addresses - chain-specific
# Note: Some DEXes deploy on multiple chains, addresses may differ
DEX_ROUTERS_BY_CHAIN = {
    'ethereum': {
        # Uniswap V2
        "Uniswap V2": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
        # Uniswap V3 Router 2
        "Uniswap V3 Router": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
        # SushiSwap
        "SushiSwap": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
        # Curve Router
        "Curve Router": "0x99C9FC46f92E8a1c0deC1b1747d010903E884bE1",
        # 1inch V5 Router
        "1inch V5": "0x1111111254EEB25477B68fb85Ed929f73A960582",
        # Balancer V2
        "Balancer V2": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        # 0x Protocol
        "0x Protocol": "0xDef1C0ded9bec7F1a1670819833240f027b25EfF",
    },
    'base': {
        # Uniswap V3 Router
        "Uniswap V3 Router": "0x2626664c2603336E57B271c5C0b26F421741e481",
        # Uniswap V2 (if available)
        "Uniswap V2": "0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24",
        # SushiSwap (if available)
        "SushiSwap": "0x6BDED42c6DA8FBf0d2bA55B2fa120C5e0c8D7891",
    },
    'arbitrum': {
        # Uniswap V3 Router
        "Uniswap V3 Router": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
        # Uniswap V2 (if available)
        "Uniswap V2": "0xf164fC0Ec4E93095b805a8881656a6b3Fbe44F6a",
        # SushiSwap
        "SushiSwap": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
        # Camelot DEX (Arbitrum native)
        "Camelot": "0xc873fEcbd354f5A56E00E710B90EF4201db2448d",
    },
    'optimism': {
        # Uniswap V3 Router
        "Uniswap V3 Router": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
        # Velodrome Finance (Optimism native)
        "Velodrome": "0x9c12939390052919aF3155f41Bf4160Fd3666A6f",
    },
    'polygon': {
        # Uniswap V3 Router
        "Uniswap V3 Router": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
        # QuickSwap (Polygon native)
        "QuickSwap": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
        # SushiSwap
        "SushiSwap": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
    },
    'monad': {
        # Placeholder - update when Monad DEXes are known
        # Will likely have Uniswap V3, etc.
    },
    'avax': {
        # Uniswap V3 Router
        "Uniswap V3 Router": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
        # Trader Joe (Avalanche native)
        "Trader Joe": "0x60aE616a2155Ee3d9A68541Ba4544862310933d4",
        # Pangolin (Avalanche native)
        "Pangolin": "0xE54Ca86531e17Ef3616d22Ca28b0D458b6C89106",
    },
    'binance': {
        # Uniswap V3 Router (if available)
        "Uniswap V3 Router": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
        # PancakeSwap (BSC native)
        "PancakeSwap": "0x10ED43C718714eb63d5aA57B78B54704E256024E",
        # Biswap (BSC native)
        "Biswap": "0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8",
    },
    'linea': {
        # Uniswap V3 Router
        "Uniswap V3 Router": "0x2626664c2603336E57B271c5C0b26F421741e481",
        # Horizondex (Linea native, if available)
    },
    'katana': {
        # Katana DEX (Ronin native)
        # Note: Ronin uses a different DEX structure
    },
}


def get_dex_routers(chain_name: str) -> dict:
    """
    Get DEX router addresses for a specific chain
    
    Args:
        chain_name: Lowercase chain name
    
    Returns:
        Dictionary of DEX name -> router address
    """
    chain_name = chain_name.lower()
    if chain_name not in DEX_ROUTERS_BY_CHAIN:
        return {}
    
    routers = DEX_ROUTERS_BY_CHAIN[chain_name].copy()
    
    # Add common DEXes that are available on most chains
    # Uniswap V3 is usually available everywhere
    if 'Uniswap V3 Router' not in routers:
        routers['Uniswap V3 Router'] = "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45"
    
    return routers

