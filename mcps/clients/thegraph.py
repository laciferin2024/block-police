"""
TheGraph MCP Client

Integration with TheGraph MCP server for blockchain data access.
"""
import asyncio
import mcps
import mcp
from mcp.client.sse import sse_client
from contextlib import AsyncExitStack
from typing import Dict, Any, List, Optional, Set
import logging

# Import centralized configuration
from config import GRAPH_MARKET_ACCESS_TOKEN, THEGRAPH_TOKEN_API_MCP

from ..base import MCPClient, MCPCapability, MCPClientConfig
from ..registry import register_mcp_client


@register_mcp_client("thegraph")
class TheGraphMCPClient(MCPClient):
    """
    TheGraph MCP Client for blockchain data analysis.
    Uses TheGraph Token API and Subgraph API for data access.
    """

    def __init__(self, config: MCPClientConfig):
        super().__init__(config)

        # Set up capabilities for this client
        self._capabilities = {
            MCPCapability.TOKEN_METADATA,
            MCPCapability.TOKEN_BALANCES,
            MCPCapability.TOKEN_TRANSFERS,
            MCPCapability.ACCOUNT_HOLDINGS,
            MCPCapability.ENS_RESOLUTION
        }

    async def connect(self) -> bool:
        """Connect to TheGraph Token API MCP server via SSE"""
        try:
            # Get API key from config or environment
            api_key = self.config.api_key or GRAPH_MARKET_ACCESS_TOKEN

            if not api_key:
                logging.error("No TheGraph Market access token available")
                return False

            # Set up TheGraph Token API MCP server connection
            params = {
                "url": self.config.endpoint or THEGRAPH_TOKEN_API_MCP,
                "headers": {"Authorization": f"Bearer {api_key}"}
            }

            # Connect to the MCP server
            read_stream, write_stream = await self._exit_stack.enter_async_context(
                mcp.client.sse.sse_client(params)
            )

            self._session = await self._exit_stack.enter_async_context(
                mcps.ClientSession(read_stream, write_stream)
            )

            await self._session.initialize()

            # List available tools
            result = await self.list_tools()
            return len(result) > 0

        except Exception as e:
            logging.error(f"Failed to connect to TheGraph MCP server: {e}")
            return False

    async def call_tool(self, tool_name: str, params: Any) -> Dict[str, Any]:
        """Call a tool on the TheGraph MCP server"""
        if not self._session:
            raise RuntimeError("Not connected to TheGraph MCP server")

        result = await self._session.call_tool(tool_name, params)

        if hasattr(result, 'content'):
            return result.content
        return {"error": "No content returned"}

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the TheGraph MCP server"""
        if not self._session:
            raise RuntimeError("Not connected to TheGraph MCP server")

        result = await self._session.list_tools()
        self._tools = result.tools
        return self._tools

    async def get_token_metadata(self, address: str, chain: str = "ethereum") -> Dict[str, Any]:
        """
        Get metadata for a specified token contract address.

        Args:
            address: The token contract address
            chain: The blockchain network (default: ethereum)

        Returns:
            Dictionary containing token metadata information
        """
        try:
            result = await self.call_tool(
                "getTokenMetadata",
                {"address": address, "chain": chain}
            )

            return result if result else {"error": "No metadata returned"}
        except Exception as e:
            return {"error": f"Error getting token metadata: {str(e)}"}

    async def get_token_holders(self,
                               address: str,
                               limit: int = 10,
                               chain: str = "ethereum") -> Dict[str, Any]:
        """
        Get holders and their balances for a specific token.

        Args:
            address: The token contract address
            limit: Maximum number of holders to return (default: 10)
            chain: The blockchain network (default: ethereum)

        Returns:
            Dictionary containing holder addresses and their balances
        """
        try:
            result = await self.call_tool(
                "getTokenHolders",
                {"address": address, "limit": limit, "chain": chain}
            )

            return result if result else {"error": "No holder data returned"}
        except Exception as e:
            return {"error": f"Error getting token holders: {str(e)}"}

    async def get_token_transfers(self,
                                address: str,
                                limit: int = 10,
                                chain: str = "ethereum") -> Dict[str, Any]:
        """
        Get recent transfers for a specific token.

        Args:
            address: The token contract address
            limit: Maximum number of transfers to return (default: 10)
            chain: The blockchain network (default: ethereum)

        Returns:
            Dictionary containing recent transfers information
        """
        try:
            result = await self.call_tool(
                "getTokenTransfers",
                {"address": address, "limit": limit, "chain": chain}
            )

            return result if result else {"error": "No transfer data returned"}
        except Exception as e:
            return {"error": f"Error getting token transfers: {str(e)}"}

    async def get_holder_tokens(self,
                              address: str,
                              limit: int = 10,
                              chain: str = "ethereum") -> Dict[str, Any]:
        """
        Get tokens held by a specific wallet address.

        Args:
            address: The wallet address
            limit: Maximum number of tokens to return (default: 10)
            chain: The blockchain network (default: ethereum)

        Returns:
            Dictionary containing tokens held by the specified address
        """
        try:
            result = await self.call_tool(
                "getAddressTokens",
                {"address": address, "limit": limit, "chain": chain}
            )

            return result if result else {"error": "No token data returned"}
        except Exception as e:
            return {"error": f"Error getting holder tokens: {str(e)}"}

    async def search_tokens(self,
                          query: str,
                          limit: int = 10,
                          chain: str = "ethereum") -> Dict[str, Any]:
        """
        Search for tokens by name or symbol.

        Args:
            query: The search query (token name or symbol)
            limit: Maximum number of results to return (default: 10)
            chain: The blockchain network (default: ethereum)

        Returns:
            Dictionary containing matching tokens
        """
        try:
            result = await self.call_tool(
                "searchTokens",
                {"query": query, "limit": limit, "chain": chain}
            )

            return result if result else {"error": "No search results returned"}
        except Exception as e:
            return {"error": f"Error searching tokens: {str(e)}"}