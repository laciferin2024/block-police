from typing import Final
import os

import dotenv

dotenv.load_dotenv()

THEGRAPH_API_KEY:Final = os.getenv("THEGRAPH_API_KEY")

GRAPH_MARKET_API_KEY = os.getenv("GRAPH_MARKET_API_KEY")

GRAPH_MARKET_ACCESS_TOKEN = os.getenv("GRAPH_MARKET_ACCESS_TOKEN")



THEGRAPH_TOKEN_API_MCP:Final="https://token-api.mcp.thegraph.com/sse"
THEGRAPH_SUBGRAPH_API_MCP:Final="https://subgraphs.mcp.thegraph.com/sse"
