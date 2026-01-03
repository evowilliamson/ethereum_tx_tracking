"""
Ethereum DEX Configuration
Contains router addresses and function signatures for all major DEX protocols

IMPORTANT: This system uses MULTIPLE detection methods:
1. Router address matching (explicit DEX detection)
2. Function signature matching (swap function detection)
3. Transfer pattern analysis (catches ANY swap, even from unknown DEXes)

Even if a DEX is not listed here, the system will still detect its swaps by
analyzing ERC-20 transfer patterns (send token A, receive token B = swap).

To add a new DEX:
1. Find the router/exchange contract address on Etherscan
2. Add it to DEX_ROUTERS below
3. Optionally add swap function signatures to SWAP_FUNCTION_SIGNATURES
"""

# Major DEX Router Contract Addresses on Ethereum Mainnet
DEX_ROUTERS = {
    # Uniswap V2
    "Uniswap V2": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    
    # Uniswap V3 Router 2
    "Uniswap V3 Router": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
    
    # SushiSwap
    "SushiSwap": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
    
    # Curve Finance (multiple pools, but we check for Curve router)
    "Curve Router": "0x99C9FC46f92E8a1c0deC1b1747d010903E884bE1",
    
    # 1inch V4 Router
    "1inch V4": "0x1111111254fb6c44bAC0beD2854e76F90643097d",
    
    # 1inch V5 Router
    "1inch V5": "0x1111111254EEB25477B68fb85Ed929f73A960582",
    
    # Balancer V2 Vault
    "Balancer V2": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    
    # 0x Protocol (Exchange Proxy)
    "0x Protocol": "0xDef1C0ded9bec7F1a1670819833240f027b25EfF",
    
    # KyberSwap Elastic Router
    "KyberSwap": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",
    
    # DODO Router
    "DODO": "0xa356867fDCEa8e71AEaF87805808803806231FdC",
    
    # Paraswap Router
    "Paraswap": "0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57",
    
    # CowSwap (CoW Protocol) - Settlement contract
    "CowSwap": "0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
    
    # Bancor Network
    "Bancor": "0x2F9bC877DfB3c0dA6D8238173d855b566E030aF4",
    
    # Fluid.io (Instadapp's unified DEX)
    # FluidDexLite contract - main DEX router
    "Fluid.io": "0xBbcb91440523216e2b87052A99F69c604A7b6e00",
    
    # Fluid.io Resolver (v1.0.0) - also used for swaps
    "Fluid.io Resolver": "0x26b696D0dfDAB6c894Aa9a6575fCD07BB25BbD2C",
    
    # Matcha (0x API frontend)
    "Matcha": "0xDef1C0ded9bec7F1a1670819833240f027b25EfF",  # Uses 0x Protocol
    
    # GMX (perpetuals DEX)
    "GMX": "0x7452c558d24f3C982916791c550C40fCC14b5952",  # GMX Router
    
    # Velodrome Finance (if on Ethereum)
    # Note: Primarily on Optimism, but checking for Ethereum deployment
    
    # Camelot DEX
    # Note: Primarily on Arbitrum
    
    # Trader Joe
    # Note: Primarily on Avalanche
    
    # PancakeSwap (if on Ethereum)
    "PancakeSwap": "0x10ED43C718714eb63d5aA57B78B54704E256024E",  # BSC router, check Ethereum
    
    # ShibaSwap
    "ShibaSwap": "0x03f7724180AA6b939894B5Ca4314783B0b36b329",
    
    # Clipper DEX
    "Clipper": "0x5130f6cE257B8F9bF7fac0A0E519b25c120cB0b6",
    
    # Hashflow
    "Hashflow": "0xE592427A0AEce92De3Edee1F18E0157C05861564",  # Hashflow Router
    
    # OpenOcean
    "OpenOcean": "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",
}

# Swap function signatures (first 4 bytes / 8 hex chars)
SWAP_FUNCTION_SIGNATURES = {
    # Uniswap V2: swapExactTokensForTokens, swapTokensForExactTokens, etc.
    "0x38ed1739",  # swapExactTokensForTokens
    "0x8803dbee",  # swapTokensForExactTokens
    "0x5c11d795",  # swapExactTokensForTokensSupportingFeeOnTransferTokens
    "0x791ac947",  # swapExactTokensForETHSupportingFeeOnTransferTokens
    "0x02751cec",  # swapExactTokensForETH
    "0x4a25d94a",  # swapETHForExactTokens
    "0x7ff36ab5",  # swapExactETHForTokens
    "0x18cbafe5",  # swapExactETHForTokensSupportingFeeOnTransferTokens
    
    # Uniswap V3: exactInputSingle, exactInput, exactOutputSingle, exactOutput
    "0x414bf389",  # exactInputSingle
    "0xdb3e2198",  # exactInput
    "0xdb3e2198",  # exactOutputSingle (same signature, different params)
    "0xf28c0498",  # exactOutput
    
    # SushiSwap (same as Uniswap V2)
    # Uses same signatures as Uniswap V2
    
    # 1inch: swap, unoswap, uniswapV3Swap, etc.
    "0x12aa3caf",  # swap
    "0x2e95b6c8",  # unoswap
    "0x2521b930",  # uniswapV3Swap
    "0xe449022e",  # unoswapTo
    
    # Curve: exchange, exchange_underlying
    "0x3df02124",  # exchange
    "0xa6417ed6",  # exchange_underlying
    
    # 0x Protocol: transformERC20
    "0x415565b0",  # transformERC20
    
    # Balancer: swap
    "0x52bbbe29",  # swap (V2)
    
    # Generic swap signatures
    "0x7c025200",  # swap (generic)
    "0x3593564c",  # swap (generic)
    
    # Hashflow: swap
    "0x415565b0",  # swap (Hashflow)
    
    # OpenOcean: swap
    "0x90411a32",  # swap (OpenOcean)
    
    # GMX: swap
    "0x3593564c",  # swap (GMX, may overlap with generic)
}

# Swap event signatures (for parsing logs)
SWAP_EVENT_SIGNATURES = {
    # Uniswap V2 Swap event
    "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822": "Uniswap V2 Swap",
    
    # Uniswap V3 Swap event
    "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67": "Uniswap V3 Swap",
    
    # SushiSwap (same as Uniswap V2)
    # Curve Swap event
    "0x8b3e96f2b889fa771c53c981b40daf005f63f637f1869f70705215e7b2503fed": "Curve TokenExchange",
    
    # Generic Transfer event (ERC-20)
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef": "ERC-20 Transfer",
}

# Rate limit delay (seconds between requests)
# Default: 0.25 seconds (free tier: 5 calls/sec)
# Can be overridden per-chain if needed
RATE_LIMIT_DELAY = 0.25

# Common token addresses
ETH_ADDRESS = "0x0000000000000000000000000000000000000000"

# Legacy defaults for Ethereum (maintained for backward compatibility)
# New code should use chains_config.get_chain_config() instead
ETHERSCAN_API_BASE = "https://api.etherscan.io/v2/api"
ETHEREUM_CHAIN_ID = "1"
WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"  # Wrapped ETH on Ethereum

