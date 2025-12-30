"""Input validation utilities for blockchain addresses and parameters."""

import re
from typing import Union


def validate_address(address: str) -> str:
    """Validate Ethereum/BSC address format (0x + 40 hex chars).

    Args:
        address: Blockchain address to validate

    Returns:
        Lowercase normalized address

    Raises:
        ValueError: If address format is invalid
    """
    if not isinstance(address, str):
        raise ValueError(f"Address must be string, got {type(address).__name__}")
    if not re.match(r"^0x[a-fA-F0-9]{40}$", address):
        raise ValueError(f"Invalid address format: {address}")
    return address.lower()


def validate_positive(value: Union[int, float], name: str) -> Union[int, float]:
    """Validate that a numeric value is positive.

    Args:
        value: Numeric value to validate
        name: Parameter name for error message

    Returns:
        The validated value

    Raises:
        ValueError: If value is not positive
    """
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


def validate_chain(chain: str, supported: list[str]) -> str:
    """Validate chain name against supported chains.

    Args:
        chain: Chain name to validate
        supported: List of supported chain names

    Returns:
        Lowercase chain name

    Raises:
        ValueError: If chain is not supported
    """
    chain_lower = chain.lower()
    if chain_lower not in supported:
        raise ValueError(f"Unsupported chain: {chain}. Available: {', '.join(supported)}")
    return chain_lower
