"""Configuration Module

Centralized configuration for the Block Police application.
Loads and provides access to environment variables and application settings.
"""

from typing import Final, Optional, Dict, Any
import os
import logging
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

# API Keys and Authentication
ALCHEMY_API_KEY: Final[Optional[str]] = os.getenv("ALCHEMY_API_KEY")
THEGRAPH_API_KEY: Final[Optional[str]] = os.getenv("THEGRAPH_API_KEY")
GRAPH_MARKET_API_KEY: Final[Optional[str]] = os.getenv("GRAPH_MARKET_API_KEY")
GRAPH_MARKET_ACCESS_TOKEN: Final[Optional[str]] = os.getenv("GRAPH_MARKET_ACCESS_TOKEN")
ASI_ONE_API_KEY: Final[Optional[str]] = os.getenv("ASI_ONE_API_KEY")

# Hedera Configuration
HEDERA_PAT: Final[Optional[str]] = os.getenv("HEDERA_PAT")
HEDERA_ACCOUNT_ID: Final[Optional[str]] = os.getenv("HEDERA_ACCOUNT_ID")
HEDERA_PRIVATE_KEY: Final[Optional[str]] = os.getenv("HEDERA_PRIVATE_KEY")
HEDERA_NETWORK: Final[str] = os.getenv("HEDERA_NETWORK", "testnet")

# MCP Endpoints
THEGRAPH_TOKEN_API_MCP: Final[str] = os.getenv(
    "THEGRAPH_TOKEN_API_MCP",
    "https://token-api.mcp.thegraph.com/sse"
)
THEGRAPH_SUBGRAPH_API_MCP: Final[str] = os.getenv(
    "THEGRAPH_SUBGRAPH_API_MCP",
    "https://subgraphs.mcp.thegraph.com/sse"
)

# Application Settings
DEBUG_MODE: Final[bool] = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL: Final[str] = os.getenv("LOG_LEVEL", "INFO")

# Validate required configuration
REQUIRED_CONFIG = ["ALCHEMY_API_KEY"]
MISSING_CONFIG = [key for key in REQUIRED_CONFIG if not globals().get(key)]

if MISSING_CONFIG:
    logging.warning(f"Missing required configuration: {', '.join(MISSING_CONFIG)}")

def get_config() -> Dict[str, Any]:
    """Get all configuration as a dictionary"""
    return {
        "ALCHEMY_API_KEY": ALCHEMY_API_KEY,
        "THEGRAPH_API_KEY": THEGRAPH_API_KEY,
        "GRAPH_MARKET_API_KEY": GRAPH_MARKET_API_KEY,
        "GRAPH_MARKET_ACCESS_TOKEN": GRAPH_MARKET_ACCESS_TOKEN,
        "ASI_ONE_API_KEY": ASI_ONE_API_KEY,
        "HEDERA_PAT": HEDERA_PAT,
        "HEDERA_ACCOUNT_ID": HEDERA_ACCOUNT_ID,
        "HEDERA_PRIVATE_KEY": HEDERA_PRIVATE_KEY,
        "HEDERA_NETWORK": HEDERA_NETWORK,
        "THEGRAPH_TOKEN_API_MCP": THEGRAPH_TOKEN_API_MCP,
        "THEGRAPH_SUBGRAPH_API_MCP": THEGRAPH_SUBGRAPH_API_MCP,
        "DEBUG_MODE": DEBUG_MODE,
        "LOG_LEVEL": LOG_LEVEL,
    }
