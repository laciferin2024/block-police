# MCP Implementation Guide

This document outlines the steps needed to fully implement the MCP clients in the Block Police project.

## Current Status

The MCP module has been successfully refactored with:

1. A clean architecture with base classes, registry, and client implementations
2. A capability-based discovery system for finding appropriate clients
3. MeTTa integration for knowledge representation and RAG
4. Stub implementations that allow the code to compile

## Required Dependencies

For full implementation, the following dependencies need to be installed:

```
pip install mcp-client-python
```

Or add to requirements.txt:

```
mcp-client-python>=0.1.0
```

## Implementation Checklist

1. **MCP Client Library**:
   - The current implementation has stubs for `mcp.client.stdio` and `mcp.client.sse`
   - Install the proper MCP client library to enable these imports

2. **AlchemyMCPClient Implementation**:
   - Update the `connect()` method to use real `mcp.StdioServerParameters`
   - Replace stub implementations in `call_tool()` and `list_tools()` with actual calls
   - Test with a valid Alchemy API key

3. **TheGraphMCPClient Implementation**:
   - Update the `connect()` method to use real `mcp.SseServerParameters`
   - Replace stub implementations in `call_tool()` and `list_tools()` with actual calls
   - Test with a valid TheGraph Market access token

4. **MeTTa Integration**:
   - Implement actual MeTTa knowledge base integration when MeTTa library is available
   - Current implementation has a simplified version that mimics MeTTa capabilities

## Configuration

Ensure these environment variables are set in the `.env` file:

```
ALCHEMY_API_KEY=your_alchemy_api_key
GRAPH_MARKET_ACCESS_TOKEN=your_thegraph_token
THEGRAPH_API_KEY=your_thegraph_api_key
THEGRAPH_TOKEN_API_MCP=https://token-api.mcp.thegraph.com/sse
```

## Testing

Once dependencies are installed:

1. Run `uv run agent_refactored.py`
2. Test with sample blockchain queries:
   - Trace funds from an address
   - Get holdings for an address or ENS name
   - Get token metadata
   - Search for tokens

## Troubleshooting

- If clients fail to connect, check API keys and network connectivity
- For SSE connection issues, ensure the endpoint URL is correct
- For NPX execution issues, ensure Node.js is installed and NPX is available