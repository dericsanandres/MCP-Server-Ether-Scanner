"""Whale detection and analysis service for multi-chain support."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

import httpx

from .blockchain_service import BlockchainService

from .chains import get_known_whales, get_exchange_addresses

logger = logging.getLogger(__name__)


class WhaleClass(Enum):
    """Whale classification levels."""

    SHRIMP = "shrimp"  # < 10 tokens
    SMALL_WHALE = "small_whale"  # 10-100 tokens
    MEDIUM_WHALE = "medium_whale"  # 100-1,000 tokens
    LARGE_WHALE = "large_whale"  # 1,000-10,000 tokens
    MEGA_WHALE = "mega_whale"  # > 10,000 tokens


@dataclass
class WhaleMetrics:
    """Metrics for whale analysis."""

    address: str
    eth_balance: float  # Native token balance (ETH, BNB, etc.)
    whale_class: WhaleClass
    total_transactions: int
    large_transactions: int  # > 50 tokens
    avg_transaction_value: float
    max_transaction_value: float
    first_seen: Optional[str]
    last_activity: Optional[str]
    activity_score: float  # 0-100
    risk_score: float  # 0-100
    token_diversity: int  # Number of different tokens held
    chain: str = "ethereum"  # Chain this analysis is for


@dataclass
class WhaleMovement:
    """Large transaction movement data."""

    tx_hash: str
    from_addr: str
    to_addr: str
    value_eth: float
    timestamp: str
    block_number: str
    whale_class_from: WhaleClass
    whale_class_to: WhaleClass
    movement_type: str  # "accumulation", "distribution", "exchange_deposit", etc.
    chain: str = "ethereum"


class WhaleDetector:
    """Advanced whale detection and analysis service with multi-chain support."""

    def __init__(self, blockchain_service: BlockchainService, chain: str = "ethereum"):
        """Initialize whale detector for a specific chain.

        Args:
            blockchain_service: Blockchain service instance
            chain: Chain name (ethereum, bsc, etc.)
        """
        self.blockchain = blockchain_service
        self.chain = chain.lower()

        # Load chain-specific addresses
        self.known_whales = get_known_whales(self.chain)
        self.exchange_addresses = get_exchange_addresses(self.chain)

    def classify_whale(self, balance: float) -> WhaleClass:
        """Classify address based on native token balance."""
        if balance >= 10000:
            return WhaleClass.MEGA_WHALE
        elif balance >= 1000:
            return WhaleClass.LARGE_WHALE
        elif balance >= 100:
            return WhaleClass.MEDIUM_WHALE
        elif balance >= 10:
            return WhaleClass.SMALL_WHALE
        else:
            return WhaleClass.SHRIMP

    async def analyze_whale(self, address: str) -> WhaleMetrics:
        """Comprehensive whale analysis of an address."""
        try:
            # Get basic balance
            balance_str = await self.blockchain.get_balance(address)
            balance = float(balance_str)
            whale_class = self.classify_whale(balance)

            # Get transaction history for analysis
            transactions = await self.blockchain.get_transactions(
                address, page=1, offset=100
            )

            if not transactions:
                return WhaleMetrics(
                    address=address,
                    eth_balance=balance,
                    whale_class=whale_class,
                    total_transactions=0,
                    large_transactions=0,
                    avg_transaction_value=0.0,
                    max_transaction_value=0.0,
                    first_seen=None,
                    last_activity=None,
                    activity_score=0.0,
                    risk_score=0.0,
                    token_diversity=0,
                    chain=self.chain,
                )

            # Analyze transactions
            total_transactions = len(transactions)
            transaction_values = []
            large_transactions = 0

            for tx in transactions:
                value = int(tx["value"]) / 10**18
                transaction_values.append(value)
                if value > 50:  # Large transaction threshold
                    large_transactions += 1

            avg_transaction_value = (
                sum(transaction_values) / len(transaction_values)
                if transaction_values
                else 0
            )
            max_transaction_value = max(transaction_values) if transaction_values else 0

            # Time analysis
            first_seen = transactions[-1]["timeStamp"] if transactions else None
            last_activity = transactions[0]["timeStamp"] if transactions else None

            # Calculate activity score (based on recent activity)
            activity_score = self._calculate_activity_score(transactions)

            # Calculate risk score (based on various factors)
            risk_score = self._calculate_risk_score(address, transactions, balance)

            # Get token diversity
            token_transfers = await self.blockchain.get_token_transfers(
                address, page=1, offset=50
            )
            unique_tokens = set()
            for transfer in token_transfers:
                unique_tokens.add(transfer.get("contractAddress", ""))
            token_diversity = len(unique_tokens)

            return WhaleMetrics(
                address=address,
                eth_balance=balance,
                whale_class=whale_class,
                total_transactions=total_transactions,
                large_transactions=large_transactions,
                avg_transaction_value=avg_transaction_value,
                max_transaction_value=max_transaction_value,
                first_seen=first_seen,
                last_activity=last_activity,
                activity_score=activity_score,
                risk_score=risk_score,
                token_diversity=token_diversity,
                chain=self.chain,
            )

        except Exception as e:
            raise Exception(f"Error analyzing whale on {self.chain}: {str(e)}")

    def _calculate_activity_score(self, transactions: List[Dict]) -> float:
        """Calculate activity score based on recent transactions."""
        if not transactions:
            return 0.0

        now = datetime.now()
        recent_count = 0

        for tx in transactions[:20]:  # Check last 20 transactions
            tx_time = datetime.fromtimestamp(int(tx["timeStamp"]))
            if (now - tx_time).days <= 30:  # Last 30 days
                recent_count += 1

        return min(100.0, (recent_count / 20) * 100)

    def _calculate_risk_score(
        self, address: str, transactions: List[Dict], balance: float
    ) -> float:
        """Calculate risk score based on various factors."""
        risk_factors = []

        # High balance risk
        if balance > 1000:
            risk_factors.append(30)

        # Known whale/exchange bonus (lower risk)
        if address.lower() in [addr.lower() for addr in self.known_whales.keys()]:
            risk_factors.append(-20)

        # Transaction pattern analysis
        if transactions:
            large_tx_ratio = sum(
                1 for tx in transactions if int(tx["value"]) / 10**18 > 100
            ) / len(transactions)
            if large_tx_ratio > 0.5:
                risk_factors.append(25)

        # New address risk
        if transactions:
            first_tx_time = datetime.fromtimestamp(int(transactions[-1]["timeStamp"]))
            if (datetime.now() - first_tx_time).days < 30:
                risk_factors.append(40)

        total_risk = sum(risk_factors)
        return max(0.0, min(100.0, total_risk))

    def get_whale_label(self, address: str) -> Optional[str]:
        """Get label for known whale addresses."""
        return self.known_whales.get(address.lower())

    def is_exchange_address(self, address: str) -> Optional[str]:
        """Check if address is a known exchange."""
        return self.exchange_addresses.get(address.lower())

    async def compare_whales(self, addresses: List[str]) -> List[WhaleMetrics]:
        """Compare multiple whale addresses."""
        whale_metrics = []

        for address in addresses:
            try:
                metrics = await self.analyze_whale(address)
                whale_metrics.append(metrics)
                # Rate limiting
                await asyncio.sleep(0.2)
            except (httpx.HTTPError, ValueError, KeyError) as e:
                logger.warning(f"Error analyzing {address}: {e}")
                continue

        # Sort by balance descending
        whale_metrics.sort(key=lambda x: x.eth_balance, reverse=True)
        return whale_metrics

    async def discover_whale_movements(
        self, min_value: float = 100.0, hours_back: int = 24
    ) -> List[Dict]:
        """Discover recent whale movements by analyzing large transactions."""
        whale_movements = []

        # Known addresses to monitor
        monitor_addresses = list(self.known_whales.keys()) + list(
            self.exchange_addresses.keys()
        )

        for address in monitor_addresses[:10]:  # Limit to avoid rate limiting
            try:
                transactions = await self.blockchain.get_transactions(
                    address, page=1, offset=20
                )

                for tx in transactions:
                    value = int(tx["value"]) / 10**18

                    if value >= min_value:
                        # Analyze both sender and receiver
                        from_whale_class = await self._get_whale_class_cached(
                            tx["from"]
                        )
                        to_whale_class = await self._get_whale_class_cached(tx["to"])

                        movement = {
                            "hash": tx["hash"],
                            "from_address": tx["from"],
                            "to_address": tx["to"],
                            "value_eth": value,
                            "timestamp": tx["timeStamp"],
                            "block_number": tx["blockNumber"],
                            "from_whale_class": (
                                from_whale_class.value
                                if from_whale_class
                                else "unknown"
                            ),
                            "to_whale_class": (
                                to_whale_class.value if to_whale_class else "unknown"
                            ),
                            "from_label": self.get_whale_label(tx["from"]),
                            "to_label": self.get_whale_label(tx["to"]),
                            "from_exchange": self.is_exchange_address(tx["from"]),
                            "to_exchange": self.is_exchange_address(tx["to"]),
                            "chain": self.chain,
                        }

                        whale_movements.append(movement)

                # Rate limiting
                await asyncio.sleep(0.3)

            except (httpx.HTTPError, ValueError, KeyError) as e:
                logger.debug(f"Skipping address in whale movements: {e}")
                continue

        # Sort by value descending
        whale_movements.sort(key=lambda x: x["value_eth"], reverse=True)
        return whale_movements[:50]  # Return top 50 movements

    async def _get_whale_class_cached(self, address: str) -> Optional[WhaleClass]:
        """Get whale class with basic caching to avoid repeated API calls."""
        try:
            balance_str = await self.blockchain.get_balance(address)
            balance = float(balance_str)
            return self.classify_whale(balance)
        except (httpx.HTTPError, ValueError) as e:
            logger.debug(f"Could not get whale class for {address}: {e}")
            return None

    async def discover_top_whales(self, min_balance: float = 1000.0) -> List[Dict]:
        """Discover top whales by analyzing high-value transaction participants."""
        discovered_whales = {}

        # Start with known addresses and analyze their transaction partners
        seed_addresses = list(self.known_whales.keys())[:5]

        for seed_address in seed_addresses:
            try:
                transactions = await self.blockchain.get_transactions(
                    seed_address, page=1, offset=50
                )

                # Collect unique addresses from large transactions
                for tx in transactions:
                    value = int(tx["value"]) / 10**18

                    if value >= 50:  # Focus on significant transactions
                        for addr in [tx["from"], tx["to"]]:
                            if addr.lower() not in discovered_whales:
                                discovered_whales[addr.lower()] = addr

                await asyncio.sleep(0.3)

            except (httpx.HTTPError, ValueError, KeyError) as e:
                logger.debug(f"Skipping seed address {seed_address}: {e}")
                continue

        # Analyze discovered addresses
        whale_list = []
        for address in list(discovered_whales.values())[:30]:  # Limit analysis
            try:
                balance_str = await self.blockchain.get_balance(address)
                balance = float(balance_str)

                if balance >= min_balance:
                    whale_class = self.classify_whale(balance)

                    whale_info = {
                        "address": address,
                        "eth_balance": balance,
                        "whale_class": whale_class.value,
                        "label": self.get_whale_label(address),
                        "exchange": self.is_exchange_address(address),
                        "discovery_method": "transaction_analysis",
                        "chain": self.chain,
                    }

                    whale_list.append(whale_info)

                await asyncio.sleep(0.2)

            except (httpx.HTTPError, ValueError, KeyError) as e:
                logger.debug(f"Skipping discovered address {address}: {e}")
                continue

        # Sort by balance descending
        whale_list.sort(key=lambda x: x["eth_balance"], reverse=True)
        return whale_list[:20]  # Return top 20 discovered whales

    async def track_exchange_whales(self, min_amount: float = 500.0) -> List[Dict]:
        """Track whale movements to/from exchanges."""
        exchange_movements = []

        # Monitor known exchange addresses
        exchange_addresses = list(self.exchange_addresses.keys())

        for exchange_addr in exchange_addresses[:5]:  # Limit to avoid rate limits
            try:
                exchange_name = self.exchange_addresses[exchange_addr]
                transactions = await self.blockchain.get_transactions(
                    exchange_addr, page=1, offset=30
                )

                for tx in transactions:
                    value = int(tx["value"]) / 10**18

                    if value >= min_amount:
                        # Determine if it's deposit or withdrawal
                        if tx["to"].lower() == exchange_addr.lower():
                            movement_type = "deposit"
                            whale_address = tx["from"]
                        else:
                            movement_type = "withdrawal"
                            whale_address = tx["to"]

                        # Get whale classification
                        whale_class = await self._get_whale_class_cached(whale_address)

                        movement = {
                            "hash": tx["hash"],
                            "exchange": exchange_name,
                            "exchange_address": exchange_addr,
                            "whale_address": whale_address,
                            "movement_type": movement_type,
                            "value_eth": value,
                            "whale_class": whale_class.value
                            if whale_class
                            else "unknown",
                            "whale_label": self.get_whale_label(whale_address),
                            "timestamp": tx["timeStamp"],
                            "block_number": tx["blockNumber"],
                            "chain": self.chain,
                        }

                        exchange_movements.append(movement)

                await asyncio.sleep(0.3)

            except (httpx.HTTPError, ValueError, KeyError) as e:
                logger.debug(f"Skipping exchange {exchange_addr}: {e}")
                continue

        # Sort by value descending
        exchange_movements.sort(key=lambda x: x["value_eth"], reverse=True)
        return exchange_movements[:30]  # Return top 30 movements

    def get_movement_significance(self, value: float) -> str:
        """Get significance level of a movement."""
        if value >= 10000:
            return "[!!!] MEGA MOVEMENT"
        elif value >= 5000:
            return "[!!] CRITICAL"
        elif value >= 1000:
            return "[!] MAJOR"
        elif value >= 500:
            return "[*] SIGNIFICANT"
        else:
            return "[-] NOTABLE"
