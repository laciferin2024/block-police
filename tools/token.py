"""
TheGraph Token API Integration

Provides tools for querying token data using TheGraph's Token API service.
"""
import os
import asyncio
import json
import mcp
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from contextlib import AsyncExitStack
from typing import Dict, Any, Optional, List
from .registry import register_tool
from config import GRAPH_MARKET_ACCESS_TOKEN, THEGRAPH_TOKEN_API_MCP
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if Token API access token is available
if not GRAPH_MARKET_ACCESS_TOKEN:
    print("Warning: GRAPH_MARKET_ACCESS_TOKEN not found in environment variables")


async def create_token_api_session() -> Optional[mcp.ClientSession]:
    """Create a session with TheGraph Token API MCP server"""
    if not GRAPH_MARKET_ACCESS_TOKEN:
        print("Cannot connect to Token API: Missing access token")
        return None

    try:
        # Create async context stack
        exit_stack = AsyncExitStack()

        # Set up Token API MCP server connection
        params = mcp.SseServerParameters(
            url=THEGRAPH_TOKEN_API_MCP,
            headers={"Authorization": f"Bearer {GRAPH_MARKET_ACCESS_TOKEN}"}
        )

        # Connect to the MCP server
        read_stream, write_stream = await exit_stack.enter_async_context(
            mcp.sse_client(params)
        )

        session = await exit_stack.enter_async_context(
            mcp.ClientSession(read_stream, write_stream)
        )

        await session.initialize()
        return session

    except Exception as e:
        print(f"Failed to connect to Token API MCP: {str(e)}")
        return None


@register_tool(
    name="token_getMetadata",
    description="Get metadata for a specified token, including name, symbol, decimals, etc."
)
async def get_token_metadata(address: str, chain: str = "ethereum") -> Dict[str, Any]:
    """
    Get metadata for a specified token contract address.

    Args:
        address: The token contract address
        chain: The blockchain network (default: ethereum)

    Returns:
        Dictionary containing token metadata information
    """
    session = await create_token_api_session()
    if not session:
        return {"error": "Failed to connect to Token API"}

    try:
        result = await session.call_tool(
            "getTokenMetadata",
            {"address": address, "chain": chain}
        )

        if hasattr(result, 'content'):
            return result.content
        else:
            return {"error": "No metadata returned from Token API"}

    except Exception as e:
        return {"error": f"Error getting token metadata: {str(e)}"}
    finally:
        if session:
            await session._exit_stack.aclose()


@register_tool(
    name="token_getHolderBalances",
    description="Get balances for holders of a specified token"
)
async def get_token_holders(address: str, limit: int = 10, chain: str = "ethereum") -> Dict[str, Any]:
    """
    Get holders and their balances for a specific token.

    Args:
        address: The token contract address
        limit: Maximum number of holders to return (default: 10)
        chain: The blockchain network (default: ethereum)

    Returns:
        Dictionary containing holder addresses and their balances
    """
    session = await create_token_api_session()
    if not session:
        return {"error": "Failed to connect to Token API"}

    try:
        result = await session.call_tool(
            "getTokenHolders",
            {"address": address, "limit": limit, "chain": chain}
        )

        if hasattr(result, 'content'):
            return result.content
        else:
            return {"error": "No holder data returned from Token API"}

    except Exception as e:
        return {"error": f"Error getting token holders: {str(e)}"}
    finally:
        if session:
            await session._exit_stack.aclose()


@register_tool(
    name="token_getTransfers",
    description="Get recent transfers for a specified token"
)
async def get_token_transfers(address: str, limit: int = 10, chain: str = "ethereum") -> Dict[str, Any]:
    """
    Get recent transfers for a specific token.

    Args:
        address: The token contract address
        limit: Maximum number of transfers to return (default: 10)
        chain: The blockchain network (default: ethereum)

    Returns:
        Dictionary containing recent transfers information
    """
    session = await create_token_api_session()
    if not session:
        return {"error": "Failed to connect to Token API"}

    try:
        result = await session.call_tool(
            "getTokenTransfers",
            {"address": address, "limit": limit, "chain": chain}
        )

        if hasattr(result, 'content'):
            return result.content
        else:
            return {"error": "No transfer data returned from Token API"}

    except Exception as e:
        return {"error": f"Error getting token transfers: {str(e)}"}
    finally:
        if session:
            await session._exit_stack.aclose()


@register_tool(
    name="token_getHolderTokens",
    description="Get tokens held by a specific wallet address"
)
async def get_holder_tokens(address: str, limit: int = 10, chain: str = "ethereum") -> Dict[str, Any]:
    """
    Get tokens held by a specific wallet address.

    Args:
        address: The wallet address
        limit: Maximum number of tokens to return (default: 10)
        chain: The blockchain network (default: ethereum)

    Returns:
        Dictionary containing tokens held by the specified address
    """
    session = await create_token_api_session()
    if not session:
        return {"error": "Failed to connect to Token API"}

    try:
        result = await session.call_tool(
            "getAddressTokens",
            {"address": address, "limit": limit, "chain": chain}
        )

        if hasattr(result, 'content'):
            return result.content
        else:
            return {"error": "No token data returned from Token API"}

    except Exception as e:
        return {"error": f"Error getting holder tokens: {str(e)}"}
    finally:
        if session:
            await session._exit_stack.aclose()


@register_tool(
    name="token_searchByName",
    description="Search for tokens by name or symbol"
)
async def search_tokens(query: str, limit: int = 10, chain: str = "ethereum") -> Dict[str, Any]:
    """
    Search for tokens by name or symbol.

    Args:
        query: The search query (token name or symbol)
        limit: Maximum number of results to return (default: 10)
        chain: The blockchain network (default: ethereum)

    Returns:
        Dictionary containing matching tokens
    """
    session = await create_token_api_session()
    if not session:
        return {"error": "Failed to connect to Token API"}

    try:
        result = await session.call_tool(
            "searchTokens",
            {"query": query, "limit": limit, "chain": chain}
        )

        if hasattr(result, 'content'):
            return result.content
        else:
            return {"error": "No search results returned from Token API"}

    except Exception as e:
        return {"error": f"Error searching tokens: {str(e)}"}
    finally:
        if session:
            await session._exit_stack.aclose()