# Block Police

A blockchain investigator agent that can traverse EVM transactions, track stolen funds, and monitor blockchain activity using the Alchemy API and Fetch.ai's uAgent framework.

## Features

- **Transaction Tracing**: Follow the path of funds across multiple hops to identify exit addresses
- **Account Analysis**: Get curated assessments about holdings of ENS users or addresses
- **Transaction Details**: Retrieve and analyze transaction data
- **Autonomous Agent Architecture**: Built on uAgents and MCP integration for natural language interaction

## Use Cases

- **Theft Investigation**: Trace funds stolen from ENS users through multiple hops
- **Fund Recovery**: Identify exit addresses where stolen funds are currently held
- **Monitoring**: Watch specific addresses for suspicious activity
- **Risk Assessment**: Analyze holdings and transaction patterns for risk evaluation

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/block-police.git
cd block-police
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your environment variables:
   - Create or modify the `.env` file with your API keys:
   ```
   ALCHEMY_API_KEY=your_alchemy_api_key
   ASI1_API_KEY=your_asi_one_api_key
   ```

## Usage

### Running the Block Police Agent

Start the agent:

```bash
python block_police_agent.py
```

This will launch the agent and print its address. The agent will be discoverable on the Fetch.ai's Agentverse.

### Testing the Agent

Run the test suite:

```bash
python test_block_police.py
```

### Example Queries

Using the agent via ASI:One LLM, you can make natural language queries:

- "Trace funds stolen from address 0x123... and tell me where they are now"
- "Analyze holdings for vitalik.eth"
- "Give me details about transaction 0xabc..."

### Project Structure

- `block_police_agent.py`: Main agent file with MCP server implementation
- `alchemy_tools.py`: Utility functions for interacting with Alchemy API
- `test_block_police.py`: Test suite for the agent

## Integration with MeTTa Knowledge Graph

For advanced reasoning about blockchain transactions and patterns, this agent is designed to work with SingularityNET's MeTTa Knowledge Graph, allowing for:

- Sophisticated pattern recognition across transaction histories
- Complex reasoning about fund movements and wallet behaviors
- Context-aware risk assessments

## Development

### Adding New Tools

To add new blockchain investigation tools:

1. Add the method to the `AlchemyTools` class in `alchemy_tools.py`
2. Expose it via the MCP server by adding a new method to the `AlchemyMCP` class in `block_police_agent.py`
3. Add appropriate tests in `test_block_police.py`

## 🔗 Useful Links

- [Alchemy API Documentation](https://www.alchemy.com/docs/alchemy-mcp-server)
- [Fetch.ai uAgents](https://innovationlab.fetch.ai/resources/docs/examples/chat-protocol/asi-compatible-uagents)
- [Agentverse](https://agentverse.ai/)
- [ASI:One](https://asi1.ai/)
- [MeTTa Documentation](https://metta-lang.dev/docs/learn/tutorials/python_use/metta_python_basics.html)