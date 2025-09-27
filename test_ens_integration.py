#!/usr/bin/env python
"""
ENS Integration Test Script

This script tests the ENS resolution tools to ensure they're properly integrated and working.
Includes tests for both custom ENS tools and Alchemy MCP integration.
"""
import asyncio
import json
import mcp
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
import os
from dotenv import load_dotenv
from tools.ens import resolve_ens_name, get_domain_details, get_domain_events

# Load environment variables
load_dotenv()

# Test domain
TEST_DOMAIN = "vitalik.eth"

# Get Alchemy API key
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
if not ALCHEMY_API_KEY:
    raise ValueError("ALCHEMY_API_KEY not found in .env file")

async def test_custom_ens_resolution():
    """Test ENS resolution using our custom tools"""
    print("\n=== Testing Custom ENS Resolution Tools ===\n")

    # Check if TheGraph API key is configured
    api_key = os.getenv("THEGRAPH_API_KEY")
    if not api_key:
        print("❌ THEGRAPH_API_KEY not found in environment variables")
        print("Please add your TheGraph API key to the .env file")
        return False

    try:
        # Test ENS name resolution
        print(f"🔍 Testing ENS resolution for: {TEST_DOMAIN}")
        address = await resolve_ens_name(TEST_DOMAIN)
        if address and not address.startswith("Error:") and not address.startswith("No data"):
            print(f"✅ Success: {TEST_DOMAIN} → {address}")

            # Test domain details
            print(f"\n🔍 Testing domain details for: {TEST_DOMAIN}")
            details = await get_domain_details(TEST_DOMAIN)
            if details and "error" not in details:
                print(f"✅ Successfully retrieved domain details")
                print(f"  Owner: {details.get('owner', 'Unknown')}")
                print(f"  Created: {details.get('created', 'Unknown')}")
                print(f"  Expiry: {details.get('expiry', 'Unknown')}")
            else:
                error = details.get('error', 'Unknown error') if details else "No details found"
                print(f"❌ Failed to get domain details: {error}")

            # Test domain events
            print(f"\n🔍 Testing domain events for: {TEST_DOMAIN}")
            events = await get_domain_events(TEST_DOMAIN)
            if events and isinstance(events, list) and (len(events) == 0 or "error" not in events[0]):
                print(f"✅ Successfully retrieved {len(events)} domain events")
                if len(events) > 0:
                    print(f"  Latest event: {events[0].get('type', 'Unknown')}")
            else:
                error = events[0].get('error', 'Unknown error') if events and isinstance(events, list) and len(events) > 0 else "No events found"
                print(f"❌ Failed to get domain events: {error}")

            return True
        else:
            print(f"❌ Failed to resolve ENS name: {address}")
            return False
    except Exception as e:
        print(f"❌ Custom ENS tools test failed: {str(e)}")
        return False

