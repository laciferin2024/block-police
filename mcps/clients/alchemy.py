"""
Alchemy MCP Client

Integration with Alchemy MCP server for blockchain data access.
"""
import asyncio
import mcps
from mcps.client.stdio import stdio_client, StdioServerParameters
from contextlib import AsyncExitStack
from typing import Dict, Any, List, Optional, Set
import logging

# Import centralized configuration
from config import ALCHEMY_API_KEY

from ..base import MCPClient, MCPCapability, MCPClientConfig
from ..registry import register_mcp_client


@register_mcp_client("alchemy")
class AlchemyMCPClient(MCPClient):
    """
    Alchemy MCP Client for blockchain investigation.
    Uses Alchemy MCP server to interact with Ethereum blockchain.
    """

    def __init__(self, config: MCPClientConfig):
        super().__init__(config)

        # Set up capabilities for this client
        self._capabilities = {
            MCPCapability.ENS_RESOLUTION,
            MCPCapability.TOKEN_METADATA,
            MCPCapability.TOKEN_BALANCES,
            MCPCapability.TRANSACTION_DETAILS,
            MCPCapability.FUND_TRACING,
            MCPCapability.ACCOUNT_HOLDINGS
        }

        # Cache for ENS resolution
        self.resolved_ens_cache = {}

    async def connect(self) -> bool:
        """Connect to Alchemy MCP server via local npx execution"""
        try:
            logging.info(f"Connecting to Alchemy MCP server with API key: {self.config.api_key}")

            # Use npx to run Alchemy MCP server locally
            params = StdioServerParameters(
                command="npx",
                args=["-y", "@alchemy/mcp-server"],
                env={"ALCHEMY_API_KEY": self.config.api_key or ALCHEMY_API_KEY}
            )

            read_stream, write_stream = await self._exit_stack.enter_async_context(
                stdio_client(params)
            )

            self._session = await self._exit_stack.enter_async_context(
                mcps.ClientSession(read_stream, write_stream)
            )

            await self._session.initialize()

            # List available tools
            result = await self.list_tools()
            return len(result) > 0

        except Exception as e:
            logging.error(f"Failed to connect to Alchemy MCP server: {e}")
            return False

    async def call_tool(self, tool_name: str, params: Any) -> Dict[str, Any]:
        """Call a tool on the Alchemy MCP server"""
        if not self._session:
            raise RuntimeError("Not connected to Alchemy MCP server")

        result = await self._session.call_tool(tool_name, params)

        if hasattr(result, 'content'):
            return result.content
        return {"error": "No content returned"}

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the Alchemy MCP server"""
        if not self._session:
            raise RuntimeError("Not connected to Alchemy MCP server")

        result = await self._session.list_tools()
        self._tools = result.tools
        return self._tools

    async def resolve_ens_to_address(self, ens_name: str) -> str:
        """
        Resolve ENS name to address using multiple methods
        Returns the original name if resolution fails
        """
        # Check cache first
        if ens_name in self.resolved_ens_cache:
            return self.resolved_ens_cache[ens_name]

        # Only try to resolve .eth names
        if not ens_name.endswith(".eth"):
            return ens_name

        # Try direct eth_getBalance first - some providers handle ENS natively
        try:
            result = await self.call_tool(
                "eth_getBalance",
                {"address": ens_name, "tag": "latest"}
            )

            if result and not isinstance(result, dict):
                # Provider can handle ENS directly
                self.resolved_ens_cache[ens_name] = ens_name
                return ens_name
        except Exception:
            pass  # Fall through to other resolution methods

        # Methods to try for ENS resolution
        methods = [
            {"method": "ens_getAddress", "params": {"name": ens_name}},
            {"method": "eth_resolveENS", "params": {"ensName": ens_name}},
            {"method": "alchemy_resolveENS", "params": {"ens": ens_name}}
        ]

        for method_info in methods:
            method = method_info["method"]
            params = method_info["params"]

            try:
                result = await self.call_tool(method, params)

                if result and not isinstance(result, dict):
                    address = result
                    # Cache the result
                    self.resolved_ens_cache[ens_name] = address
                    return address
            except Exception:
                continue  # Try next method

        # If all resolution methods fail, return the original ENS name
        return ens_name

    async def trace_evm_funds(self, start_address: str, hop_limit: int = 100) -> Dict[str, Any]:
        """
        Traces the path of funds across EVM transactions, hop by hop.
        Uses Alchemy MCP server tools directly.
        """
        try:
            # Resolve ENS if needed
            address = await self.resolve_ens_to_address(start_address)

            # Check which tools are available for tracing
            trace_tools = [tool for tool in self._tools if 'trace' in tool.name.lower()]

            if not trace_tools:
                # If no specific trace tools, use getAssetTransfers
                result = await self.call_tool(
                    "alchemy_getAssetTransfers",
                    {
                        "fromAddress": address,
                        "category": ["external", "internal", "erc20", "erc721", "erc1155"],
                        "maxCount": "0x" + format(hop_limit, 'x')
                    }
                )

                # Process the result to create a trace path
                if result and isinstance(result, dict):
                    transfers = result.get('transfers', [])

                    if transfers and len(transfers) > 0:
                        # Find the last hop (simplified approach)
                        last_transfer = transfers[-1]
                        exit_hop_address = last_transfer.get('to', 'Unknown')

                        return {
                            "source_address": start_address,
                            "exit_hop_address": exit_hop_address,
                            "transfers": transfers,
                            "hops_traced": len(transfers)
                        }
            else:
                # Use available trace tools
                trace_tool = trace_tools[0]
                result = await self.call_tool(
                    trace_tool.name,
                    {"address": address, "limit": hop_limit}
                )

                if result and isinstance(result, dict):
                    return result

            return {"error": "Tracing not successful", "source_address": start_address}

        except Exception as e:
            return {"error": f"Error tracing funds: {str(e)}", "source_address": start_address}

    async def get_curated_holdings(self, address_or_ens: str) -> Dict[str, Any]:
        """
        Retrieves a multi-chain assessment of crypto holdings for an address or ENS.
        Uses Alchemy MCP server tools directly.
        """
        try:
            # Resolve ENS to address if needed
            address = await self.resolve_ens_to_address(address_or_ens)

            # Get ETH balance - Using params object instead of array
            balance_result = await self.call_tool(
                "eth_getBalance",
                {"address": address, "tag": "latest"}
            )

            # Get token balances
            token_balances_result = await self.call_tool(
                "alchemy_getTokenBalances",
                {"address": address}
            )

            # Get NFTs if the tool is available
            nft_tools = [tool for tool in self._tools if 'nft' in tool.name.lower()]
            nfts = None

            if nft_tools:
                nft_tool = nft_tools[0]
                nft_result = await self.call_tool(
                    nft_tool.name,
                    {"owner": address}
                )

                if nft_result and isinstance(nft_result, dict):
                    nfts = nft_result

            # Process ETH balance
            eth_balance = 0
            if balance_result and not isinstance(balance_result, dict):
                eth_balance_hex = balance_result
                eth_balance_wei = int(eth_balance_hex, 16) if isinstance(eth_balance_hex, str) else 0
                eth_balance = eth_balance_wei / 1e18

            # Process token balances
            tokens = []
            if token_balances_result and isinstance(token_balances_result, dict):
                tokens = token_balances_result.get('tokenBalances', [])

            # Prepare response
            holdings = {
                "address": address_or_ens,
                "ETH_Balance": f"{eth_balance:.6f} ETH",
                "tokens": tokens,
                "nfts": nfts,
                "risk_assessment": self._generate_risk_assessment(eth_balance, len(tokens))
            }

            return holdings

        except Exception as e:
            return {"error": f"Failed to fetch holdings for {address_or_ens}: {str(e)}"}

    def _generate_risk_assessment(self, eth_balance: float, token_count: int) -> str:
        """Generate a simplified risk assessment based on holdings"""
        if eth_balance > 100:
            return "High value account with significant ETH holdings."
        elif token_count > 10:
            return "Diverse portfolio with multiple token types."
        else:
            return "Standard account with typical holdings."