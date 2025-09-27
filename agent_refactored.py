"""
Block Police Agent

Blockchain investigator agent that can trace EVM transactions,
analyze wallets, and provide insights using MCP servers.
"""
import os
import asyncio
import json
import time
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from uuid import uuid4
from uagents import Agent, Context, Protocol
from contextlib import AsyncExitStack
import mcps
from dotenv import load_dotenv
from tools import get_registered_tools

# Import MCP client registry and capabilities
from mcps import MCPRegistry, MCPCapability, MCPClientConfig
from mcps.clients.alchemy import AlchemyMCPClient
from mcps.clients.thegraph import TheGraphMCPClient
from mcps.metta.rag import MeTTaRAG
from mcps.metta.knowledge_base import MeTTaKnowledgeBase

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("block_police")

# Check for required API keys
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
GRAPH_MARKET_ACCESS_TOKEN = os.getenv("GRAPH_MARKET_ACCESS_TOKEN")
ASI_ONE_API_KEY = os.getenv("ASI_ONE_API_KEY")
THEGRAPH_API_KEY = os.getenv("THEGRAPH_API_KEY")

if not ALCHEMY_API_KEY:
    raise ValueError("ALCHEMY_API_KEY not found in .env file")


# --- MCP Manager Implementation ---
class MCPManager:
    """
    MCP Manager for blockchain investigation.
    Manages multiple MCP clients and coordinates interactions.
    """

    def __init__(self, ctx: Context):
        self._ctx = ctx
        self.registry = MCPRegistry()
        self.rag_engine = None
        self._initialized = False

    async def initialize(self):
        """Initialize and connect all MCP clients"""
        if self._initialized:
            return True

        # Register and connect Alchemy client
        await self._setup_alchemy_client()

        # Register and connect TheGraph client if API key available
        if GRAPH_MARKET_ACCESS_TOKEN:
            await self._setup_thegraph_client()

        # Initialize RAG engine
        self.rag_engine = MeTTaRAG(MeTTaKnowledgeBase())

        self._initialized = True
        return True

    async def _setup_alchemy_client(self):
        """Set up and connect to Alchemy MCP server"""
        self._ctx.logger.info("Setting up Alchemy MCP client...")

        # Create and register Alchemy client
        alchemy_config = MCPClientConfig(
            name="alchemy",
            api_key=ALCHEMY_API_KEY,
            command="npx",
            args=["-y", "@alchemy/mcp-server"],
            env_vars={"ALCHEMY_API_KEY": ALCHEMY_API_KEY}
        )

        # Create client through registry
        alchemy_client = self.registry.create_client("alchemy", alchemy_config)

        if not alchemy_client:
            self._ctx.logger.error("Failed to create Alchemy MCP client")
            return False

        # Connect to Alchemy MCP server
        try:
            success = await alchemy_client.connect()
            if success:
                self._ctx.logger.info("Connected to Alchemy MCP server")
                return True
            else:
                self._ctx.logger.error("Failed to connect to Alchemy MCP server")
                return False
        except Exception as e:
            self._ctx.logger.error(f"Error connecting to Alchemy MCP server: {e}")
            return False

    async def _setup_thegraph_client(self):
        """Set up and connect to TheGraph Token API MCP server"""
        self._ctx.logger.info("Setting up TheGraph MCP client...")

        # Create and register TheGraph client
        thegraph_config = MCPClientConfig(
            name="thegraph",
            api_key=GRAPH_MARKET_ACCESS_TOKEN,
            endpoint=os.getenv("THEGRAPH_TOKEN_API_MCP",
                              "https://token-api.mcp.thegraph.com/sse")
        )

        # Create client through registry
        thegraph_client = self.registry.create_client("thegraph", thegraph_config)

        if not thegraph_client:
            self._ctx.logger.error("Failed to create TheGraph MCP client")
            return False

        # Connect to TheGraph MCP server
        try:
            success = await thegraph_client.connect()
            if success:
                self._ctx.logger.info("Connected to TheGraph MCP server")
                return True
            else:
                self._ctx.logger.error("Failed to connect to TheGraph MCP server")
                return False
        except Exception as e:
            self._ctx.logger.error(f"Error connecting to TheGraph MCP server: {e}")
            return False

    async def resolve_ens_to_address(self, ens_name: str) -> str:
        """
        Resolve ENS name to address using all available clients
        Returns the original name if resolution fails
        """
        # Check if any client has ENS_RESOLUTION capability
        clients = self.registry.find_clients_with_capability(MCPCapability.ENS_RESOLUTION)

        if not clients:
            self._ctx.logger.warning("No clients available with ENS resolution capability")
            return ens_name

        # Try each client in sequence
        for client in clients:
            try:
                if hasattr(client, "resolve_ens_to_address"):
                    result = await client.resolve_ens_to_address(ens_name)
                    if result != ens_name:
                        self._ctx.logger.info(f"Resolved {ens_name} to {result} using {client.name}")
                        return result
            except Exception as e:
                self._ctx.logger.error(f"Error resolving ENS with {client.name}: {e}")
                continue

        # If all resolution methods fail, return the original ENS name
        self._ctx.logger.warning(f"Failed to resolve {ens_name} with any client")
        return ens_name

    async def trace_evm_funds(self, start_address: str, hop_limit: int = 100) -> Dict[str, Any]:
        """
        Traces the path of funds across EVM transactions, hop by hop.
        Uses MCP client with FUND_TRACING capability.
        """
        # Resolve ENS if needed
        address = await self.resolve_ens_to_address(start_address)

        # Find clients with FUND_TRACING capability
        clients = self.registry.find_clients_with_capability(MCPCapability.FUND_TRACING)

        if not clients:
            return {"error": "No clients available with fund tracing capability",
                   "source_address": start_address}

        # Use the first available client
        client = clients[0]

        try:
            if hasattr(client, "trace_evm_funds"):
                result = await client.trace_evm_funds(address, hop_limit)
                return result
            else:
                return {"error": "Client does not support trace_evm_funds method",
                       "source_address": start_address}
        except Exception as e:
            self._ctx.logger.error(f"Error tracing funds: {e}")
            return {"error": f"Error tracing funds: {str(e)}",
                   "source_address": start_address}

    async def get_curated_holdings(self, address_or_ens: str) -> Dict[str, Any]:
        """
        Retrieves a multi-chain assessment of crypto holdings for an address or ENS.
        Uses MCP client with ACCOUNT_HOLDINGS capability.
        """
        # Resolve ENS if needed
        address = await self.resolve_ens_to_address(address_or_ens)

        # Find clients with ACCOUNT_HOLDINGS capability
        clients = self.registry.find_clients_with_capability(MCPCapability.ACCOUNT_HOLDINGS)

        if not clients:
            return {"error": "No clients available with holdings capability",
                   "address": address_or_ens}

        # Use the first available client
        client = clients[0]

        try:
            if hasattr(client, "get_curated_holdings"):
                result = await client.get_curated_holdings(address)
                return result
            else:
                return {"error": "Client does not support get_curated_holdings method",
                       "address": address_or_ens}
        except Exception as e:
            self._ctx.logger.error(f"Error getting holdings: {e}")
            return {"error": f"Failed to fetch holdings for {address_or_ens}: {str(e)}"}

    async def get_token_metadata(self, address: str, chain: str = "ethereum") -> Dict[str, Any]:
        """Get token metadata using TheGraph Token API"""
        clients = self.registry.find_clients_with_capability(MCPCapability.TOKEN_METADATA)

        if not clients:
            return {"error": "No clients available with token metadata capability"}

        for client in clients:
            try:
                if hasattr(client, "get_token_metadata"):
                    result = await client.get_token_metadata(address, chain)
                    if result and not result.get("error"):
                        return result
            except Exception as e:
                self._ctx.logger.error(f"Error getting token metadata with {client.name}: {e}")
                continue

        return {"error": "Failed to get token metadata from any client"}

    async def get_token_holders(self, address: str, limit: int = 10,
                              chain: str = "ethereum") -> Dict[str, Any]:
        """Get token holders using TheGraph Token API"""
        clients = self.registry.find_clients_with_capability(MCPCapability.TOKEN_BALANCES)

        if not clients:
            return {"error": "No clients available with token balances capability"}

        for client in clients:
            try:
                if hasattr(client, "get_token_holders"):
                    result = await client.get_token_holders(address, limit, chain)
                    if result and not result.get("error"):
                        return result
            except Exception as e:
                self._ctx.logger.error(f"Error getting token holders with {client.name}: {e}")
                continue

        return {"error": "Failed to get token holders from any client"}

    async def get_token_transfers(self, address: str, limit: int = 10,
                               chain: str = "ethereum") -> Dict[str, Any]:
        """Get token transfers using TheGraph Token API"""
        clients = self.registry.find_clients_with_capability(MCPCapability.TOKEN_TRANSFERS)

        if not clients:
            return {"error": "No clients available with token transfers capability"}

        for client in clients:
            try:
                if hasattr(client, "get_token_transfers"):
                    result = await client.get_token_transfers(address, limit, chain)
                    if result and not result.get("error"):
                        return result
            except Exception as e:
                self._ctx.logger.error(f"Error getting token transfers with {client.name}: {e}")
                continue

        return {"error": "Failed to get token transfers from any client"}

    async def search_tokens(self, query: str, limit: int = 10,
                         chain: str = "ethereum") -> Dict[str, Any]:
        """Search for tokens using TheGraph Token API"""
        # Find clients with TOKEN_METADATA capability (which can search tokens)
        clients = self.registry.find_clients_with_capability(MCPCapability.TOKEN_METADATA)

        if not clients:
            return {"error": "No clients available with token search capability"}

        for client in clients:
            try:
                if hasattr(client, "search_tokens"):
                    result = await client.search_tokens(query, limit, chain)
                    if result and not result.get("error"):
                        return result
            except Exception as e:
                self._ctx.logger.error(f"Error searching tokens with {client.name}: {e}")
                continue

        return {"error": "Failed to search tokens with any client"}

    async def query_with_rag(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Query the RAG engine for intelligent insights"""
        if not self.rag_engine:
            return {"error": "RAG engine not initialized"}

        try:
            result = await self.rag_engine.query(query, context)
            return result
        except Exception as e:
            self._ctx.logger.error(f"Error querying RAG engine: {e}")
            return {"error": f"Failed to query RAG engine: {str(e)}"}

    async def cleanup(self):
        """Clean up all MCP clients"""
        clients = self.registry.get_all_clients()

        for client in clients:
            try:
                await client.cleanup()
            except Exception as e:
                self._ctx.logger.error(f"Error cleaning up {client.name}: {e}")


# --- Chat Protocol Setup ---
from uagents_core.contrib.protocols.chat import (
    chat_protocol_spec,
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
    EndSessionContent,
    StartSessionContent,
)

# User sessions store: session_id -> {mcp_manager, last_activity}
user_sessions = {}

# Session timeout (30 minutes)
SESSION_TIMEOUT = 30 * 60

# --- Agent Setup ---
chat_proto = Protocol(spec=chat_protocol_spec)
agent = Agent(name="block_police_agent", port=8002, mailbox=True)

def create_text_chat(text: str, end_session: bool = False) -> ChatMessage:
    """Helper to create a chat message with text content"""
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=content,
    )

def is_session_valid(session_id: str) -> bool:
    """Check if session is valid and hasn't expired"""
    if session_id not in user_sessions:
        return False

    last_activity = user_sessions[session_id].get('last_activity', 0)
    if time.time() - last_activity > SESSION_TIMEOUT:
        # Session expired, clean it up
        if session_id in user_sessions:
            del user_sessions[session_id]
        return False

    return True

async def get_mcp_manager(ctx: Context, session_id: str) -> MCPManager:
    """Get or create MCP Manager for session"""
    if session_id not in user_sessions or not is_session_valid(session_id):
        # Create new manager
        manager = MCPManager(ctx)
        await manager.initialize()
        user_sessions[session_id] = {
            'manager': manager,
            'last_activity': time.time()
        }

    return user_sessions[session_id]['manager']

@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming chat messages"""
    session_id = str(ctx.session)

    # Send acknowledgment first
    ack_msg = ChatAcknowledgement(
        timestamp=datetime.now(timezone.utc),
        acknowledged_msg_id=msg.msg_id
    )
    await ctx.send(sender, ack_msg)

    for item in msg.content:
        if isinstance(item, StartSessionContent):
            ctx.logger.info(f"Starting session with {sender}")

            welcome_message = """🚨 **Block Police Blockchain Investigator** 🚨

I can help you investigate blockchain transactions, trace funds, and analyze wallets.

**Available commands:**
- Trace funds from an address
- Get holdings for an address or ENS name
- Get transaction details
- Get ENS domain details
- Get ENS domain events history
- Get token metadata
- Get token holders
- Get token transfers
- Search for tokens
- Monitor suspicious activities

How can I assist with your blockchain investigation today?"""

            await ctx.send(sender, create_text_chat(welcome_message))

        elif isinstance(item, TextContent):
            ctx.logger.info(f"Received message from {sender}: '{item.text}'")

            # Update session activity
            if session_id in user_sessions:
                user_sessions[session_id]['last_activity'] = time.time()

            query = item.text.strip()

            # Show processing message
            processing_msg = create_text_chat("🔍 Processing your blockchain investigation request...")
            await ctx.send(sender, processing_msg)

            try:
                # Get MCP manager for this session
                manager = await get_mcp_manager(ctx, session_id)

                # Process based on query content
                response_text = await process_blockchain_query(ctx, manager, query)

            except Exception as e:
                ctx.logger.error(f"Error processing query: {e}")
                response_text = f"""❌ **Error investigating blockchain**

Something went wrong: {str(e)}

Please try a different query or check your input format."""

            # Send response
            await ctx.send(sender, create_text_chat(response_text))

@chat_proto.on_message(ChatAcknowledgement)
async def handle_chat_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handle chat acknowledgements"""
    pass

async def process_blockchain_query(ctx: Context, manager: MCPManager, query: str) -> str:
    """Process blockchain investigation query"""
    query_lower = query.lower()

    # Optionally use RAG for more complex queries
    rag_context = {"query": query}
    rag_result = await manager.query_with_rag(query, rag_context)

    # Check for token metadata queries
    if any(phrase in query_lower for phrase in ['token info', 'token metadata', 'token details']):
        import re
        address_match = re.search(r'0x[a-fA-F0-9]{40}', query)

        if address_match:
            address = address_match.group(0)
            ctx.logger.info(f"Detected token metadata request for: {address}")

            # Extract chain if specified
            chain = "ethereum"
            if "polygon" in query_lower or "matic" in query_lower:
                chain = "polygon"
            elif "arbitrum" in query_lower:
                chain = "arbitrum"

            try:
                metadata = await manager.get_token_metadata(address, chain)

                if isinstance(metadata, dict) and "error" in metadata:
                    return f"""❌ **Token Metadata Failed**

Unable to get metadata for {address}:
{metadata.get('error', 'Unknown error')}

Please verify the token address is correct and try again."""

                return f"""📊 **Token Metadata**

**Name:** {metadata.get('name', 'Unknown')}
**Symbol:** {metadata.get('symbol', 'Unknown')}
**Decimals:** {metadata.get('decimals', 'Unknown')}
**Total Supply:** {metadata.get('totalSupply', 'Unknown')}
**Chain:** {chain}
**Contract:** {address}

*This data is provided by TheGraph Token API.*"""

            except Exception as e:
                ctx.logger.error(f"Error getting token metadata: {e}")
                return f"""❌ **Token Metadata Failed**

Encountered an error while fetching metadata for {address}:
{str(e)}

Please try again later."""

        else:
            return """⚠️ **Token Address Not Detected**

I need a valid token contract address to check token details.
Please provide a query with a valid token address (0x...).

Example: "Get token details for 0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984\""""

    # Check for token holders queries
    elif any(phrase in query_lower for phrase in ['token holders', 'who owns', 'token owners', 'holder list']):
        import re
        address_match = re.search(r'0x[a-fA-F0-9]{40}', query)

        if address_match:
            address = address_match.group(0)
            ctx.logger.info(f"Detected token holders request for: {address}")

            # Extract chain if specified
            chain = "ethereum"
            if "polygon" in query_lower or "matic" in query_lower:
                chain = "polygon"
            elif "arbitrum" in query_lower:
                chain = "arbitrum"

            # Extract limit if specified
            limit = 10
            limit_match = re.search(r'top\s+(\d+)', query_lower)
            if limit_match:
                try:
                    limit = int(limit_match.group(1))
                    limit = min(100, max(1, limit))  # Ensure limit is between 1 and 100
                except:
                    pass

            try:
                holders = await manager.get_token_holders(address, limit, chain)

                if isinstance(holders, dict) and "error" in holders:
                    return f"""❌ **Token Holders Query Failed**

Unable to get holders for {address}:
{holders.get('error', 'Unknown error')}

Please verify the token address is correct and try again."""

                holder_list = holders.get('holders', [])
                holder_count = len(holder_list)

                # Format the holder list
                formatted_holders = "\n".join([f"**{i+1}.** {h['address']} - {h['balance']}" for i, h in enumerate(holder_list[:limit])])

                return f"""👥 **Token Holders**

**Token Address:** {address}
**Chain:** {chain}
**Total Holders Found:** {holder_count}

**Top {limit} Holders:**
{formatted_holders}

*This data is provided by TheGraph Token API.*"""

            except Exception as e:
                ctx.logger.error(f"Error getting token holders: {e}")
                return f"""❌ **Token Holders Query Failed**

Encountered an error while fetching holders for {address}:
{str(e)}

Please try again later."""

        else:
            return """⚠️ **Token Address Not Detected**

I need a valid token contract address to check token holders.
Please provide a query with a valid token address (0x...).

Example: "Get top holders for 0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984\""""

    # Check for token transfers queries
    elif any(phrase in query_lower for phrase in ['token transfers', 'token transactions', 'token movements']):
        import re
        address_match = re.search(r'0x[a-fA-F0-9]{40}', query)

        if address_match:
            address = address_match.group(0)
            ctx.logger.info(f"Detected token transfers request for: {address}")

            # Extract chain if specified
            chain = "ethereum"
            if "polygon" in query_lower or "matic" in query_lower:
                chain = "polygon"
            elif "arbitrum" in query_lower:
                chain = "arbitrum"

            # Extract limit if specified
            limit = 10
            limit_match = re.search(r'(\d+)\s+transfers', query_lower)
            if limit_match:
                try:
                    limit = int(limit_match.group(1))
                    limit = min(100, max(1, limit))  # Ensure limit is between 1 and 100
                except:
                    pass

            try:
                transfers = await manager.get_token_transfers(address, limit, chain)

                if isinstance(transfers, dict) and "error" in transfers:
                    return f"""❌ **Token Transfers Query Failed**

Unable to get transfers for {address}:
{transfers.get('error', 'Unknown error')}

Please verify the token address is correct and try again."""

                transfer_list = transfers.get('transfers', [])
                transfer_count = len(transfer_list)

                # Format the transfer list
                formatted_transfers = "\n".join([f"**{i+1}.** From {t['from'][:10]}...{t['from'][-6:]} to {t['to'][:10]}...{t['to'][-6:]} - {t['value']}" for i, t in enumerate(transfer_list[:limit])])

                return f"""📦 **Token Transfers**

**Token Address:** {address}
**Chain:** {chain}
**Total Transfers Found:** {transfer_count}

**Recent Transfers:**
{formatted_transfers}

*This data is provided by TheGraph Token API.*"""

            except Exception as e:
                ctx.logger.error(f"Error getting token transfers: {e}")
                return f"""❌ **Token Transfers Query Failed**

Encountered an error while fetching transfers for {address}:
{str(e)}

Please try again later."""

        else:
            return """⚠️ **Token Address Not Detected**

I need a valid token contract address to check token transfers.
Please provide a query with a valid token address (0x...).

Example: "Get token transfers for 0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984\""""

    # Check for token search queries
    elif any(phrase in query_lower for phrase in ['search token', 'find token', 'lookup token']):
        # Extract search query
        import re
        search_match = re.search(r'token[s]?\s+(?:for|with|named|called)\s+[\"]?([\w\s]+)[\"]?', query_lower)

        if not search_match:
            search_match = re.search(r'(?:search|find|lookup)\s+[\"]?([\w\s]+)[\"]?\s+token', query_lower)

        if search_match:
            search_term = search_match.group(1).strip()
            ctx.logger.info(f"Detected token search request for: {search_term}")

            # Extract chain if specified
            chain = "ethereum"
            if "polygon" in query_lower or "matic" in query_lower:
                chain = "polygon"
            elif "arbitrum" in query_lower:
                chain = "arbitrum"

            try:
                results = await manager.search_tokens(search_term, 10, chain)

                if isinstance(results, dict) and "error" in results:
                    return f"""❌ **Token Search Failed**

Unable to search for '{search_term}':
{results.get('error', 'Unknown error')}

Please try a different search term."""

                tokens = results.get('tokens', [])
                token_count = len(tokens)

                if token_count == 0:
                    return f"""🔍 **Token Search Results**

**Search Term:** {search_term}
**Chain:** {chain}
**Results:** No tokens found matching your search.

Try a different search term or check the spelling."""

                # Format the token list
                formatted_tokens = "\n".join([f"**{i+1}.** {t['name']} ({t['symbol']}) - {t['address']}" for i, t in enumerate(tokens[:10])])

                return f"""🔍 **Token Search Results**

**Search Term:** {search_term}
**Chain:** {chain}
**Total Results:** {token_count}

**Matching Tokens:**
{formatted_tokens}

*This data is provided by TheGraph Token API.*"""

            except Exception as e:
                ctx.logger.error(f"Error searching tokens: {e}")
                return f"""❌ **Token Search Failed**

Encountered an error while searching for '{search_term}':
{str(e)}

Please try again later."""

        else:
            return """⚠️ **Search Term Not Detected**

I need a search term to find tokens.
Please provide a query with a clear search term.

Example: "Search for tokens named Uniswap" or "Find tokens with DAI\""""

    # Check for ENS domain details request
    elif any(phrase in query_lower for phrase in ['ens details', 'domain details', 'ens info', 'domain info']):
        import re
        ens_match = re.search(r'[a-zA-Z0-9_-]+\.eth', query)

        if ens_match:
            ens_name = ens_match.group(0)
            ctx.logger.info(f"Detected ENS details request for: {ens_name}")

            try:
                # Use tools.ens directly since we already have it implemented
                from tools.ens import get_domain_details
                domain_details = await get_domain_details(ens_name)

                if isinstance(domain_details, dict) and "error" in domain_details:
                    return f"""❌ **ENS Domain Analysis Failed**

Unable to get details for {ens_name}:
{domain_details.get('error', 'Unknown error')}

Please verify the ENS name is correct and try again."""

                return f"""📋 **ENS Domain Details**

**Name:** {ens_name}
**Address:** {domain_details.get('address', 'None')}
**Owner:** {domain_details.get('owner', 'None')}
**Created:** {domain_details.get('created', 'Unknown')}
**Expiry:** {domain_details.get('expiry', 'Unknown')}
**Subdomain Count:** {domain_details.get('subdomainCount', '0')}

*For more detailed information, please use a specialized ENS lookup service.*"""

            except Exception as e:
                ctx.logger.error(f"Error getting ENS details: {e}")
                return f"""❌ **ENS Domain Analysis Failed**

Encountered an error while fetching details for {ens_name}:
{str(e)}

Please try again later."""

        else:
            return """⚠️ **ENS Name Not Detected**

I need a valid ENS name to check domain details.
Please provide a query with a valid ENS name (name.eth).

Example: "Get ENS details for vitalik.eth\""""

    # Check for ENS domain events request
    elif any(phrase in query_lower for phrase in ['ens events', 'domain events', 'ens history', 'domain history']):
        import re
        ens_match = re.search(r'[a-zA-Z0-9_-]+\.eth', query)

        if ens_match:
            ens_name = ens_match.group(0)
            ctx.logger.info(f"Detected ENS events request for: {ens_name}")

            try:
                # Use tools.ens directly since we already have it implemented
                from tools.ens import get_domain_events
                events = await get_domain_events(ens_name)

                if isinstance(events, list) and len(events) > 0 and "error" in events[0]:
                    return f"""❌ **ENS Domain Events Failed**

Unable to get events for {ens_name}:
{events[0].get('error', 'Unknown error')}

Please verify the ENS name is correct and try again."""

                event_count = len(events)
                return f"""📜 **ENS Domain Events**

**Name:** {ens_name}
**Total Events:** {event_count}

**Recent Events:**
{', '.join([event.get('type', 'Unknown') for event in events[:5]])}...

*For a complete event history, please use a specialized ENS lookup service.*"""

            except Exception as e:
                ctx.logger.error(f"Error getting ENS events: {e}")
                return f"""❌ **ENS Domain Events Failed**

Encountered an error while fetching events for {ens_name}:
{str(e)}

Please try again later."""

        else:
            return """⚠️ **ENS Name Not Detected**

I need a valid ENS name to check domain events.
Please provide a query with a valid ENS name (name.eth).

Example: "Get ENS events for vitalik.eth\""""

    # Check for trace/tracking queries
    elif any(word in query_lower for word in ['trace', 'track', 'follow', 'stolen', 'theft']):
        # Extract addresses using a simple regex pattern
        import re
        address_match = re.search(r'0x[a-fA-F0-9]{40}', query)

        if address_match:
            address = address_match.group(0)
            ctx.logger.info(f"Detected trace request for address: {address}")

            result = await manager.trace_evm_funds(address)

            if "error" in result:
                return f"""❌ **Fund Tracing Failed**

Unable to trace funds from {address}:
{result.get('error', 'Unknown error')}

Please verify the address is correct and try again."""

            # Format tracing result
            exit_hop = result.get("exit_hop_address", "Unknown")
            hops = result.get("hops_traced", 0)

            return f"""🔍 **Fund Tracing Complete**

**Source Address:** {address}
**Exit Hop Address:** {exit_hop}
**Hops Traversed:** {hops}

The funds were traced through {hops} transactions to the final exit address.
This address should be monitored for further activity.

*Note: For legal action, please contact relevant authorities with this information.*"""

        else:
            return """⚠️ **Address Not Detected**

I need a valid Ethereum address to trace funds.
Please provide a query with a valid address (0x...).

Example: "Trace funds from 0x123abc..."
"""

    # Check for holdings/balance queries
    elif any(word in query_lower for word in ['holdings', 'balance', 'portfolio', 'assets', 'wallet']):
        # Extract addresses or ENS names
        import re
        address_match = re.search(r'0x[a-fA-F0-9]{40}', query)
        ens_match = re.search(r'[a-zA-Z0-9_-]+\.eth', query)

        target = None
        if address_match:
            target = address_match.group(0)
        elif ens_match:
            target = ens_match.group(0)

        if target:
            ctx.logger.info(f"Detected holdings request for: {target}")

            result = await manager.get_curated_holdings(target)

            if "error" in result:
                return f"""❌ **Holdings Analysis Failed**

Unable to get holdings for {target}:
{result.get('error', 'Unknown error')}

Please verify the address/ENS is correct and try again."""

            # Format holdings result
            eth_balance = result.get("ETH_Balance", "0 ETH")
            token_count = len(result.get("tokens", []))
            nft_count = len(result.get("nfts", [])) if result.get("nfts") else 0
            assessment = result.get("risk_assessment", "No assessment available")

            return f"""💰 **Holdings Analysis Complete**

**Address:** {target}
**ETH Balance:** {eth_balance}
**ERC-20 Tokens:** {token_count} different tokens
**NFTs:** {nft_count} NFTs

**Risk Assessment:**
{assessment}

*Note: This is a preliminary assessment based on on-chain data.*"""

        else:
            return """⚠️ **Address Not Detected**

I need a valid Ethereum address or ENS name to check holdings.
Please provide a query with a valid address (0x...) or ENS name (name.eth).

Example: "Check holdings for vitalik.eth"
"""

    # Check for transaction queries
    elif any(word in query_lower for word in ['transaction', 'tx', 'hash']):
        # Extract transaction hash
        import re
        tx_match = re.search(r'0x[a-fA-F0-9]{64}', query)

        if tx_match:
            tx_hash = tx_match.group(0)
            ctx.logger.info(f"Detected transaction request for: {tx_hash}")

            # Use Alchemy client directly for now
            alchemy_client = manager.registry.get_client("alchemy")
            if not alchemy_client:
                return """❌ **Transaction Analysis Failed**

Alchemy client not available for transaction analysis.

Please try again later."""

            result = await alchemy_client.call_tool(
                "eth_getTransactionByHash",
                {"txHash": tx_hash}
            )

            if isinstance(result, dict) and "error" in result:
                return f"""❌ **Transaction Analysis Failed**

Unable to get transaction details for {tx_hash}:
{result.get('error', 'Unknown error')}

Please verify the transaction hash is correct and try again."""

            # Format transaction result
            from_addr = result.get("from", "Unknown")
            to_addr = result.get("to", "Unknown")
            value_wei = int(result.get("value", "0x0"), 16)
            value_eth = value_wei / 1e18
            gas = int(result.get("gas", "0x0"), 16)

            return f"""📊 **Transaction Analysis Complete**

**Transaction Hash:** {tx_hash}
**From:** {from_addr}
**To:** {to_addr}
**Value:** {value_eth:.6f} ETH
**Gas Limit:** {gas}
**Block Number:** {int(result.get("blockNumber", "0x0"), 16)}

*Note: This is raw transaction data. For detailed insights, consider a full forensic analysis.*"""

        else:
            return """⚠️ **Transaction Hash Not Detected**

I need a valid Ethereum transaction hash to analyze.
Please provide a query with a valid transaction hash (0x...).

Example: "Analyze transaction 0x123abc..."
"""

    # Help message for other queries
    else:
        # Check if we got a useful RAG response
        if rag_result and isinstance(rag_result, dict) and "answer" in rag_result and rag_result["answer"].get("result"):
            answer = rag_result["answer"]
            confidence = rag_result.get("confidence", 0)

            if confidence > 0.5:
                return f"""🤖 **AI-Generated Response**

{answer['result']}

*Note: This response was generated using AI analysis with {confidence:.0%} confidence.*"""

        return """🚨 **Block Police Help**

I can help you investigate blockchain activities. Try one of these queries:

1️⃣ **Trace stolen funds**
   Example: "Trace funds from 0x123abc..."

2️⃣ **Analyze wallet holdings**
   Example: "Check holdings for vitalik.eth"

3️⃣ **Examine transactions**
   Example: "Analyze transaction 0x456def..."

4️⃣ **ENS Domain Details**
   Example: "Get ENS details for vitalik.eth"

5️⃣ **ENS Domain Events**
   Example: "Get ENS events for vitalik.eth"

6️⃣ **Token Metadata**
   Example: "Get token info for 0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"

7️⃣ **Token Holders**
   Example: "Get top holders for 0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"

8️⃣ **Token Transfers**
   Example: "Get token transfers for 0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"

9️⃣ **Search Tokens**
   Example: "Search for tokens named Uniswap"

Just provide the appropriate address, ENS name, or transaction hash with your query."""

# Add shutdown handler to cleanup clients
@agent.on_event("shutdown")
async def on_shutdown(ctx: Context):
    """Cleanup on agent shutdown"""
    for session_data in user_sessions.values():
        if 'manager' in session_data:
            await session_data['manager'].cleanup()

# Include chat protocol
agent.include(chat_proto, publish_manifest=True)

# --- Main Execution Block ---
if __name__ == "__main__":
    print(f"Block Police Agent starting on http://localhost:8001")
    print(f"Agent address: {agent.address}")
    print("🚨 Ready to investigate blockchain activities!")

    try:
        agent.run()
    except KeyboardInterrupt:
        print("Agent stopped by user")
    except Exception as e:
        print(f"Agent error: {e}")