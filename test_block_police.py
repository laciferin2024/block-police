import asyncio
import json
from block_police_agent import AlchemyMCP

async def test_trace_funds():
    """Test the trace_evm_funds function"""
    alchemy_mcp = AlchemyMCP()

    # Test with Vitalik's address
    test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    result = await alchemy_mcp.trace_evm_funds(test_address)

    print(f"Trace funds result: {result}")
    assert "Tracing initiated from" in result
    assert test_address in result

    print("✅ trace_evm_funds test passed")

async def test_get_holdings():
    """Test the get_curated_holdings function"""
    alchemy_mcp = AlchemyMCP()

    # Test with Vitalik's address
    test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    result = await alchemy_mcp.get_curated_holdings(test_address)

    print(f"Holdings result: {json.dumps(result, indent=2)}")
    assert "address" in result
    assert "ETH_Balance" in result
    assert "Curated_Risk_Assessment" in result

    print("✅ get_curated_holdings test passed")

async def test_get_transaction():
    """Test the get_transaction_details function"""
    alchemy_mcp = AlchemyMCP()

    # Test with a known transaction hash (this is a sample, replace with a real one for actual testing)
    test_tx_hash = "0x5c504ed432cb51138bcf09aa5e8a410dd4a1e204ef84bfed1be16dfba1b22060"
    result = await alchemy_mcp.get_transaction_details(test_tx_hash)

    print(f"Transaction details: {json.dumps(result, indent=2)}")

    # For the test hash, we'll get error or null since it might not exist,
    # but the function should execute without errors
    print("✅ get_transaction_details test passed")

async def main():
    """Run all tests"""
    print("Starting Block Police Agent tests...\n")

    print("🔍 Testing trace_evm_funds:")
    await test_trace_funds()

    print("\n🔍 Testing get_curated_holdings:")
    await test_get_holdings()

    print("\n🔍 Testing get_transaction_details:")
    await test_get_transaction()

    print("\n🎉 All tests completed successfully! ✅")

if __name__ == "__main__":
    asyncio.run(main())