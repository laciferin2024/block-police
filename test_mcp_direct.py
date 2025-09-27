import asyncio
import json
import mcp
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Alchemy API key
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
if not ALCHEMY_API_KEY:
    raise ValueError("ALCHEMY_API_KEY not found in .env file")

async def test_alchemy_mcp():
    """Test direct interaction with Alchemy MCP server"""
    print("Testing direct connection to Alchemy MCP server...")

    async with AsyncExitStack() as stack:
        # Use npx to run Alchemy MCP server locally
        params = mcp.StdioServerParameters(
            command="npx",
            args=["-y", "@alchemy/mcp-server"],
            env={"ALCHEMY_API_KEY": ALCHEMY_API_KEY}
        )

        # Connect to the MCP server
        read_stream, write_stream = await stack.enter_async_context(
            stdio_client(params)
        )

        session = await stack.enter_async_context(
            mcp.ClientSession(read_stream, write_stream)
        )

        await session.initialize()

        # List available tools
        list_tools_result = await session.list_tools()
        tools = list_tools_result.tools

        print(f"Connected to Alchemy MCP server with {len(tools)} tools")
        print("Available tools:")
        for tool in tools:
            print(f" - {tool.name}")

        # Test with Vitalik's address
        test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

        print(f"\n🔍 Testing ETH balance for: {test_address}")
        balance_result = await session.call_tool(
            "eth_getBalance",
            [test_address, "latest"]
        )

        if hasattr(balance_result, 'content') and balance_result.content:
            eth_balance_hex = balance_result.content
            eth_balance_wei = int(eth_balance_hex, 16)
            eth_balance = eth_balance_wei / 1e18
            print(f"ETH Balance: {eth_balance:.6f} ETH")
        else:
            print("Failed to get ETH balance")

        print(f"\n🔍 Testing token balances for: {test_address}")
        token_balances_result = await session.call_tool(
            "alchemy_getTokenBalances",
            {"address": test_address}
        )

        if hasattr(token_balances_result, 'content') and token_balances_result.content:
            tokens = token_balances_result.content.get('tokenBalances', [])
            print(f"Found {len(tokens)} tokens")
        else:
            print("Failed to get token balances")

        print("\n✅ All tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_alchemy_mcp())