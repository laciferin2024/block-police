from typing import Final
import os

import dotenv

dotenv.load_dotenv()

THEGRAPH_API_KEY:Final = os.getenv("THEGRAPH_API_KEY")

GRAPH_MARKET_API_KEY = os.getenv("GRAPH_MARKET_API_KEY")

GRAPH_MARKET_ACCESS_TOKEN = os.getenv("GRAPH_MARKET_ACCESS_TOKEN")



THEGRAPH_TOKEN_API_MCP:Final="https://token-api.mcp.thegraph.com/sse"
THEGRAPH_SUBGRAPH_API_MCP:Final="https://subgraphs.mcp.thegraph.com/sse"


HEDERA_PAT=os.getenv("HEDERA_PAT")
HEDERA_ACCOUNT_ID=os.getenv("HEDERA_ACCOUNT_ID")
HEDERA_PRIVATE_KEY=os.getenv("HEDERA_PRIVATE_KEY")
HEDERA_NETWORK=os.getenv("HEDERA_NETWORK", "testnet")
