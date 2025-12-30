"""MCP server implementation for multi-chain blockchain data."""

import os
from typing import Dict, Literal, Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .blockchain_service import BlockchainService
from .chains import get_supported_chains, get_chain_config
from .validators import validate_address, validate_positive
from .whale_detector import WhaleDetector, WhaleClass

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("Multi-Chain Blockchain Scanner")

# Supported chains type
ChainType = Literal["ethereum", "bsc"]

# Initialize services for each configured chain
_services: Dict[str, BlockchainService] = {}
_whale_detectors: Dict[str, WhaleDetector] = {}

rate_limit = int(os.getenv("RATE_LIMIT", "5"))


def _get_service(chain: str) -> BlockchainService:
    """Get or create blockchain service for a chain."""
    chain = chain.lower()
    if chain not in _services:
        try:
            _services[chain] = BlockchainService(chain, rate_limit)
            _whale_detectors[chain] = WhaleDetector(_services[chain], chain)
        except ValueError as e:
            raise ValueError(f"Cannot initialize {chain}: {e}")
    return _services[chain]


def _get_whale_detector(chain: str) -> WhaleDetector:
    """Get whale detector for a chain."""
    _get_service(chain)  # Ensure service is initialized
    return _whale_detectors[chain.lower()]


def _format_chain_header(chain: str) -> str:
    """Format chain name for output headers."""
    config = get_chain_config(chain)
    return f"[{config.name}]"


@mcp.tool()
async def check_balance(address: str, chain: str = "ethereum") -> str:
    """Get native token balance for an address.

    Args:
        address: Blockchain address to check balance for
        chain: Blockchain network (ethereum, bsc). Default: ethereum

    Returns:
        Native token balance as a formatted string
    """
    try:
        address = validate_address(address)
        service = _get_service(chain)
        balance = await service.get_balance(address)
        return f"{_format_chain_header(chain)} {service.symbol} balance for {address}: {balance} {service.symbol}"
    except Exception as e:
        return f"Error getting balance: {str(e)}"


@mcp.tool()
async def get_transactions(
    address: str,
    chain: str = "ethereum",
    start_block: int = 0,
    end_block: int = 99999999,
    page: int = 1,
    offset: int = 10,
) -> str:
    """Get transaction history for an address.

    Args:
        address: Address to get transactions for
        chain: Blockchain network (ethereum, bsc). Default: ethereum
        start_block: Starting block number (default: 0)
        end_block: Ending block number (default: 99999999)
        page: Page number (default: 1)
        offset: Number of transactions to return (default: 10)

    Returns:
        Formatted transaction history
    """
    try:
        address = validate_address(address)
        service = _get_service(chain)
        transactions = await service.get_transactions(
            address, start_block, end_block, page, offset
        )

        if not transactions:
            return f"{_format_chain_header(chain)} No transactions found for {address}"

        result = f"{_format_chain_header(chain)} Found {len(transactions)} transactions for {address}:\n\n"
        for tx in transactions[:5]:  # Show first 5
            result += f"Hash: {tx['hash']}\n"
            result += f"From: {tx['from']}\n"
            result += f"To: {tx['to']}\n"
            result += f"Value: {int(tx['value']) / 10**18:.6f} {service.symbol}\n"
            result += f"Gas Used: {tx['gasUsed']}\n"
            result += f"Block: {tx['blockNumber']}\n\n"

        return result
    except Exception as e:
        return f"Error getting transactions: {str(e)}"


