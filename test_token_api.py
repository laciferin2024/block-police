#!/usr/bin/env python
"""
Token API Integration Test Script

This script tests TheGraph Token API tools to ensure they're properly integrated and working.
"""
import asyncio
import json
from dotenv import load_dotenv
from tools.token import (get_token_metadata, get_token_holders,
                        get_token_transfers, get_holder_tokens,
                        search_tokens)
from config import GRAPH_MARKET_ACCESS_TOKEN

# Load environment variables
load_dotenv()

# Test token addresses (Ethereum mainnet)
UNI_TOKEN_ADDRESS = "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"  # Uniswap
WALLET_ADDRESS = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # vitalik.eth


async def test_token_metadata():
    """Test token metadata retrieval"""
    print(f"\n=== Testing Token Metadata for {UNI_TOKEN_ADDRESS} ===")

    try:
        metadata = await get_token_metadata(UNI_TOKEN_ADDRESS)

        print("Token Metadata:")
        if isinstance(metadata, dict) and "error" not in metadata:
            for key, value in metadata.items():
                print(f"  {key}: {value}")
            print("✅ Token metadata test passed")
            return True
        else:
            error = metadata.get('error', 'Unknown error') if metadata else "No metadata returned"
            print(f"❌ Token metadata test failed: {error}")
            return False
    except Exception as e:
        print(f"❌ Token metadata test failed with exception: {e}")
        return False


async def test_token_holders():
    """Test token holders retrieval"""
    print(f"\n=== Testing Token Holders for {UNI_TOKEN_ADDRESS} ===")

    try:
        holders = await get_token_holders(UNI_TOKEN_ADDRESS, 5)

        print("Token Holders:")
        if isinstance(holders, dict) and "error" not in holders:
            holder_list = holders.get('holders', [])
            print(f"  Found {len(holder_list)} holders")

            # Print first 5 holders
            for i, holder in enumerate(holder_list[:5]):
                print(f"  {i+1}. {holder.get('address')}: {holder.get('balance')}")

            print("✅ Token holders test passed")
            return True
        else:
            error = holders.get('error', 'Unknown error') if holders else "No holders returned"
            print(f"❌ Token holders test failed: {error}")
            return False
    except Exception as e:
        print(f"❌ Token holders test failed with exception: {e}")
        return False


async def test_token_transfers():
    """Test token transfers retrieval"""
    print(f"\n=== Testing Token Transfers for {UNI_TOKEN_ADDRESS} ===")

    try:
        transfers = await get_token_transfers(UNI_TOKEN_ADDRESS, 5)

        print("Token Transfers:")
        if isinstance(transfers, dict) and "error" not in transfers:
            transfer_list = transfers.get('transfers', [])
            print(f"  Found {len(transfer_list)} transfers")

            # Print first 5 transfers
            for i, transfer in enumerate(transfer_list[:5]):
                print(f"  {i+1}. From: {transfer.get('from')[:10]}... To: {transfer.get('to')[:10]}... Value: {transfer.get('value')}")

            print("✅ Token transfers test passed")
            return True
        else:
            error = transfers.get('error', 'Unknown error') if transfers else "No transfers returned"
            print(f"❌ Token transfers test failed: {error}")
            return False
    except Exception as e:
        print(f"❌ Token transfers test failed with exception: {e}")
        return False


async def test_holder_tokens():
    """Test holder tokens retrieval"""
    print(f"\n=== Testing Holder Tokens for {WALLET_ADDRESS} ===")

    try:
        tokens = await get_holder_tokens(WALLET_ADDRESS, 5)

        print("Holder Tokens:")
        if isinstance(tokens, dict) and "error" not in tokens:
            token_list = tokens.get('tokens', [])
            print(f"  Found {len(token_list)} tokens")

            # Print first 5 tokens
            for i, token in enumerate(token_list[:5]):
                print(f"  {i+1}. {token.get('name')} ({token.get('symbol')}): {token.get('balance')}")

            print("✅ Holder tokens test passed")
            return True
        else:
            error = tokens.get('error', 'Unknown error') if tokens else "No tokens returned"
            print(f"❌ Holder tokens test failed: {error}")
            return False
    except Exception as e:
        print(f"❌ Holder tokens test failed with exception: {e}")
        return False


async def test_token_search():
    """Test token search"""
    print(f"\n=== Testing Token Search for 'Uniswap' ===")

    try:
        results = await search_tokens("Uniswap", 5)

        print("Token Search Results:")
        if isinstance(results, dict) and "error" not in results:
            token_list = results.get('tokens', [])
            print(f"  Found {len(token_list)} tokens")

            # Print first 5 tokens
            for i, token in enumerate(token_list[:5]):
                print(f"  {i+1}. {token.get('name')} ({token.get('symbol')}): {token.get('address')}")

            print("✅ Token search test passed")
            return True
        else:
            error = results.get('error', 'Unknown error') if results else "No search results returned"
            print(f"❌ Token search test failed: {error}")
            return False
    except Exception as e:
        print(f"❌ Token search test failed with exception: {e}")
        return False


async def run_tests():
    """Run all tests and report results"""
    print("🔍 Starting Token API Integration Tests")

    # Check if Token API access token is configured
    if not GRAPH_MARKET_ACCESS_TOKEN:
        print("❌ GRAPH_MARKET_ACCESS_TOKEN not found in environment variables")
        print("Please add your TheGraph Market access token to the .env file")
        return

    # Run tests
    metadata_passed = await test_token_metadata()
    holders_passed = await test_token_holders()
    transfers_passed = await test_token_transfers()
    holder_tokens_passed = await test_holder_tokens()
    search_passed = await test_token_search()

    # Report results
    print("\n=== Test Results ===")
    print(f"Token Metadata: {'✅ Passed' if metadata_passed else '❌ Failed'}")
    print(f"Token Holders: {'✅ Passed' if holders_passed else '❌ Failed'}")
    print(f"Token Transfers: {'✅ Passed' if transfers_passed else '❌ Failed'}")
    print(f"Holder Tokens: {'✅ Passed' if holder_tokens_passed else '❌ Failed'}")
    print(f"Token Search: {'✅ Passed' if search_passed else '❌ Failed'}")

    if all([metadata_passed, holders_passed, transfers_passed, holder_tokens_passed, search_passed]):
        print("\n✅ All tests passed! Token API integration is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(run_tests())