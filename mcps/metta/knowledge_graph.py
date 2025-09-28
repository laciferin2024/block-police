"""
MeTTa Knowledge Graph Module

Provides enhanced knowledge representation using SingularityNET's MeTTa system
with graph-based knowledge structures for blockchain data.
"""
from typing import Dict, List, Any, Optional, Set, Tuple
import logging
import json
import time
from datetime import datetime

try:
    from hyperon import MeTTa as metta, E, S, ValueAtom
except ImportError:
    logging.warning("metta_python not found; using mock implementation")
    # Mock implementation for when metta_python is not available
    class MockMeTTa:
        class SpaceAtom:
            def __init__(self, *args, **kwargs):
                self.atoms = {}
                self.name = kwargs.get("name", "MockSpace")

            def add_atom(self, atom, parent=None):
                self.atoms[atom.name] = atom
                return True

            def query(self, pattern):
                return []

            def get_atoms(self):
                return list(self.atoms.values())

        class Atom:
            def __init__(self, expr=None, name=None):
                self.expr = expr
                self.name = name or str(time.time())

            def __str__(self):
                return f"Atom({self.name})"

        def __init__(self):
            self.spaces = {}

        def new_space(self, name="default"):
            space = self.SpaceAtom(name=name)
            self.spaces[name] = space
            return space

        def parse_atom(self, expr):
            return self.Atom(expr=expr)

    metta = MockMeTTa()