@mcp.tool()
async def get_token_transfers(
    address: str,
    chain: str = "ethereum",
    contract_address: Optional[str] = None,
    page: int = 1,
    offset: int = 10,
) -> str:
    """Get ERC20/BEP20 token transfer events for an address.

    Args:
        address: Address to get token transfers for
        chain: Blockchain network (ethereum, bsc). Default: ethereum
        contract_address: Optional specific token contract address
        page: Page number (default: 1)
        offset: Number of transfers to return (default: 10)

    Returns:
        Formatted token transfer history
    """
    try:
        address = validate_address(address)
        if contract_address:
            contract_address = validate_address(contract_address)
        service = _get_service(chain)
        transfers = await service.get_token_transfers(
            address, contract_address, page, offset
        )

        if not transfers:
            return (
                f"{_format_chain_header(chain)} No token transfers found for {address}"
            )

        result = f"{_format_chain_header(chain)} Found {len(transfers)} token transfers for {address}:\n\n"
        for transfer in transfers[:5]:  # Show first 5
            result += f"Hash: {transfer['hash']}\n"
            result += f"Token: {transfer['tokenName']} ({transfer['tokenSymbol']})\n"
            result += f"From: {transfer['from']}\n"
            result += f"To: {transfer['to']}\n"
            decimals = int(transfer["tokenDecimal"])
            value = int(transfer["value"]) / (10**decimals)
            result += f"Value: {value:.6f} {transfer['tokenSymbol']}\n"
            result += f"Block: {transfer['blockNumber']}\n\n"

        return result
    except Exception as e:
        return f"Error getting token transfers: {str(e)}"


@mcp.tool()
async def get_contract_abi(address: str, chain: str = "ethereum") -> str:
    """Get ABI for a verified smart contract.

    Args:
        address: Contract address to get ABI for
        chain: Blockchain network (ethereum, bsc). Default: ethereum

    Returns:
        Contract ABI as JSON string
    """
    try:
        address = validate_address(address)
        service = _get_service(chain)
        abi = await service.get_contract_abi(address)
        return f"{_format_chain_header(chain)} Contract ABI for {address}:\n\n{abi}"
    except Exception as e:
        return f"Error getting contract ABI: {str(e)}"


@mcp.tool()
async def get_gas_prices(chain: str = "ethereum") -> str:
    """Get current gas prices on the network.

    Args:
        chain: Blockchain network (ethereum, bsc). Default: ethereum

    Returns:
        Current gas prices (safe, standard, fast) in Gwei
    """
    try:
        service = _get_service(chain)
        gas_prices = await service.get_gas_prices()
        result = f"{_format_chain_header(chain)} Current gas prices (in Gwei):\n"
        result += f"Safe: {gas_prices['safe']} Gwei\n"
        result += f"Standard: {gas_prices['standard']} Gwei\n"
        result += f"Fast: {gas_prices['fast']} Gwei"
        return result
    except Exception as e:
        return f"Error getting gas prices: {str(e)}"


