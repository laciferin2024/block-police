"""
MCP Client Registry

Manages the registration and discovery of MCP clients.
"""
import logging
from typing import Dict, Any, List, Callable, Optional, Set, Type
from .base import MCPClient, MCPCapability, MCPClientConfig


class MCPRegistry:
    """Registry for MCP clients"""

    _instance = None
    _clients: Dict[str, MCPClient] = {}
    _client_factories: Dict[str, Callable[..., MCPClient]] = {}

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super(MCPRegistry, cls).__new__(cls)
        return cls._instance

    def register_client(self, client: MCPClient) -> None:
        """Register an MCP client instance"""
        self._clients[client.name] = client
        logging.info(f"Registered MCP client: {client.name}")

    def register_client_factory(self,
                               client_type: str,
                               factory: Callable[..., MCPClient]) -> None:
        """Register a factory function for creating MCP clients"""
        self._client_factories[client_type] = factory
        logging.info(f"Registered MCP client factory for type: {client_type}")

    def get_client(self, name: str) -> Optional[MCPClient]:
        """Get a registered MCP client by name"""
        return self._clients.get(name)

    def create_client(self, client_type: str, config: MCPClientConfig) -> Optional[MCPClient]:
        """Create a new MCP client using registered factory"""
        factory = self._client_factories.get(client_type)
        if not factory:
            logging.error(f"No factory registered for client type: {client_type}")
            return None

        try:
            client = factory(config)
            self.register_client(client)
            return client
        except Exception as e:
            logging.error(f"Failed to create MCP client: {str(e)}")
            return None

    def get_all_clients(self) -> List[MCPClient]:
        """Get all registered MCP clients"""
        return list(self._clients.values())

    def find_clients_with_capability(self, capability: MCPCapability) -> List[MCPClient]:
        """Find all MCP clients that have a specific capability"""
        return [client for client in self._clients.values()
                if client.has_capability(capability)]

    def find_best_client_for_capability(self, capability: MCPCapability) -> Optional[MCPClient]:
        """Find the best MCP client for a specific capability"""
        # Simple implementation - just return the first client with the capability
        clients = self.find_clients_with_capability(capability)
        return clients[0] if clients else None


def register_mcp_client(client_type: str):
    """Decorator for registering MCP client factories"""
    def decorator(cls: Type[MCPClient]):
        registry = MCPRegistry()
        registry.register_client_factory(client_type, cls)
        return cls
    return decorator