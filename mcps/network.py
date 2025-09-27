"""
Network Utility Module

Provides utilities for managing and distinguishing between blockchain networks.
"""
from enum import Enum
from typing import Dict, Any, Optional, List


class NetworkType(Enum):
    """Enum for different blockchain network types"""
    EVM = "evm"  # Ethereum Virtual Machine compatible
    HEDERA = "hedera"  # Hedera Hashgraph
    SOLANA = "solana"  # Solana
    NEAR = "near"  # NEAR Protocol
    OTHER = "other"  # Other blockchain types


class EVMNetwork(Enum):
    """Enum for different EVM networks"""
    ETHEREUM_MAINNET = "ethereum"
    ETHEREUM_GOERLI = "goerli"
    ETHEREUM_SEPOLIA = "sepolia"
    POLYGON_MAINNET = "polygon"
    POLYGON_MUMBAI = "polygon-mumbai"
    ARBITRUM_ONE = "arbitrum"
    ARBITRUM_NOVA = "arbitrum-nova"
    OPTIMISM = "optimism"
    AVALANCHE_C = "avalanche"
    BSC = "bsc"  # Binance Smart Chain
    BASE = "base"
    FANTOM = "fantom"
    CRONOS = "cronos"
    GNOSIS = "gnosis"  # formerly xDai
    CELO = "celo"


class HederaNetwork(Enum):
    """Enum for Hedera networks"""
    MAINNET = "mainnet"
    TESTNET = "testnet"
    PREVIEWNET = "previewnet"


