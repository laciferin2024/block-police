# 🚨 Block Police - Blockchain Investigation Agent

A powerful blockchain investigator agent that can traverse EVM transactions, track stolen funds, and monitor blockchain activity using direct integration with Alchemy MCP server and Fetch.ai's uAgent framework.

## 🎯 Overview

The **Block Police Agent** is designed to investigate blockchain activities and trace stolen funds through multiple transaction hops. It provides:

- **Transaction Tracing**: Track funds through multiple hops to find exit addresses
- **Wallet Analysis**: Detailed reports on addresses and ENS names
- **Direct API Integration**: Zero custom code for blockchain access

## 🏗️ Architecture

### Core Components

1. **`block_police_agent.py`**: Main uAgent with Alchemy MCP client integration
2. **`test_mcp_direct.py`**: Simple test script for direct MCP interaction
3. **`.env`**: Environment variables for API keys

### Technology Stack

- **Alchemy MCP Server**: Direct blockchain data access
- **Fetch.ai uAgents**: Agent framework and protocol
- **MCP Client**: Standardized tool interaction
- **Agentverse**: Agent discovery and interaction

## 🔍 Blockchain Investigation Tools

The agent leverages direct MCP integration for powerful blockchain analysis:

### Fund Tracing
```python
# Use getAssetTransfers for fund tracing
result = await self._session.call_tool(
    "alchemy_getAssetTransfers",
    {
        "fromAddress": start_address,
        "category": ["external", "internal", "erc20", "erc721", "erc1155"],
        "maxCount": "0x" + format(hop_limit, 'x')
    }
)
```

### Wallet Analysis
```python
# Get ETH balance
balance_result = await self._session.call_tool(
    "eth_getBalance",
    [address_or_ens, "latest"]
)

# Get token balances
token_balances_result = await self._session.call_tool(
    "alchemy_getTokenBalances",
    {"address": address_or_ens}
)
```

### Transaction Details
```python
# Get transaction details
result = await self._session.call_tool(
    "eth_getTransactionByHash",
    [tx_hash]
)
```

## 🔄 Investigation Workflow

### Step 1: Direct Connection to MCP Server
```python
# Connect to Alchemy MCP server
params = mcp.StdioServerParameters(
    command="npx",
    args=["-y", "@alchemy/mcp-server"],
    env={"ALCHEMY_API_KEY": ALCHEMY_API_KEY}
)

read_stream, write_stream = await self._exit_stack.enter_async_context(
    stdio_client(params)
)

self._session = await self._exit_stack.enter_async_context(
    mcp.ClientSession(read_stream, write_stream)
)
```

### Step 2: Tool Discovery and Usage
```python
# List available blockchain tools
list_tools_result = await self._session.list_tools()
tools = list_tools_result.tools

# Dynamically find and use relevant tools
trace_tools = [tool for tool in self.tools if 'trace' in tool.name.lower()]
nft_tools = [tool for tool in self.tools if 'nft' in tool.name.lower()]
```

## 🎯 Key Features

### 1. **Direct MCP Integration**
- No custom API handling code
- Access to all Alchemy API tools
- Automatic tool discovery

### 2. **Natural Language Processing**
- Extract addresses and transaction hashes from queries
- Detect intent (tracing, holdings, transaction analysis)
- Format responses for readability

### 3. **Risk Assessment**
- Evaluates wallet value and activity
- Identifies high-value accounts
- Provides basic risk scoring

### 4. **Multi-hop Transaction Tracing**
- Follows fund movements across multiple transactions
- Identifies exit addresses
- Traces stolen funds across the blockchain

## 🚀 Usage

### Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**:
   ```bash
   # Modify .env file
   ALCHEMY_API_KEY=your_alchemy_api_key
   ASI_ONE_API_KEY=your_asi_one_api_key
   ```

3. **Run the agent**:
   ```bash
   python block_police_agent.py
   ```

### Testing

Test the direct MCP integration:
```bash
python test_mcp_direct.py
```

### Example Interactions

**User**: "Trace funds from address 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

**Agent**:
```
🔍 Fund Tracing Complete

Source Address: 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
Exit Hop Address: 0x3E3a3D69DC66bA10737F531ed088954a9EC2d8D5
Hops Traversed: 17

The funds were traced through 17 transactions to the final exit address.
This address should be monitored for further activity.

Note: For legal action, please contact relevant authorities with this information.
```

**User**: "Check holdings for vitalik.eth"

**Agent**:
```
💰 Holdings Analysis Complete

Address: vitalik.eth
ETH Balance: 1,245.782435 ETH
ERC-20 Tokens: 63 different tokens
NFTs: 31 NFTs

Risk Assessment:
High value account with significant ETH holdings.

Note: This is a preliminary assessment based on on-chain data.
```

## 🧪 Testing Capabilities

The test script verifies:
- ✅ Connection to Alchemy MCP server
- ✅ Tool discovery and listing
- ✅ ETH balance retrieval
- ✅ Token balance querying
- ✅ Server response handling

## 🔧 Configuration

The agent is configured to use the Alchemy MCP server directly:

```json
{
  "mcpServers": {
    "alchemy": {
      "command": "npx",
      "args": ["-y", "@alchemy/mcp-server"],
      "env": {
        "ALCHEMY_API_KEY": "YOUR_API_KEY"
      }
    }
  }
}
```

## 📊 Example Investigation Scenarios

### Tracing Stolen Funds
- **Start Address**: Victim's wallet address
- **Investigation**: Trace through multiple hops
- **Result**: Exit address where funds are currently held
- **Action**: Monitor exit address for off-ramping attempts

### High-Value Wallet Analysis
- **Target**: ENS name or address
- **Investigation**: Complete holdings analysis
- **Result**: ETH balance, tokens, NFTs, risk assessment
- **Action**: Identify potential high-value targets

### Transaction Analysis
- **Input**: Transaction hash
- **Investigation**: Detailed transaction examination
- **Result**: Sender, recipient, value, gas usage
- **Action**: Understand transaction purpose and context

## 🎉 Benefits

The Block Police agent provides:
- **Simplified Blockchain Investigation**: No coding required
- **Direct API Integration**: No custom API handling
- **Natural Language Interface**: Query in plain English
- **Real-Time Monitoring**: Track addresses and transactions
- **Agentverse Integration**: Easy discovery and interaction

## 🔗 Integration Options

This blockchain investigation agent can integrate with:
- Law enforcement tools
- Crypto security platforms
- Wallet monitoring services
- Security operations centers
- Fraud detection systems

The direct MCP integration makes it easy to add new tools and capabilities as they become available in the Alchemy API.

## 🔗 Useful Links

- [Alchemy API Documentation](https://www.alchemy.com/docs/alchemy-mcp-server)
- [Fetch.ai uAgents](https://innovationlab.fetch.ai/resources/docs/examples/chat-protocol/asi-compatible-uagents)
- [Agentverse](https://agentverse.ai/)
- [ASI:One](https://asi1.ai/)