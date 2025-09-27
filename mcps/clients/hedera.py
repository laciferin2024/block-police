"""
Hedera MCP Client

Integration with Hedera MCP server for blockchain data access and operations.
"""
import asyncio
import mcps
import mcp
from mcp.client.stdio import stdio_client, StdioServerParameters
from contextlib import AsyncExitStack
from typing import Dict, Any, List, Optional, Set
import logging

# Import centralized configuration
from config import HEDERA_ACCOUNT_ID, HEDERA_PRIVATE_KEY, HEDERA_NETWORK

from ..base import MCPClient, MCPCapability, MCPClientConfig
from ..registry import register_mcp_client


@register_mcp_client("hedera")
class HederaMCPClient(MCPClient):
    """
    Hedera MCP Client for blockchain operations.
    Uses Hedera MCP server to interact with the Hedera network.
    """

    def __init__(self, config: MCPClientConfig):
        super().__init__(config)

        # Set up capabilities for this client
        self._capabilities = {
            MCPCapability.ACCOUNT_HOLDINGS,
            MCPCapability.TOKEN_BALANCES,
            MCPCapability.TOKEN_TRANSFERS,
            MCPCapability.TOKEN_METADATA,
            MCPCapability.HEDERA_TOKEN_CREATE,
            MCPCapability.HEDERA_TOKEN_MINT,
            MCPCapability.HEDERA_TOKEN_ASSOCIATE,
            MCPCapability.HEDERA_TOKEN_TRANSFER,
            MCPCapability.HEDERA_NFT_OPERATIONS,
            MCPCapability.HEDERA_AIRDROP
        }

        # Extract Hedera configuration
        self.account_id = HEDERA_ACCOUNT_ID or ""
        self.private_key = HEDERA_PRIVATE_KEY or ""
        self.network = HEDERA_NETWORK

    async def connect(self) -> bool:
        """Connect to Hedera MCP server via local npx execution"""
        try:
            logging.info(f"Connecting to Hedera MCP server with account: {self.account_id}")

            # Use npx to run Hedera MCP server locally
            params = StdioServerParameters(
                command="npx",
                args=[
                    "-y",
                    "hedera-mcp",
                    f"--hedera_account_id={self.account_id}",
                    f"--hedera_private_key={self.private_key}",
                    f"--hedera_network={self.network}"
                ]
            )

            read_stream, write_stream = await self._exit_stack.enter_async_context(
                stdio_client(params)
            )

            self._session = await self._exit_stack.enter_async_context(
                mcps.ClientSession(read_stream, write_stream)
            )

            await self._session.initialize()

            # List available tools
            result = await self.list_tools()
            return len(result) > 0

        except Exception as e:
            logging.error(f"Failed to connect to Hedera MCP server: {e}")
            return False

    async def call_tool(self, tool_name: str, params: Any) -> Dict[str, Any]:
        """Call a tool on the Hedera MCP server"""
        if not self._session:
            raise RuntimeError("Not connected to Hedera MCP server")

        result = await self._session.call_tool(tool_name, params)

        if hasattr(result, 'content'):
            return result.content
        return {"error": "No content returned"}

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the Hedera MCP server"""
        if not self._session:
            raise RuntimeError("Not connected to Hedera MCP server")

        result = await self._session.list_tools()
        self._tools = result.tools
        return self._tools

    async def get_hbar_balance(self, account_id: str = None) -> Dict[str, Any]:
        """
        Get the HBAR balance for an account.

        Args:
            account_id: Optional account ID, uses the configured account if None

        Returns:
            Dictionary containing the HBAR balance information
        """
        account = account_id if account_id else self.account_id

        try:
            result = await self.call_tool(
                "hedera_get_hbar_balance",
                {"accountId": account}
            )

            return result
        except Exception as e:
            return {"error": f"Error getting HBAR balance: {str(e)}"}

    async def get_token_balances(self, account_id: str = None) -> Dict[str, Any]:
        """
        Get all token balances for an account.

        Args:
            account_id: Optional account ID, uses the configured account if None

        Returns:
            Dictionary containing all token balances
        """
        account = account_id if account_id else self.account_id

        try:
            result = await self.call_tool(
                "hedera_get_all_token_balances",
                {"accountId": account}
            )

            return result
        except Exception as e:
            return {"error": f"Error getting token balances: {str(e)}"}

    async def get_specific_token_balance(self, token_id: str, account_id: str = None) -> Dict[str, Any]:
        """
        Get the balance of a specific token for an account.

        Args:
            token_id: Token ID to check balance for
            account_id: Optional account ID, uses the configured account if None

        Returns:
            Dictionary containing the token balance information
        """
        account = account_id if account_id else self.account_id

        try:
            result = await self.call_tool(
                "hedera_get_hts_balance",
                {"accountId": account, "tokenId": token_id}
            )

            return result
        except Exception as e:
            return {"error": f"Error getting specific token balance: {str(e)}"}

    async def get_token_holders(self, token_id: str) -> Dict[str, Any]:
        """
        Get holders of a specific token.

        Args:
            token_id: Token ID to get holders for

        Returns:
            Dictionary containing token holder information
        """
        try:
            result = await self.call_tool(
                "hedera_get_token_holders",
                {"tokenId": token_id}
            )

            return result
        except Exception as e:
            return {"error": f"Error getting token holders: {str(e)}"}

    async def transfer_hbar(self, to_account: str, amount: float) -> Dict[str, Any]:
        """
        Transfer HBAR to another account.

        Args:
            to_account: Destination account ID
            amount: Amount of HBAR to transfer

        Returns:
            Dictionary containing the transfer result
        """
        try:
            result = await self.call_tool(
                "hedera_transfer_native_hbar_token",
                {"toAccountId": to_account, "amount": amount}
            )

            return result
        except Exception as e:
            return {"error": f"Error transferring HBAR: {str(e)}"}

    async def transfer_token(self, token_id: str, to_account: str, amount: float) -> Dict[str, Any]:
        """
        Transfer tokens to another account.

        Args:
            token_id: Token ID to transfer
            to_account: Destination account ID
            amount: Amount of tokens to transfer

        Returns:
            Dictionary containing the transfer result
        """
        try:
            result = await self.call_tool(
                "hedera_transfer_token",
                {"tokenId": token_id, "toAccountId": to_account, "amount": amount}
            )

            return result
        except Exception as e:
            return {"error": f"Error transferring token: {str(e)}"}

    async def create_fungible_token(self, name: str, symbol: str,
                                  initial_supply: int, decimals: int = 2,
                                  max_supply: int = None) -> Dict[str, Any]:
        """
        Create a new fungible token.

        Args:
            name: Token name
            symbol: Token symbol
            initial_supply: Initial supply amount
            decimals: Number of decimals (default: 2)
            max_supply: Maximum supply (default: None for unlimited)

        Returns:
            Dictionary containing the created token information
        """
        params = {
            "tokenName": name,
            "tokenSymbol": symbol,
            "initialSupply": initial_supply,
            "decimals": decimals
        }

        if max_supply is not None:
            params["maxSupply"] = max_supply

        try:
            result = await self.call_tool(
                "hedera_create_fungible_token",
                params
            )

            return result
        except Exception as e:
            return {"error": f"Error creating fungible token: {str(e)}"}

    async def mint_fungible_token(self, token_id: str, amount: int) -> Dict[str, Any]:
        """
        Mint additional fungible tokens.

        Args:
            token_id: Token ID to mint
            amount: Amount to mint

        Returns:
            Dictionary containing the minting result
        """
        try:
            result = await self.call_tool(
                "hedera_mint_fungible_token",
                {"tokenId": token_id, "amount": amount}
            )

            return result
        except Exception as e:
            return {"error": f"Error minting fungible token: {str(e)}"}

    async def create_nft(self, name: str, symbol: str,
                       max_supply: int = None) -> Dict[str, Any]:
        """
        Create a new non-fungible token collection.

        Args:
            name: NFT collection name
            symbol: NFT collection symbol
            max_supply: Maximum supply (default: None for unlimited)

        Returns:
            Dictionary containing the created NFT collection information
        """
        params = {
            "tokenName": name,
            "tokenSymbol": symbol
        }

        if max_supply is not None:
            params["maxSupply"] = max_supply

        try:
            result = await self.call_tool(
                "hedera_create_non_fungible_token",
                params
            )

            return result
        except Exception as e:
            return {"error": f"Error creating NFT collection: {str(e)}"}

    async def mint_nft(self, token_id: str, metadata: str) -> Dict[str, Any]:
        """
        Mint a new non-fungible token.

        Args:
            token_id: NFT collection ID
            metadata: Metadata for the NFT

        Returns:
            Dictionary containing the minting result
        """
        try:
            result = await self.call_tool(
                "hedera_mint_nft",
                {"tokenId": token_id, "metadata": metadata}
            )

            return result
        except Exception as e:
            return {"error": f"Error minting NFT: {str(e)}"}

    async def associate_token(self, token_id: str, account_id: str = None) -> Dict[str, Any]:
        """
        Associate a token with an account.

        Args:
            token_id: Token ID to associate
            account_id: Optional account ID, uses the configured account if None

        Returns:
            Dictionary containing the association result
        """
        account = account_id if account_id else self.account_id

        try:
            result = await self.call_tool(
                "hedera_associate_token",
                {"accountId": account, "tokenId": token_id}
            )

            return result
        except Exception as e:
            return {"error": f"Error associating token: {str(e)}"}

    async def dissociate_token(self, token_id: str, account_id: str = None) -> Dict[str, Any]:
        """
        Dissociate a token from an account.

        Args:
            token_id: Token ID to dissociate
            account_id: Optional account ID, uses the configured account if None

        Returns:
            Dictionary containing the dissociation result
        """
        account = account_id if account_id else self.account_id

        try:
            result = await self.call_tool(
                "hedera_dissociate_token",
                {"accountId": account, "tokenId": token_id}
            )

            return result
        except Exception as e:
            return {"error": f"Error dissociating token: {str(e)}"}

    async def airdrop_token(self, token_id: str, recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a token airdrop to multiple accounts.

        Args:
            token_id: Token ID to airdrop
            recipients: List of recipients with account IDs and amounts
                       Format: [{"accountId": "0.0.123", "amount": 10}, ...]

        Returns:
            Dictionary containing the airdrop result
        """
        try:
            result = await self.call_tool(
                "hedera_airdrop_token",
                {"tokenId": token_id, "recipients": recipients}
            )

            return result
        except Exception as e:
            return {"error": f"Error creating token airdrop: {str(e)}"}

    async def get_pending_airdrops(self, account_id: str = None) -> Dict[str, Any]:
        """
        Get pending airdrops for an account.

        Args:
            account_id: Optional account ID, uses the configured account if None

        Returns:
            Dictionary containing pending airdrop information
        """
        account = account_id if account_id else self.account_id

        try:
            result = await self.call_tool(
                "hedera_get_pending_airdrop",
                {"accountId": account}
            )

            return result
        except Exception as e:
            return {"error": f"Error getting pending airdrops: {str(e)}"}

    async def claim_airdrop(self, airdrop_id: str, account_id: str = None) -> Dict[str, Any]:
        """
        Claim tokens from an airdrop.

        Args:
            airdrop_id: Airdrop ID to claim
            account_id: Optional account ID, uses the configured account if None

        Returns:
            Dictionary containing the claim result
        """
        account = account_id if account_id else self.account_id

        try:
            result = await self.call_tool(
                "hedera_claim_airdrop",
                {"accountId": account, "airdropId": airdrop_id}
            )

            return result
        except Exception as e:
            return {"error": f"Error claiming airdrop: {str(e)}"}

    async def reject_token(self, token_id: str, account_id: str = None) -> Dict[str, Any]:
        """
        Reject a token sent to an account.

        Args:
            token_id: Token ID to reject
            account_id: Optional account ID, uses the configured account if None

        Returns:
            Dictionary containing the rejection result
        """
        account = account_id if account_id else self.account_id

        try:
            result = await self.call_tool(
                "hedera_reject_token",
                {"accountId": account, "tokenId": token_id}
            )

            return result
        except Exception as e:
            return {"error": f"Error rejecting token: {str(e)}"}