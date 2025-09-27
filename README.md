# Block Police

A blockchain investigator agent that can traverse EVM transactions, track stolen funds, and monitor blockchain activity using direct integration with Alchemy MCP server and Fetch.ai's uAgent framework.

## Features

- **Transaction Tracing**: Follow the path of funds across multiple hops to identify exit addresses
- **Account Analysis**: Get curated assessments about holdings of ENS users or addresses
- **Transaction Details**: Retrieve and analyze transaction data
- **Direct MCP Integration**: Uses Alchemy MCP server directly without custom implementation
- **Autonomous Agent Architecture**: Built on uAgents for natural language interaction

## Use Cases

- **Theft Investigation**: Trace funds stolen from ENS users through multiple hops
- **Fund Recovery**: Identify exit addresses where stolen funds are currently held
- **Monitoring**: Watch specific addresses for suspicious activity
- **Risk Assessment**: Analyze holdings and transaction patterns for risk evaluation

## How It Works

This agent uses:
- **Direct Alchemy MCP Integration**: Uses the `@alchemy/mcp-server` NPM package via the MCP client
- **No Custom API Handling**: All blockchain interactions are handled directly by the MCP server
- **Fetch.ai Agent Framework**: Provides a chat interface and discovery on Agentverse

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
   - Modify the `.env` file with your API keys:
   ```
   ALCHEMY_API_KEY=your_alchemy_api_key
   ASI_ONE_API_KEY=your_asi_one_api_key
   ```

## Usage

### Running the Block Police Agent

Start the agent:

```bash
python block_police_agent.py
```

This will launch the agent and print its address. The agent will be discoverable on Fetch.ai's Agentverse.

### Testing the Direct MCP Integration

To test the direct MCP integration:

```bash
python test_mcp_direct.py
```

### Example Queries

Using the agent via ASI:One LLM, you can make natural language queries:

- "Trace funds stolen from address 0x123... and tell me where they are now"
- "Analyze holdings for vitalik.eth"
- "Give me details about transaction 0xabc..."

### Project Structure

- `block_police_agent.py`: Main agent file with Alchemy MCP client integration
- `test_mcp_direct.py`: Simple test script for direct MCP interaction
- `.env`: Environment variables for API keys

## Configuration

The agent is configured to use the Alchemy MCP server directly, which is launched using NPX with:

```json
{
  "mcpServers": {
    "alchemy": {
      "command": "npx",
      "args": [
        "-y",
        "@alchemy/mcp-server"
      ],
      "env": {
        "ALCHEMY_API_KEY": "YOUR_API_KEY"
      }
    }
  }
}
```

## 🔗 Useful Links

- [Alchemy API Documentation](https://www.alchemy.com/docs/alchemy-mcp-server)
- [Fetch.ai uAgents](https://innovationlab.fetch.ai/resources/docs/examples/chat-protocol/asi-compatible-uagents)
- [Agentverse](https://agentverse.ai/)
- [ASI:One](https://asi1.ai/)