@mcp.tool()
async def analyze_whale(address: str, chain: str = "ethereum") -> str:
    """Comprehensive whale analysis of an address.

    Analyzes an address to determine whale classification, activity patterns,
    and risk metrics based on balance, transaction history, and behavior.

    Args:
        address: Address to analyze for whale characteristics
        chain: Blockchain network (ethereum, bsc). Default: ethereum

    Returns:
        Detailed whale analysis including classification, metrics, and risk assessment
    """
    try:
        address = validate_address(address)
        detector = _get_whale_detector(chain)
        service = _get_service(chain)
        metrics = await detector.analyze_whale(address)

        # Format whale class
        whale_class_names = {
            WhaleClass.MEGA_WHALE: f"[MEGA WHALE] >10,000 {service.symbol}",
            WhaleClass.LARGE_WHALE: f"[LARGE WHALE] 1,000-10,000 {service.symbol}",
            WhaleClass.MEDIUM_WHALE: f"[MEDIUM WHALE] 100-1,000 {service.symbol}",
            WhaleClass.SMALL_WHALE: f"[SMALL WHALE] 10-100 {service.symbol}",
            WhaleClass.SHRIMP: f"[SHRIMP] <10 {service.symbol}",
        }

        result = f"{_format_chain_header(chain)} WHALE ANALYSIS: {address}\n"
        result += "=" * 50 + "\n\n"

        # Classification and balance
        result += f"Classification: {whale_class_names[metrics.whale_class]}\n"
        result += (
            f"{service.symbol} Balance: {metrics.eth_balance:.6f} {service.symbol}\n\n"
        )

        # Known whale check
        label = detector.get_whale_label(address)
        if label:
            result += f"Known Entity: {label}\n"

        exchange = detector.is_exchange_address(address)
        if exchange:
            result += f"Exchange: {exchange}\n"

        result += "\n"

        # Transaction metrics
        result += "ACTIVITY METRICS:\n"
        result += f"Total Transactions: {metrics.total_transactions:,}\n"
        result += f"Large Transactions (>50 {service.symbol}): {metrics.large_transactions:,}\n"
        result += f"Average Transaction: {metrics.avg_transaction_value:.6f} {service.symbol}\n"
        result += f"Largest Transaction: {metrics.max_transaction_value:.6f} {service.symbol}\n\n"

        # Scores and analysis
        result += "ANALYSIS SCORES:\n"
        result += f"Activity Score: {metrics.activity_score:.1f}/100 "
        if metrics.activity_score > 70:
            result += "(Very Active)\n"
        elif metrics.activity_score > 40:
            result += "(Active)\n"
        else:
            result += "(Inactive)\n"

        result += f"Risk Score: {metrics.risk_score:.1f}/100 "
        if metrics.risk_score > 70:
            result += "(High Risk)\n"
        elif metrics.risk_score > 40:
            result += "(Medium Risk)\n"
        else:
            result += "(Low Risk)\n"

        result += f"Token Diversity: {metrics.token_diversity} different tokens\n\n"

        # Timestamps
        if metrics.first_seen:
            result += f"First Activity: {metrics.first_seen}\n"
        if metrics.last_activity:
            result += f"Last Activity: {metrics.last_activity}\n"

        return result

    except Exception as e:
        return f"Error analyzing whale: {str(e)}"


@mcp.tool()
async def detect_whale_class(address: str, chain: str = "ethereum") -> str:
    """Quick whale classification based on native token balance.

    Provides a simple classification of an address as whale, dolphin, or shrimp
    based solely on their current balance.

    Args:
        address: Address to classify
        chain: Blockchain network (ethereum, bsc). Default: ethereum

    Returns:
        Whale classification with balance and emoji
    """
    try:
        address = validate_address(address)
        service = _get_service(chain)
        detector = _get_whale_detector(chain)

        balance_str = await service.get_balance(address)
        balance = float(balance_str)
        whale_class = detector.classify_whale(balance)

        class_info = {
            WhaleClass.MEGA_WHALE: ("MEGA WHALE", "Institutional-level holdings"),
            WhaleClass.LARGE_WHALE: ("LARGE WHALE", "Major market participant"),
            WhaleClass.MEDIUM_WHALE: ("MEDIUM WHALE", "Significant holder"),
            WhaleClass.SMALL_WHALE: ("SMALL WHALE", "Notable position"),
            WhaleClass.SHRIMP: ("SHRIMP", "Retail holder"),
        }

        class_name, description = class_info[whale_class]

        result = f"{_format_chain_header(chain)} WHALE CLASSIFICATION: {address}\n\n"
        result += f"Class: {class_name}\n"
        result += f"Balance: {balance:.6f} {service.symbol}\n"
        result += f"Description: {description}\n"

        # Add some context about their position
        if whale_class in [WhaleClass.MEGA_WHALE, WhaleClass.LARGE_WHALE]:
            result += f"\n[!] This address holds significant {service.symbol} - movements may impact market"
        elif whale_class == WhaleClass.MEDIUM_WHALE:
            result += "\n[i] Moderate holder - worth monitoring for large movements"

        return result

    except Exception as e:
        return f"Error detecting whale class: {str(e)}"


