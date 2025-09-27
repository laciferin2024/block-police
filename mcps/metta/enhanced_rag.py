"""
Enhanced RAG Module with Knowledge Graph Integration

Provides retrieval-augmented generation capabilities with knowledge graph integration
for deeper context awareness and improved response quality.
"""
from typing import Dict, List, Any, Optional, Tuple
import logging
import json
import asyncio
from datetime import datetime

from .knowledge_base import MeTTaKnowledgeBase
from .knowledge_graph import BlockchainKnowledgeGraph
from .rag import MeTTaRAG

# Mock LLM interface for RAG
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    logging.warning("OpenAI not found; using mock implementation")


class EnhancedMeTTaRAG:
    """Enhanced RAG system with knowledge graph integration"""

    def __init__(self,
                 knowledge_base: Optional[MeTTaKnowledgeBase] = None,
                 knowledge_graph: Optional[BlockchainKnowledgeGraph] = None,
                 api_key: Optional[str] = None):
        """
        Initialize the enhanced RAG system

        Args:
            knowledge_base: Optional MeTTaKnowledgeBase instance
            knowledge_graph: Optional BlockchainKnowledgeGraph instance
            api_key: Optional API key for LLM provider
        """
        self.knowledge_base = knowledge_base or MeTTaKnowledgeBase()
        self.knowledge_graph = knowledge_graph or BlockchainKnowledgeGraph()
        self.api_key = api_key

        # Initialize client if OpenAI is available
        self.client = None
        if HAS_OPENAI and api_key:
            self.client = OpenAI(api_key=api_key)

        # Configure basic system prompts
        self.system_prompts = {
            "blockchain_investigation": """You are a blockchain investigation assistant.
Use the retrieved knowledge and graph data to provide accurate insights about blockchain addresses,
transactions, tokens, and other on-chain activities. Always cite your sources and level of confidence.""",

            "network_analysis": """You are a blockchain network analysis specialist.
Analyze the provided network data, identify patterns, and explain relationships between addresses.
Focus on fund flows, token interactions, and potential anomalies.""",

            "default": """You are an assistant with knowledge about blockchain technology.
Use the provided context to give helpful and accurate responses about blockchain concepts, technologies, and data."""
        }

    async def query(self,
                   query: str,
                   context: Dict[str, Any] = None,
                   query_type: str = "blockchain_investigation") -> Dict[str, Any]:
        """
        Query the system with enhanced knowledge graph context

        Args:
            query: The user's query string
            context: Additional context to include
            query_type: Type of query to adjust response style

        Returns:
            Dictionary containing the answer and metadata
        """
        if context is None:
            context = {}

        # Extract entities from query and context
        entities = await self._extract_entities(query, context)

        # Retrieve information from knowledge base
        kb_results = await self._retrieve_from_knowledge_base(query, entities)

        # Retrieve information from knowledge graph for identified entities
        kg_results = await self._retrieve_from_knowledge_graph(entities)

        # Get query type specific system prompt
        system_prompt = self.system_prompts.get(query_type, self.system_prompts["default"])

        # Format context for LLM
        formatted_context = self._format_context(query, kb_results, kg_results, context)

        # Generate response using LLM
        try:
            answer = await self._generate_response(system_prompt, formatted_context, query)
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            answer = {
                "result": f"I encountered an error processing your query about '{query}'. Please try again with a more specific question.",
                "sources": []
            }

        # Add metadata to the response
        result = {
            "query": query,
            "answer": answer,
            "metadata": {
                "kb_results_count": len(kb_results),
                "kg_results_count": len(kg_results),
                "entities_detected": [e["text"] for e in entities],
                "query_type": query_type,
                "timestamp": datetime.now().isoformat()
            },
            "confidence": self._calculate_confidence(kb_results, kg_results)
        }

        return result

    async def _extract_entities(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract blockchain entities from the query"""
        entities = []

        # Check for Ethereum addresses (simplified regex)
        import re
        eth_address_pattern = re.compile(r'0x[a-fA-F0-9]{40}')
        eth_addresses = eth_address_pattern.findall(query)
        for addr in eth_addresses:
            entities.append({
                "type": "address",
                "text": addr,
                "source": "query"
            })

        # Check for ENS domains
        ens_pattern = re.compile(r'[a-zA-Z0-9_-]+\.eth')
        ens_domains = ens_pattern.findall(query)
        for domain in ens_domains:
            entities.append({
                "type": "ens_domain",
                "text": domain,
                "source": "query"
            })

        # Check for transaction hashes
        tx_pattern = re.compile(r'0x[a-fA-F0-9]{64}')
        tx_hashes = tx_pattern.findall(query)
        for tx in tx_hashes:
            entities.append({
                "type": "transaction",
                "text": tx,
                "source": "query"
            })

        # Check for token symbols - this is less precise
        token_pattern = re.compile(r'\b(ETH|BTC|USDT|USDC|DAI|UNI|LINK|AAVE|SNX|YFI)\b')
        token_symbols = token_pattern.findall(query)
        for symbol in token_symbols:
            entities.append({
                "type": "token_symbol",
                "text": symbol,
                "source": "query"
            })

        # Extract entities from provided context
        if "network" in context:
            entities.append({
                "type": "network",
                "text": context["network"],
                "source": "context"
            })

        if "address" in context:
            entities.append({
                "type": "address",
                "text": context["address"],
                "source": "context"
            })

        return entities

    async def _retrieve_from_knowledge_base(self, query: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Retrieve relevant documents from knowledge base"""
        # Build enhanced query using entities
        enhanced_query = query
        for entity in entities:
            if entity["type"] in ["address", "ens_domain", "transaction"]:
                enhanced_query += f" {entity['text']}"

        # Get documents from knowledge base
        documents = self.knowledge_base.search(enhanced_query)

        # Enrich with metadata
        for doc in documents:
            if "relevance" not in doc:
                doc["relevance"] = 0.7  # Default relevance

        # Sort by relevance
        documents.sort(key=lambda x: x.get("relevance", 0), reverse=True)

        return documents[:5]  # Return top 5 documents

    async def _retrieve_from_knowledge_graph(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Retrieve relevant information from knowledge graph"""
        results = []

        for entity in entities:
            if entity["type"] == "address":
                # Get address info from graph
                address_info = self.knowledge_graph.query_entity("Address", entity["text"])
                if address_info and "error" not in address_info:
                    results.append({
                        "type": "address_info",
                        "data": address_info,
                        "source": "knowledge_graph"
                    })

                    # Also get relationships
                    relationships = self.knowledge_graph.get_address_relationships(entity["text"])
                    if relationships:
                        results.append({
                            "type": "address_relationships",
                            "data": relationships,
                            "source": "knowledge_graph"
                        })

            elif entity["type"] == "ens_domain":
                # Get ENS domain info
                ens_info = self.knowledge_graph.query_entity("ENSDomain", entity["text"])
                if ens_info and "error" not in ens_info:
                    results.append({
                        "type": "ens_info",
                        "data": ens_info,
                        "source": "knowledge_graph"
                    })

            elif entity["type"] == "transaction":
                # Get transaction info
                tx_info = self.knowledge_graph.query_entity("Transaction", entity["text"])
                if tx_info and "error" not in tx_info:
                    results.append({
                        "type": "transaction_info",
                        "data": tx_info,
                        "source": "knowledge_graph"
                    })

            elif entity["type"] == "token_symbol":
                # Search for tokens by symbol
                token_entities = self.knowledge_graph.search_entities("Token", {"symbol": entity["text"]})
                if token_entities:
                    results.append({
                        "type": "token_info",
                        "data": {"tokens": token_entities},
                        "source": "knowledge_graph"
                    })

        return results

    def _format_context(self, query: str, kb_results: List[Dict[str, Any]],
                       kg_results: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
        """Format retrieved information into context for LLM"""
        formatted_context = f"Query: {query}\n\n"

        # Add knowledge base results
        if kb_results:
            formatted_context += "Knowledge Base Information:\n"
            for i, doc in enumerate(kb_results, 1):
                formatted_context += f"{i}. {doc.get('title', 'Document ' + str(i))}: "
                formatted_context += f"{doc.get('content', 'No content available')[:500]}...\n\n"

        # Add knowledge graph results
        if kg_results:
            formatted_context += "Knowledge Graph Information:\n"
            for result in kg_results:
                if result["type"] == "address_info":
                    addr_info = result["data"]
                    formatted_context += f"Address: {addr_info.get('id', 'Unknown')}\n"
                    formatted_context += f"Properties: {json.dumps(addr_info.get('properties', {}))}\n\n"

                elif result["type"] == "address_relationships":
                    rel_info = result["data"]
                    addr = rel_info.get("address", "Unknown")
                    tokens = rel_info.get("tokens", [])
                    sent_txs = rel_info.get("sent_transactions", [])
                    received_txs = rel_info.get("received_transactions", [])

                    formatted_context += f"Address Relationships for {addr}:\n"
                    formatted_context += f"- Owns {len(tokens)} tokens\n"
                    formatted_context += f"- Sent {len(sent_txs)} transactions\n"
                    formatted_context += f"- Received {len(received_txs)} transactions\n\n"

                elif result["type"] == "transaction_info":
                    tx_info = result["data"]
                    formatted_context += f"Transaction: {tx_info.get('id', 'Unknown')}\n"
                    formatted_context += f"Properties: {json.dumps(tx_info.get('properties', {}))}\n\n"

                elif result["type"] == "token_info":
                    tokens = result["data"].get("tokens", [])
                    formatted_context += f"Tokens ({len(tokens)}):\n"
                    for token in tokens[:3]:  # Limit to first 3 tokens
                        formatted_context += f"- {token.get('id', 'Unknown')}: {json.dumps(token.get('properties', {}))}\n"
                    formatted_context += "\n"

        # Add additional context
        if context:
            formatted_context += "Additional Context:\n"
            for key, value in context.items():
                if key not in ["query", "query_type"]:
                    formatted_context += f"{key}: {value}\n"

        return formatted_context

    async def _generate_response(self, system_prompt: str, formatted_context: str, query: str) -> Dict[str, Any]:
        """Generate response using LLM"""
        if self.client:
            # Use OpenAI if available
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo",  # Use an appropriate model
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": formatted_context},
                        {"role": "user", "content": f"Question: {query}"}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )

                return {
                    "result": response.choices[0].message.content,
                    "sources": []  # Could be enhanced to track sources
                }
            except Exception as e:
                logging.error(f"OpenAI API error: {e}")
                # Fall back to mock response

        # Mock LLM response when OpenAI is not available
        await asyncio.sleep(0.5)  # Simulate API call

        # Generate a simple mock response based on entity type
        mock_response = f"Based on the available information, I can provide insights about your query: '{query}'."

        if "address" in formatted_context.lower():
            mock_response += " The address you mentioned has transaction history that shows regular activity."

        if "transaction" in formatted_context.lower():
            mock_response += " The transaction was confirmed and represents a transfer of digital assets."

        if "token" in formatted_context.lower():
            mock_response += " The token information shows standard ERC-20 properties with market activity."

        return {
            "result": mock_response,
            "sources": []
        }

    def _calculate_confidence(self, kb_results: List[Dict[str, Any]], kg_results: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on available information"""
        # Base confidence
        confidence = 0.5

        # Adjust based on knowledge base results
        if kb_results:
            kb_factor = min(len(kb_results) * 0.1, 0.3)
            confidence += kb_factor

        # Adjust based on knowledge graph results
        if kg_results:
            kg_factor = min(len(kg_results) * 0.15, 0.4)
            confidence += kg_factor

        # Cap at 0.95 max confidence
        return min(confidence, 0.95)

    async def update_knowledge_from_query(self, query: str, context: Dict[str, Any],
                                        result: Dict[str, Any]) -> bool:
        """Update knowledge based on query and results"""
        entities = await self._extract_entities(query, context)

        updates_made = False

        # Extract and store new knowledge from results
        for entity in entities:
            if entity["type"] == "address" and entity["text"]:
                # Add address to knowledge graph
                address = entity["text"]
                properties = {"last_queried": datetime.now().isoformat()}

                # Add network info if available
                if "network" in context:
                    properties["network"] = context["network"]

                updates_made = self.knowledge_graph.add_address(address, properties) or updates_made

            elif entity["type"] == "ens_domain" and entity["text"]:
                # Add ENS domain to knowledge graph
                domain = entity["text"]
                properties = {"last_queried": datetime.now().isoformat()}

                updates_made = self.knowledge_graph.add_ens_domain(domain, properties) or updates_made

                # If we know the resolved address, link them
                if "resolved_address" in context:
                    updates_made = self.knowledge_graph.add_relationship(
                        ("ENSDomain", domain),
                        "ResolvedTo",
                        ("Address", context["resolved_address"]),
                        {"timestamp": datetime.now().isoformat()}
                    ) or updates_made

        return updates_made

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge system"""
        kb_stats = {
            "document_count": len(self.knowledge_base.documents),
            "total_content_size": sum(len(doc.get("content", "")) for doc in self.knowledge_base.documents)
        }

        kg_stats = self.knowledge_graph.get_graph_statistics()

        return {
            "knowledge_base": kb_stats,
            "knowledge_graph": kg_stats,
            "timestamp": datetime.now().isoformat()
        }