class KnowledgeGraph:
    """Knowledge graph implementation using MeTTa"""

    def __init__(self, name: str = "blockchain_knowledge"):
        """Initialize a new knowledge graph"""
        self.name = name
        self.space = metta.new_space(name)
        self.entities = set()  # Track added entities
        self.relationships = set()  # Track added relationships
        self.last_updated = datetime.now()

    def add_entity(self, entity_type: str, entity_id: str, properties: Dict[str, Any] = None) -> bool:
        """
        Add an entity to the knowledge graph

        Args:
            entity_type: The type of entity (e.g., 'address', 'token', 'transaction')
            entity_id: Unique identifier for the entity
            properties: Dictionary of properties for the entity

        Returns:
            True if successfully added
        """
        if not properties:
            properties = {}

        # Create an entity atom with type and ID
        entity_key = f"{entity_type}:{entity_id}"

        if entity_key in self.entities:
            # Entity already exists, update it
            return self._update_entity(entity_type, entity_id, properties)

        # Construct the entity atom
        entity_expr = f"(Entity {entity_type} {entity_id})"
        entity_atom = metta.parse_atom(entity_expr)

        # Add entity to space
        success = self.space.add_atom(entity_atom)

        if success:
            # Add each property as a separate atom
            for prop_name, prop_value in properties.items():
                prop_expr = f"(Property {entity_type} {entity_id} {prop_name} {json.dumps(prop_value)})"
                prop_atom = metta.parse_atom(prop_expr)
                self.space.add_atom(prop_atom)

            self.entities.add(entity_key)
            self.last_updated = datetime.now()

        return success

    def _update_entity(self, entity_type: str, entity_id: str, properties: Dict[str, Any]) -> bool:
        """Update an existing entity's properties"""
        for prop_name, prop_value in properties.items():
            prop_expr = f"(Property {entity_type} {entity_id} {prop_name} {json.dumps(prop_value)})"
            prop_atom = metta.parse_atom(prop_expr)
            self.space.add_atom(prop_atom)

        self.last_updated = datetime.now()
        return True

    def add_relationship(self, from_entity: Tuple[str, str],
                         relationship_type: str,
                         to_entity: Tuple[str, str],
                         properties: Dict[str, Any] = None) -> bool:
        """
        Add a relationship between two entities

        Args:
            from_entity: Tuple of (entity_type, entity_id) for source entity
            relationship_type: Type of relationship (e.g., 'owns', 'created', 'transferred')
            to_entity: Tuple of (entity_type, entity_id) for target entity
            properties: Optional properties for the relationship

        Returns:
            True if successfully added
        """
        if not properties:
            properties = {}

        # Extract entity information
        from_type, from_id = from_entity
        to_type, to_id = to_entity

        # Ensure both entities exist
        from_key = f"{from_type}:{from_id}"
        to_key = f"{to_type}:{to_id}"

        if from_key not in self.entities:
            self.add_entity(from_type, from_id)

        if to_key not in self.entities:
            self.add_entity(to_type, to_id)

        # Create relationship key for tracking
        rel_key = f"{from_key}:{relationship_type}:{to_key}"

        # Construct the relationship atom
        rel_expr = f"(Relationship {from_type} {from_id} {relationship_type} {to_type} {to_id})"
        rel_atom = metta.parse_atom(rel_expr)

        # Add relationship to space
        success = self.space.add_atom(rel_atom)

        if success:
            # Add properties for the relationship
            for prop_name, prop_value in properties.items():
                prop_expr = f"(RelProperty {from_type} {from_id} {relationship_type} {to_type} {to_id} {prop_name} {json.dumps(prop_value)})"
                prop_atom = metta.parse_atom(prop_expr)
                self.space.add_atom(prop_atom)

            self.relationships.add(rel_key)
            self.last_updated = datetime.now()

        return success

    def query_entity(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """
        Query properties of an entity

        Args:
            entity_type: The type of entity
            entity_id: Identifier of the entity

        Returns:
            Dictionary of properties
        """
        entity_key = f"{entity_type}:{entity_id}"

        if entity_key not in self.entities:
            return {"error": f"Entity {entity_key} not found"}

        # Query pattern to find properties
        query_pattern = f"(Property {entity_type} {entity_id} $prop_name $prop_value)"
        results = self.space.query(metta.parse_atom(query_pattern))

        # Build property dictionary
        properties = {}
        for result in results:
            try:
                prop_name = result.get("prop_name")
                prop_value_json = result.get("prop_value")
                if prop_name and prop_value_json:
                    properties[prop_name] = json.loads(prop_value_json)
            except Exception as e:
                logging.error(f"Error parsing property result: {e}")

        return {
            "type": entity_type,
            "id": entity_id,
            "properties": properties
        }

    def query_relationships(self, entity_type: str, entity_id: str,
                           direction: str = "outgoing") -> List[Dict[str, Any]]:
        """
        Query relationships of an entity

        Args:
            entity_type: The type of entity
            entity_id: Identifier of the entity
            direction: 'outgoing', 'incoming', or 'both'

        Returns:
            List of relationships
        """
        results = []

        if direction in ["outgoing", "both"]:
            # Query outgoing relationships
            query_pattern = f"(Relationship {entity_type} {entity_id} $rel_type $to_type $to_id)"
            outgoing = self.space.query(metta.parse_atom(query_pattern))

            for result in outgoing:
                rel_type = result.get("rel_type")
                to_type = result.get("to_type")
                to_id = result.get("to_id")

                if rel_type and to_type and to_id:
                    # Get relationship properties
                    rel_props = self._get_relationship_properties(
                        entity_type, entity_id, rel_type, to_type, to_id
                    )

                    results.append({
                        "type": rel_type,
                        "direction": "outgoing",
                        "from": {"type": entity_type, "id": entity_id},
                        "to": {"type": to_type, "id": to_id},
                        "properties": rel_props
                    })

        if direction in ["incoming", "both"]:
            # Query incoming relationships
            query_pattern = f"(Relationship $from_type $from_id $rel_type {entity_type} {entity_id})"
            incoming = self.space.query(metta.parse_atom(query_pattern))

            for result in incoming:
                from_type = result.get("from_type")
                from_id = result.get("from_id")
                rel_type = result.get("rel_type")

                if from_type and from_id and rel_type:
                    # Get relationship properties
                    rel_props = self._get_relationship_properties(
                        from_type, from_id, rel_type, entity_type, entity_id
                    )

                    results.append({
                        "type": rel_type,
                        "direction": "incoming",
                        "from": {"type": from_type, "id": from_id},
                        "to": {"type": entity_type, "id": entity_id},
                        "properties": rel_props
                    })

        return results

    def _get_relationship_properties(self, from_type: str, from_id: str,
                                    rel_type: str, to_type: str, to_id: str) -> Dict[str, Any]:
        """Get properties for a specific relationship"""
        query_pattern = f"(RelProperty {from_type} {from_id} {rel_type} {to_type} {to_id} $prop_name $prop_value)"
        results = self.space.query(metta.parse_atom(query_pattern))

        properties = {}
        for result in results:
            try:
                prop_name = result.get("prop_name")
                prop_value_json = result.get("prop_value")
                if prop_name and prop_value_json:
                    properties[prop_name] = json.loads(prop_value_json)
            except Exception as e:
                logging.error(f"Error parsing relationship property: {e}")

        return properties

    def search_entities(self, entity_type: Optional[str] = None,
                       property_filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search for entities matching certain criteria

        Args:
            entity_type: Optional filter for entity type
            property_filters: Dictionary of property name/value pairs to filter by

        Returns:
            List of matching entities
        """
        # Start with all entities or filter by type
        if entity_type:
            query_pattern = f"(Entity {entity_type} $entity_id)"
        else:
            query_pattern = "(Entity $entity_type $entity_id)"

        # Get basic entities
        entities_results = self.space.query(metta.parse_atom(query_pattern))

        # Extract entity types and IDs
        entities = []
        for result in entities_results:
            e_type = result.get("entity_type") or entity_type
            e_id = result.get("entity_id")

            if e_type and e_id:
                # Get full entity with properties
                entity = self.query_entity(e_type, e_id)

                # Apply property filters if specified
                if property_filters:
                    match = True
                    for prop_name, prop_value in property_filters.items():
                        entity_value = entity.get("properties", {}).get(prop_name)
                        if entity_value != prop_value:
                            match = False
                            break

                    if match:
                        entities.append(entity)
                else:
                    entities.append(entity)

        return entities

    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph"""
        # Entity counts by type
        entity_types = {}
        for entity_key in self.entities:
            entity_type = entity_key.split(":")[0]
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

        # Relationship counts by type
        relationship_types = {}
        for rel_key in self.relationships:
            rel_parts = rel_key.split(":")
            if len(rel_parts) >= 3:
                rel_type = rel_parts[2]
                relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1

        return {
            "name": self.name,
            "total_entities": len(self.entities),
            "total_relationships": len(self.relationships),
            "entity_types": entity_types,
            "relationship_types": relationship_types,
            "last_updated": self.last_updated.isoformat()
        }

    def export_to_json(self) -> str:
        """Export the knowledge graph to a JSON string"""
        # Get all entities with their properties
        entities = []
        for entity_key in self.entities:
            entity_type, entity_id = entity_key.split(":", 1)
            entity = self.query_entity(entity_type, entity_id)
            entities.append(entity)

        # Get all relationships
        relationships = []
        for rel_key in self.relationships:
            rel_parts = rel_key.split(":")
            if len(rel_parts) >= 5:
                from_type, from_id = rel_parts[0].split(":", 1)
                rel_type = rel_parts[2]
                to_type, to_id = rel_parts[3].split(":", 1)

                # Get relationship properties
                props = self._get_relationship_properties(
                    from_type, from_id, rel_type, to_type, to_id
                )

                relationships.append({
                    "from": {"type": from_type, "id": from_id},
                    "type": rel_type,
                    "to": {"type": to_type, "id": to_id},
                    "properties": props
                })

        # Construct full graph data
        graph_data = {
            "metadata": {
                "name": self.name,
                "exported_at": datetime.now().isoformat(),
                "entities_count": len(entities),
                "relationships_count": len(relationships)
            },
            "entities": entities,
            "relationships": relationships
        }

        return json.dumps(graph_data, indent=2)

    def import_from_json(self, json_data: str) -> bool:
        """Import knowledge graph from a JSON string"""
        try:
            data = json.loads(json_data)

            # Import entities
            for entity in data.get("entities", []):
                entity_type = entity.get("type")
                entity_id = entity.get("id")
                properties = entity.get("properties", {})

                if entity_type and entity_id:
                    self.add_entity(entity_type, entity_id, properties)

            # Import relationships
            for relationship in data.get("relationships", []):
                from_entity = (relationship.get("from", {}).get("type"),
                              relationship.get("from", {}).get("id"))
                rel_type = relationship.get("type")
                to_entity = (relationship.get("to", {}).get("type"),
                            relationship.get("to", {}).get("id"))
                properties = relationship.get("properties", {})

                if all(from_entity) and rel_type and all(to_entity):
                    self.add_relationship(from_entity, rel_type, to_entity, properties)

            return True
        except Exception as e:
            logging.error(f"Error importing knowledge graph: {e}")
            return False


class BlockchainKnowledgeGraph(KnowledgeGraph):
    """Specialized knowledge graph for blockchain data"""

    def __init__(self, name: str = "blockchain_data"):
        super().__init__(name)
        self._setup_schema()

    def _setup_schema(self):
        """Setup schema for blockchain entities and relationships"""
        # Define basic schema atoms
        schema_atoms = [
            # Entity types
            "(EntityType Address)",
            "(EntityType Token)",
            "(EntityType Transaction)",
            "(EntityType Block)",
            "(EntityType Contract)",
            "(EntityType ENSDomain)",

            # Relationship types
            "(RelationType Owns)",
            "(RelationType Created)",
            "(RelationType SentTo)",
            "(RelationType ReceivedFrom)",
            "(RelationType Deployed)",
            "(RelationType Interacted)",
            "(RelationType Contains)"
        ]

        # Add schema atoms to space
        for atom_expr in schema_atoms:
            atom = metta.parse_atom(atom_expr)
            self.space.add_atom(atom)

    def add_address(self, address: str, properties: Dict[str, Any] = None) -> bool:
        """Add an address entity"""
        if properties is None:
            properties = {}
        return self.add_entity("Address", address, properties)

    def add_token(self, token_address: str, properties: Dict[str, Any] = None) -> bool:
        """Add a token entity"""
        if properties is None:
            properties = {}
        return self.add_entity("Token", token_address, properties)

    def add_transaction(self, tx_hash: str, properties: Dict[str, Any] = None) -> bool:
        """Add a transaction entity"""
        if properties is None:
            properties = {}
        return self.add_entity("Transaction", tx_hash, properties)

    def add_contract(self, contract_address: str, properties: Dict[str, Any] = None) -> bool:
        """Add a contract entity"""
        if properties is None:
            properties = {}
        return self.add_entity("Contract", contract_address, properties)

    def add_ens_domain(self, domain_name: str, properties: Dict[str, Any] = None) -> bool:
        """Add an ENS domain entity"""
        if properties is None:
            properties = {}
        return self.add_entity("ENSDomain", domain_name, properties)

    def link_address_to_token(self, address: str, token_address: str,
                             amount: float, relationship: str = "Owns") -> bool:
        """Link an address to a token with balance information"""
        return self.add_relationship(
            ("Address", address),
            relationship,
            ("Token", token_address),
            {"amount": amount}
        )

    def link_address_to_transaction(self, address: str, tx_hash: str,
                                  direction: str, value: float = 0.0) -> bool:
        """Link an address to a transaction"""
        if direction.lower() == "sent":
            return self.add_relationship(
                ("Address", address),
                "SentTo",
                ("Transaction", tx_hash),
                {"value": value}
            )
        elif direction.lower() == "received":
            return self.add_relationship(
                ("Address", address),
                "ReceivedFrom",
                ("Transaction", tx_hash),
                {"value": value}
            )
        else:
            return False

    def link_addresses(self, from_address: str, to_address: str,
                      tx_hash: str, value: float = 0.0) -> bool:
        """Link two addresses via a transaction"""
        # First add the transaction if not exists
        self.add_transaction(tx_hash, {"value": value})

        # Link sender to transaction
        self.link_address_to_transaction(from_address, tx_hash, "sent", value)

        # Link receiver to transaction
        self.link_address_to_transaction(to_address, tx_hash, "received", value)

        return True

    def get_address_relationships(self, address: str) -> Dict[str, Any]:
        """Get comprehensive information about an address"""
        # Get basic entity info
        entity = self.query_entity("Address", address)

        # Get relationships
        relationships = self.query_relationships("Address", address, "both")

        # Categorize relationships
        tokens_owned = []
        transactions_sent = []
        transactions_received = []
        contracts_deployed = []

        for rel in relationships:
            rel_type = rel["type"]
            direction = rel["direction"]

            if rel_type == "Owns" and direction == "outgoing":
                # Token ownership
                token_id = rel["to"]["id"]
                amount = rel["properties"].get("amount", 0)
                token_data = self.query_entity("Token", token_id)

                tokens_owned.append({
                    "address": token_id,
                    "amount": amount,
                    "details": token_data.get("properties", {})
                })

            elif rel_type == "SentTo" and direction == "outgoing":
                # Sent transactions
                tx_hash = rel["to"]["id"]
                value = rel["properties"].get("value", 0)
                tx_data = self.query_entity("Transaction", tx_hash)

                transactions_sent.append({
                    "hash": tx_hash,
                    "value": value,
                    "details": tx_data.get("properties", {})
                })

            elif rel_type == "ReceivedFrom" and direction == "outgoing":
                # Received transactions
                tx_hash = rel["to"]["id"]
                value = rel["properties"].get("value", 0)
                tx_data = self.query_entity("Transaction", tx_hash)

                transactions_received.append({
                    "hash": tx_hash,
                    "value": value,
                    "details": tx_data.get("properties", {})
                })

            elif rel_type == "Deployed" and direction == "outgoing":
                # Deployed contracts
                contract_addr = rel["to"]["id"]
                contract_data = self.query_entity("Contract", contract_addr)

                contracts_deployed.append({
                    "address": contract_addr,
                    "details": contract_data.get("properties", {})
                })

        return {
            "address": address,
            "properties": entity.get("properties", {}),
            "tokens": tokens_owned,
            "sent_transactions": transactions_sent,
            "received_transactions": transactions_received,
            "deployed_contracts": contracts_deployed
        }

    def search_similar_addresses(self, address: str) -> List[Dict[str, Any]]:
        """Find addresses with similar transaction patterns"""
        # This would typically use pattern matching in MeTTa
        # For now, implement a simple version based on common transactions

        # Get transactions for this address
        sent_txs = set()
        received_txs = set()

        relationships = self.query_relationships("Address", address, "outgoing")
        for rel in relationships:
            if rel["type"] == "SentTo" and rel["to"]["type"] == "Transaction":
                sent_txs.add(rel["to"]["id"])
            elif rel["type"] == "ReceivedFrom" and rel["to"]["type"] == "Transaction":
                received_txs.add(rel["to"]["id"])

        # Find addresses with common transactions
        similar_addresses = {}

        # Get all addresses
        all_addresses = self.search_entities("Address")
        for addr_entity in all_addresses:
            addr_id = addr_entity["id"]
            if addr_id == address:
                continue  # Skip self

            # Check for common transactions
            addr_rels = self.query_relationships("Address", addr_id, "outgoing")
            addr_sent = set()
            addr_received = set()

            for rel in addr_rels:
                if rel["type"] == "SentTo" and rel["to"]["type"] == "Transaction":
                    addr_sent.add(rel["to"]["id"])
                elif rel["type"] == "ReceivedFrom" and rel["to"]["type"] == "Transaction":
                    addr_received.add(rel["to"]["id"])

            # Calculate similarity scores
            sent_overlap = len(sent_txs.intersection(addr_sent))
            received_overlap = len(received_txs.intersection(addr_received))
            total_overlap = sent_overlap + received_overlap

            if total_overlap > 0:
                similar_addresses[addr_id] = {
                    "address": addr_id,
                    "similarity_score": total_overlap,
                    "common_sent": sent_overlap,
                    "common_received": received_overlap
                }

        # Sort by similarity score
        results = list(similar_addresses.values())
        results.sort(key=lambda x: x["similarity_score"], reverse=True)

        return results[:10]  # Return top 10 similar addresses
