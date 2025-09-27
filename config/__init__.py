from typing import Final
import os

THEGRAPH_API_KEY:Final = os.getenv("THEGRAPH_API_KEY")


THEGRAPH_TOKEN_API_MCP:Final="https://token-api.mcp.thegraph.com/sse"
THEGRAPH_SUBGRAPH_API_MCP:Final="https://subgraphs.mcp.thegraph.com/sse"
