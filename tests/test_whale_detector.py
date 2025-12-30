"""Tests for whale detector module."""

import pytest

from core.whale_detector import WhaleClass, WhaleDetector
from core.chains import get_known_whales, get_exchange_addresses


class TestWhaleClassification:
    """Tests for whale classification thresholds."""

    @pytest.fixture
    def mock_detector(self, mocker):
        """Create detector with mocked blockchain service."""
        mock_service = mocker.Mock()
        mock_service.symbol = "ETH"
        return WhaleDetector(mock_service, "ethereum")

    def test_shrimp_below_10(self, mock_detector):
        """Balance < 10 is SHRIMP."""
        assert mock_detector.classify_whale(0) == WhaleClass.SHRIMP
        assert mock_detector.classify_whale(5) == WhaleClass.SHRIMP
        assert mock_detector.classify_whale(9.99) == WhaleClass.SHRIMP

    def test_small_whale_10_to_100(self, mock_detector):
        """Balance 10-100 is SMALL_WHALE."""
        assert mock_detector.classify_whale(10) == WhaleClass.SMALL_WHALE
        assert mock_detector.classify_whale(50) == WhaleClass.SMALL_WHALE
        assert mock_detector.classify_whale(99.99) == WhaleClass.SMALL_WHALE

    def test_medium_whale_100_to_1000(self, mock_detector):
        """Balance 100-1000 is MEDIUM_WHALE."""
        assert mock_detector.classify_whale(100) == WhaleClass.MEDIUM_WHALE
        assert mock_detector.classify_whale(500) == WhaleClass.MEDIUM_WHALE
        assert mock_detector.classify_whale(999.99) == WhaleClass.MEDIUM_WHALE

    def test_large_whale_1000_to_10000(self, mock_detector):
        """Balance 1000-10000 is LARGE_WHALE."""
        assert mock_detector.classify_whale(1000) == WhaleClass.LARGE_WHALE
        assert mock_detector.classify_whale(5000) == WhaleClass.LARGE_WHALE
        assert mock_detector.classify_whale(9999.99) == WhaleClass.LARGE_WHALE

    def test_mega_whale_above_10000(self, mock_detector):
        """Balance >= 10000 is MEGA_WHALE."""
        assert mock_detector.classify_whale(10000) == WhaleClass.MEGA_WHALE
        assert mock_detector.classify_whale(50000) == WhaleClass.MEGA_WHALE
        assert mock_detector.classify_whale(1000000) == WhaleClass.MEGA_WHALE


class TestKnownWhales:
    """Tests for known whale address lookup."""

    def test_ethereum_whales_exist(self):
        """Ethereum has known whale addresses."""
        whales = get_known_whales("ethereum")
        assert len(whales) > 0

    def test_bsc_whales_exist(self):
        """BSC has known whale addresses."""
        whales = get_known_whales("bsc")
        assert len(whales) > 0

    def test_ethereum_foundation_labeled(self):
        """Ethereum Foundation address is labeled."""
        whales = get_known_whales("ethereum")
        eth_foundation = "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae"
        assert eth_foundation in whales
        assert "Ethereum Foundation" in whales[eth_foundation]

    def test_unknown_chain_returns_empty(self):
        """Unknown chain returns empty dict."""
        whales = get_known_whales("unknown_chain")
        assert whales == {}


class TestExchangeAddresses:
    """Tests for exchange address lookup."""

    def test_ethereum_exchanges_exist(self):
        """Ethereum has known exchange addresses."""
        exchanges = get_exchange_addresses("ethereum")
        assert len(exchanges) > 0

    def test_bsc_exchanges_exist(self):
        """BSC has known exchange addresses."""
        exchanges = get_exchange_addresses("bsc")
        assert len(exchanges) > 0

    def test_binance_labeled_on_bsc(self):
        """Binance hot wallet is labeled on BSC."""
        exchanges = get_exchange_addresses("bsc")
        binance_hot = "0xf977814e90da44bfa03b6295a0616a897441acec"
        assert binance_hot in exchanges
        assert "Binance" in exchanges[binance_hot]

    def test_unknown_chain_returns_empty(self):
        """Unknown chain returns empty dict."""
        exchanges = get_exchange_addresses("unknown_chain")
        assert exchanges == {}


class TestMovementSignificance:
    """Tests for movement significance classification."""

    @pytest.fixture
    def mock_detector(self, mocker):
        """Create detector with mocked blockchain service."""
        mock_service = mocker.Mock()
        mock_service.symbol = "ETH"
        return WhaleDetector(mock_service, "ethereum")

    def test_mega_movement(self, mock_detector):
        """Value >= 10000 is MEGA MOVEMENT."""
        assert "MEGA" in mock_detector.get_movement_significance(10000)
        assert "MEGA" in mock_detector.get_movement_significance(50000)

    def test_critical_movement(self, mock_detector):
        """Value 5000-10000 is CRITICAL."""
        assert "CRITICAL" in mock_detector.get_movement_significance(5000)
        assert "CRITICAL" in mock_detector.get_movement_significance(9999)

    def test_major_movement(self, mock_detector):
        """Value 1000-5000 is MAJOR."""
        assert "MAJOR" in mock_detector.get_movement_significance(1000)
        assert "MAJOR" in mock_detector.get_movement_significance(4999)

    def test_significant_movement(self, mock_detector):
        """Value 500-1000 is SIGNIFICANT."""
        assert "SIGNIFICANT" in mock_detector.get_movement_significance(500)
        assert "SIGNIFICANT" in mock_detector.get_movement_significance(999)

    def test_notable_movement(self, mock_detector):
        """Value < 500 is NOTABLE."""
        assert "NOTABLE" in mock_detector.get_movement_significance(100)
        assert "NOTABLE" in mock_detector.get_movement_significance(499)
