# 🎰 Banker Agent - Deal-or-No-Deal Style Card Game AI

A sophisticated AI-powered banker agent that negotiates offers in a card-based money game, combining **SingularityNET's MeTTa Knowledge Graph** with **Fetch.ai's uAgents** framework to create an intelligent, autonomous negotiation system.

## 🎯 Overview

The **Banker Agent** is designed to make realistic monetary offers based on remaining game states while maintaining a **house advantage**. It uses a hybrid approach:

- **Deterministic Rules** (MeTTa): Mathematical calculations for fair offers
- **Generative AI** (LLM): Persuasive dialogue and psychological tactics

## 🏗️ Architecture

### Core Components

1. **`agent.py`**: Main uAgent implementation with Chat Protocol
2. **`metta/knowledge.py`**: MeTTa knowledge graph with banker rules
3. **`metta/banker_rag.py`**: Game state management and calculations
4. **`metta/utils.py`**: LLM integration and negotiation logic

### Technology Stack

- **MeTTa**: Knowledge graph and rules engine
- **Fetch.ai uAgents**: Agent framework
- **ASI:One API**: LLM for natural language generation
- **Agentverse**: Agent discovery and interaction

## 🧠 MeTTa Knowledge Graph

The system uses MeTTa to store structured game rules and negotiation strategies:

### House Edge Rules
```python
# Round-based multipliers
early_round (1-2): 0.65  # 35% house edge
mid_round (3-4): 0.75    # 25% house edge  
late_round (5+): 0.85    # 15% house edge
```

### Sentiment Adjustments
```python
confident: 1.05    # Slightly higher offers
desperate: 0.95    # Lower offers to exploit
aggressive: 0.90   # Significantly lower offers
neutral: 1.0       # Base offers
```

### Risk Adjustments
```python
high_variance: 0.90   # When big cards remain
low_variance: 1.05    # When mostly small cards
medium_variance: 1.0  # Balanced risk
```

## 🎮 Game State Management

The banker agent processes these inputs every round:

1. **Remaining Cards**: List of hidden card values still in play
2. **Burnt Cards**: List of revealed/discarded card values  
3. **Round Number**: Impacts aggressiveness of offers
4. **Expected Value (EV)**: Mean of remaining cards
5. **User Behavior**: Sentiment analysis of player's negotiation text
6. **Offer History**: Past offers and acceptance patterns

## 🔄 Banker Workflow

### Step 1: Deterministic Calculation (MeTTa)
```python
# Calculate base offer using rules
expected_value = sum(remaining_cards) / len(remaining_cards)
house_edge = get_house_edge_multiplier(round_num)
sentiment_mult = get_sentiment_multiplier(sentiment)
risk_adj = get_risk_adjustment(remaining_cards)

base_offer = expected_value * house_edge * sentiment_mult * risk_adj
```

### Step 2: Persuasion Layer (LLM)
```python
# Generate psychological negotiation message
context = f"""
You are the Banker AI in a high-stakes money game.
- Remaining cards: {remaining_cards}
- Expected Value: ${expected_value}
- My offer: ${base_offer}
- Player sentiment: {sentiment}

Rules:
1. Always offer less than EV
2. Use psychological pressure
3. Be witty and shrewd
4. Keep messages short (1-3 sentences)
"""
```

## 🎯 Key Features

### 1. **Dynamic Offer Calculation**
- Maintains house edge based on round progression
- Adjusts offers based on player sentiment
- Considers risk variance of remaining cards

### 2. **Psychological Negotiation**
- Witty, shrewd personality
- Uses pressure tactics appropriate to game stage
- Adapts tone based on player behavior

### 3. **Sentiment Analysis**
- Analyzes player messages for confidence/desperation
- Adjusts offers accordingly
- Maintains psychological advantage

### 4. **MeTTa Rules Engine**
- Declarative rule definitions
- Easy to modify negotiation strategies
- No need to retrain LLM for rule changes

## 🚀 Usage

### Setup

1. **Install dependencies**:
   ```bash
   uv pip install -r requirements.txt
   ```

2. **Set environment variables**:
   ```bash
   # Create .env file
   ASI_ONE_API_KEY=your_asi_one_api_key_here
   ```

3. **Run the agent**:
   ```bash
   uv run python agent.py
   ```

### Testing

Run the test suite to verify functionality:
```bash
uv run python simple_test.py
```

### Example Interactions

**Player**: "Round 1, remaining cards: [1, 5, 10, 25, 50, 100, 500, 1000, 2500, 5000, 10000, 25000, 50000, 75000, 100000, 200000, 300000, 400000, 500000, 750000, 1000000]"

**Banker**: 
```
🎯 Round 1 Offer

💰 My Offer: $2,024

💬 You've got quite the spread there. My offer is $2,024 - take the guaranteed money or risk it all for a single buck!

🧠 Psychology: The house always wins in the end.

📊 Game State:
   • Expected Value: $3,320
   • House Edge: 35.0%
   • Remaining Cards: 21 cards
   • Player Sentiment: neutral
   • Cards: [1, 5, 10, 25, 50, 100, 500, 1000, 2500, 5000, 10000, 25000, 50000, 75000, 100000, 200000, 300000, 400000, 500000, 750000, 1000000]
```

## 🧪 Test Results

The test suite verifies:
- ✅ MeTTa knowledge graph initialization
- ✅ House edge calculations (35% early, 25% mid, 15% late)
- ✅ Sentiment analysis (confident, desperate, aggressive, neutral)
- ✅ Expected value calculations
- ✅ Offer calculation with all multipliers
- ✅ House advantage maintained

## 🔧 Customization

### Modifying Banker Rules

Edit `metta/knowledge.py` to adjust:
- House edge multipliers
- Sentiment adjustments
- Risk tolerance factors
- Psychological tactics

### Changing Negotiation Style

Update `metta/utils.py` to modify:
- LLM prompts
- Response formatting
- Personality traits
- Pressure tactics

## 📊 Example Scenarios

### Early Round - Confident Player
- **Cards**: [1, 5, 10, 25, 50, 100, 500, 1000, 2500, 5000, 10000, 25000, 50000, 75000, 100000, 200000, 300000, 400000, 500000, 750000, 1000000]
- **Round**: 1
- **Sentiment**: confident
- **Expected Value**: $3,320
- **Banker Offer**: $2,024 (35% house edge)
- **Psychology**: "Tease about big cards ahead"

### Late Round - Desperate Player  
- **Cards**: [1000, 5000, 10000, 500000, 1000000]
- **Round**: 6
- **Sentiment**: desperate
- **Expected Value**: $303,200
- **Banker Offer**: $257,720 (15% house edge)
- **Psychology**: "Highlight guaranteed money vs risk"

## 🎉 Success Metrics

The banker agent successfully:
- Maintains consistent house advantage across all rounds
- Adapts offers based on player psychology
- Uses MeTTa for declarative rule management
- Generates engaging, persuasive dialogue
- Integrates seamlessly with Fetch.ai ecosystem

## 🔗 Integration

This banker agent can be integrated into:
- Card-based money games
- Deal-or-No-Deal style applications
- Negotiation training systems
- Game theory demonstrations
- AI agent marketplaces

The modular design allows easy adaptation to different game rules and negotiation styles while maintaining the core house advantage logic.
