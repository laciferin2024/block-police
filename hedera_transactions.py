#!/usr/bin/env python3
"""
Hedera Transaction Query Example

This script demonstrates how to query transactions and events on the Hedera blockchain
using the MCP (Metaprogramming Client Protocol) architecture.
"""
import asyncio
import logging
import json
from typing import Dict, Any, List, Optional

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
logger = logging.getLogger("hedera_transactions")


async def setup_hedera_client() -> tuple:
    """Set up and connect to a Hedera MCP client"""
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
        return None, {"error": "Failed to create Hedera MCP client"}

    try:
        # Connect to the Hedera MCP server
        logger.info("Connecting to Hedera MCP server...")
        success = await hedera_client.connect()

        if not success:
            logger.error("Failed to connect to Hedera MCP server")
            return None, {"error": "Failed to connect to Hedera MCP server"}

        logger.info("Connected to Hedera MCP server")
        return hedera_client, {"success": True}

    except Exception as e:
        logger.error(f"Error connecting to Hedera MCP server: {e}")
        return None, {"error": f"Failed to connect to Hedera MCP server: {str(e)}"}


async def get_transaction_by_id(transaction_id: str) -> Dict[str, Any]:
    """Get transaction details by transaction ID"""
    logger.info(f"Getting transaction details for ID: {transaction_id}")

    hedera_client, result = await setup_hedera_client()
    if not hedera_client:
        return result

    try:
        # Query the transaction
        if hasattr(hedera_client, "get_transaction_by_id"):
            result = await hedera_client.get_transaction_by_id(transaction_id)
            return result
        else:
            # Try using the generic call_tool method instead
            result = await hedera_client.call_tool(
                "getTransactionById",
                {"transactionId": transaction_id}
            )
            return result
    except Exception as e:
        logger.error(f"Error getting transaction: {e}")
        return {"error": f"Failed to get transaction: {str(e)}"}
    finally:
        # Clean up the client
        if hedera_client:
            try:
                await hedera_client.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up Hedera client: {e}")


async def get_account_transactions(account_id: str = None, limit: int = 10) -> Dict[str, Any]:
    """Get recent transactions for an account"""
    account_id = account_id or HEDERA_ACCOUNT_ID
    logger.info(f"Getting transactions for account: {account_id}")

    hedera_client, result = await setup_hedera_client()
    if not hedera_client:
        return result

    try:
        # Query the account transactions
        if hasattr(hedera_client, "get_account_transactions"):
            result = await hedera_client.get_account_transactions(account_id, limit)
            return result
        else:
            # Try using the generic call_tool method instead
            result = await hedera_client.call_tool(
                "getAccountTransactions",
                {"accountId": account_id, "limit": limit}
            )
            return result
    except Exception as e:
        logger.error(f"Error getting account transactions: {e}")
        return {"error": f"Failed to get account transactions: {str(e)}"}
    finally:
        # Clean up the client
        if hedera_client:
            try:
                await hedera_client.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up Hedera client: {e}")


async def get_token_info(token_id: str) -> Dict[str, Any]:
    """Get detailed information about a token"""
    logger.info(f"Getting token info for: {token_id}")

    hedera_client, result = await setup_hedera_client()
    if not hedera_client:
        return result

    try:
        # Query token info
        if hasattr(hedera_client, "get_token_info"):
            result = await hedera_client.get_token_info(token_id)
            return result
        else:
            # Try using the generic call_tool method instead
            result = await hedera_client.call_tool(
                "getTokenInfo",
                {"tokenId": token_id}
            )
            return result
    except Exception as e:
        logger.error(f"Error getting token info: {e}")
        return {"error": f"Failed to get token info: {str(e)}"}
    finally:
        # Clean up the client
        if hedera_client:
            try:
                await hedera_client.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up Hedera client: {e}")