@mcp.tool()
async def compare_whales(addresses: str, chain: str = "ethereum") -> str:
    """Compare multiple addresses for whale analysis.

    Analyzes multiple addresses and ranks them by whale size,
    providing comparative metrics and insights.

    Args:
        addresses: Comma-separated list of addresses to compare
        chain: Blockchain network (ethereum, bsc). Default: ethereum

    Returns:
        Comparative analysis of all addresses ranked by whale size
    """
    try:
        service = _get_service(chain)
        detector = _get_whale_detector(chain)

        # Parse and validate addresses
        addr_list = [addr.strip() for addr in addresses.split(",") if addr.strip()]

        if len(addr_list) > 10:
            return "Error: Maximum 10 addresses allowed for comparison"

        if len(addr_list) < 2:
            return "Error: At least 2 addresses required for comparison"

        # Validate all addresses
        addr_list = [validate_address(addr) for addr in addr_list]

        # Analyze all whales
        whale_metrics = await detector.compare_whales(addr_list)

        if not whale_metrics:
            return "Error: Could not analyze any of the provided addresses"

        result = f"{_format_chain_header(chain)} WHALE COMPARISON ({len(whale_metrics)} addresses)\n"
        result += "=" * 60 + "\n\n"

        for i, metrics in enumerate(whale_metrics, 1):
            result += f"{i}. [{metrics.whale_class.value.upper()}] {metrics.address[:10]}...{metrics.address[-6:]}\n"
            result += f"   Balance: {metrics.eth_balance:.2f} {service.symbol} | "
            result += f"Class: {metrics.whale_class.value.replace('_', ' ').title()}\n"
            result += f"   Activity: {metrics.activity_score:.0f}/100 | "
            result += f"Risk: {metrics.risk_score:.0f}/100 | "
            result += f"Tokens: {metrics.token_diversity}\n"

            # Add known label if available
            label = detector.get_whale_label(metrics.address)
            if label:
                result += f"   Known as: {label}\n"

            result += "\n"

        # Summary stats
        total = sum(m.eth_balance for m in whale_metrics)
        avg_activity = sum(m.activity_score for m in whale_metrics) / len(whale_metrics)

        result += "SUMMARY:\n"
        result += f"Total {service.symbol}: {total:.2f} {service.symbol}\n"
        result += f"Average Activity Score: {avg_activity:.1f}/100\n"
        result += (
            f"Largest Whale: {whale_metrics[0].eth_balance:.2f} {service.symbol}\n"
        )

        return result

    except Exception as e:
        return f"Error comparing whales: {str(e)}"


@mcp.tool()
async def discover_whale_movements(
    chain: str = "ethereum", min_value: float = 100.0
) -> str:
    """Discover recent large whale movements and transactions.

    Scans recent transactions from known whale addresses and exchanges to find
    significant movements that may indicate whale activity.

    Args:
        chain: Blockchain network (ethereum, bsc). Default: ethereum
        min_value: Minimum value to consider as whale movement (default: 100)

    Returns:
        List of recent whale movements with sender/receiver classification
    """
    try:
        min_value = validate_positive(min_value, "min_value")
        service = _get_service(chain)
        detector = _get_whale_detector(chain)

        movements = await detector.discover_whale_movements(min_value)

        if not movements:
            return f"{_format_chain_header(chain)} No whale movements found above {min_value} {service.symbol}"

        result = f"{_format_chain_header(chain)} RECENT WHALE MOVEMENTS (>{min_value} {service.symbol})\n"
        result += "=" * 60 + "\n\n"

        for i, movement in enumerate(movements[:15], 1):  # Show top 15
            significance = detector.get_movement_significance(movement["value_eth"])

            result += f"{i}. {significance}\n"
            result += f"Amount: {movement['value_eth']:.2f} {service.symbol}\n"
            result += f"From: {movement['from_address'][:10]}...{movement['from_address'][-6:]}"

            # Add from labels/exchanges
            if movement["from_label"]:
                result += f" ({movement['from_label']})"
            elif movement["from_exchange"]:
                result += f" ({movement['from_exchange']} Exchange)"
            else:
                result += f" [{movement['from_whale_class'].replace('_', ' ').title()}]"

            result += (
                f"\nTo: {movement['to_address'][:10]}...{movement['to_address'][-6:]}"
            )

            # Add to labels/exchanges
            if movement["to_label"]:
                result += f" ({movement['to_label']})"
            elif movement["to_exchange"]:
                result += f" ({movement['to_exchange']} Exchange)"
            else:
                result += f" [{movement['to_whale_class'].replace('_', ' ').title()}]"

            result += f"\nTx Hash: {movement['hash']}\n"
            result += f"Block: {movement['block_number']}\n\n"

        result += "SUMMARY:\n"
        result += f"Total movements found: {len(movements)}\n"
        result += f"Total value: {sum(m['value_eth'] for m in movements):.2f} {service.symbol}\n"
        result += (
            f"Largest movement: {movements[0]['value_eth']:.2f} {service.symbol}\n"
        )

        return result

    except Exception as e:
        return f"Error discovering whale movements: {str(e)}"


