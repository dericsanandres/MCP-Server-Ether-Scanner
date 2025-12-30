"""Blockchain explorer API service for multi-chain support."""

import asyncio
import os
from typing import Any, Dict, List, Optional

import httpx

from .chains import get_chain_config


class BlockchainService:
    """Service for interacting with blockchain explorer APIs (Etherscan, BscScan, etc.)."""

    def __init__(self, chain: str = "ethereum", rate_limit: int = 5):
        """Initialize service for a specific chain.

        Args:
            chain: Chain name (ethereum, bsc, etc.)
            rate_limit: Max requests per second
        """
        self.chain_config = get_chain_config(chain)
        self.chain = chain

        # Get API key from environment
        self.api_key = os.getenv(self.chain_config.api_key_env)
        if not self.api_key:
            raise ValueError(
                f"{self.chain_config.api_key_env} environment variable is required "
                f"for {self.chain_config.name}"
            )

        self.rate_limit = rate_limit
        self._client = httpx.AsyncClient()
        self._last_request_time = 0.0

    @property
    def symbol(self) -> str:
        """Get the native token symbol for this chain."""
        return self.chain_config.symbol

    @property
    def name(self) -> str:
        """Get the chain name."""
        return self.chain_config.name

    async def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make rate-limited request to blockchain explorer API."""
        # Basic rate limiting
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self._last_request_time
        min_interval = 1.0 / self.rate_limit

        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)

        # V2 API requires chainid parameter (only for etherscan.io/v2)
        if "/v2/" in self.chain_config.api_url:
            params["chainid"] = self.chain_config.chain_id
        params["apikey"] = self.api_key

        try:
            response = await self._client.get(self.chain_config.api_url, params=params)
            response.raise_for_status()
            data = response.json()

            self._last_request_time = asyncio.get_event_loop().time()

            if data.get("status") == "0":
                error_msg = data.get("message", "Unknown error")
                # "No transactions found" is not an error
                if "No transactions found" not in error_msg:
                    raise Exception(f"{self.chain_config.name} API error: {error_msg}")
                return {"result": []}

            return data
        except httpx.HTTPError as e:
            raise Exception(f"HTTP error on {self.chain_config.name}: {e}")

    async def get_balance(self, address: str) -> str:
        """Get native token balance for an address."""
        params = {
            "module": "account",
            "action": "balance",
            "address": address,
            "tag": "latest",
        }
        data = await self._make_request(params)
        # Convert wei to native token
        wei_balance = int(data["result"])
        balance = wei_balance / 10**18
        return f"{balance:.6f}"

    async def get_transactions(
        self,
        address: str,
        start_block: int = 0,
        end_block: int = 99999999,
        page: int = 1,
        offset: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get transaction history for an address."""
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": start_block,
            "endblock": end_block,
            "page": page,
            "offset": offset,
            "sort": "desc",
        }
        data = await self._make_request(params)
        return data["result"]

    async def get_token_transfers(
        self,
        address: str,
        contract_address: Optional[str] = None,
        page: int = 1,
        offset: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get ERC20/BEP20 token transfer events."""
        params = {
            "module": "account",
            "action": "tokentx",
            "address": address,
            "page": page,
            "offset": offset,
            "sort": "desc",
        }

        if contract_address:
            params["contractaddress"] = contract_address

        data = await self._make_request(params)
        return data["result"]

    async def get_contract_abi(self, address: str) -> str:
        """Get contract ABI for a verified contract."""
        params = {
            "module": "contract",
            "action": "getabi",
            "address": address,
        }
        data = await self._make_request(params)
        return data["result"]

    async def get_gas_prices(self) -> Dict[str, str]:
        """Get current gas prices."""
        params = {
            "module": "gastracker",
            "action": "gasoracle",
        }
        data = await self._make_request(params)
        result = data["result"]
        return {
            "safe": result["SafeGasPrice"],
            "standard": result["ProposeGasPrice"],
            "fast": result["FastGasPrice"],
        }

    async def get_native_price(self) -> Dict[str, str]:
        """Get native token price in USD and BTC."""
        params = {
            "module": "stats",
            "action": self.chain_config.price_action,
        }
        data = await self._make_request(params)
        result = data["result"]
        return {
            "usd": result.get("ethusd") or result.get("bnbusd", "0"),
            "btc": result.get("ethbtc") or result.get("bnbbtc", "0"),
        }

    async def close(self):
        """Clean up the HTTP client."""
        await self._client.aclose()


# Backwards compatibility alias
EtherscanService = BlockchainService