async def query_topic_messages(topic_id: str, limit: int = 10) -> Dict[str, Any]:
    """Query messages from a consensus topic"""
    logger.info(f"Querying messages from topic: {topic_id}")

    hedera_client, result = await setup_hedera_client()
    if not hedera_client:
        return result

    try:
        # Query topic messages
        if hasattr(hedera_client, "get_topic_messages"):
            result = await hedera_client.get_topic_messages(topic_id, limit)
            return result
        else:
            # Try using the generic call_tool method instead
            result = await hedera_client.call_tool(
                "getTopicMessages",
                {"topicId": topic_id, "limit": limit}
            )
            return result
    except Exception as e:
        logger.error(f"Error querying topic messages: {e}")
        return {"error": f"Failed to query topic messages: {str(e)}"}
    finally:
        # Clean up the client
        if hedera_client:
            try:
                await hedera_client.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up Hedera client: {e}")


async def submit_query_to_mcp(query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Submit a custom query to the Hedera MCP"""
    logger.info(f"Submitting custom query: {query_type}")

    hedera_client, result = await setup_hedera_client()
    if not hedera_client:
        return result

    try:
        # Submit custom query
        result = await hedera_client.call_tool(query_type, params)
        return result
    except Exception as e:
        logger.error(f"Error submitting custom query: {e}")
        return {"error": f"Failed to submit query: {str(e)}"}
    finally:
        # Clean up the client
        if hedera_client:
            try:
                await hedera_client.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up Hedera client: {e}")


def print_json(data: Dict[str, Any]) -> None:
    """Print data as formatted JSON"""
    print(json.dumps(data, indent=2))


async def main():
    """Main function to demonstrate Hedera transaction queries"""
    print("Hedera Transaction Query Example")
    print("-------------------------------")

    # Check if we have Hedera credentials
    if not HEDERA_ACCOUNT_ID or not HEDERA_PRIVATE_KEY:
        print("ERROR: Hedera credentials not found in config.py")
        print("Please set HEDERA_ACCOUNT_ID and HEDERA_PRIVATE_KEY in the config file.")
        return

    print(f"Using Hedera network: {HEDERA_NETWORK}")
    print(f"Using account ID: {HEDERA_ACCOUNT_ID}")
    print()

    # Interactive menu
    while True:
        print("\nHedera Transaction Query Menu:")
        print("1. Get transaction by ID")
        print("2. Get account transactions")
        print("3. Get token information")
        print("4. Query consensus topic messages")
        print("5. Submit custom MCP query")
        print("0. Exit")

        choice = input("\nEnter your choice (0-5): ")

        if choice == "0":
            break
        elif choice == "1":
            tx_id = input("Transaction ID: ")

            print("\nQuerying transaction...")
            result = await get_transaction_by_id(tx_id)

            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print("\nTransaction details:")
                print_json(result)

        elif choice == "2":
            account = input("Account ID (leave empty for default): ")
            account = account if account else None
            try:
                limit = int(input("Number of transactions (default 10): ") or "10")
            except ValueError:
                print("Invalid number input")
                continue

            print("\nQuerying account transactions...")
            result = await get_account_transactions(account, limit)

            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print("\nAccount transactions:")
                print_json(result)

        elif choice == "3":
            token_id = input("Token ID: ")

            print("\nQuerying token information...")
            result = await get_token_info(token_id)

            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print("\nToken information:")
                print_json(result)

        elif choice == "4":
            topic_id = input("Topic ID: ")
            try:
                limit = int(input("Number of messages (default 10): ") or "10")
            except ValueError:
                print("Invalid number input")
                continue

            print("\nQuerying topic messages...")
            result = await query_topic_messages(topic_id, limit)

            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print("\nTopic messages:")
                print_json(result)

        elif choice == "5":
            query_type = input("Query type (MCP command): ")
            params_str = input("Parameters (JSON format): ")

            try:
                params = json.loads(params_str)
            except json.JSONDecodeError:
                print("Invalid JSON parameters")
                continue

            print("\nSubmitting custom query...")
            result = await submit_query_to_mcp(query_type, params)

            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print("\nQuery results:")
                print_json(result)

        else:
            print("Invalid choice. Please try again.")

    print("\nHedera transaction query demonstration complete.")


if __name__ == "__main__":
    asyncio.run(main())