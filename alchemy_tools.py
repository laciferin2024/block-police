"""
Alchemy API integration tools for blockchain investigation.
This module contains functions for interacting with the Alchemy API
to perform blockchain analysis and investigations.
"""

import os
import json
from typing import Dict, List, Any, Optional
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AlchemyTools:
    """Tools for interacting with Alchemy API for blockchain investigations"""

    def __init__(self):
        self.api_key = os.getenv("ALCHEMY_API_KEY", "")
        if not self.api_key:
            print("Warning: ALCHEMY_API_KEY not found in environment variables")

        self.base_url = "https://eth-mainnet.g.alchemy.com/v2/"

    async def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """Get transaction details by hash"""
        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "eth_getTransactionByHash",
            "params": [tx_hash]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{self.api_key}",
                json=payload
            )

            if response.status_code == 200:
                return response.json()["result"]
            else:
                return {"error": f"Failed to fetch transaction: {response.text}"}

    async def get_balance(self, address: str) -> Dict[str, Any]:
        """Get ETH balance for an address"""
        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "eth_getBalance",
            "params": [address, "latest"]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{self.api_key}",
                json=payload
            )

            if response.status_code == 200:
                result = response.json()["result"]
                # Convert hex to decimal
                balance_wei = int(result, 16)
                balance_eth = balance_wei / 1e18
                return {
                    "address": address,
                    "balance_wei": balance_wei,
                    "balance_eth": balance_eth,
                    "raw": result
                }
            else:
                return {"error": f"Failed to fetch balance: {response.text}"}

    async def get_token_balances(self, address: str) -> Dict[str, Any]:
        """Get token balances for an address"""
        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "alchemy_getTokenBalances",
            "params": [address]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{self.api_key}",
                json=payload
            )

            if response.status_code == 200:
                return response.json()["result"]
            else:
                return {"error": f"Failed to fetch token balances: {response.text}"}

    async def trace_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """Trace a transaction execution"""
        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "debug_traceTransaction",
            "params": [tx_hash]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{self.api_key}",
                json=payload
            )

            if response.status_code == 200:
                return response.json()["result"]
            else:
                return {"error": f"Failed to trace transaction: {response.text}"}

    async def trace_address_transactions(self, address: str, start_block: int, end_block: int = None) -> List[Dict[str, Any]]:
        """Get transactions for an address within a block range"""
        if end_block is None:
            # Get latest block if end_block not specified
            end_block = await self._get_latest_block_number()

        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "alchemy_getAssetTransfers",
            "params": [
                {
                    "fromBlock": hex(start_block),
                    "toBlock": hex(end_block),
                    "fromAddress": address,
                    "category": ["external", "internal", "erc20", "erc721", "erc1155"]
                }
            ]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{self.api_key}",
                json=payload
            )

            if response.status_code == 200:
                return response.json()["result"]["transfers"]
            else:
                return [{"error": f"Failed to trace address transactions: {response.text}"}]

    async def _get_latest_block_number(self) -> int:
        """Get latest block number"""
        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "eth_blockNumber",
            "params": []
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{self.api_key}",
                json=payload
            )

            if response.status_code == 200:
                # Convert hex to int
                return int(response.json()["result"], 16)
            else:
                return 0

    async def trace_funds_path(self, start_address: str, hop_limit: int = 100) -> Dict[str, Any]:
        """
        Trace the path of funds from a starting address,
        following transactions hop by hop up to the hop limit.

        This is a simplified implementation that would need to be expanded
        with graph algorithms and heuristics for real usage.
        """
        # Start with the latest block and look back 10000 blocks
        latest_block = await self._get_latest_block_number()
        look_back_blocks = 10000

        start_block = latest_block - look_back_blocks

        # Get outgoing transactions from the start address
        transfers = await self.trace_address_transactions(
            address=start_address,
            start_block=start_block,
            end_block=latest_block
        )

        if isinstance(transfers, list) and len(transfers) > 0 and "error" not in transfers[0]:
            # Find the largest value transfer (simplified heuristic)
            largest_transfer = None
            largest_value = 0

            for transfer in transfers:
                if "value" in transfer and float(transfer.get("value", 0)) > largest_value:
                    largest_value = float(transfer.get("value", 0))
                    largest_transfer = transfer

            if largest_transfer:
                # In a real implementation, we would recursively follow this path
                # up to hop_limit, but for this demo we just return the first hop
                return {
                    "source_address": start_address,
                    "destination_address": largest_transfer.get("to", "unknown"),
                    "value": largest_transfer.get("value", 0),
                    "asset": largest_transfer.get("asset", "ETH"),
                    "transaction_hash": largest_transfer.get("hash", "unknown"),
                    "block_num": largest_transfer.get("blockNum", "unknown"),
                    "path": [{
                        "from": start_address,
                        "to": largest_transfer.get("to", "unknown"),
                        "value": largest_transfer.get("value", 0),
                        "asset": largest_transfer.get("asset", "ETH"),
                    }],
                    "exit_hop_address": largest_transfer.get("to", "unknown")
                }

        # Fallback with simulated data for demo purposes
        return {
            "source_address": start_address,
            "exit_hop_address": "0xExitHopAddressSimulated",
            "path": [
                {"from": start_address, "to": "0xIntermediary1", "value": 10.5},
                {"from": "0xIntermediary1", "to": "0xIntermediary2", "value": 10.4},
                {"from": "0xIntermediary2", "to": "0xExitHopAddressSimulated", "value": 10.3}
            ],
            "hops_traversed": 3,
            "note": "This is simulated data for demonstration"
        }