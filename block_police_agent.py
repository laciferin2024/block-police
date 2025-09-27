import os
import asyncio
import json
from typing import Any, Dict, List, Optional
from uagents import Agent, Context, Protocol
from uagents_adapter import MCPServerAdapter
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Import our Alchemy tools
from alchemy_tools import AlchemyTools

# Load environment variables
load_dotenv()

# --- 1. Define the Alchemy/EVM Tools (FastMCP Server Implementation) ---
class AlchemyMCP(FastMCP):
    def __init__(self):
        super().__init__("alchemy_evm_investigator")
        # Initialize our Alchemy tools
        self.alchemy_tools = AlchemyTools()

    @FastMCP.tool()
    async def trace_evm_funds(self, start_address: str, hop_limit: int = 100) -> str:
        """
        Traces the path of funds stolen from an ENS user across EVM transactions,
        hop by hop, up to a specified limit. Returns the final exit hop address
        where the funds are currently held.
        """
        try:
            # Use our Alchemy tools to trace funds
            result = await self.alchemy_tools.trace_funds_path(start_address, hop_limit)
            exit_address = result.get("exit_hop_address", "Unknown")
            return f"Tracing initiated from {start_address}. Funds confirmed at exit address: {exit_address}"
        except Exception as e:
            return f"Error tracing funds: {str(e)}"

    @FastMCP.tool()
    async def get_curated_holdings(self, address_or_ens: str) -> dict[str, Any]:
        """
        Retrieves a curated, multi-chain assessment of the crypto holdings
        (e.g., ERC-20, NFT, liquidity positions) for a given ENS user or address.
        """
        try:
            # Get ETH balance
            eth_balance = await self.alchemy_tools.get_balance(address_or_ens)

            # Get token balances (simplified for demo)
            token_balances = await self.alchemy_tools.get_token_balances(address_or_ens)

            # Prepare response
            holdings = {
                "address": address_or_ens,
                "ETH_Balance": f"{eth_balance.get('balance_eth', 0)} ETH",
                "token_balances": token_balances,
                "Curated_Risk_Assessment": self._generate_risk_assessment(eth_balance, token_balances)
            }

            return holdings
        except Exception as e:
            return {"error": f"Failed to fetch holdings for {address_or_ens}: {str(e)}"}

    def _generate_risk_assessment(self, eth_balance: Dict[str, Any], token_balances: Dict[str, Any]) -> str:
        """Generate a simplified risk assessment based on holdings"""
        # This would be more sophisticated in a real implementation,
        # potentially using MeTTa Knowledge Graph for reasoning

        if isinstance(eth_balance, dict) and eth_balance.get("balance_eth", 0) > 100:
            return "High value account with significant ETH holdings."
        else:
            return "Standard account with typical holdings."

    @FastMCP.tool()
    async def get_transaction_details(self, tx_hash: str) -> dict[str, Any]:
        """
        Gets detailed information about a specific transaction.
        """
        try:
            tx_details = await self.alchemy_tools.get_transaction(tx_hash)
            return tx_details
        except Exception as e:
            return {"error": f"Failed to fetch transaction details: {str(e)}"}

# --- 2. Create the Agent and Adapter ---
def create_block_police_agent():
    # Instantiate the MCP Server (Tool Logic)
    alchemy_mcp_server = AlchemyMCP()

    # Create the uAgent instance
    block_police_agent = Agent(
        name="BlockPolice",
        seed="block police agent secret key",  # Use AGENT_SECRET_KEY from .env for production
        port=8000
    )

    # Instantiate the MCPServerAdapter to wrap the FastMCP server as a uAgent
    try:
        asi1_key = os.getenv("ASI1_API_KEY", "")

        if not asi1_key:
            print("Warning: ASI1_API_KEY not found in environment variables")

        mcp_adapter = MCPServerAdapter(
            mcp_server=alchemy_mcp_server,
            asi1_api_key=asi1_key,
            model="asi1-mini"
        )

        # Include protocols from the adapter
        for protocol in mcp_adapter.protocols:
            block_police_agent.include(protocol, publish_manifest=True)

        return block_police_agent, mcp_adapter

    except Exception as e:
        print(f"Error setting up MCPServerAdapter: {e}")
        return None, None

# --- 3. Main Execution Block ---
if __name__ == "__main__":
    agent, adapter = create_block_police_agent()

    if agent and adapter:
        print(f"Starting Block Police Agent @ {agent.address}...")
        try:
            adapter.run(agent)
        except Exception as e:
            print(f"Agent failed to run: {e}")
    else:
        print("Failed to create Block Police agent")