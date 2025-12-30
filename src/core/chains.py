"""Chain configuration registry for multi-blockchain support."""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ChainConfig:
    """Configuration for a blockchain network."""

    name: str
    symbol: str
    api_url: str
    api_key_env: str
    explorer_url: str
    chain_id: int
    # For stats endpoint differences (bnbprice vs ethprice)
    price_action: str = "ethprice"
    supply_action: str = "ethsupply"


# Etherscan V2 API base URL (works for all chains with chainid param)
ETHERSCAN_V2_API = "https://api.etherscan.io/v2/api"

# Chain registry - easy to extend with new chains
CHAIN_REGISTRY: Dict[str, ChainConfig] = {
    "ethereum": ChainConfig(
        name="Ethereum",
        symbol="ETH",
        api_url=ETHERSCAN_V2_API,
        api_key_env="ETHERSCAN_API_KEY",
        explorer_url="https://etherscan.io",
        chain_id=1,
        price_action="ethprice",
        supply_action="ethsupply",
    ),
    "bsc": ChainConfig(
        name="BNB Smart Chain",
        symbol="BNB",
        api_url=ETHERSCAN_V2_API,  # V2 API (requires paid plan for BSC)
        api_key_env="ETHERSCAN_API_KEY",  # Same key as Ethereum
        explorer_url="https://bscscan.com",
        chain_id=56,
        price_action="bnbprice",
        supply_action="bnbsupply",
    ),
    # Future chains (uncomment when ready):
    # "polygon": ChainConfig(
    #     name="Polygon",
    #     symbol="MATIC",
    #     api_url="https://api.polygonscan.com/api",
    #     api_key_env="POLYGONSCAN_API_KEY",
    #     explorer_url="https://polygonscan.com",
    #     chain_id=137,
    # ),
    # "arbitrum": ChainConfig(
    #     name="Arbitrum One",
    #     symbol="ETH",
    #     api_url="https://api.arbiscan.io/api",
    #     api_key_env="ARBISCAN_API_KEY",
    #     explorer_url="https://arbiscan.io",
    #     chain_id=42161,
    # ),
    # "base": ChainConfig(
    #     name="Base",
    #     symbol="ETH",
    #     api_url="https://api.basescan.org/api",
    #     api_key_env="BASESCAN_API_KEY",
    #     explorer_url="https://basescan.org",
    #     chain_id=8453,
    # ),
}


# Known whale addresses per chain
KNOWN_WHALES: Dict[str, Dict[str, str]] = {
    "ethereum": {
        "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae": "Ethereum Foundation",
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": "WETH Contract",
        "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8": "Binance 7",
        "0x28c6c06298d514db089934071355e5743bf21d60": "Binance 14",
        "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance 8",
        "0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503": "Binance: Binance-Peg Tokens",
    },
    "bsc": {
        "0xf977814e90da44bfa03b6295a0616a897441acec": "Binance Hot Wallet 20",
        "0x8894e0a0c962cb723c1976a4421c95949be2d4e3": "Binance Hot Wallet 6",
        "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c": "WBNB Contract",
        "0x0000000000000000000000000000000000001004": "BSC Token Hub",
        "0x10ed43c718714eb63d5aa57b78b54704e256024e": "PancakeSwap Router v2",
        "0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82": "CAKE Token",
        "0x55d398326f99059ff775485246999027b3197955": "Binance-Peg USDT",
    },
}


# Exchange addresses per chain
EXCHANGE_ADDRESSES: Dict[str, Dict[str, str]] = {
    "ethereum": {
        "0x28c6c06298d514db089934071355e5743bf21d60": "Binance",
        "0xa090e606e30bd747d4e6245a1517ebe430f0057e": "Gemini",
        "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b": "OKEx",
        "0x2b5634c42055806a59e9107ed44d43c426e58258": "KuCoin",
        "0x71660c4005ba85c37ccec55d0c4493e66fe775d3": "Coinbase",
        "0xfbb1b73c4f0bda4f67dca266ce6ef42f520fbb98": "Bittrex",
    },
    "bsc": {
        "0xf977814e90da44bfa03b6295a0616a897441acec": "Binance",
        "0x8894e0a0c962cb723c1976a4421c95949be2d4e3": "Binance 6",
        "0x28c6c06298d514db089934071355e5743bf21d60": "Binance 14",
        "0x7c0629bbbaf7d68ffaa393e3fedc9b633679fa5f": "OKX",
        "0xf89d7b9c864f589bbf53a82105107622b35eaa40": "Bybit",
        "0x53f78a071d04224b8e254e243fffc6d9f2f3fa23": "KuCoin",
        "0x0d0707963952f2fba59dd06f2b425ace40b492fe": "Gate.io",
        "0x72a53cdbbcc1b9efa39c834a540550e23463aacb": "Crypto.com",
        "0xefdca55e4bce6c1d535cb2d0687b5567eef2ae83": "Huobi",
    },
}


def get_chain_config(chain: str) -> ChainConfig:
    """Get configuration for a chain by name."""
    chain_lower = chain.lower()
    if chain_lower not in CHAIN_REGISTRY:
        available = ", ".join(CHAIN_REGISTRY.keys())
        raise ValueError(f"Unknown chain: {chain}. Available: {available}")
    return CHAIN_REGISTRY[chain_lower]


def get_supported_chains() -> list[str]:
    """Get list of supported chain names."""
    return list(CHAIN_REGISTRY.keys())


def get_known_whales(chain: str) -> Dict[str, str]:
    """Get known whale addresses for a chain."""
    return KNOWN_WHALES.get(chain.lower(), {})


def get_exchange_addresses(chain: str) -> Dict[str, str]:
    """Get exchange addresses for a chain."""
    return EXCHANGE_ADDRESSES.get(chain.lower(), {})
