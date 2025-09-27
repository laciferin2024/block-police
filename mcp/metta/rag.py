"""
MeTTa RAG Module

Implements Retrieval-Augmented Generation (RAG) using MeTTa for blockchain data.
"""
from typing import Dict, List, Any, Optional, Set, Tuple
import logging
import json
from .knowledge_base import MeTTaKnowledgeBase


class MeTTaRAG:
    """
    Retrieval-Augmented Generation system for blockchain data using MeTTa.

    This class implements RAG patterns for querying and reasoning about
    blockchain data, leveraging the MeTTa knowledge representation.
    """

    def __init__(self, kb: Optional[MeTTaKnowledgeBase] = None):
        self.kb = kb or MeTTaKnowledgeBase()
        self._query_cache = {}
        self._query_history = []

    async def query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Query the knowledge base using natural language.

        Args:
            query: Natural language query
            context: Additional context for the query

        Returns:
            Dictionary with query results and reasoning steps
        """
        # Check cache
        cache_key = query
        if context:
            cache_key += str(sorted(context.items()))

        if cache_key in self._query_cache:
            return self._query_cache[cache_key]

        # Process the query
        query_type = self._classify_query(query)

        # Get relevant data based on query type
        data = await self._retrieve_relevant_data(query, query_type, context)

        # Generate response
        response = await self._generate_response(query, query_type, data, context)

        # Cache the result
        self._query_cache[cache_key] = response
        self._query_history.append((query, response))

        return response

    def _classify_query(self, query: str) -> str:
        """Classify the query type"""
        query = query.lower()

        if any(word in query for word in ["trace", "track", "follow", "stolen", "theft"]):
            return "fund_tracing"

        if any(word in query for word in ["holdings", "balance", "portfolio", "assets", "wallet"]):
            return "account_holdings"

        if any(word in query for word in ["transaction", "tx", "hash"]):
            return "transaction_details"

        if any(phrase in query for phrase in ["suspicious", "illegal", "laundering", "detect", "pattern"]):
            return "pattern_detection"

        if any(phrase in query for phrase in ["ens", "domain", "name", "resolve"]):
            return "ens_resolution"

        if any(phrase in query for phrase in ["token", "erc20", "holders", "transfers"]):
            return "token_analysis"

        return "general"

    async def _retrieve_relevant_data(self, query: str, query_type: str,
                               context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Retrieve relevant data from the knowledge base"""
        data = {"query_type": query_type}

        # Extract entities from query
        entities = self._extract_entities(query)
        data["entities"] = entities

        # Get data based on query type
        if query_type == "fund_tracing":
            if "address" in entities:
                data["fund_flows"] = self.kb.query_fund_flow(entities["address"], depth=5)

        elif query_type == "account_holdings":
            if "address" in entities:
                data["entity"] = self.kb.get_entity(entities["address"])
                data["relations"] = self.kb.get_relations(entities["address"])

        elif query_type == "transaction_details":
            if "tx_hash" in entities:
                data["transaction"] = self.kb.get_transaction(entities["tx_hash"])

        elif query_type == "pattern_detection":
            data["suspicious_patterns"] = self.kb.detect_suspicious_patterns()

        return data

    async def _generate_response(self, query: str, query_type: str,
                          data: Dict[str, Any],
                          context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a response based on retrieved data"""
        # In a full implementation, this would use an LLM or rule-based system
        # Here we're implementing a simplified version

        response = {
            "query": query,
            "query_type": query_type,
            "reasoning_steps": [],
            "answer": {},
            "confidence": 0.0
        }

        if query_type == "fund_tracing":
            response = self._generate_fund_tracing_response(response, data)

        elif query_type == "account_holdings":
            response = self._generate_account_holdings_response(response, data)

        elif query_type == "transaction_details":
            response = self._generate_transaction_details_response(response, data)

        elif query_type == "pattern_detection":
            response = self._generate_pattern_detection_response(response, data)

        elif query_type == "ens_resolution":
            response = self._generate_ens_resolution_response(response, data)

        elif query_type == "token_analysis":
            response = self._generate_token_analysis_response(response, data)

        else:
            response["reasoning_steps"].append(
                "Unable to classify query into a specific type. Using general response."
            )
            response["answer"] = {"result": "I need more specific information to answer this query."}
            response["confidence"] = 0.2

        return response

    def _generate_fund_tracing_response(self, response: Dict[str, Any],
                                      data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response for fund tracing queries"""
        response["reasoning_steps"].append(
            f"Analyzing fund flows for address: {data.get('entities', {}).get('address', 'unknown')}"
        )

        fund_flows = data.get("fund_flows", [])

        if not fund_flows:
            response["reasoning_steps"].append("No fund flows found for the address.")
            response["answer"] = {
                "result": "No fund flows found for this address.",
                "exit_hop_address": None,
                "hops_traced": 0
            }
            response["confidence"] = 0.7
        else:
            # Find the most likely exit hop (last address in the longest path)
            longest_path = max(fund_flows, key=len) if fund_flows else []
            exit_hop = longest_path[-1]["to"] if longest_path else None

            response["reasoning_steps"].append(
                f"Found {len(fund_flows)} distinct fund flow paths."
            )
            response["reasoning_steps"].append(
                f"Longest path has {len(longest_path)} hops, ending at {exit_hop}."
            )

            response["answer"] = {
                "result": f"Funds were traced through {len(longest_path)} transactions to {exit_hop}.",
                "exit_hop_address": exit_hop,
                "hops_traced": len(longest_path),
                "paths": fund_flows
            }
            response["confidence"] = min(0.9, 0.5 + 0.1 * len(longest_path))

        return response

    def _generate_account_holdings_response(self, response: Dict[str, Any],
                                         data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response for account holdings queries"""
        entity = data.get("entity", {})
        relations = data.get("relations", [])

        if not entity:
            response["reasoning_steps"].append(
                f"No entity found for address: {data.get('entities', {}).get('address', 'unknown')}"
            )
            response["answer"] = {"result": "No account data found."}
            response["confidence"] = 0.5
        else:
            response["reasoning_steps"].append(
                f"Found entity data with {len(entity.get('transactions', []))} transactions."
            )
            response["reasoning_steps"].append(
                f"Found {len(relations)} relationships with other entities."
            )

            response["answer"] = {
                "result": f"Account has activity across {len(entity.get('transactions', []))} transactions.",
                "entity": entity,
                "relations": relations
            }
            response["confidence"] = 0.8

        return response

    def _generate_transaction_details_response(self, response: Dict[str, Any],
                                           data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response for transaction details queries"""
        tx = data.get("transaction", {})

        if not tx:
            response["reasoning_steps"].append(
                f"No transaction found with hash: {data.get('entities', {}).get('tx_hash', 'unknown')}"
            )
            response["answer"] = {"result": "Transaction not found."}
            response["confidence"] = 0.9
        else:
            response["reasoning_steps"].append("Found transaction details.")

            # Extract key transaction information
            from_addr = tx.get("from", "unknown")
            to_addr = tx.get("to", "unknown")
            value = int(tx.get("value", "0"), 16) if isinstance(tx.get("value"), str) else tx.get("value", 0)
            value_eth = value / 10**18

            response["answer"] = {
                "result": f"Transaction from {from_addr} to {to_addr} with value {value_eth:.6f} ETH",
                "transaction": tx
            }
            response["confidence"] = 0.95

        return response

    def _generate_pattern_detection_response(self, response: Dict[str, Any],
                                         data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response for pattern detection queries"""
        patterns = data.get("suspicious_patterns", [])

        if not patterns:
            response["reasoning_steps"].append("No suspicious patterns detected.")
            response["answer"] = {"result": "No suspicious patterns detected."}
            response["confidence"] = 0.7
        else:
            response["reasoning_steps"].append(
                f"Detected {len(patterns)} suspicious patterns."
            )

            # Categorize patterns
            pattern_types = {}
            for pattern in patterns:
                pattern_type = pattern.get("type", "unknown")
                if pattern_type not in pattern_types:
                    pattern_types[pattern_type] = 0
                pattern_types[pattern_type] += 1

            pattern_summary = ", ".join(
                f"{count} {p_type}" for p_type, count in pattern_types.items()
            )

            response["answer"] = {
                "result": f"Detected suspicious activity: {pattern_summary}.",
                "patterns": patterns
            }
            response["confidence"] = min(0.9, 0.6 + 0.1 * len(patterns))

        return response

    def _generate_ens_resolution_response(self, response: Dict[str, Any],
                                       data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response for ENS resolution queries"""
        ens_name = data.get("entities", {}).get("ens_name")

        if not ens_name:
            response["reasoning_steps"].append("No ENS name found in query.")
            response["answer"] = {"result": "No ENS name specified."}
            response["confidence"] = 0.5
        else:
            response["reasoning_steps"].append(f"Processing ENS resolution for {ens_name}")

            # In a full implementation, this would call the ENS resolution service
            response["answer"] = {
                "result": f"ENS name information for {ens_name}",
                "ens_name": ens_name,
                "resolution_status": "placeholder"  # Would be replaced with actual resolution
            }
            response["confidence"] = 0.7

        return response

    def _generate_token_analysis_response(self, response: Dict[str, Any],
                                       data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response for token analysis queries"""
        token_address = data.get("entities", {}).get("token_address")

        if not token_address:
            response["reasoning_steps"].append("No token address found in query.")
            response["answer"] = {"result": "No token address specified."}
            response["confidence"] = 0.5
        else:
            response["reasoning_steps"].append(f"Processing token analysis for {token_address}")

            # In a full implementation, this would call token analysis services
            response["answer"] = {
                "result": f"Token analysis for {token_address}",
                "token_address": token_address,
                "analysis_status": "placeholder"  # Would be replaced with actual analysis
            }
            response["confidence"] = 0.7

        return response

    def _extract_entities(self, query: str) -> Dict[str, str]:
        """Extract entities from the query"""
        entities = {}

        # Simple regex-based entity extraction
        import re

        # Extract Ethereum addresses
        addr_match = re.search(r'0x[a-fA-F0-9]{40}', query)
        if addr_match:
            entities["address"] = addr_match.group(0)

        # Extract transaction hashes
        tx_match = re.search(r'0x[a-fA-F0-9]{64}', query)
        if tx_match:
            entities["tx_hash"] = tx_match.group(0)

        # Extract ENS names
        ens_match = re.search(r'[a-zA-Z0-9_-]+\.eth', query)
        if ens_match:
            entities["ens_name"] = ens_match.group(0)

        # Extract token addresses (same format as Ethereum addresses)
        # If we already found an address, check if the context suggests it's a token
        if "address" in entities and any(word in query.lower() for word in ["token", "erc20", "erc721"]):
            entities["token_address"] = entities["address"]

        return entities

    def add_transaction_to_kb(self, tx_hash: str, tx_data: Dict[str, Any]) -> bool:
        """Add a transaction to the knowledge base"""
        return self.kb.add_transaction(tx_hash, tx_data)

    def add_entity_to_kb(self, address: str, entity_data: Dict[str, Any]) -> bool:
        """Add an entity to the knowledge base"""
        return self.kb.add_entity(address, entity_data)

    def save_kb(self, filepath: str) -> bool:
        """Save the knowledge base to a file"""
        return self.kb.save_to_file(filepath)

    def load_kb(self, filepath: str) -> bool:
        """Load the knowledge base from a file"""
        return self.kb.load_from_file(filepath)