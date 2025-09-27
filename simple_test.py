#!/usr/bin/env python3
"""
Simple test script for the Banker Agent core functionality
Tests MeTTa knowledge graph and calculation logic
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_meTTa_knowledge():
    """Test MeTTa knowledge graph initialization."""
    print("🧪 Testing MeTTa Knowledge Graph...")
    
    try:
        from hyperon import MeTTa
        from metta.knowledge import initialize_banker_knowledge
        
        metta = MeTTa()
        initialize_banker_knowledge(metta)
        
        # Test querying house edge multipliers
        query_str = '!(match &self (house_edge early_round $multiplier) $multiplier)'
        results = metta.run(query_str)
        
        if results and results[0]:
            multiplier = float(results[0][0].get_object().value)
            print(f"   Early round house edge: {multiplier:.2f}")
            assert 0.5 <= multiplier <= 0.8, f"House edge should be between 0.5-0.8, got {multiplier}"
            print("   ✅ House edge query successful")
        else:
            print("   ❌ Failed to query house edge")
            return False
            
        # Test sentiment multipliers
        query_str = '!(match &self (sentiment_multiplier confident $multiplier) $multiplier)'
        results = metta.run(query_str)
        
        if results and results[0]:
            multiplier = float(results[0][0].get_object().value)
            print(f"   Confident sentiment multiplier: {multiplier:.2f}")
            assert multiplier > 1.0, f"Confident multiplier should be > 1.0, got {multiplier}"
            print("   ✅ Sentiment multiplier query successful")
        else:
            print("   ❌ Failed to query sentiment multiplier")
            return False
            
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing MeTTa: {e}")
        return False

def test_banker_calculations():
    """Test banker calculation logic."""
    print("\n🧮 Testing Banker Calculations...")
    
    try:
        from hyperon import MeTTa
        from metta.knowledge import initialize_banker_knowledge
        from metta.banker_rag import BankerRAG
        
        metta = MeTTa()
        initialize_banker_knowledge(metta)
        rag = BankerRAG(metta)
        
        # Test expected value calculation
        test_cards = [100, 500, 1000, 5000, 10000]
        expected_value = rag.calculate_expected_value(test_cards)
        expected = sum(test_cards) / len(test_cards)
        
        print(f"   Cards: {test_cards}")
        print(f"   Expected Value: {expected_value:.2f} (should be {expected:.2f})")
        assert abs(expected_value - expected) < 0.01, f"Expected value calculation wrong"
        print("   ✅ Expected value calculation correct")
        
        # Test house edge multipliers
        early_edge = rag.get_house_edge_multiplier(1)
        late_edge = rag.get_house_edge_multiplier(6)
        
        print(f"   Early round edge: {early_edge:.2f}")
        print(f"   Late round edge: {late_edge:.2f}")
        assert early_edge < late_edge, "Late rounds should have higher house edge"
        print("   ✅ House edge progression correct")
        
        # Test sentiment analysis
        test_messages = [
            ("I'm confident!", "confident"),
            ("Please help me!", "desperate"),
            ("I demand better!", "aggressive"),
            ("What's the offer?", "neutral")
        ]
        
        for message, expected in test_messages:
            result = rag.analyze_user_behavior(message)
            print(f"   '{message}' -> {result} (expected: {expected})")
            assert result == expected, f"Expected {expected}, got {result}"
        
        print("   ✅ Sentiment analysis correct")
        
        # Test full offer calculation
        offer_data = rag.calculate_base_offer([100, 500, 1000, 5000, 10000], 2, "neutral")
        
        print(f"   Full offer calculation:")
        print(f"     Expected Value: ${offer_data['expectedValue']:,}")
        print(f"     Banker Offer: ${offer_data['offer']:,}")
        print(f"     House Edge: {offer_data['houseEdge']:.1%}")
        
        assert offer_data['offer'] < offer_data['expectedValue'], "Offer should be less than EV"
        print("   ✅ Full offer calculation correct")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing calculations: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🎰 Banker Agent Core Test Suite 🎰")
    print("=" * 50)
    
    success = True
    
    # Test MeTTa knowledge graph
    if not test_meTTa_knowledge():
        success = False
    
    # Test banker calculations
    if not test_banker_calculations():
        success = False
    
    if success:
        print("\n🎉 All core tests passed! The Banker Agent logic is working correctly!")
        print("\nKey Features Verified:")
        print("✅ MeTTa knowledge graph initialization")
        print("✅ House edge calculations")
        print("✅ Sentiment analysis")
        print("✅ Expected value calculations")
        print("✅ Offer calculation with all multipliers")
        print("✅ House advantage maintained")
        
        print("\nTo run the full agent:")
        print("1. Set your ASI_ONE_API_KEY in .env file")
        print("2. Run: python agent.py")
        print("3. Connect via Agentverse and start negotiating!")
        
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