class NetworkManager:
    """
    Manages network identification and selection for blockchain operations.
    """

    def __init__(self):
        # Default network settings
        self.default_evm_network = EVMNetwork.ETHEREUM_MAINNET
        self.default_hedera_network = HederaNetwork.TESTNET

        # Network name mappings for natural language processing
        self.network_aliases = {
            # Ethereum aliases
            "eth": EVMNetwork.ETHEREUM_MAINNET,
            "ethereum": EVMNetwork.ETHEREUM_MAINNET,
            "mainnet": EVMNetwork.ETHEREUM_MAINNET,
            "goerli": EVMNetwork.ETHEREUM_GOERLI,
            "sepolia": EVMNetwork.ETHEREUM_SEPOLIA,

            # Polygon aliases
            "polygon": EVMNetwork.POLYGON_MAINNET,
            "matic": EVMNetwork.POLYGON_MAINNET,
            "polygon-mumbai": EVMNetwork.POLYGON_MUMBAI,
            "mumbai": EVMNetwork.POLYGON_MUMBAI,

            # Arbitrum aliases
            "arbitrum": EVMNetwork.ARBITRUM_ONE,
            "arbitrum-one": EVMNetwork.ARBITRUM_ONE,
            "arbitrum-nova": EVMNetwork.ARBITRUM_NOVA,
            "nova": EVMNetwork.ARBITRUM_NOVA,

            # Other EVM chains
            "optimism": EVMNetwork.OPTIMISM,
            "op": EVMNetwork.OPTIMISM,
            "avalanche": EVMNetwork.AVALANCHE_C,
            "avax": EVMNetwork.AVALANCHE_C,
            "bsc": EVMNetwork.BSC,
            "binance": EVMNetwork.BSC,
            "base": EVMNetwork.BASE,
            "fantom": EVMNetwork.FANTOM,
            "ftm": EVMNetwork.FANTOM,
            "cronos": EVMNetwork.CRONOS,
            "cro": EVMNetwork.CRONOS,
            "gnosis": EVMNetwork.GNOSIS,
            "xdai": EVMNetwork.GNOSIS,
            "celo": EVMNetwork.CELO,

            # Hedera aliases
            "hedera-mainnet": HederaNetwork.MAINNET,
            "hedera-testnet": HederaNetwork.TESTNET,
            "hedera-previewnet": HederaNetwork.PREVIEWNET
        }

    def identify_network_from_query(self, query: str) -> Dict[str, Any]:
        """
        Identify blockchain network from a natural language query.

        Args:
            query: User's natural language query

        Returns:
            Dictionary with identified network type and network name
        """
        query_lower = query.lower()
        network_info = {
            "network_type": NetworkType.EVM,
            "network": self.default_evm_network
        }

        # Check for Hedera mentions
        if any(word in query_lower for word in ["hedera", "hbar"]):
            network_info["network_type"] = NetworkType.HEDERA
            network_info["network"] = self.default_hedera_network

        # Check for specific network mentions
        for alias, network in self.network_aliases.items():
            if f" {alias} " in f" {query_lower} " or f"on {alias}" in query_lower:
                if isinstance(network, EVMNetwork):
                    network_info["network_type"] = NetworkType.EVM
                    network_info["network"] = network
                elif isinstance(network, HederaNetwork):
                    network_info["network_type"] = NetworkType.HEDERA
                    network_info["network"] = network

        return network_info

    def get_network_config(self, network_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get configuration details for a specific network.

        Args:
            network_info: Dictionary with network_type and network

        Returns:
            Dictionary with network configuration details
        """
        network_type = network_info.get("network_type", NetworkType.EVM)
        network = network_info.get("network", self.default_evm_network)

        if network_type == NetworkType.EVM:
            if isinstance(network, str):
                for enum_val in EVMNetwork:
                    if enum_val.value == network:
                        network = enum_val
                        break

            config = {
                "name": network.value if isinstance(network, EVMNetwork) else str(network),
                "type": "evm",
                "chain_id": self._get_evm_chain_id(network),
                "explorer_url": self._get_explorer_url(network),
                "rpc_url": None  # This would be populated from configuration or environment variables
            }

        elif network_type == NetworkType.HEDERA:
            if isinstance(network, str):
                for enum_val in HederaNetwork:
                    if enum_val.value == network:
                        network = enum_val
                        break

            config = {
                "name": network.value if isinstance(network, HederaNetwork) else str(network),
                "type": "hedera",
                "mirror_node": self._get_hedera_mirror_node(network),
                "explorer_url": self._get_hedera_explorer_url(network)
            }

        else:
            config = {
                "name": "unknown",
                "type": "unknown"
            }

        return config

    def _get_evm_chain_id(self, network: EVMNetwork) -> int:
        """Get the chain ID for an EVM network"""
        chain_ids = {
            EVMNetwork.ETHEREUM_MAINNET: 1,
            EVMNetwork.ETHEREUM_GOERLI: 5,
            EVMNetwork.ETHEREUM_SEPOLIA: 11155111,
            EVMNetwork.POLYGON_MAINNET: 137,
            EVMNetwork.POLYGON_MUMBAI: 80001,
            EVMNetwork.ARBITRUM_ONE: 42161,
            EVMNetwork.ARBITRUM_NOVA: 42170,
            EVMNetwork.OPTIMISM: 10,
            EVMNetwork.AVALANCHE_C: 43114,
            EVMNetwork.BSC: 56,
            EVMNetwork.BASE: 8453,
            EVMNetwork.FANTOM: 250,
            EVMNetwork.CRONOS: 25,
            EVMNetwork.GNOSIS: 100,
            EVMNetwork.CELO: 42220
        }
        return chain_ids.get(network, 1)  # Default to Ethereum mainnet

    def _get_explorer_url(self, network: EVMNetwork) -> str:
        """Get block explorer URL for an EVM network"""
        explorers = {
            EVMNetwork.ETHEREUM_MAINNET: "https://etherscan.io",
            EVMNetwork.ETHEREUM_GOERLI: "https://goerli.etherscan.io",
            EVMNetwork.ETHEREUM_SEPOLIA: "https://sepolia.etherscan.io",
            EVMNetwork.POLYGON_MAINNET: "https://polygonscan.com",
            EVMNetwork.POLYGON_MUMBAI: "https://mumbai.polygonscan.com",
            EVMNetwork.ARBITRUM_ONE: "https://arbiscan.io",
            EVMNetwork.ARBITRUM_NOVA: "https://nova.arbiscan.io",
            EVMNetwork.OPTIMISM: "https://optimistic.etherscan.io",
            EVMNetwork.AVALANCHE_C: "https://snowtrace.io",
            EVMNetwork.BSC: "https://bscscan.com",
            EVMNetwork.BASE: "https://basescan.org",
            EVMNetwork.FANTOM: "https://ftmscan.com",
            EVMNetwork.CRONOS: "https://cronoscan.com",
            EVMNetwork.GNOSIS: "https://gnosisscan.io",
            EVMNetwork.CELO: "https://celoscan.io"
        }
        return explorers.get(network, "https://etherscan.io")  # Default to Etherscan

    def _get_hedera_mirror_node(self, network: HederaNetwork) -> str:
        """Get mirror node URL for a Hedera network"""
        mirror_nodes = {
            HederaNetwork.MAINNET: "https://mainnet-public.mirrornode.hedera.com",
            HederaNetwork.TESTNET: "https://testnet.mirrornode.hedera.com",
            HederaNetwork.PREVIEWNET: "https://previewnet.mirrornode.hedera.com"
        }
        return mirror_nodes.get(network, "https://testnet.mirrornode.hedera.com")

    def _get_hedera_explorer_url(self, network: HederaNetwork) -> str:
        """Get explorer URL for a Hedera network"""
        explorers = {
            HederaNetwork.MAINNET: "https://hashscan.io/mainnet",
            HederaNetwork.TESTNET: "https://hashscan.io/testnet",
            HederaNetwork.PREVIEWNET: "https://hashscan.io/previewnet"
        }
        return explorers.get(network, "https://hashscan.io/testnet")

    def format_network_name(self, network: Any) -> str:
        """Convert network to a user-friendly display name"""
        if isinstance(network, EVMNetwork):
            network_names = {
                EVMNetwork.ETHEREUM_MAINNET: "Ethereum",
                EVMNetwork.ETHEREUM_GOERLI: "Ethereum Goerli",
                EVMNetwork.ETHEREUM_SEPOLIA: "Ethereum Sepolia",
                EVMNetwork.POLYGON_MAINNET: "Polygon",
                EVMNetwork.POLYGON_MUMBAI: "Polygon Mumbai",
                EVMNetwork.ARBITRUM_ONE: "Arbitrum One",
                EVMNetwork.ARBITRUM_NOVA: "Arbitrum Nova",
                EVMNetwork.OPTIMISM: "Optimism",
                EVMNetwork.AVALANCHE_C: "Avalanche C-Chain",
                EVMNetwork.BSC: "BNB Smart Chain",
                EVMNetwork.BASE: "Base",
                EVMNetwork.FANTOM: "Fantom",
                EVMNetwork.CRONOS: "Cronos",
                EVMNetwork.GNOSIS: "Gnosis Chain",
                EVMNetwork.CELO: "Celo"
            }
            return network_names.get(network, "Unknown EVM Network")

        elif isinstance(network, HederaNetwork):
            network_names = {
                HederaNetwork.MAINNET: "Hedera Mainnet",
                HederaNetwork.TESTNET: "Hedera Testnet",
                HederaNetwork.PREVIEWNET: "Hedera Previewnet"
            }
            return network_names.get(network, "Unknown Hedera Network")

        elif isinstance(network, str):
            # Try to convert string to enum
            for evm_net in EVMNetwork:
                if evm_net.value == network:
                    return self.format_network_name(evm_net)

            for hedera_net in HederaNetwork:
                if hedera_net.value == network:
                    return self.format_network_name(hedera_net)

            return network.title()  # Capitalize the string

        return "Unknown Network"


# Create a singleton instance
network_manager = NetworkManager()