@mcp.tool()
async def discover_top_whales(
    chain: str = "ethereum", min_balance: float = 1000.0
) -> str:
    """Discover top whale addresses by analyzing transaction networks.

    Finds whale addresses by analyzing participants in large transactions,
    starting from known whales and exchanges to discover their counterparties.

    Args:
        chain: Blockchain network (ethereum, bsc). Default: ethereum
        min_balance: Minimum balance to qualify as discovered whale (default: 1000)

    Returns:
        List of discovered whale addresses ranked by balance
    """
    try:
        min_balance = validate_positive(min_balance, "min_balance")
        service = _get_service(chain)
        detector = _get_whale_detector(chain)

        whales = await detector.discover_top_whales(min_balance)

        if not whales:
            return f"{_format_chain_header(chain)} No whales discovered with balance >{min_balance} {service.symbol}"

        result = f"{_format_chain_header(chain)} DISCOVERED TOP WHALES (>{min_balance} {service.symbol})\n"
        result += "=" * 60 + "\n\n"

        for i, whale in enumerate(whales, 1):
            result += f"{i}. [{whale['whale_class'].upper()}] {whale['address'][:10]}...{whale['address'][-6:]}\n"
            result += f"   Balance: {whale['eth_balance']:.2f} {service.symbol}\n"
            result += f"   Class: {whale['whale_class'].replace('_', ' ').title()}\n"

            if whale["label"]:
                result += f"   Known as: {whale['label']}\n"
            elif whale["exchange"]:
                result += f"   Exchange: {whale['exchange']}\n"

            result += f"   Discovery: {whale['discovery_method'].replace('_', ' ').title()}\n\n"

        # Summary statistics
        total = sum(w["eth_balance"] for w in whales)
        mega_whales = len([w for w in whales if w["whale_class"] == "mega_whale"])
        large_whales = len([w for w in whales if w["whale_class"] == "large_whale"])

        result += "DISCOVERY SUMMARY:\n"
        result += f"Whales discovered: {len(whales)}\n"
        result += f"Total {service.symbol} discovered: {total:.2f} {service.symbol}\n"
        result += f"Mega whales (>10K): {mega_whales}\n"
        result += f"Large whales (1K-10K): {large_whales}\n"
        result += f"Largest whale: {whales[0]['eth_balance']:.2f} {service.symbol}\n"

        return result

    except Exception as e:
        return f"Error discovering top whales: {str(e)}"


