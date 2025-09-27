import os
import asyncio
import json
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from uuid import uuid4
from uagents import Agent, Context, Protocol
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
import mcp
from dotenv import load_dotenv
from tools import get_registered_tools
from tools.ens import resolve_ens_name, get_domain_details, get_domain_events
from tools.token import get_token_metadata, get_token_holders, get_token_transfers, get_holder_tokens, search_tokens

# Load environment variables
load_dotenv()

# Check for required API keys
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
ASI_ONE_API_KEY = os.getenv("ASI_ONE_API_KEY")

if not ALCHEMY_API_KEY:
    raise ValueError("ALCHEMY_API_KEY not found in .env file")

# --- Alchemy MCP Client Implementation ---
class AlchemyMCPClient:
    """
    Alchemy MCP Client for blockchain investigation.
    Uses Alchemy MCP server to interact with Ethereum blockchain.
    """

    def __init__(self, ctx: Context):
        self._ctx = ctx
        self._session = None
        self._exit_stack = AsyncExitStack()
        self.tools = []  # Will be populated after connection
        self.resolved_ens_cache = {}  # Cache for ENS resolution

    async def connect(self):
        """Connect to Alchemy MCP server via local npx execution"""
        try:
            self._ctx.logger.info("Connecting to Alchemy MCP server via npx...")

            # Use npx to run Alchemy MCP server locally
            params = mcp.StdioServerParameters(
                command="npx",
                args=["-y", "@alchemy/mcp-server"],
                env={"ALCHEMY_API_KEY": ALCHEMY_API_KEY}
            )

            read_stream, write_stream = await self._exit_stack.enter_async_context(
                stdio_client(params)
            )

            self._session = await self._exit_stack.enter_async_context(
                mcp.ClientSession(read_stream, write_stream)
            )

            await self._session.initialize()

            # List available tools
            list_tools_result = await self._session.list_tools()
            self.tools = list_tools_result.tools

            self._ctx.logger.info(f"Connected to Alchemy MCP server with {len(self.tools)} tools")
            for tool in self.tools:
                self._ctx.logger.info(f"Available tool: {tool.name}")

        except Exception as e:
            self._ctx.logger.error(f"Failed to connect to Alchemy MCP server: {e}")
            raise

    async def resolve_ens_to_address(self, ens_name: str) -> str:
        """
        Resolve ENS name to address using multiple methods
        Returns the original name if resolution fails
        """
        # Check cache first
        if ens_name in self.resolved_ens_cache:
            return self.resolved_ens_cache[ens_name]

        # Only try to resolve .eth names
        if not ens_name.endswith(".eth"):
            return ens_name

        self._ctx.logger.info(f"Resolving ENS name: {ens_name}")

        # First try our custom ENS resolution tool
        try:
            self._ctx.logger.info(f"Using custom ENS resolution tool")
            address = await resolve_ens_name(ens_name)

            # Check if we got a valid address or error message
            if address and not address.startswith("Error:") and not address.startswith("No data"):
                self._ctx.logger.info(f"Successfully resolved {ens_name} to {address} using custom tool")
                # Cache the result
                self.resolved_ens_cache[ens_name] = address
                return address
        except Exception as e:
            self._ctx.logger.error(f"Error with custom ENS resolution: {e}")

        # Try a direct call to eth_getBalance as a secondary method
        # Some providers handle ENS resolution internally
        try:
            self._ctx.logger.info("Trying direct eth_getBalance to see if the provider handles ENS")
            result = await self._session.call_tool(
                "eth_getBalance",
                {"address": ens_name, "tag": "latest"}
            )

            if hasattr(result, 'content') and result.content:
                self._ctx.logger.info(f"Provider can handle ENS directly, using {ens_name} as is")
                # Since the provider can handle ENS directly, cache the original name
                self.resolved_ens_cache[ens_name] = ens_name
                return ens_name
        except Exception as e:
            self._ctx.logger.error(f"Direct eth_getBalance with ENS failed: {e}")

        # Fall back to Alchemy MCP methods if custom resolution fails
        # Methods to try in order of preference
        methods_to_try = [
            {"method": "ens_getAddress", "params": {"name": ens_name}},
            {"method": "eth_resolveENS", "params": {"ensName": ens_name}},
            {"method": "alchemy_resolveENS", "params": {"ens": ens_name}}
        ]

        for method_info in methods_to_try:
            method = method_info["method"]
            params = method_info["params"]

            try:
                self._ctx.logger.info(f"Trying ENS resolution method: {method}")
                result = await self._session.call_tool(method, params)

                if hasattr(result, 'content') and result.content:
                    address = result.content
                    self._ctx.logger.info(f"Successfully resolved {ens_name} to {address} using {method}")
                    # Cache the result
                    self.resolved_ens_cache[ens_name] = address
                    return address
            except Exception as e:
                self._ctx.logger.error(f"Error with {method}: {e}")

        # Skip this step as we already tried direct eth_getBalance above

        # If all resolution methods fail, return the original ENS name
        self._ctx.logger.warning(f"Failed to resolve {ens_name}, using as is")
        return ens_name

    async def trace_evm_funds(self, start_address: str, hop_limit: int = 100) -> Dict[str, Any]:
        """
        Traces the path of funds across EVM transactions, hop by hop.
        Uses Alchemy MCP server tools directly.
        """
        try:
            self._ctx.logger.info(f"Tracing funds from address: {start_address}")

            # Resolve ENS if needed
            address = await self.resolve_ens_to_address(start_address)

            # Check which tools are available for tracing
            trace_tools = [tool for tool in self.tools if 'trace' in tool.name.lower()]

            if not trace_tools:
                # If no specific trace tools, use getAssetTransfers
                self._ctx.logger.info("Using getAssetTransfers for tracing")
                result = await self._session.call_tool(
                    "alchemy_getAssetTransfers",
                    {
                        "fromAddress": address,
                        "category": ["external", "internal", "erc20", "erc721", "erc1155"],
                        "maxCount": "0x" + format(hop_limit, 'x')
                    }
                )

                # Process the result to create a trace path
                if hasattr(result, 'content') and result.content:
                    transfers = result.content.get('transfers', [])

                    if transfers and len(transfers) > 0:
                        # Find the last hop (simplified approach)
                        last_transfer = transfers[-1]
                        exit_hop_address = last_transfer.get('to', 'Unknown')

                        return {
                            "source_address": start_address,
                            "exit_hop_address": exit_hop_address,
                            "transfers": transfers,
                            "hops_traced": len(transfers)
                        }
            else:
                # Use available trace tools
                trace_tool = trace_tools[0]
                self._ctx.logger.info(f"Using trace tool: {trace_tool.name}")

                result = await self._session.call_tool(
                    trace_tool.name,
                    {"address": address, "limit": hop_limit}
                )

                if hasattr(result, 'content'):
                    return result.content

            return {"error": "Tracing not successful", "source_address": start_address}

        except Exception as e:
            self._ctx.logger.error(f"Error tracing funds: {e}")
            return {"error": f"Error tracing funds: {str(e)}", "source_address": start_address}

    async def get_curated_holdings(self, address_or_ens: str) -> Dict[str, Any]:
        """
        Retrieves a multi-chain assessment of crypto holdings for an address or ENS.
        Uses Alchemy MCP server tools directly.
        """
        try:
            self._ctx.logger.info(f"Getting holdings for: {address_or_ens}")

            # Resolve ENS to address if needed
            address = await self.resolve_ens_to_address(address_or_ens)

            # Get ETH balance - Using params object instead of array
            balance_result = await self._session.call_tool(
                "eth_getBalance",
                {"address": address, "tag": "latest"}
            )

            # Get token balances
            token_balances_result = await self._session.call_tool(
                "alchemy_getTokenBalances",
                {"address": address}
            )

            # Get NFTs if the tool is available
            nft_tools = [tool for tool in self.tools if 'nft' in tool.name.lower()]
            nfts = None

            if nft_tools:
                nft_tool = nft_tools[0]
                self._ctx.logger.info(f"Using NFT tool: {nft_tool.name}")

                nft_result = await self._session.call_tool(
                    nft_tool.name,
                    {"owner": address}
                )

                if hasattr(nft_result, 'content'):
                    nfts = nft_result.content

            # Process ETH balance
            eth_balance = 0
            if hasattr(balance_result, 'content') and balance_result.content:
                eth_balance_hex = balance_result.content
                eth_balance_wei = int(eth_balance_hex, 16) if isinstance(eth_balance_hex, str) else 0
                eth_balance = eth_balance_wei / 1e18

            # Process token balances
            tokens = []
            if hasattr(token_balances_result, 'content') and token_balances_result.content:
                tokens = token_balances_result.content.get('tokenBalances', [])

            # Prepare response
            holdings = {
                "address": address_or_ens,
                "ETH_Balance": f"{eth_balance:.6f} ETH",
                "tokens": tokens,
                "nfts": nfts,
                "risk_assessment": self._generate_risk_assessment(eth_balance, len(tokens))
            }

            return holdings

        except Exception as e:
            self._ctx.logger.error(f"Error getting holdings: {e}")
            return {"error": f"Failed to fetch holdings for {address_or_ens}: {str(e)}"}

    def _generate_risk_assessment(self, eth_balance: float, token_count: int) -> str:
        """Generate a simplified risk assessment based on holdings"""
        if eth_balance > 100:
            return "High value account with significant ETH holdings."
        elif token_count > 10:
            return "Diverse portfolio with multiple token types."
        else:
            return "Standard account with typical holdings."

    async def get_transaction_details(self, tx_hash: str) -> Dict[str, Any]:
        """
        Gets detailed information about a specific transaction.
        Uses Alchemy MCP server tools directly.
        """
        try:
            self._ctx.logger.info(f"Getting transaction details for: {tx_hash}")

            # Note: tx_hash is already a transaction hash, not an ENS name
            # but we include this check for consistency in case the method
            # is called with an address parameter that could be ENS
            if tx_hash.endswith('.eth'):
                tx_hash = await self.resolve_ens_to_address(tx_hash)

            result = await self._session.call_tool(
                "eth_getTransactionByHash",
                {"txHash": tx_hash}
            )

            if hasattr(result, 'content') and result.content:
                return result.content
            else:
                return {"error": "Transaction not found", "tx_hash": tx_hash}

        except Exception as e:
            self._ctx.logger.error(f"Error getting transaction: {e}")
            return {"error": f"Failed to fetch transaction details: {str(e)}"}

    async def cleanup(self):
        """Clean up the MCP connection"""
        try:
            if self._exit_stack:
                await self._exit_stack.aclose()
            self._ctx.logger.info("Alchemy MCP client cleaned up")
        except Exception as e:
            self._ctx.logger.error(f"Error during cleanup: {e}")

