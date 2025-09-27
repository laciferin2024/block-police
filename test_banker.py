#!/usr/bin/env python3
"""
Test script for the Banker Agent
Tests the core functionality without requiring the full uAgent framework
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hyperon import MeTTa
from metta.knowledge import initialize_banker_knowledge
from metta.banker_rag import BankerRAG
from metta.utils import LLM, process_banker_query

def test_banker_calculations():
    """Test the core banker calculation logic."""
    print("🧪 Testing Banker Calculations...")
    
    # Initialize MeTTa and knowledge
    metta = MeTTa()
    initialize_banker_knowledge(metta)
    rag = BankerRAG(metta)
    
    # Test scenarios
    test_cases = [
        {
            "name": "Early Round - Conservative Player",
            "remaining_cards": [1, 5, 10, 25, 50, 100, 500, 1000, 2500, 5000, 10000, 25000, 50000, 75000, 100000, 200000, 300000, 400000, 500000, 750000, 1000000],
            "round": 1,
            "sentiment": "neutral"
        },
        {
            "name": "Mid Round - Confident Player",
            "remaining_cards": [100, 500, 1000, 5000, 10000, 25000, 100000, 500000, 1000000],
            "round": 3,
            "sentiment": "confident"
        },
        {
            "name": "Late Round - Desperate Player",
            "remaining_cards": [1000, 5000, 10000, 500000, 1000000],
            "round": 6,
            "sentiment": "desperate"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📊 {test_case['name']}")
        print(f"   Cards: {test_case['remaining_cards']}")
        print(f"   Round: {test_case['round']}")
        print(f"   Sentiment: {test_case['sentiment']}")
        
        # Calculate offer
        offer_data = rag.calculate_base_offer(
            test_case['remaining_cards'],
            test_case['round'],
            test_case['sentiment']
        )
        
        print(f"   Expected Value: ${offer_data['expectedValue']:,}")
        print(f"   Banker Offer: ${offer_data['offer']:,}")
        print(f"   House Edge: {offer_data['houseEdge']:.1%}")
        print(f"   Risk Adjustment: {offer_data['riskAdjustment']:.2f}")
        
        # Verify house edge is maintained
        ev = offer_data['expectedValue']
        offer = offer_data['offer']
        actual_edge = (ev - offer) / ev if ev > 0 else 0
        print(f"   Actual Edge: {actual_edge:.1%}")
        
        assert offer < ev, f"Offer ${offer} should be less than EV ${ev}"
        print("   ✅ House edge maintained")

def test_sentiment_analysis():
    """Test sentiment analysis functionality."""
    print("\n🧠 Testing Sentiment Analysis...")
    
    metta = MeTTa()
    initialize_banker_knowledge(metta)
    rag = BankerRAG(metta)
    
    test_messages = [
        ("I'm confident and ready to win!", "confident"),
        ("Please help me, I'm desperate!", "desperate"),
        ("I demand a better offer!", "aggressive"),
        ("What's your offer?", "neutral")
    ]
    
    for message, expected in test_messages:
        result = rag.analyze_user_behavior(message)
        print(f"   '{message}' -> {result} (expected: {expected})")
        assert result == expected, f"Expected {expected}, got {result}"
        print("   ✅ Correct sentiment detected")

def test_meTTa_queries():
    """Test MeTTa knowledge graph queries."""
    print("\n🔍 Testing MeTTa Queries...")
    
    metta = MeTTa()
    initialize_banker_knowledge(metta)
    rag = BankerRAG(metta)
    
    # Test house edge multipliers
    early_edge = rag.get_house_edge_multiplier(1)
    mid_edge = rag.get_house_edge_multiplier(3)
    late_edge = rag.get_house_edge_multiplier(6)
    
    print(f"   Early round edge: {early_edge:.2f}")
    print(f"   Mid round edge: {mid_edge:.2f}")
    print(f"   Late round edge: {late_edge:.2f}")
    
    assert early_edge < mid_edge < late_edge, "House edge should increase with rounds"
    print("   ✅ House edge progression correct")
    
    # Test sentiment multipliers
    confident_mult = rag.get_sentiment_multiplier("confident")
    desperate_mult = rag.get_sentiment_multiplier("desperate")
    
    print(f"   Confident multiplier: {confident_mult:.2f}")
    print(f"   Desperate multiplier: {desperate_mult:.2f}")
    
    assert confident_mult > desperate_mult, "Confident players should get higher offers"
    print("   ✅ Sentiment multipliers correct")

def test_risk_adjustments():
    """Test risk adjustment calculations."""
    print("\n⚖️ Testing Risk Adjustments...")
    
    metta = MeTTa()
    initialize_banker_knowledge(metta)
    rag = BankerRAG(metta)
    
    # High variance (big range)
    high_var_cards = [1, 100, 1000, 100000, 1000000]
    high_var_adj = rag.get_risk_adjustment(high_var_cards)
    
    # Low variance (small range)
    low_var_cards = [1000, 1100, 1200, 1300, 1400]
    low_var_adj = rag.get_risk_adjustment(low_var_cards)
    
    print(f"   High variance cards: {high_var_cards} -> adjustment: {high_var_adj:.2f}")
    print(f"   Low variance cards: {low_var_cards} -> adjustment: {low_var_adj:.2f}")
    
    assert high_var_adj < low_var_adj, "High variance should result in lower offers"
    print("   ✅ Risk adjustments correct")

def main():
    """Run all tests."""
    print("🎰 Banker Agent Test Suite 🎰")
    print("=" * 50)
    
    try:
        test_meTTa_queries()
        test_sentiment_analysis()
        test_risk_adjustments()
        test_banker_calculations()
        
        print("\n🎉 All tests passed! The Banker Agent is ready to play!")
        print("\nTo run the full agent:")
        print("1. Set your ASI_ONE_API_KEY in .env file")
        print("2. Run: python agent.py")
        print("3. Connect via Agentverse and start negotiating!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
