"""MCP Multi-Chain Blockchain Scanner - Python implementation."""

__version__ = "2.0.0"

from .chains import (
    CHAIN_REGISTRY,
    ChainConfig,
    get_chain_config,
    get_supported_chains,
)
from .blockchain_service import BlockchainService, EtherscanService
from .validators import validate_address, validate_positive, validate_chain

__all__ = [
    "BlockchainService",
    "EtherscanService",  # Backwards compatibility
    "ChainConfig",
    "CHAIN_REGISTRY",
    "get_chain_config",
    "get_supported_chains",
    "validate_address",
    "validate_positive",
    "validate_chain",
]
