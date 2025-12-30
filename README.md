# Multi-Chain Blockchain Scanner - MCP Server

MCP server for whale detection and blockchain analysis. Works with **Claude Code**, **GPT Codex**, and any MCP-compatible client.

## Supported Chains

| Chain | Symbol | Free Tier |
|-------|--------|-----------|
| Ethereum | ETH | Yes |
| BNB Smart Chain | BNB | Paid plan only |

Uses **Etherscan V2 API** - one API key for all chains.

## Quick Start

```bash
# 1. Setup
make setup
cp .env.example .env
# Edit .env with your API keys

# 2. Configure MCP client
make config-claude   # For Claude Desktop
make config-codex    # For GPT Codex

# 3. Restart your MCP client
```

## Available Tools

| Tool | Description |
|------|-------------|
| `check_balance` | Get native token balance |
| `get_transactions` | Transaction history |
| `get_token_transfers` | ERC20/BEP20 transfers |
| `analyze_whale` | Full whale analysis with metrics |
| `detect_whale_class` | Quick whale classification |
| `compare_whales` | Compare multiple addresses |
| `discover_whale_movements` | Track large movements |
| `discover_top_whales` | Find whales via network analysis |
| `track_exchange_whales` | Monitor exchange deposits/withdrawals |
| `get_gas_prices` | Current gas prices |
| `get_native_price` | ETH/BNB price |
| `list_supported_chains` | Show available chains |

All tools accept `chain` parameter: `ethereum` (default) or `bsc`.

## Examples

```
Check balance on Ethereum: 0xbe0eb53f46cd790cd13851d5eff43d12404d33e8

Analyze whale on BSC: 0xf977814e90da44bfa03b6295a0616a897441acec

Track whale movements above 1000 BNB on BSC
```

## Whale Classifications

| Class | Balance |
|-------|---------|
| MEGA WHALE | >10,000 tokens |
| LARGE WHALE | 1,000-10,000 |
| MEDIUM WHALE | 100-1,000 |
| SMALL WHALE | 10-100 |
| SHRIMP | <10 |

## Make Commands

```bash
make setup        # Create venv, install deps
make run          # Start MCP server
make test         # Verify installation
make lint         # Check code style
make format       # Auto-format
make check        # Verify config
make clean        # Remove venv
make config-claude # Show Claude config
make config-codex  # Show Codex config
```

## Configuration

```env
# .env
ETHERSCAN_API_KEY=your_key    # from etherscan.io/myapikey
RATE_LIMIT=5                  # requests/sec (optional)
```

Get a free API key: https://etherscan.io/myapikey

## Architecture

```
src/core/
├── server.py           # MCP tools
├── blockchain_service.py # Multi-chain API client
├── whale_detector.py   # Analysis engine
├── chains.py           # Chain registry
└── __init__.py
```

## Adding New Chains

Edit `src/core/chains.py`:

```python
CHAIN_REGISTRY["polygon"] = ChainConfig(
    name="Polygon",
    symbol="MATIC",
    api_url="https://api.polygonscan.com/api",
    api_key_env="POLYGONSCAN_API_KEY",
    explorer_url="https://polygonscan.com",
    chain_id=137,
)
```

## Requirements

- Python 3.10+
- Etherscan API key (free tier: Ethereum only)
- MCP-compatible client (Claude Desktop, GPT Codex, etc.)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Module not found | `make setup` |
| API key error | Check `.env` file |
| Rate limit | Lower `RATE_LIMIT` in `.env` |
| Unknown chain | `list_supported_chains()` |

## License

MIT
