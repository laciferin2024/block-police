"""
MeTTa Knowledge Base

Implements a knowledge base using MeTTa for blockchain data representation and reasoning.
"""
from typing import Dict, List, Any, Optional, Set, Tuple
import logging
import json

# Note: In a real implementation, we would import MeTTa libraries
# Since we don't have MeTTa installed, we're creating a simplified placeholder

class MeTTaKnowledgeBase:
    """
    Simplified MeTTa-based knowledge representation system for blockchain data.

    In a full implementation, this would integrate with MeTTa/Hyperon libraries.
    For now, it serves as a structured representation placeholder.
    """

    def __init__(self):
        self._transaction_store = {}  # Stores transaction data
        self._entity_store = {}       # Stores entity data (addresses, contracts)
        self._pattern_store = {}      # Stores detected patterns
        self._relation_store = {}     # Stores relationships between entities

    def add_transaction(self, tx_hash: str, tx_data: Dict[str, Any]) -> bool:
        """Add a transaction to the knowledge base"""
        if tx_hash in self._transaction_store:
            return False

        self._transaction_store[tx_hash] = tx_data

        # Extract and store entities involved in the transaction
        self._extract_entities(tx_data)

        # Check for known patterns
        self._detect_patterns(tx_hash, tx_data)

        return True

    def add_entity(self, address: str, entity_data: Dict[str, Any]) -> bool:
        """Add an entity (address or contract) to the knowledge base"""
        if address in self._entity_store:
            # Update existing entity with new data
            self._entity_store[address].update(entity_data)
        else:
            self._entity_store[address] = entity_data

        return True

    def add_relation(self, entity1: str, entity2: str, relation_type: str,
                    relation_data: Dict[str, Any]) -> bool:
        """Add a relationship between entities"""
        relation_key = f"{entity1}:{relation_type}:{entity2}"

        if relation_key in self._relation_store:
            # Update existing relation
            self._relation_store[relation_key].update(relation_data)
        else:
            self._relation_store[relation_key] = relation_data

        return True

    def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Get transaction data by hash"""
        return self._transaction_store.get(tx_hash)

    def get_entity(self, address: str) -> Optional[Dict[str, Any]]:
        """Get entity data by address"""
        return self._entity_store.get(address)

    def get_relations(self, entity: str) -> List[Dict[str, Any]]:
        """Get all relations for an entity"""
        relations = []

        for rel_key, rel_data in self._relation_store.items():
            parts = rel_key.split(':')
            if len(parts) == 3:
                e1, rel_type, e2 = parts
                if e1 == entity or e2 == entity:
                    relations.append({
                        "entity1": e1,
                        "entity2": e2,
                        "type": rel_type,
                        "data": rel_data
                    })

        return relations

    def query_fund_flow(self, source_address: str, depth: int = 3) -> List[Dict[str, Any]]:
        """
        Query the knowledge base for fund flow from a source address.

        Args:
            source_address: Starting address
            depth: Maximum depth of fund flow to trace

        Returns:
            List of transaction paths representing fund flows
        """
        paths = []
        visited = set()

        self._trace_fund_flow(source_address, [], paths, visited, depth)

        return paths

    def _trace_fund_flow(self, address: str, current_path: List[Dict[str, Any]],
                        paths: List[List[Dict[str, Any]]], visited: Set[str], depth: int):
        """Recursive helper for fund flow tracing"""
        if depth <= 0 or address in visited:
            return

        visited.add(address)

        # Find all outgoing transfers from this address
        outgoing = []
        for tx_hash, tx_data in self._transaction_store.items():
            if tx_data.get("from") == address:
                outgoing.append((tx_hash, tx_data))

        # Sort by timestamp (most recent first)
        outgoing.sort(key=lambda x: x[1].get("timestamp", 0), reverse=True)

        for tx_hash, tx_data in outgoing:
            to_address = tx_data.get("to")
            if to_address:
                # Add this transaction to the current path
                current_path.append({
                    "tx_hash": tx_hash,
                    "from": address,
                    "to": to_address,
                    "value": tx_data.get("value", 0),
                    "timestamp": tx_data.get("timestamp", 0)
                })

                # If this is a leaf node or we've reached max depth, add the path
                if depth == 1 or to_address in visited:
                    paths.append(current_path.copy())

                # Recurse deeper
                self._trace_fund_flow(to_address, current_path, paths, visited, depth - 1)

                # Backtrack
                current_path.pop()

    def _extract_entities(self, tx_data: Dict[str, Any]) -> None:
        """Extract entities from transaction data"""
        from_addr = tx_data.get("from")
        to_addr = tx_data.get("to")

        if from_addr:
            if from_addr not in self._entity_store:
                self._entity_store[from_addr] = {"type": "address", "transactions": []}
            self._entity_store[from_addr]["transactions"].append(tx_data.get("hash"))

        if to_addr:
            if to_addr not in self._entity_store:
                self._entity_store[to_addr] = {"type": "address", "transactions": []}
            self._entity_store[to_addr]["transactions"].append(tx_data.get("hash"))

    def _detect_patterns(self, tx_hash: str, tx_data: Dict[str, Any]) -> None:
        """Detect patterns in transaction data"""
        # Check for large transfers
        value = int(tx_data.get("value", "0"), 16) if isinstance(tx_data.get("value"), str) else tx_data.get("value", 0)
        if value > 100 * 10**18:  # > 100 ETH
            pattern_key = f"large_transfer:{tx_hash}"
            self._pattern_store[pattern_key] = {
                "type": "large_transfer",
                "tx_hash": tx_hash,
                "value": value,
                "timestamp": tx_data.get("timestamp", 0)
            }

        # Check for contract creation
        if not tx_data.get("to") and tx_data.get("input", "0x") != "0x":
            pattern_key = f"contract_creation:{tx_hash}"
            self._pattern_store[pattern_key] = {
                "type": "contract_creation",
                "tx_hash": tx_hash,
                "creator": tx_data.get("from"),
                "timestamp": tx_data.get("timestamp", 0)
            }

    def detect_suspicious_patterns(self) -> List[Dict[str, Any]]:
        """
        Detect suspicious transaction patterns in the knowledge base.

        Returns:
            List of suspicious patterns detected
        """
        suspicious = []

        # Check for splitting patterns (one-to-many transfers)
        self._detect_splitting_patterns(suspicious)

        # Check for merging patterns (many-to-one transfers)
        self._detect_merging_patterns(suspicious)

        # Check for cyclic transfers
        self._detect_cyclic_transfers(suspicious)

        return suspicious

    def _detect_splitting_patterns(self, suspicious: List[Dict[str, Any]]) -> None:
        """Detect fund splitting patterns (one-to-many)"""
        # Group transactions by from address and timestamp window
        from_groups = {}

        for tx_hash, tx_data in self._transaction_store.items():
            from_addr = tx_data.get("from")
            timestamp = tx_data.get("timestamp", 0)

            if from_addr:
                # Group by 1-hour windows
                time_window = timestamp - (timestamp % 3600)
                key = f"{from_addr}:{time_window}"

                if key not in from_groups:
                    from_groups[key] = []

                from_groups[key].append((tx_hash, tx_data))

        # Check for groups with many outgoing transfers
        for key, txs in from_groups.items():
            if len(txs) >= 5:  # 5+ transfers in the same hour
                from_addr = key.split(":")[0]

                # Check if transfers go to distinct addresses
                to_addrs = set(tx_data.get("to") for _, tx_data in txs if tx_data.get("to"))

                if len(to_addrs) >= 3:  # 3+ distinct recipients
                    suspicious.append({
                        "type": "fund_splitting",
                        "from_address": from_addr,
                        "recipient_count": len(to_addrs),
                        "transaction_count": len(txs),
                        "transactions": [tx_hash for tx_hash, _ in txs]
                    })

    def _detect_merging_patterns(self, suspicious: List[Dict[str, Any]]) -> None:
        """Detect fund merging patterns (many-to-one)"""
        # Group transactions by to address and timestamp window
        to_groups = {}

        for tx_hash, tx_data in self._transaction_store.items():
            to_addr = tx_data.get("to")
            timestamp = tx_data.get("timestamp", 0)

            if to_addr:
                # Group by 1-hour windows
                time_window = timestamp - (timestamp % 3600)
                key = f"{to_addr}:{time_window}"

                if key not in to_groups:
                    to_groups[key] = []

                to_groups[key].append((tx_hash, tx_data))

        # Check for groups with many incoming transfers
        for key, txs in to_groups.items():
            if len(txs) >= 5:  # 5+ transfers in the same hour
                to_addr = key.split(":")[0]

                # Check if transfers come from distinct addresses
                from_addrs = set(tx_data.get("from") for _, tx_data in txs if tx_data.get("from"))

                if len(from_addrs) >= 3:  # 3+ distinct senders
                    suspicious.append({
                        "type": "fund_merging",
                        "to_address": to_addr,
                        "sender_count": len(from_addrs),
                        "transaction_count": len(txs),
                        "transactions": [tx_hash for tx_hash, _ in txs]
                    })

    def _detect_cyclic_transfers(self, suspicious: List[Dict[str, Any]]) -> None:
        """Detect cyclic transfer patterns"""
        # Build directed graph of transfers
        graph = {}

        for tx_hash, tx_data in self._transaction_store.items():
            from_addr = tx_data.get("from")
            to_addr = tx_data.get("to")

            if from_addr and to_addr:
                if from_addr not in graph:
                    graph[from_addr] = {}

                if to_addr not in graph[from_addr]:
                    graph[from_addr][to_addr] = []

                graph[from_addr][to_addr].append(tx_hash)

        # Check for cycles using DFS
        for start_addr in graph.keys():
            visited = set()
            path = []

            cycle = self._find_cycle(graph, start_addr, visited, path)

            if cycle:
                suspicious.append({
                    "type": "cyclic_transfers",
                    "addresses": cycle,
                    "transactions": self._get_cycle_transactions(graph, cycle)
                })

    def _find_cycle(self, graph: Dict[str, Dict[str, List[str]]],
                   current: str, visited: Set[str], path: List[str]) -> List[str]:
        """Helper for cycle detection using DFS"""
        visited.add(current)
        path.append(current)

        if current in graph:
            for neighbor in graph[current]:
                if neighbor not in visited:
                    result = self._find_cycle(graph, neighbor, visited, path)
                    if result:
                        return result
                elif neighbor in path:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:]

        path.pop()
        return []

    def _get_cycle_transactions(self, graph: Dict[str, Dict[str, List[str]]],
                              cycle: List[str]) -> List[str]:
        """Get transactions forming a cycle"""
        transactions = []

        for i in range(len(cycle)):
            from_addr = cycle[i]
            to_addr = cycle[(i + 1) % len(cycle)]

            if from_addr in graph and to_addr in graph[from_addr]:
                transactions.extend(graph[from_addr][to_addr])

        return transactions

    def save_to_file(self, filepath: str) -> bool:
        """Save knowledge base to a file"""
        try:
            data = {
                "transactions": self._transaction_store,
                "entities": self._entity_store,
                "patterns": self._pattern_store,
                "relations": self._relation_store
            }

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

            return True
        except Exception as e:
            logging.error(f"Failed to save knowledge base: {e}")
            return False

    def load_from_file(self, filepath: str) -> bool:
        """Load knowledge base from a file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            self._transaction_store = data.get("transactions", {})
            self._entity_store = data.get("entities", {})
            self._pattern_store = data.get("patterns", {})
            self._relation_store = data.get("relations", {})

            return True
        except Exception as e:
            logging.error(f"Failed to load knowledge base: {e}")
            return False