# --- Chat Protocol Setup ---
from uagents_core.contrib.protocols.chat import (
    chat_protocol_spec,
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
    EndSessionContent,
    StartSessionContent,
)

# User sessions store: session_id -> {client, last_activity}
user_sessions = {}

# Session timeout (30 minutes)
SESSION_TIMEOUT = 30 * 60

# --- Agent Setup ---
chat_proto = Protocol(spec=chat_protocol_spec)
agent = Agent(name="block_police_agent", port=8001, mailbox=True)

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

async def get_alchemy_client(ctx: Context, session_id: str) -> AlchemyMCPClient:
    """Get or create Alchemy MCP client for session"""
    if session_id not in user_sessions or not is_session_valid(session_id):
        # Create new client
        client = AlchemyMCPClient(ctx)
        await client.connect()
        user_sessions[session_id] = {
            'client': client,
            'last_activity': time.time()
        }

    return user_sessions[session_id]['client']

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
                # Get Alchemy client for this session
                client = await get_alchemy_client(ctx, session_id)

                # Process based on query content
                response_text = await process_blockchain_query(ctx, client, query)

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

async def process_blockchain_query(ctx: Context, client: AlchemyMCPClient, query: str) -> str:
    """Process blockchain investigation query"""
    query_lower = query.lower()

    # Check for ENS domain details request
    if any(phrase in query_lower for phrase in ['ens details', 'domain details', 'ens info', 'domain info']):
        import re
        ens_match = re.search(r'[a-zA-Z0-9_-]+\.eth', query)

        if ens_match:
            ens_name = ens_match.group(0)
            ctx.logger.info(f"Detected ENS details request for: {ens_name}")

            try:
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
                metadata = await get_token_metadata(address, chain)

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
                holders = await get_token_holders(address, limit, chain)

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
                transfers = await get_token_transfers(address, limit, chain)

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
        search_match = re.search(r'token[s]?\s+(?:for|with|named|called)\s+["]?([\w\s]+)["]?', query_lower)

        if not search_match:
            search_match = re.search(r'(?:search|find|lookup)\s+["]?([\w\s]+)["]?\s+token', query_lower)

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
                results = await search_tokens(search_term, 10, chain)

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

    # Check for trace/tracking queries
    elif any(word in query_lower for word in ['trace', 'track', 'follow', 'stolen', 'theft']):
        # Extract addresses using a simple regex pattern
        import re
        address_match = re.search(r'0x[a-fA-F0-9]{40}', query)

        if address_match:
            address = address_match.group(0)
            ctx.logger.info(f"Detected trace request for address: {address}")

            result = await client.trace_evm_funds(address)

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

            result = await client.get_curated_holdings(target)

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

            result = await client.get_transaction_details(tx_hash)

            if "error" in result:
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
        if 'client' in session_data:
            await session_data['client'].cleanup()

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