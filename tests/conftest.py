"""Pytest configuration and fixtures."""

import sys
from pathlib import Path

import pytest

# Add src to path so tests can import core modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def valid_eth_address():
    """Ethereum Foundation address."""
    return "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae"


@pytest.fixture
def valid_bsc_address():
    """Binance Hot Wallet on BSC."""
    return "0xf977814e90da44bfa03b6295a0616a897441acec"


@pytest.fixture
def invalid_addresses():
    """Collection of invalid address formats."""
    return [
        "",  # Empty
        "0x",  # Too short
        "0xabc",  # Too short
        "0xde0b295669a9fd93d5f28d9ec85e40f4cb697ba",  # 39 chars
        "0xde0b295669a9fd93d5f28d9ec85e40f4cb697baee",  # 41 chars
        "de0b295669a9fd93d5f28d9ec85e40f4cb697bae",  # Missing 0x
        "0xGGGb295669a9fd93d5f28d9ec85e40f4cb697bae",  # Invalid hex
        None,  # None type
        123,  # Number type
    ]
