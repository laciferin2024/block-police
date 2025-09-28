#!/usr/bin/env python3
"""
Hedera Token Operations Example

This script demonstrates how to create and manage tokens on the Hedera blockchain
using the MCP (Metaprogramming Client Protocol) architecture.
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
logger = logging.getLogger("hedera_tokens")


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


async def create_fungible_token(name: str, symbol: str, initial_supply: int,
                               decimals: int = 2) -> Dict[str, Any]:
    """Create a new fungible token on Hedera"""
    logger.info(f"Creating fungible token: {name} ({symbol})")

    hedera_client, result = await setup_hedera_client()
    if not hedera_client:
        return result

    try:
        # Create the token
        if hasattr(hedera_client, "create_fungible_token"):
            result = await hedera_client.create_fungible_token(name, symbol, initial_supply, decimals)
            return result
        else:
            return {"error": "Hedera client does not support create_fungible_token method"}
    except Exception as e:
        logger.error(f"Error creating token: {e}")
        return {"error": f"Failed to create token: {str(e)}"}
    finally:
        # Clean up the client
        if hedera_client:
            try:
                await hedera_client.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up Hedera client: {e}")


async def transfer_token(token_id: str, to_account: str, amount: float) -> Dict[str, Any]:
    """Transfer tokens on Hedera"""
    logger.info(f"Transferring {amount} of token {token_id} to {to_account}")

    hedera_client, result = await setup_hedera_client()
    if not hedera_client:
        return result

    try:
        # Transfer the token
        if hasattr(hedera_client, "transfer_token"):
            result = await hedera_client.transfer_token(token_id, to_account, amount)
            return result
        else:
            return {"error": "Hedera client does not support transfer_token method"}
    except Exception as e:
        logger.error(f"Error transferring token: {e}")
        return {"error": f"Failed to transfer token: {str(e)}"}
    finally:
        # Clean up the client
        if hedera_client:
            try:
                await hedera_client.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up Hedera client: {e}")


async def associate_token(token_id: str, account_id: str = None) -> Dict[str, Any]:
    """Associate a token with an account on Hedera"""
    logger.info(f"Associating token {token_id} with account {account_id or 'default'}")

    hedera_client, result = await setup_hedera_client()
    if not hedera_client:
        return result

    try:
        # Associate the token
        if hasattr(hedera_client, "associate_token"):
            result = await hedera_client.associate_token(token_id, account_id)
            return result
        else:
            return {"error": "Hedera client does not support associate_token method"}
    except Exception as e:
        logger.error(f"Error associating token: {e}")
        return {"error": f"Failed to associate token: {str(e)}"}
    finally:
        # Clean up the client
        if hedera_client:
            try:
                await hedera_client.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up Hedera client: {e}")


async def create_nft_collection(name: str, symbol: str, max_supply: int = None) -> Dict[str, Any]:
    """Create a new NFT collection on Hedera"""
    logger.info(f"Creating NFT collection: {name} ({symbol})")

    hedera_client, result = await setup_hedera_client()
    if not hedera_client:
        return result

    try:
        # Create the NFT collection
        if hasattr(hedera_client, "create_nft"):
            result = await hedera_client.create_nft(name, symbol, max_supply)
            return result
        else:
            return {"error": "Hedera client does not support create_nft method"}
    except Exception as e:
        logger.error(f"Error creating NFT collection: {e}")
        return {"error": f"Failed to create NFT collection: {str(e)}"}
    finally:
        # Clean up the client
        if hedera_client:
            try:
                await hedera_client.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up Hedera client: {e}")


async def mint_nft(token_id: str, metadata: str) -> Dict[str, Any]:
    """Mint a new NFT on Hedera"""
    logger.info(f"Minting NFT for token {token_id} with metadata {metadata}")

    hedera_client, result = await setup_hedera_client()
    if not hedera_client:
        return result

    try:
        # Mint the NFT
        if hasattr(hedera_client, "mint_nft"):
            result = await hedera_client.mint_nft(token_id, metadata)
            return result
        else:
            return {"error": "Hedera client does not support mint_nft method"}
    except Exception as e:
        logger.error(f"Error minting NFT: {e}")
        return {"error": f"Failed to mint NFT: {str(e)}"}
    finally:
        # Clean up the client
        if hedera_client:
            try:
                await hedera_client.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up Hedera client: {e}")


async def main():
    """Main function to demonstrate Hedera token operations"""
    print("Hedera Token Operations Example")
    print("------------------------------")

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
        print("\nHedera Token Operations Menu:")
        print("1. Create fungible token")
        print("2. Transfer token")
        print("3. Associate token with account")
        print("4. Create NFT collection")
        print("5. Mint NFT")
        print("0. Exit")

        choice = input("\nEnter your choice (0-5): ")

        if choice == "0":
            break
        elif choice == "1":
            name = input("Token name: ")
            symbol = input("Token symbol: ")
            try:
                initial_supply = int(input("Initial supply: "))
                decimals = int(input("Decimals (default 2): ") or "2")
            except ValueError:
                print("Invalid number input")
                continue

            print("\nCreating token...")
            result = await create_fungible_token(name, symbol, initial_supply, decimals)

            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"Token created successfully!")
                print(f"Token ID: {result.get('tokenId', 'Unknown')}")

        elif choice == "2":
            token_id = input("Token ID: ")
            to_account = input("Recipient account ID: ")
            try:
                amount = float(input("Amount to transfer: "))
            except ValueError:
                print("Invalid amount input")
                continue

            print("\nTransferring token...")
            result = await transfer_token(token_id, to_account, amount)

            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"Token transferred successfully!")
                print(f"Transaction ID: {result.get('transactionId', 'Unknown')}")

        elif choice == "3":
            token_id = input("Token ID: ")
            account_id = input("Account ID (leave empty for default): ")
            account_id = account_id if account_id else None

            print("\nAssociating token...")
            result = await associate_token(token_id, account_id)

            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"Token associated successfully!")
                print(f"Transaction ID: {result.get('transactionId', 'Unknown')}")

        elif choice == "4":
            name = input("Collection name: ")
            symbol = input("Collection symbol: ")
            max_supply_input = input("Max supply (leave empty for unlimited): ")
            max_supply = int(max_supply_input) if max_supply_input else None

            print("\nCreating NFT collection...")
            result = await create_nft_collection(name, symbol, max_supply)

            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"NFT collection created successfully!")
                print(f"Token ID: {result.get('tokenId', 'Unknown')}")

        elif choice == "5":
            token_id = input("NFT collection token ID: ")
            metadata = input("NFT metadata (e.g. IPFS URL): ")

            print("\nMinting NFT...")
            result = await mint_nft(token_id, metadata)

            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"NFT minted successfully!")
                print(f"Serial Number: {result.get('serialNumber', 'Unknown')}")
                print(f"Transaction ID: {result.get('transactionId', 'Unknown')}")

        else:
            print("Invalid choice. Please try again.")

    print("\nHedera token operations demonstration complete.")


if __name__ == "__main__":
    asyncio.run(main())