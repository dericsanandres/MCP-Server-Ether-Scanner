"""Tests for validators module."""

import pytest

from core.validators import validate_address, validate_positive, validate_chain


class TestValidateAddress:
    """Tests for validate_address function."""

    def test_valid_lowercase_address(self, valid_eth_address):
        """Valid lowercase address passes."""
        result = validate_address(valid_eth_address)
        assert result == valid_eth_address.lower()

    def test_valid_uppercase_address(self):
        """Valid uppercase address is normalized to lowercase."""
        upper = "0xDE0B295669A9FD93D5F28D9EC85E40F4CB697BAE"
        result = validate_address(upper)
        assert result == upper.lower()

    def test_valid_mixed_case_address(self):
        """Mixed case address is normalized."""
        mixed = "0xDe0B295669a9FD93d5f28d9eC85E40F4Cb697BaE"
        result = validate_address(mixed)
        assert result == mixed.lower()

    def test_empty_string_raises(self):
        """Empty string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid address"):
            validate_address("")

    def test_short_address_raises(self):
        """Too short address raises ValueError."""
        with pytest.raises(ValueError, match="Invalid address"):
            validate_address("0xabc123")

    def test_long_address_raises(self):
        """Too long address raises ValueError."""
        with pytest.raises(ValueError, match="Invalid address"):
            validate_address("0x" + "a" * 41)

    def test_missing_prefix_raises(self):
        """Address without 0x prefix raises ValueError."""
        with pytest.raises(ValueError, match="Invalid address"):
            validate_address("de0b295669a9fd93d5f28d9ec85e40f4cb697bae")

    def test_invalid_hex_raises(self):
        """Non-hex characters raise ValueError."""
        with pytest.raises(ValueError, match="Invalid address"):
            validate_address("0xGGGb295669a9fd93d5f28d9ec85e40f4cb697bae")

    def test_none_raises(self):
        """None raises ValueError."""
        with pytest.raises(ValueError, match="must be string"):
            validate_address(None)

    def test_number_raises(self):
        """Number raises ValueError."""
        with pytest.raises(ValueError, match="must be string"):
            validate_address(123)


class TestValidatePositive:
    """Tests for validate_positive function."""

    def test_positive_int_passes(self):
        """Positive integer passes."""
        assert validate_positive(100, "value") == 100

    def test_positive_float_passes(self):
        """Positive float passes."""
        assert validate_positive(100.5, "value") == 100.5

    def test_zero_raises(self):
        """Zero raises ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            validate_positive(0, "min_value")

    def test_negative_raises(self):
        """Negative value raises ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            validate_positive(-10, "amount")

    def test_error_includes_name(self):
        """Error message includes parameter name."""
        with pytest.raises(ValueError, match="min_balance"):
            validate_positive(-5, "min_balance")


class TestValidateChain:
    """Tests for validate_chain function."""

    def test_valid_chain_passes(self):
        """Valid chain name passes."""
        assert validate_chain("ethereum", ["ethereum", "bsc"]) == "ethereum"

    def test_uppercase_normalized(self):
        """Uppercase chain is normalized."""
        assert validate_chain("ETHEREUM", ["ethereum", "bsc"]) == "ethereum"

    def test_invalid_chain_raises(self):
        """Invalid chain raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported chain"):
            validate_chain("polygon", ["ethereum", "bsc"])

    def test_error_lists_available(self):
        """Error message lists available chains."""
        with pytest.raises(ValueError, match="ethereum, bsc"):
            validate_chain("invalid", ["ethereum", "bsc"])