@mcp.tool()
async def track_exchange_whales(
    chain: str = "ethereum", min_amount: float = 500.0
) -> str:
    """Track whale deposits and withdrawals from major exchanges.

    Monitors large movements to/from known exchange addresses to identify
    whale trading activity and potential market impact movements.

    Args:
        chain: Blockchain network (ethereum, bsc). Default: ethereum
        min_amount: Minimum amount to track (default: 500)

    Returns:
        List of whale exchange movements with deposit/withdrawal classification
    """
    try:
        min_amount = validate_positive(min_amount, "min_amount")
        service = _get_service(chain)
        detector = _get_whale_detector(chain)

        movements = await detector.track_exchange_whales(min_amount)

        if not movements:
            return f"{_format_chain_header(chain)} No exchange whale movements found above {min_amount} {service.symbol}"

        result = f"{_format_chain_header(chain)} EXCHANGE WHALE TRACKING (>{min_amount} {service.symbol})\n"
        result += "=" * 60 + "\n\n"

        # Group by movement type
        deposits = [m for m in movements if m["movement_type"] == "deposit"]
        withdrawals = [m for m in movements if m["movement_type"] == "withdrawal"]

        # Show deposits
        if deposits:
            result += "WHALE DEPOSITS (Potential Selling Pressure):\n\n"
            for i, movement in enumerate(deposits[:8], 1):
                significance = detector.get_movement_significance(movement["value_eth"])

                result += f"{i}. {significance}\n"
                result += f"   Amount: {movement['value_eth']:.2f} {service.symbol} → {movement['exchange']}\n"
                result += f"   Whale: {movement['whale_address'][:10]}...{movement['whale_address'][-6:]}"

                if movement["whale_label"]:
                    result += f" ({movement['whale_label']})"
                else:
                    result += f" [{movement['whale_class'].replace('_', ' ').title()}]"

                result += f"\n   Tx: {movement['hash']}\n\n"

        # Show withdrawals
        if withdrawals:
            result += "WHALE WITHDRAWALS (Potential Accumulation):\n\n"
            for i, movement in enumerate(withdrawals[:8], 1):
                significance = detector.get_movement_significance(movement["value_eth"])

                result += f"{i}. {significance}\n"
                result += f"   Amount: {movement['value_eth']:.2f} {service.symbol} ← {movement['exchange']}\n"
                result += f"   Whale: {movement['whale_address'][:10]}...{movement['whale_address'][-6:]}"

                if movement["whale_label"]:
                    result += f" ({movement['whale_label']})"
                else:
                    result += f" [{movement['whale_class'].replace('_', ' ').title()}]"

                result += f"\n   Tx: {movement['hash']}\n\n"

        # Summary analysis
        total_deposits = sum(m["value_eth"] for m in deposits)
        total_withdrawals = sum(m["value_eth"] for m in withdrawals)
        net_flow = total_withdrawals - total_deposits

        result += "MARKET IMPACT ANALYSIS:\n"
        result += f"Total Deposits: {total_deposits:.2f} {service.symbol} (Selling pressure)\n"
        result += f"Total Withdrawals: {total_withdrawals:.2f} {service.symbol} (Accumulation)\n"
        result += f"Net Flow: {net_flow:.2f} {service.symbol} "

        if net_flow > 0:
            result += "(Net accumulation - Bullish signal)\n"
        elif net_flow < 0:
            result += "(Net selling - Bearish signal)\n"
        else:
            result += "(Balanced flow)\n"

        result += f"Active exchanges: {len(set(m['exchange'] for m in movements))}\n"

        return result

    except Exception as e:
        return f"Error tracking exchange whales: {str(e)}"


@mcp.tool()
async def list_supported_chains() -> str:
    """List all supported blockchain networks.

    Returns:
        List of supported chains with their configuration
    """
    chains = get_supported_chains()
    result = "SUPPORTED BLOCKCHAIN NETWORKS:\n"
    result += "=" * 40 + "\n\n"

    for chain_name in chains:
        config = get_chain_config(chain_name)
        # Check if API key is configured
        api_key = os.getenv(config.api_key_env)
        status = "[OK] Configured" if api_key else "[!] API key missing"

        result += f"- {config.name} ({chain_name})\n"
        result += f"  Symbol: {config.symbol}\n"
        result += f"  Chain ID: {config.chain_id}\n"
        result += f"  Explorer: {config.explorer_url}\n"
        result += f"  Status: {status}\n\n"

    result += "To use a chain, set the 'chain' parameter in any tool.\n"
    result += "Example: check_balance(address='0x...', chain='bsc')"

    return result
