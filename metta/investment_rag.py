import re
import random
from typing import List, Dict, Any
from hyperon import MeTTa, E, S, ValueAtom

class BankerRAG:
    def __init__(self, metta_instance: MeTTa):
        self.metta = metta_instance
        self.game_state = {
            "round": 1,
            "remaining_cards": [],
            "burnt_cards": [],
            "offer_history": [],
            "user_behavior": "neutral"
        }

    def calculate_expected_value(self, remaining_cards: List[int]) -> float:
        """Calculate the expected value of remaining cards."""
        if not remaining_cards:
            return 0.0
        return sum(remaining_cards) / len(remaining_cards)

    def get_house_edge_multiplier(self, round_num: int) -> float:
        """Get house edge multiplier based on round number."""
        if round_num <= 2:
            query_str = '!(match &self (house_edge early_round $multiplier) $multiplier)'
        elif round_num <= 4:
            query_str = '!(match &self (house_edge mid_round $multiplier) $multiplier)'
        else:
            query_str = '!(match &self (house_edge late_round $multiplier) $multiplier)'
        
        results = self.metta.run(query_str)
        return float(results[0][0].get_object().value) if results and results[0] else 0.75

    def get_sentiment_multiplier(self, sentiment: str) -> float:
        """Get offer multiplier based on player sentiment."""
        sentiment = sentiment.strip('"')
        query_str = f'!(match &self (sentiment_multiplier {sentiment} $multiplier) $multiplier)'
        results = self.metta.run(query_str)
        return float(results[0][0].get_object().value) if results and results[0] else 1.0

    def get_risk_adjustment(self, remaining_cards: List[int]) -> float:
        """Get risk adjustment based on variance of remaining cards."""
        if not remaining_cards:
            return 1.0
        
        variance = max(remaining_cards) - min(remaining_cards)
        avg_value = sum(remaining_cards) / len(remaining_cards)
        
        if variance > avg_value * 2:  # High variance
            query_str = '!(match &self (risk_adjustment high_variance $adjustment) $adjustment)'
        elif variance < avg_value * 0.5:  # Low variance
            query_str = '!(match &self (risk_adjustment low_variance $adjustment) $adjustment)'
        else:  # Medium variance
            query_str = '!(match &self (risk_adjustment medium_variance $adjustment) $adjustment)'
        
        results = self.metta.run(query_str)
        return float(results[0][0].get_object().value) if results and results[0] else 1.0

    def calculate_base_offer(self, remaining_cards: List[int], round_num: int, sentiment: str) -> Dict[str, Any]:
        """Calculate the base offer using MeTTa rules."""
        expected_value = self.calculate_expected_value(remaining_cards)
        house_edge = self.get_house_edge_multiplier(round_num)
        sentiment_mult = self.get_sentiment_multiplier(sentiment)
        risk_adj = self.get_risk_adjustment(remaining_cards)
        
        # Apply all multipliers
        base_offer = expected_value * house_edge * sentiment_mult * risk_adj
        
        # Add some randomness to make offers feel more natural
        random_factor = random.uniform(0.95, 1.05)
        final_offer = int(base_offer * random_factor)
        
        return {
            "offer": final_offer,
            "expectedValue": int(expected_value),
            "houseEdge": round(1 - house_edge, 2),
            "round": round_num,
            "cardsRemaining": remaining_cards,
            "sentiment": sentiment,
            "riskAdjustment": round(risk_adj, 2)
        }

    def get_pressure_tactic(self, round_num: int) -> str:
        """Get psychological pressure tactic based on round."""
        if round_num <= 2:
            query_str = '!(match &self (pressure_tactic early_game $tactic) $tactic)'
        elif round_num <= 4:
            query_str = '!(match &self (pressure_tactic mid_game $tactic) $tactic)'
        else:
            query_str = '!(match &self (pressure_tactic late_game $tactic) $tactic)'
        
        results = self.metta.run(query_str)
        return results[0][0].get_object().value if results and results[0] else "standard pressure"

    def get_presentation_style(self, sentiment: str) -> str:
        """Get presentation style based on player sentiment."""
        sentiment = sentiment.strip('"')
        query_str = f'!(match &self (presentation_style {sentiment}_player $style) $style)'
        results = self.metta.run(query_str)
        return results[0][0].get_object().value if results and results[0] else "professional and persuasive"

    def update_game_state(self, round_num: int, remaining_cards: List[int], burnt_cards: List[int], 
                         offer: int, accepted: bool = None):
        """Update the game state with new information."""
        self.game_state["round"] = round_num
        self.game_state["remaining_cards"] = remaining_cards
        self.game_state["burnt_cards"] = burnt_cards
        self.game_state["offer_history"].append({
            "offer": offer,
            "accepted": accepted,
            "round": round_num
        })

    def analyze_user_behavior(self, user_message: str) -> str:
        """Analyze user message to determine sentiment/behavior."""
        user_message = user_message.lower()
        
        # Simple keyword-based sentiment analysis
        confident_keywords = ["confident", "sure", "definitely", "bring it on", "let's go", "i'm ready"]
        desperate_keywords = ["please", "need", "desperate", "help", "scared", "worried", "nervous"]
        aggressive_keywords = ["demand", "insist", "must", "require", "angry", "frustrated"]
        
        if any(keyword in user_message for keyword in confident_keywords):
            return "confident"
        elif any(keyword in user_message for keyword in desperate_keywords):
            return "desperate"
        elif any(keyword in user_message for keyword in aggressive_keywords):
            return "aggressive"
        else:
            return "neutral"

    def get_banker_personality_traits(self) -> Dict[str, str]:
        """Get banker personality traits from knowledge graph."""
        traits = {}
        
        # Get base tone
        query_str = '!(match &self (personality base_tone $tone) $tone)'
        results = self.metta.run(query_str)
        traits["base_tone"] = results[0][0].get_object().value if results and results[0] else "witty and shrewd"
        
        # Get negotiation style
        query_str = '!(match &self (personality negotiation_style $style) $style)'
        results = self.metta.run(query_str)
        traits["negotiation_style"] = results[0][0].get_object().value if results and results[0] else "psychological pressure"
        
        # Get risk communication
        query_str = '!(match &self (personality risk_communication $comm) $comm)'
        results = self.metta.run(query_str)
        traits["risk_communication"] = results[0][0].get_object().value if results and results[0] else "emphasize downside"
        
        return traits

    def add_knowledge(self, relation_type, subject, object_value):
        """Add new banker knowledge dynamically."""
        if isinstance(object_value, str):
            object_value = ValueAtom(object_value)
        self.metta.space().add_atom(E(S(relation_type), S(subject), object_value))
        return f"Added {relation_type}: {subject} → {object_value}"