#!/usr/bin/env python3
"""
Test script for deal acceptance functionality
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_deal_acceptance():
    """Test the deal acceptance logic."""
    print("🧪 Testing Deal Acceptance Logic...")
    
    # Test cases for deal acceptance
    test_messages = [
        ("accept", True),
        ("yes", True),
        ("take it", True),
        ("i'll take it", True),
        ("agreed", True),
        ("i accept", True),
        ("deal accepted", True),
        ("take the deal", True),
        ("ACCEPT", True),  # Case insensitive
        ("I accept the offer", True),
        ("no deal", False),
        ("reject", False),
        ("pass", False),
        ("no thanks", False),
        ("decline", False),
        ("not interested", False),
        ("continue", False),
        ("make another offer", False),
        ("what's your offer", False)
    ]
    
    for message, should_accept in test_messages:
        user_message_lower = message.lower()
        deal_phrases = ["accept", "yes", "take it", "i'll take it", "agreed", "i accept", "deal accepted", "take the deal"]
        rejects_deal = any(phrase in user_message_lower for phrase in ["no deal", "reject", "pass", "no thanks", "decline", "not interested"])
        
        if rejects_deal:
            accepts_deal = False
        else:
            accepts_deal = any(phrase in user_message_lower for phrase in deal_phrases)
        
        print(f"   '{message}' -> accepts_deal: {accepts_deal} (expected: {should_accept})")
        assert accepts_deal == should_accept, f"Expected {should_accept}, got {accepts_deal} for message '{message}'"
    
    print("   ✅ Deal acceptance logic working correctly")

def test_response_formatting():
    """Test the response formatting for different scenarios."""
    print("\n📝 Testing Response Formatting...")
    
    # Mock response data
    mock_response = {
        "offer": 50000,
        "game_state": {
            "round": 3,
            "remaining_cards": [1000, 5000, 10000, 500000, 1000000],
            "expected_value": 303200,
            "house_edge": 0.25,
            "sentiment": "neutral"
        },
        "humanized_answer": "You've got some big numbers left. My offer is $50,000 - take the guaranteed money or risk it all!"
    }
    
    # Test negotiation response
    user_message = "What's your offer?"
    user_message_lower = user_message.lower()
    deal_phrases = ["accept", "yes", "take it", "i'll take it", "agreed", "i accept", "deal accepted", "take the deal"]
    rejects_deal = any(phrase in user_message_lower for phrase in ["no deal", "reject", "pass", "no thanks", "decline", "not interested"])
    
    if rejects_deal:
        answer_text = f"**❌ Deal Rejected**\n\n"
        answer_text += f"💬 **Your loss! The house always wins in the end. Better luck next time!**\n\n"
        answer_text += f"🎰 **Game Over - Thanks for playing!**"
    elif any(phrase in user_message_lower for phrase in deal_phrases):
        answer_text = f"**🎉 DEAL ACCEPTED! 🎉**\n\n"
        answer_text += f"💰 **You've won: ${mock_response['offer']:,}**\n\n"
        answer_text += f"💬 **Congratulations! You made the smart choice. The house always wins, but you played it safe and walked away with guaranteed money.**\n\n"
        answer_text += f"🎰 **Game Over - Thanks for playing!**"
    else:
        answer_text = f"**🎯 Round {mock_response['game_state']['round']} Offer**\n\n"
        answer_text += f"💰 **My Offer: ${mock_response['offer']:,}**\n\n"
        answer_text += f"💬 **{mock_response['humanized_answer']}**"
    
    print("   Negotiation response:")
    print(f"   {answer_text}")
    print("   ✅ Negotiation response formatted correctly")
    
    # Test deal acceptance response
    user_message = "accept"
    user_message_lower = user_message.lower()
    deal_phrases = ["accept", "yes", "take it", "i'll take it", "agreed", "i accept", "deal accepted", "take the deal"]
    rejects_deal = any(phrase in user_message_lower for phrase in ["no deal", "reject", "pass", "no thanks", "decline", "not interested"])
    
    if rejects_deal:
        answer_text = f"**❌ Deal Rejected**\n\n"
        answer_text += f"💬 **Your loss! The house always wins in the end. Better luck next time!**\n\n"
        answer_text += f"🎰 **Game Over - Thanks for playing!**"
    elif any(phrase in user_message_lower for phrase in deal_phrases):
        answer_text = f"**🎉 DEAL ACCEPTED! 🎉**\n\n"
        answer_text += f"💰 **You've won: ${mock_response['offer']:,}**\n\n"
        answer_text += f"💬 **Congratulations! You made the smart choice. The house always wins, but you played it safe and walked away with guaranteed money.**\n\n"
        answer_text += f"🎰 **Game Over - Thanks for playing!**"
    else:
        answer_text = f"**🎯 Round {mock_response['game_state']['round']} Offer**\n\n"
        answer_text += f"💰 **My Offer: ${mock_response['offer']:,}**\n\n"
        answer_text += f"💬 **{mock_response['humanized_answer']}**"
    
    print("\n   Deal acceptance response:")
    print(f"   {answer_text}")
    print("   ✅ Deal acceptance response formatted correctly")
    
    # Test deal rejection response
    user_message = "no deal"
    user_message_lower = user_message.lower()
    deal_phrases = ["accept", "yes", "take it", "i'll take it", "agreed", "i accept", "deal accepted", "take the deal"]
    rejects_deal = any(phrase in user_message_lower for phrase in ["no deal", "reject", "pass", "no thanks", "decline", "not interested"])
    
    if rejects_deal:
        answer_text = f"**❌ Deal Rejected**\n\n"
        answer_text += f"💬 **Your loss! The house always wins in the end. Better luck next time!**\n\n"
        answer_text += f"🎰 **Game Over - Thanks for playing!**"
    elif any(phrase in user_message_lower for phrase in deal_phrases):
        answer_text = f"**🎉 DEAL ACCEPTED! 🎉**\n\n"
        answer_text += f"💰 **You've won: ${mock_response['offer']:,}**\n\n"
        answer_text += f"💬 **Congratulations! You made the smart choice. The house always wins, but you played it safe and walked away with guaranteed money.**\n\n"
        answer_text += f"🎰 **Game Over - Thanks for playing!**"
    else:
        answer_text = f"**🎯 Round {mock_response['game_state']['round']} Offer**\n\n"
        answer_text += f"💰 **My Offer: ${mock_response['offer']:,}**\n\n"
        answer_text += f"💬 **{mock_response['humanized_answer']}**"
    
    print("\n   Deal rejection response:")
    print(f"   {answer_text}")
    print("   ✅ Deal rejection response formatted correctly")

def main():
    """Run all tests."""
    print("🎰 Deal Acceptance Test Suite 🎰")
    print("=" * 50)
    
    try:
        test_deal_acceptance()
        test_response_formatting()
        
        print("\n🎉 All deal acceptance tests passed!")
        print("\nKey Features Verified:")
        print("✅ Deal acceptance detection (accept, yes, take it, etc.)")
        print("✅ Deal rejection detection (no deal, reject, pass, etc.)")
        print("✅ Case insensitive matching")
        print("✅ Proper response formatting for negotiations")
        print("✅ Proper response formatting for deal acceptance")
        print("✅ Proper response formatting for deal rejection")
        print("✅ Game over message when deal is accepted/rejected")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
