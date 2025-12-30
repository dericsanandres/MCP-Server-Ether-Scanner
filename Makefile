# MCP Multi-Chain Blockchain Scanner
# Works with: Claude Code, GPT Codex, any MCP-compatible client
# Platforms: macOS, Linux, Windows (via Git Bash/WSL)

# Detect OS
ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
    PYTHON := python
    VENV_BIN := .venv/Scripts
    SEP := \\
else
    DETECTED_OS := $(shell uname -s)
    PYTHON := python3
    VENV_BIN := .venv/bin
    SEP := /
endif

VENV := .venv
PIP := $(VENV_BIN)$(SEP)pip
PY := $(VENV_BIN)$(SEP)python
SRC := src

.PHONY: help setup install run test lint format clean check config-claude config-codex

# Default
help:
	@echo "MCP Multi-Chain Blockchain Scanner"
	@echo "==================================="
	@echo ""
	@echo "Setup:"
	@echo "  make setup        - Create venv and install deps"
	@echo "  make config-claude - Generate Claude Desktop config"
	@echo "  make config-codex  - Generate GPT Codex config"
	@echo ""
	@echo "Run:"
	@echo "  make run          - Start MCP server"
	@echo "  make test         - Verify installation"
	@echo ""
	@echo "Dev:"
	@echo "  make lint         - Check code style (ruff)"
	@echo "  make format       - Auto-format code"
	@echo "  make clean        - Remove venv and cache"
	@echo ""
	@echo "Detected OS: $(DETECTED_OS)"

# Setup
setup: $(VENV) install
	@echo ""
	@echo "Setup complete. Next:"
	@echo "  1. Copy .env.example to .env"
	@echo "  2. Add API keys to .env"
	@echo "  3. Run: make config-claude OR make config-codex"
	@echo "  4. Restart your MCP client"

$(VENV):
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip

install: $(VENV)
	$(PIP) install -r requirements.txt

# Run
run:
	@test -f .env || (echo "ERROR: .env not found. Run: cp .env.example .env" && exit 1)
	cd $(SRC) && ../$(PY) -m core.server

# Test
test: $(VENV)
	@echo "Running pytest..."
	$(PIP) install -q pytest pytest-mock pytest-asyncio
	$(PY) -m pytest tests/ -v
	@echo "All tests passed!"

# Quick import check
check-imports: $(VENV)
	@echo "Testing imports..."
	cd $(SRC) && ../$(PY) -c "from core import BlockchainService, get_supported_chains; print('Chains:', get_supported_chains())"
	@echo "OK"

# Lint
lint: $(VENV)
	$(PIP) install -q ruff
	$(PY) -m ruff check $(SRC)/

format: $(VENV)
	$(PIP) install -q ruff
	$(PY) -m ruff format $(SRC)/
	$(PY) -m ruff check --fix $(SRC)/

# Clean
clean:
	rm -rf $(VENV) build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Check env
check:
	@echo "Config Check"
	@echo "============"
	@test -d $(VENV) && echo "[OK] venv" || echo "[!] venv missing - run: make setup"
	@test -f .env && echo "[OK] .env" || echo "[!] .env missing - run: cp .env.example .env"
	@grep -q "ETHERSCAN_API_KEY=.*[^=]" .env 2>/dev/null && echo "[OK] ETHERSCAN_API_KEY" || echo "[!] ETHERSCAN_API_KEY not set (get from etherscan.io/myapikey)"

# Generate Claude Desktop config snippet
config-claude:
	@echo ""
	@echo "Claude Desktop Configuration"
	@echo "============================"
	@echo "Add to: ~/Library/Application Support/Claude/claude_desktop_config.json (Mac)"
	@echo "    or: %APPDATA%\\Claude\\claude_desktop_config.json (Windows)"
	@echo ""
	@echo '{'
	@echo '  "mcpServers": {'
	@echo '    "blockchain-scanner": {'
	@echo '      "command": "$(shell cd $(VENV_BIN) && pwd)/python",'
	@echo '      "args": ["-m", "core.server"],'
	@echo '      "cwd": "$(shell pwd)/src",'
	@echo '      "env": {'
	@echo '        "ETHERSCAN_API_KEY": "YOUR_KEY",'
	@echo '        "BSCSCAN_API_KEY": "YOUR_KEY"'
	@echo '      }'
	@echo '    }'
	@echo '  }'
	@echo '}'

# Generate GPT Codex / OpenAI MCP config snippet
config-codex:
	@echo ""
	@echo "GPT Codex / OpenAI Configuration"
	@echo "================================="
	@echo "Add to your MCP client configuration:"
	@echo ""
	@echo '{'
	@echo '  "servers": {'
	@echo '    "blockchain-scanner": {'
	@echo '      "command": "$(shell cd $(VENV_BIN) && pwd)/python",'
	@echo '      "args": ["-m", "core.server"],'
	@echo '      "cwd": "$(shell pwd)/src",'
	@echo '      "env": {'
	@echo '        "ETHERSCAN_API_KEY": "YOUR_KEY",'
	@echo '        "BSCSCAN_API_KEY": "YOUR_KEY"'
	@echo '      }'
	@echo '    }'
	@echo '  }'
	@echo '}'
	@echo ""
	@echo "Note: Config format may vary by client. Core fields:"
	@echo "  - command: path to Python in venv"
	@echo "  - args: [\"-m\", \"core.server\"]"
	@echo "  - cwd: path to src/ directory"
