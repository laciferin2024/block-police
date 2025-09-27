"""
Base MCP Client Interface

Defines the abstract base classes and interfaces for MCP clients.
"""
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Dict, Any, List, Optional, Set, Union
from contextlib import AsyncExitStack
from dataclasses import dataclass


class MCPCapability(Enum):
    """Capabilities provided by MCP clients"""

    # Blockchain data access
    ENS_RESOLUTION = auto()
    TOKEN_METADATA = auto()
    TOKEN_BALANCES = auto()
    TOKEN_TRANSFERS = auto()

    # Transaction tracing
    TRANSACTION_DETAILS = auto()
    FUND_TRACING = auto()

    # Account analysis
    ACCOUNT_HOLDINGS = auto()
    ACCOUNT_ACTIVITY = auto()

    # Chain interaction
    CALL_CONTRACT = auto()
    ESTIMATE_GAS = auto()


@dataclass
class MCPClientConfig:
    """Configuration for MCP clients"""
    name: str
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    env_vars: Optional[Dict[str, str]] = None
    command: Optional[str] = None
    args: Optional[List[str]] = None


class MCPClient(ABC):
    """Base class for all MCP clients"""

    def __init__(self, config: MCPClientConfig):
        self.config = config
        self.name = config.name
        self._exit_stack = AsyncExitStack()
        self._session = None
        self._capabilities: Set[MCPCapability] = set()
        self._tools: List[Dict[str, Any]] = []

    @property
    def capabilities(self) -> Set[MCPCapability]:
        """Get the capabilities of this MCP client"""
        return self._capabilities

    @property
    def tools(self) -> List[Dict[str, Any]]:
        """Get the available tools from this MCP client"""
        return self._tools

    def has_capability(self, capability: MCPCapability) -> bool:
        """Check if this client has a specific capability"""
        return capability in self._capabilities

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the MCP server"""
        pass

    @abstractmethod
    async def call_tool(self, tool_name: str, params: Any) -> Dict[str, Any]:
        """Call a tool on the MCP server"""
        pass

    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server"""
        pass

    async def cleanup(self):
        """Clean up resources"""
        if self._exit_stack:
            await self._exit_stack.aclose()