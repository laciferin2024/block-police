"""
Block Police MCP Module

Handles the integration with different Model Context Protocol (MCP) servers
to provide blockchain investigation capabilities.
"""

from .registry import MCPRegistry, register_mcp_client
from .base import MCPClient, MCPCapability, MCPClientConfig