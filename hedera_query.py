#!/usr/bin/env python3
"""
Hedera MCP Query Example

This script demonstrates how to query the Hedera blockchain using the MCP
(Metaprogramming Client Protocol) architecture.
"""
import asyncio
import logging
from typing import Dict, Any

# Import MCP client registry and capabilities
from mcps import MCPRegistry, MCPCapability, MCPClientConfig
from mcps.clients.hedera import HederaMCPClient
from mcps.network import HederaNetwork

# Import config for credentials
from config import (
    HEDERA_ACCOUNT_ID,
    HEDERA_PRIVATE_KEY,
    HEDERA_NETWORK,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("hedera_query")


async def query_hedera_balance(account_id: str = None) -> Dict[str, Any]:
    """Query the HBAR balance for a Hedera account"""
    logger.info(f"Querying Hedera balance for account: {account_id or 'default account'}")

    # Create MCP registry
    registry = MCPRegistry()

    # Set up Hedera client config
    hedera_config = MCPClientConfig(
        name="hedera",
        api_key=HEDERA_PRIVATE_KEY,
        command="npx",
        args=[
            "-y",
            "hedera-mcp",
            f"--hedera_account_id={HEDERA_ACCOUNT_ID}",
            f"--hedera_private_key={HEDERA_PRIVATE_KEY}",
            f"--hedera_network={HEDERA_NETWORK}"
        ],
        env_vars={
            "HEDERA_ACCOUNT_ID": HEDERA_ACCOUNT_ID,
            "HEDERA_PRIVATE_KEY": HEDERA_PRIVATE_KEY
        }
    )

    # Create client through registry
    hedera_client = registry.create_client("hedera", hedera_config)

    if not hedera_client:
        logger.error("Failed to create Hedera MCP client")
        return {"error": "Failed to create Hedera MCP client"}

    try:
        # Connect to the Hedera MCP server
        logger.info("Connecting to Hedera MCP server...")
        success = await hedera_client.connect()

        if not success:
            logger.error("Failed to connect to Hedera MCP server")
            return {"error": "Failed to connect to Hedera MCP server"}

        logger.info("Connected to Hedera MCP server")

        # Query the balance
        if hasattr(hedera_client, "get_hbar_balance"):
            result = await hedera_client.get_hbar_balance(account_id)
            return result
        else:
            return {"error": "Hedera client does not support get_hbar_balance method"}

    except Exception as e:
        logger.error(f"Error querying Hedera balance: {e}")
        return {"error": f"Failed to query Hedera balance: {str(e)}"}
    finally:
        # Clean up the client
        if hedera_client:
            try:
                await hedera_client.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up Hedera client: {e}")


async def query_hedera_token_balances(account_id: str = None) -> Dict[str, Any]:
    """Query all token balances for a Hedera account"""
    logger.info(f"Querying token balances for account: {account_id or 'default account'}")

    # Create MCP registry
    registry = MCPRegistry()

    # Set up Hedera client config
    hedera_config = MCPClientConfig(
        name="hedera",
        api_key=HEDERA_PRIVATE_KEY,
        command="npx",
        args=[
            "-y",
            "hedera-mcp",
            f"--hedera_account_id={HEDERA_ACCOUNT_ID}",
            f"--hedera_private_key={HEDERA_PRIVATE_KEY}",
            f"--hedera_network={HEDERA_NETWORK}"
        ],
        env_vars={
            "HEDERA_ACCOUNT_ID": HEDERA_ACCOUNT_ID,
            "HEDERA_PRIVATE_KEY": HEDERA_PRIVATE_KEY
        }
    )

    # Create client through registry
    hedera_client = registry.create_client("hedera", hedera_config)

    if not hedera_client:
        logger.error("Failed to create Hedera MCP client")
        return {"error": "Failed to create Hedera MCP client"}

    try:
        # Connect to the Hedera MCP server
        logger.info("Connecting to Hedera MCP server...")
        success = await hedera_client.connect()

        if not success:
            logger.error("Failed to connect to Hedera MCP server")
            return {"error": "Failed to connect to Hedera MCP server"}

        logger.info("Connected to Hedera MCP server")

        # Query token balances
        if hasattr(hedera_client, "get_token_balances"):
            result = await hedera_client.get_token_balances(account_id)
            return result
        else:
            return {"error": "Hedera client does not support get_token_balances method"}

    except Exception as e:
        logger.error(f"Error querying token balances: {e}")
        return {"error": f"Failed to query token balances: {str(e)}"}
    finally:
        # Clean up the client
        if hedera_client:
            try:
                await hedera_client.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up Hedera client: {e}")


async def main():
    """Main function to demonstrate Hedera MCP queries"""
    print("Hedera MCP Query Example")
    print("------------------------")

    # Check if we have Hedera credentials
    if not HEDERA_ACCOUNT_ID or not HEDERA_PRIVATE_KEY:
        print("ERROR: Hedera credentials not found in config.py")
        print("Please set HEDERA_ACCOUNT_ID and HEDERA_PRIVATE_KEY in the config file.")
        return

    print(f"Using Hedera network: {HEDERA_NETWORK}")
    print(f"Using account ID: {HEDERA_ACCOUNT_ID}")
    print()

    # Query HBAR balance
    print("Querying HBAR balance...")
    balance_result = await query_hedera_balance()

    if "error" in balance_result:
        print(f"Error: {balance_result['error']}")
    else:
        print(f"Account ID: {balance_result.get('account', HEDERA_ACCOUNT_ID)}")
        print(f"HBAR Balance: {balance_result.get('balance', 'Unknown')}")

    print()

    # Query token balances
    print("Querying token balances...")
    tokens_result = await query_hedera_token_balances()

    if "error" in tokens_result:
        print(f"Error: {tokens_result['error']}")
    else:
        print(f"Account ID: {tokens_result.get('account', HEDERA_ACCOUNT_ID)}")
        tokens = tokens_result.get("tokens", [])

        if not tokens:
            print("No tokens found for this account")
        else:
            print(f"Found {len(tokens)} tokens:")
            for token in tokens:
                print(f"  - Token ID: {token.get('tokenId', 'Unknown')}")
                print(f"    Balance: {token.get('balance', '0')}")

    print("\nHedera MCP query demonstration complete.")


if __name__ == "__main__":
    asyncio.run(main())