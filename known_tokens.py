"""
Known token addresses and metadata
Used as fallback when Etherscan API fails
"""

KNOWN_TOKENS = {
    # Binance Smart Chain tokens
    "0xe846d164b88ed2e1209609fea3cf7a3d89d70d2d": {
        "name": "Hawk",
        "symbol": "Hawk",
        "decimals": 18
    },
    "0x00000000efe302beaa2b3e6e1b18d08d69a9012a": {
        "name": "AUSD",
        "symbol": "AUSD",
        "decimals": 6
    },
    "0x009986e0d9fef14aea1efd21703522406aa964ab": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0x0221c87862f9231e3877b6822eb2948ee1184077": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0x056b269eb1f75477a8666ae8c7fe01b64dd55ecc": {
        "name": "USD3",
        "symbol": "USD3",
        "decimals": 6
    },
    "0x07b850ddfa8e4218a9b18fb61e90404f84c62395": {
        "name": "U‎‎‎‏‍⁣S‎‌‍D​⁣ ‌‌C‎‏⁣‍oі‍‏n",
        "symbol": "U‍⁣‌‎⁣‍S⁣‏D‎⁣C‏‍",
        "decimals": 18
    },
    "0x0b873b3214c76bb29fc4ce164497b88a5b6e67f6": {
        "name": "Crypto Pump Meme",
        "symbol": "CPM",
        "decimals": 18
    },
    "0x0e5bd5dad3211f9e7138a0a2f6d6241f6476d7c3": {
        "name": "Tether USD",
        "symbol": "USDT",
        "decimals": 6
    },
    "0x0f359fd18bda75e9c49bc027e7da59a4b01bf32a": {
        "name": "Relend USDC",
        "symbol": "reUSDC",
        "decimals": 18
    },
    "0x0f49943d89e7417522107f6e824c30aad487e6c0": {
        "name": "Padre Spurdo",
        "symbol": "SP",
        "decimals": 18
    },
    "0x10fb6bbcba3f405e82f21b140280de43eda5aab2": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0x11113ff3a60c2450f4b22515cb760417259ee94b": {
        "name": "Nest Basis",
        "symbol": "nBASIS",
        "decimals": 6
    },
    "0x111bb5c4157f3ec5f1967e57025ea84a924efe07": {
        "name": "Shibo Kibo",
        "symbol": "KEB",
        "decimals": 18
    },
    "0x1222d4c967af7affb9dd25f35813c205fc2f4e2b": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0x12b004719fb632f1e7c010c6f5d6009fb4258442": {
        "name": "Locked iUSD - 1 weeks",
        "symbol": "liUSD-1w",
        "decimals": 18
    },
    "0x161a4682a69a0cf35713268f1348a068d745a5d2": {
        "name": "Stars",
        "symbol": "Stars",
        "decimals": 18
    },
    "0x1bdef722a55a3fa811d4f7bde0a837986dc1b08d": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0x1d9c909099beda97381ac03a68f605e57b038a17": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0x1f79bc2bf1facf86410a8f18ccca7e0ee01abc7e": {
        "name": "PT reUSDe 18DEC2025",
        "symbol": "PT-reUSDe-18DEC2025",
        "decimals": 18
    },
    "0x1fb3c5c35d95f48e48ffc8e36bcce5cb5f29f57c": {
        "name": "PT Strata Senior USDe 15JAN2026",
        "symbol": "PT-srUSDe-15JAN2026",
        "decimals": 18
    },
    "0x1fb5eaa93251fd014773dc66dd740bdb2637379d": {
        "name": "Trump Gone",
        "symbol": "GONE",
        "decimals": 18
    },
    "0x2088933e4242cc7020fb8fb18481c7d22f3e8a55": {
        "name": "XMOVE",
        "symbol": "XMOVE",
        "decimals": 18
    },
    "0x20e6a1f7cfd50ae3c994a69fd99ce231b7ec32b7": {
        "name": "Tether USD",
        "symbol": "USDT",
        "decimals": 6
    },
    "0x215a6a2a0d1c563d0cb55ebd8d126f3bc0b92cf2": {
        "name": "PT Neutrl USD 26FEB2026",
        "symbol": "PT-NUSD-26FEB2026",
        "decimals": 18
    },
    "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": {
        "name": "Wrapped BTC",
        "symbol": "WBTC",
        "decimals": 8
    },
    "0x23878914efe38d27c4d67ab83ed1b93a74d4086a": {
        "name": "Aave Ethereum USDT",
        "symbol": "aEthUSDT",
        "decimals": 6
    },
    "0x243ea21e3a451ebf7707c421678ae4e3b1152bd0": {
        "name": "EꓔH",
        "symbol": "EꓔH",
        "decimals": 18
    },
    "0x2672a609c8e0b09830e62db2bd26475fb060b1c8": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0x27b9be969cef0ed06de2801acf88ca728595eeb0": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0x289f8baab9f7587214377744bcaaeb6021accf95": {
        "name": "Disco Kendu",
        "symbol": "DOK",
        "decimals": 18
    },
    "0x29fd7180e5cced14ad148c7997e6b6857a8be86e": {
        "name": "PT Resolv Liquidity Provider Token 9APR2026",
        "symbol": "PT-RLP-9APR2026",
        "decimals": 6
    },
    "0x2e9555c4d34b96b0e76b641457293d5a9fbe4d03": {
        "name": "Grok",
        "symbol": "Grok",
        "decimals": 18
    },
    "0x30929f710c035da471d5a22519c3caf65ac52a2b": {
        "name": "Pa‌‌⁣‏x‌o⁣‌‍‍s⁣​‎ ‎⁣Go‌‌l⁣‏​d‏‌",
        "symbol": "P‏⁣‎А⁣X‎⁣G‏⁣​‌⁣‌‎",
        "decimals": 18
    },
    "0x32ee8ae557dda839435c6adff60fcc2b0aa082a3": {
        "name": "ꓴꓢꓓꓔ",
        "symbol": "ꓴꓢꓓꓔ",
        "decimals": 6
    },
    "0x356b8d89c1e1239cbbb9de4815c39a1474d5ba7d": {
        "name": "Syrup USDT",
        "symbol": "syrupUSDT",
        "decimals": 6
    },
    "0x3635375dc4175659f5c95720ec386747e455c7ff": {
        "name": "PT Staked USN 29JAN2026",
        "symbol": "PT-sUSN-29JAN2026",
        "decimals": 18
    },
    "0x38c503a438185cde29b5cf4dc1442fd6f074f1cc": {
        "name": "Aave Ethereum PT_USDe_27NOV2025",
        "symbol": "aEthPT_USDe_27NOV2025",
        "decimals": 18
    },
    "0x3ec911da0fcc826948b04fd94c3f870e564b3e41": {
        "name": "Tether USD",
        "symbol": "USDT",
        "decimals": 6
    },
    "0x3fc29836e84e471a053d2d9e80494a867d670ead": {
        "name": "Ethereum Games",
        "symbol": "ETHG",
        "decimals": 8
    },
    "0x40cb7714cc07c36fe8b631a329ec82c5d06a7498": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0x40d16fc0246ad3160ccc09b8d0d3a2cd28ae6c2f": {
        "name": "GHO Token",
        "symbol": "GHO",
        "decimals": 18
    },
    "0x44040f6c123a95dce1b8ba85214aac34fb5c772d": {
        "name": "ꓴꓢꓓС",
        "symbol": "ꓴꓢꓓС",
        "decimals": 6
    },
    "0x45804880de22913dafe09f4980848ece6ecbaf78": {
        "name": "Paxos Gold",
        "symbol": "PAXG",
        "decimals": 18
    },
    "0x477e8ba4ffcb8b2e22e2406f634e54d429e8769b": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0x48f9e38f3070ad8945dfeae3fa70987722e3d89c": {
        "name": "infiniFi USD",
        "symbol": "iUSD",
        "decimals": 18
    },
    "0x4c9edd5852cd905f086c759e8383e09bff1e68b3": {
        "name": "USDe",
        "symbol": "USDe",
        "decimals": 18
    },
    "0x4d5f47fa6a74757f35c14fd3a6ef8e3c9bc514e8": {
        "name": "Aave Ethereum WETH",
        "symbol": "aEthWETH",
        "decimals": 18
    },
    "0x4f5923fc5fd4a93352581b38b7cd26943012decf": {
        "name": "Aave Ethereum USDe",
        "symbol": "aEthUSDe",
        "decimals": 18
    },
    "0x51e5315e62460e4fe50d80dea05765747f88f51c": {
        "name": "EePIN",
        "symbol": "EPIN",
        "decimals": 18
    },
    "0x53f3373f0d811902405f91eb0d5cc3957887220d": {
        "name": "PT Strata Junior USDe 15JAN2026",
        "symbol": "PT-jrUSDe-15JAN2026",
        "decimals": 18
    },
    "0x54bf2659b5cdfd86b75920e93c0844c0364f5166": {
        "name": "PT Staked NUSD 5MAR2026",
        "symbol": "PT-sNUSD-5MAR2026",
        "decimals": 18
    },
    "0x54e6f2cd4c092700542a98f77a1f929dd47a01c6": {
        "name": "EꓔH",
        "symbol": "EꓔH",
        "decimals": 18
    },
    "0x57e114b691db790c35207b2e685d4a43181e6061": {
        "name": "Ethena",
        "symbol": "ENA",
        "decimals": 18
    },
    "0x58d97b57bb95320f9a05dc918aef65434969c2b2": {
        "name": "Morpho Token",
        "symbol": "MORPHO",
        "decimals": 18
    },
    "0x58e2f7a7d5e9e0cbe9e94a37f930a783782dedb3": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0x5d85e2b013c5fd07338bad72e83de69874604451": {
        "name": "Tether USD",
        "symbol": "USDT",
        "decimals": 6
    },
    "0x5ee5bf7ae06d1be5997a1a72006fe6c607ec6de8": {
        "name": "Aave Ethereum WBTC",
        "symbol": "aEthWBTC",
        "decimals": 8
    },
    "0x6110132f941119d0e036cb58b47b52ce597bfa67": {
        "name": "ꓴꓢꓓС",
        "symbol": "ꓴꓢꓓС",
        "decimals": 6
    },
    "0x62c6e813b9589c3631ba0cdb013acdb8544038b7": {
        "name": "PT Ethena USDe 27NOV2025",
        "symbol": "PT-USDe-27NOV2025",
        "decimals": 18
    },
    "0x62f7c4aca52f22f42e5755d648b054ecf741ebd2": {
        "name": "⁠U‍S﻿D⁬С﻿‍",
        "symbol": "⁭U⁪S⁭D⁬С⁭⁭",
        "decimals": 6
    },
    "0x63b19ca11ec7b24d7281c55152ca08f9c686e2ef": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0x63e9b27ae2247f4bf61ca7ff85ca8d718995396e": {
        "name": "Tether USD",
        "symbol": "USDT",
        "decimals": 6
    },
    "0x6554bc7e300b3f77d34b7100a26e515f52b462fa": {
        "name": "PT AI Dollar 29JAN2026",
        "symbol": "PT-AID-29JAN2026",
        "decimals": 18
    },
    "0x660b045699ecc049036c0db165bcb99fc22a2d51": {
        "name": "Meta Boost",
        "symbol": "MB",
        "decimals": 18
    },
    "0x66a3c2fa3e467aa586e90912f977e648589cabaf": {
        "name": "AI Chain Coin",
        "symbol": "AICC",
        "decimals": 8
    },
    "0x68749665ff8d2d112fa859aa293f07a622782f38": {
        "name": "Tether Gold",
        "symbol": "XAUt",
        "decimals": 6
    },
    "0x692cd1cce74bfb88947a3e02f6993ce677d54638": {
        "name": "xAI",
        "symbol": "xAI",
        "decimals": 18
    },
    "0x6a29a46e21c730dca1d8b23d637c101cec605c5b": {
        "name": "Fluid Gho Token",
        "symbol": "fGHO",
        "decimals": 18
    },
    "0x6d386ca1f7e2b6f6ab1aa6d85fd53fe4af29f721": {
        "name": "EꓔH",
        "symbol": "EꓔH",
        "decimals": 18
    },
    "0x6df1c1e379bc5a00a7b4c6e67a203333772f45a8": {
        "name": "Aave Ethereum Variable Debt USDT",
        "symbol": "variableDebtEthUSDT",
        "decimals": 6
    },
    "0x6ecc748c6f860cf011f6f7c005ebd8a678fea8fd": {
        "name": "Tether USD",
        "symbol": "USDT",
        "decimals": 6
    },
    "0x6f9fe88ce51936bdf7701bf23d7d479dbb05d44a": {
        "name": "Spurdo Bun",
        "symbol": "SPD",
        "decimals": 18
    },
    "0x7204b7dbf9412567835633b6f00c3edc3a8d6330": {
        "name": "Coinshift USDC",
        "symbol": "csUSDC",
        "decimals": 18
    },
    "0x7226a7a4925aebebf5b62beefe278991717cf738": {
        "name": "ꓴꓢꓓС",
        "symbol": "ꓴꓢꓓС",
        "decimals": 6
    },
    "0x72e95b8931767c79ba4eee721354d6e99a61d004": {
        "name": "Aave Ethereum Variable Debt USDC",
        "symbol": "variableDebtEthUSDC",
        "decimals": 6
    },
    "0x73f7d02d546025843f952a22abd92050650cc3d4": {
        "name": "AlphaGo",
        "symbol": "AlphaGo",
        "decimals": 18
    },
    "0x7592ac82f572873b2edb4a9963425150cc018857": {
        "name": "ꓴꓢꓓꓔ",
        "symbol": "ꓴꓢꓓꓔ",
        "decimals": 6
    },
    "0x777791c4d6dc2ce140d00d2828a7c93503c67777": {
        "name": "Hyperithm USDC",
        "symbol": "hyperUSDC",
        "decimals": 18
    },
    "0x7c3d6c5d55b367dd769b023b493d3e35c00264e0": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0x7f3ba3f18f1378fbd8efa0a20bfe7016e2efd266": {
        "name": "YES",
        "symbol": "YES",
        "decimals": 18
    },
    "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9": {
        "name": "Aave Token",
        "symbol": "AAVE",
        "decimals": 18
    },
    "0x808507121b80c02388fad14726482e061b8da827": {
        "name": "Pendle",
        "symbol": "PENDLE",
        "decimals": 18
    },
    "0x80ac24aa929eaf5013f6436cda2a7ba190f5cc0b": {
        "name": "Syrup USDC",
        "symbol": "syrupUSDC",
        "decimals": 6
    },
    "0x814708d8d74719a147887af01da1be44f640a27b": {
        "name": "PT Nest Basis 26MAR2026",
        "symbol": "PT-nBASIS-26MAR2026",
        "decimals": 6
    },
    "0x8236a87084f8b84306f72007f36f2618a5634494": {
        "name": "Lombard Staked BTC",
        "symbol": "LBTC",
        "decimals": 8
    },
    "0x86ade43ada326c0ff10b2941a4cd5ef0bbda621a": {
        "name": "ꓴꓢꓓꓔ",
        "symbol": "ꓴꓢꓓꓔ",
        "decimals": 6
    },
    "0x88887be419578051ff9f4eb6c858a951921d8888": {
        "name": "Staked cap USD",
        "symbol": "stcUSD",
        "decimals": 18
    },
    "0x8fc85e00e036218c7ada916f98c39293ed0d4ca0": {
        "name": "ꓴꓢꓓС",
        "symbol": "ꓴꓢꓓС",
        "decimals": 6
    },
    "0x9102468d31301d55d4e5550e19132434e9b7b0a7": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0x9692cf346fcd622ba20aaefc5052f8d52d0bbf58": {
        "name": "ꓴꓢꓓС",
        "symbol": "ꓴꓢꓓС",
        "decimals": 6
    },
    "0x98c23e9d8f34fefb1b7bd6a91b7ff122f4e16f5c": {
        "name": "Aave Ethereum USDC",
        "symbol": "aEthUSDC",
        "decimals": 6
    },
    "0x9db20496f41f9713b9e8b5d316f5fdccd4fdcfdd": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0x9e351a9d94d7a0727f273450f4a75f2b062e479b": {
        "name": "Kibo Shib",
        "symbol": "KIB",
        "decimals": 18
    },
    "0x9fb7b4477576fe5b32be4c1843afb1e55f251b33": {
        "name": "Fluid USD Coin",
        "symbol": "fUSDC",
        "decimals": 6
    },
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {
        "name": "USDC",
        "symbol": "USDC",
        "decimals": 6
    },
    "0xa0e83d59040f6d8333e7c47f0bb34ef66c6cb85a": {
        "name": "Tether USD",
        "symbol": "USDT",
        "decimals": 6
    },
    "0xa700b4eb416be35b2911fd5dee80678ff64ff6c9": {
        "name": "Aave Ethereum AAVE",
        "symbol": "aEthAAVE",
        "decimals": 18
    },
    "0xa95f8e69cc32388c80986caf947bbfa60a0aa8cd": {
        "name": "ꓴꓢꓓС",
        "symbol": "ꓴꓢꓓС",
        "decimals": 6
    },
    "0xac350b9e0186b0c1dd5cff226605b5b19cbc90e9": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0xae7ab96520de3a18e5e111b5eaab095312d7fe84": {
        "name": "stETH",
        "symbol": "stETH",
        "decimals": 18
    },
    "0xb0c9151d3acbcdb18b67e66124eb9eb0fdf6c4cc": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0xb0f05e4de970a1aaf77f8c2f823953a367504ba9": {
        "name": "Alpha USDC Core",
        "symbol": "aUSDC",
        "decimals": 18
    },
    "0xb10da2f9147f9cf2b8826877cd0c95c18a0f42dc": {
        "name": "PT Compounding Open Dollar 20NOV2025",
        "symbol": "PT-cUSDO-20NOV2025",
        "decimals": 18
    },
    "0xb326eaaadbf8ea838aec8cc2a88e466e7d0aaea8": {
        "name": "Tether USD",
        "symbol": "USDT",
        "decimals": 6
    },
    "0xb44cdbef3145c1c1e772e8228e1154c80e70618e": {
        "name": "PT infiniFi USD 4DEC2025",
        "symbol": "PT-iUSD-4DEC2025",
        "decimals": 18
    },
    "0xb5ff0b0f9c2972801860d9ed823d648ace067aef": {
        "name": "GPT4",
        "symbol": "GPT4",
        "decimals": 18
    },
    "0xb9d514814c1780c235e4b973d16210d917e32926": {
        "name": "Trump Bone",
        "symbol": "BONE",
        "decimals": 18
    },
    "0xbba15a107880a1f2dfbf93448e20e0c0546ca737": {
        "name": "ꓴꓢꓓС",
        "symbol": "ꓴꓢꓓС",
        "decimals": 6
    },
    "0xbd33da1f9a0cc70224e9a71c80baa92fd0eb82d0": {
        "name": "BullRun Meme",
        "symbol": "BRM",
        "decimals": 18
    },
    "0xbe54767735fb7acca2aa7e2d209a6f705073536d": {
        "name": "Aave Ethereum PT_sUSDe_5FEB_2026",
        "symbol": "aEthPT_sUSDe_5FEB_2026",
        "decimals": 18
    },
    "0xc00e94cb662c3520282e6f5717214004a7f26888": {
        "name": "Compound",
        "symbol": "COMP",
        "decimals": 18
    },
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": {
        "name": "Wrapped Ether",
        "symbol": "WETH",
        "decimals": 18
    },
    "0xc211e9abd80202afbf6e5ec821a1103e2bda0b14": {
        "name": "ꓴꓢꓓС",
        "symbol": "ꓴꓢꓓС",
        "decimals": 6
    },
    "0xc3c7e5e277d31cd24a3ac4cc9af3b6770f30ea33": {
        "name": "PT Staked cap USD 29JAN2026",
        "symbol": "PT-stcUSD-29JAN2026",
        "decimals": 18
    },
    "0xc5193ceb45a9b75e7f6c073d275bcd817e809e2e": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0xc6e074a62d19a5d54a37a204d2e87b74570c1365": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0xc76aa60ed672b3ceb922eb207b6a443d487d97eb": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0xca68440d9d81cd63e74ce2c2262ff07d8e0544be": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0xcc781b043933c10a04409b22aada3a3d1a7f29d4": {
        "name": "Pendle Market",
        "symbol": "PENDLE-LPT",
        "decimals": 18
    },
    "0xcccc62962d17b8914c62d74ffb843d73b2a3cccc": {
        "name": "cap USD",
        "symbol": "cUSD",
        "decimals": 18
    },
    "0xcdd7c442f3c7af33c48e06ec343b8776e8524c65": {
        "name": "Token",
        "symbol": "ERC20",
        "decimals": 18
    },
    "0xd1071163ea0670b011d7456c10a9456e5528b4e6": {
        "name": "Wall Life",
        "symbol": "LIFE",
        "decimals": 18
    },
    "0xd1396f7cd157eea7d096326ddec871c9fe22eda8": {
        "name": "EꓔH",
        "symbol": "EꓔH",
        "decimals": 18
    },
    "0xd2cd73fa955aba07f5c3f53a1e01744a2b857daf": {
        "name": "PT Fluid Gho Token 18DEC2025",
        "symbol": "PT-fGHO-18DEC2025",
        "decimals": 18
    },
    "0xd4419c2d3daa986dc30444fa333a846be44fd1eb": {
        "name": "ZIK coin",
        "symbol": "ZIK",
        "decimals": 18
    },
    "0xd63070114470f685b75b74d60eec7c1113d33a3d": {
        "name": "Usual Boosted USDC",
        "symbol": "USUALUSDC+",
        "decimals": 18
    },
    "0xda67b4284609d2d48e5d10cfac411572727dc1ed": {
        "name": "USN",
        "symbol": "USN",
        "decimals": 18
    },
    "0xdac17f958d2ee523a2206206994597c13d831ec7": {
        "name": "Tether USD",
        "symbol": "USDT",
        "decimals": 6
    },
    "0xdbdc1ef57537e34680b898e1febd3d68c7389bcb": {
        "name": "Staked infiniFi USD",
        "symbol": "siUSD",
        "decimals": 18
    },
    "0xddc0f880ff6e4e22e4b74632fbb43ce4df6ccc5a": {
        "name": "Re Protocol reUSDe",
        "symbol": "reUSDe",
        "decimals": 18
    },
    "0xe24a3dc889621612422a64e6388927901608b91d": {
        "name": "Staked USN",
        "symbol": "sUSN",
        "decimals": 18
    },
    "0xe3df25369d98e17fa7f98e6e5f4f629419990edc": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0xe4619c1f015cb6a6d9b82433968458974c5ee23d": {
        "name": "ꓴꓢꓓС",
        "symbol": "ꓴꓢꓓС",
        "decimals": 6
    },
    "0xe556aba6fe6036275ec1f87eda296be72c811bce": {
        "name": "Neutrl USD",
        "symbol": "NUSD",
        "decimals": 18
    },
    "0xe8483517077afa11a9b07f849cee2552f040d7b2": {
        "name": "PT Ethena sUSDE 5FEB2026",
        "symbol": "PT-sUSDE-5FEB2026",
        "decimals": 18
    },
    "0xec53bf9167f50cdeb3ae105f56099aaab9061f83": {
        "name": "Eigen",
        "symbol": "EIGEN",
        "decimals": 18
    },
    "0xec808669ecbeca87d55f5bbb172fc130ebf483b4": {
        "name": "ꓴꓢꓓС",
        "symbol": "ꓴꓢꓓС",
        "decimals": 6
    },
    "0xee61acd56bd8eda16b402dd078560c931cf38b63": {
        "name": "Token",
        "symbol": "ERC20",
        "decimals": 18
    },
    "0xf16498b7bb8a1c6195354ca09c95b561f8c79a25": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0xf28ccd4e6a2faad9ab050e181273ccf24bc36a70": {
        "name": "DOGX",
        "symbol": "DOGX",
        "decimals": 18
    },
    "0xfa53e7420687c982e373815400d28a60bcca92ff": {
        "name": "ꓴꓢꓓС",
        "symbol": "ꓴꓢꓓС",
        "decimals": 6
    },
    "0xfa9fbcf2e52037328f9376ad8fadbac07b0e863d": {
        "name": "PT Syrup USDC 18DEC2025",
        "symbol": "PT-syrupUSDC-18DEC2025",
        "decimals": 6
    },
    "0xfac06aa109ba98bc9a76bb1109d0eb41f2692ebc": {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6
    },
    "0xfe0c30065b384f05761f15d0cc899d4f9f9cc0eb": {
        "name": "ether.fi governance token",
        "symbol": "ETHFI",
        "decimals": 18
    },
}
