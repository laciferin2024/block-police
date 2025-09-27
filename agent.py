from datetime import datetime, timezone
from uuid import uuid4
from typing import Any, Dict, List, Optional
import json
import os
import re
from dotenv import load_dotenv
from uagents import Context, Model, Protocol, Agent
from hyperon import MeTTa

from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

from metta.banker_rag import BankerRAG
from metta.knowledge import initialize_banker_knowledge
from metta.utils import LLM, process_banker_query, extract_game_state_from_message

load_dotenv()

agent = Agent(name="Banker agent", port=8008, mailbox=True, publish_agent_details=True)

class GameState(Model):
    round: int
    remaining_cards: List[int]
    burnt_cards: List[int]
    user_card: Optional[int] = None

class BankerOffer(Model):
    offer: int
    expected_value: int
    house_edge: float
    round: int
    sentiment: str
    message: str
    psychology: str

def create_text_chat(text: str, end_session: bool = False) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=content,
    )

def get_default_game_state() -> Dict[str, Any]:
    """Get default game state for testing."""
    return {
        "round": 1,
        "remaining_cards": [1, 5, 10, 25, 50, 100, 500, 1000, 2500, 5000, 10000, 25000, 50000, 75000, 100000, 200000, 300000, 400000, 500000, 750000, 1000000],
        "burnt_cards": [],
        "user_card": None
    }

def parse_game_state_from_message(message: str) -> Dict[str, Any]:
    """Parse game state from user message."""
    # Try to extract from message first
    extracted_state = extract_game_state_from_message(message)
    if extracted_state:
        return extracted_state
    
    # Default game state
    return get_default_game_state()

metta = MeTTa()
initialize_banker_knowledge(metta)
rag = BankerRAG(metta)
llm = LLM(api_key=os.getenv("ASI_ONE_API_KEY"))

chat_proto = Protocol(spec=chat_protocol_spec)

@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    ctx.storage.set(str(ctx.session), sender)
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id),
    )

    for item in msg.content:
        if isinstance(item, StartSessionContent):
            ctx.logger.info(f"Got a start session message from {sender}")
            # Start directly with round 1 offer using default game state
            game_state = get_default_game_state()
            
            try:
                # Process banker query with default game state
                response = process_banker_query(
                    "start game", 
                    rag, 
                    llm,
                    game_state["remaining_cards"],
                    game_state["burnt_cards"],
                    game_state["round"]
                )
                
                # Format response for negotiation
                if isinstance(response, dict):
                    answer_text = f"**🎯 Round {response['game_state']['round']} Offer**\n\n"
                    answer_text += f"💰 **My Offer: ${response['offer']:,}**\n\n"
                    answer_text += f"💬 **{response['humanized_answer']}**"
                else:
                    answer_text = str(response)
                
                await ctx.send(sender, create_text_chat(answer_text))
                
            except Exception as e:
                ctx.logger.error(f"Error processing initial banker query: {e}")
                await ctx.send(
                    sender, 
                    create_text_chat("I apologize, but I encountered an error starting the game. Please try again.")
                )
            continue
        elif isinstance(item, TextContent):
            user_message = item.text.strip()
            ctx.logger.info(f"Got a banker query from {sender}: {user_message}")
            
            try:
                # Parse game state from message
                game_state = parse_game_state_from_message(user_message)
                
                # Process banker query
                response = process_banker_query(
                    user_message, 
                    rag, 
                    llm,
                    game_state["remaining_cards"],
                    game_state["burnt_cards"],
                    game_state["round"]
                )
                
                # Check if player accepted the deal
                user_message_lower = user_message.lower()
                # More precise deal acceptance detection
                deal_phrases = ["accept", "yes", "take it", "i'll take it", "agreed", "i accept", "deal accepted", "take the deal"]
                rejects_deal = any(phrase in user_message_lower for phrase in ["no deal", "reject", "pass", "no thanks", "decline", "not interested"])
                
                if rejects_deal:
                    # Player explicitly rejected
                    answer_text = f"**❌ Deal Rejected**\n\n"
                    answer_text += f"💬 **Your loss! The house always wins in the end. Better luck next time!**\n\n"
                    answer_text += f"🎰 **Game Over - Thanks for playing!**"
                elif any(phrase in user_message_lower for phrase in deal_phrases):
                    answer_text = f"**🎉 DEAL ACCEPTED! 🎉**\n\n"
                    answer_text += f"💰 **You've won: ${response['offer']:,}**\n\n"
                    answer_text += f"💬 **Congratulations! You made the smart choice. The house always wins, but you played it safe and walked away with guaranteed money.**\n\n"
                    answer_text += f"🎰 **Game Over - Thanks for playing!**"
                else:
                    # Format response for negotiation
                    if isinstance(response, dict):
                        answer_text = f"**🎯 Round {response['game_state']['round']} Offer**\n\n"
                        answer_text += f"💰 **My Offer: ${response['offer']:,}**\n\n"
                        answer_text += f"💬 **{response['humanized_answer']}**"
                    else:
                        answer_text = str(response)
                
                await ctx.send(sender, create_text_chat(answer_text))
                
            except Exception as e:
                ctx.logger.error(f"Error processing banker query: {e}")
                await ctx.send(
                    sender, 
                    create_text_chat("I apologize, but I encountered an error processing your request. Please try again with a clear game state description.")
                )
        else:
            ctx.logger.info(f"Got unexpected content from {sender}")

@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Got an acknowledgement from {sender} for {msg.acknowledged_msg_id}")

agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run()