async def test_alchemy_ens_integration():
    """Test ENS resolution using Alchemy MCP server"""
    print("\n=== Testing ENS Integration with Alchemy MCP Server ===\n")

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

        # List available tools to find ENS resolution tools
        list_tools_result = await session.list_tools()
        tools = list_tools_result.tools

        print(f"Connected to Alchemy MCP server with {len(tools)} tools")

        # Find ENS-related tools and other useful tools
        ens_tools = [tool for tool in tools if 'ens' in tool.name.lower()]
        eth_tools = [tool for tool in tools if 'eth' in tool.name.lower()]
        alchemy_tools = [tool for tool in tools if 'alchemy' in tool.name.lower()]

        print("Available ENS tools:")
        for tool in ens_tools:
            print(f" - {tool.name}")

        print("\nAvailable ETH tools:")
        for tool in eth_tools[:5]:  # Show just the first 5 to avoid excessive output
            print(f" - {tool.name}")

        print("\nAvailable Alchemy tools:")
        for tool in alchemy_tools[:5]:  # Show just the first 5
            print(f" - {tool.name}")

        # Test with vitalik.eth
        test_ens = TEST_DOMAIN
        print(f"\n🔍 Testing ENS resolution for: {test_ens}")

        # Try different methods to resolve ENS - adding Alchemy's own resolveENS
        methods_to_try = [
            {"method": "ens_getAddress", "params": {"name": test_ens}},
            {"method": "eth_resolveENS", "params": {"ensName": test_ens}},
            {"method": "alchemy_resolveENS", "params": {"ens": test_ens}}
        ]

        resolved_address = None

        for method_info in methods_to_try:
            method = method_info["method"]
            params = method_info["params"]

            try:
                print(f"Trying method: {method}")
                result = await session.call_tool(method, params)

                if hasattr(result, 'content') and result.content:
                    resolved_address = result.content
                    print(f"✅ Success with {method}: {test_ens} → {resolved_address}")
                    break
                else:
                    print(f"❌ Failed with {method}: No result content")
            except Exception as e:
                print(f"❌ Failed with {method}: {str(e)}")

        # Trying direct call with ENS name to see if Alchemy's provider handles it natively
        print(f"\n🔍 Trying direct eth_getBalance call with ENS: {test_ens}")
        try:
            balance_result = await session.call_tool(
                "eth_getBalance",
                {"address": test_ens, "tag": "latest"}
            )

            if hasattr(balance_result, 'content') and balance_result.content:
                eth_balance_hex = balance_result.content
                eth_balance_wei = int(eth_balance_hex, 16)
                eth_balance = eth_balance_wei / 1e18
                print(f"✅ Direct ETH Balance call successful: {eth_balance:.6f} ETH")
                resolved_address = test_ens  # Provider handles ENS natively
            else:
                print("❌ Failed direct balance call with ENS: No result content")
        except Exception as e:
            print(f"❌ Failed direct balance call with ENS: {str(e)}")

        if resolved_address:
            # Now test getting balance with the resolved address if needed
            if resolved_address != test_ens:  # Skip if we already got the balance above
                print(f"\n🔍 Getting ETH balance for resolved address: {resolved_address}")
                try:
                    balance_result = await session.call_tool(
                        "eth_getBalance",
                        {"address": resolved_address, "tag": "latest"}
                    )

                    if hasattr(balance_result, 'content') and balance_result.content:
                        eth_balance_hex = balance_result.content
                        eth_balance_wei = int(eth_balance_hex, 16)
                        eth_balance = eth_balance_wei / 1e18
                        print(f"ETH Balance: {eth_balance:.6f} ETH")
                    else:
                        print("❌ Failed to get balance: No result content")
                except Exception as e:
                    print(f"❌ Failed to get balance: {str(e)}")

            # Test getting token balances
            print(f"\n🔍 Getting token balances for resolved address: {resolved_address}")
            try:
                token_result = await session.call_tool(
                    "alchemy_getTokenBalances",
                    {"address": resolved_address}
                )

                if hasattr(token_result, 'content') and token_result.content:
                    tokens = token_result.content.get('tokenBalances', [])
                    print(f"Found {len(tokens)} tokens")
                    return True
                else:
                    print("❌ Failed to get token balances: No result content")
                    return False
            except Exception as e:
                print(f"❌ Failed to get token balances: {str(e)}")
                return False
        else:
            print("❌ Could not resolve or use ENS name with any method")
            return False

async def run_tests():
    """Run all tests and report results"""
    print("🔍 Starting ENS Integration Tests")

    # Check if TheGraph API key is configured
    api_key = os.getenv("THEGRAPH_API_KEY")
    if not api_key:
        print("❌ THEGRAPH_API_KEY not found in environment variables")
        print("Please add your TheGraph API key to the .env file")

        # We can still run the Alchemy tests
        print("Running only Alchemy MCP server tests...")
        alchemy_passed = await test_alchemy_ens_integration()

        print("\n=== Test Results ===")
        print(f"Custom ENS Tools: ❌ Skipped (TheGraph API key missing)")
        print(f"Alchemy Integration: {'✅ Passed' if alchemy_passed else '❌ Failed'}")

        if alchemy_passed:
            print("\n✅ Alchemy ENS integration is working correctly.")
        else:
            print("\n❌ Alchemy ENS integration failed. Please check the errors above.")
        return

    # Run tests
    custom_passed = await test_custom_ens_resolution()
    alchemy_passed = await test_alchemy_ens_integration()

    # Report results
    print("\n=== Test Results ===")
    print(f"Custom ENS Tools: {'✅ Passed' if custom_passed else '❌ Failed'}")
    print(f"Alchemy Integration: {'✅ Passed' if alchemy_passed else '❌ Failed'}")

    if custom_passed and alchemy_passed:
        print("\n✅ All tests passed! ENS integration is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    asyncio.run(run_tests())