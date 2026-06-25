"""
Concept Correlation Graph Schema
=================================
Neo4j schema for contract concept correlation and risk topology.

Node Types:
- Concept: Legal concepts (Termination, Liability, IP Rights, etc.)
- ContractType: Contract archetypes (MSA, SaaS, NDA, Employment, EPC)
- Contract: Individual contracts with concept profiles

Relationship Types:
- CORRELATES_WITH: Concept <-> Concept (Pearson correlation weight)
- HAS_CONCEPT: ContractType -> Concept (strength 0-1)
- EXHIBITS_CONCEPT: Contract -> Concept (extracted strength from clauses)
- IS_TYPE: Contract -> ContractType (archetype classification)

Properties:
- Concept: id, name, color, description, avg_strength
- ContractType: id, name, description, edge_density
- CORRELATES_WITH: weight (Pearson correlation), pearson
- HAS_CONCEPT: strength (archetype concept strength 0-1)
- EXHIBITS_CONCEPT: strength (extracted from contract), clause_count, updated_at

Author: PrimeContractAI System
"""

import logging
from typing import Dict, List, Any, Optional
from contractai.neo4j_config import get_neo4j_driver, check_neo4j_available
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Constants from concept_correlation_service.py
CONCEPTS = [
    "Termination",
    "Liability",
    "Indemnification",
    "IP Rights",
    "Risk Allocation",
    "Arbitration",
    "Penalty",
    "Obligations",
    "Data Protection",
    "Force Majeure",
]

CONCEPT_COLORS = {
    "Termination": "#F16667",
    "Liability": "#F79767",
    "Indemnification": "#FFD86E",
    "IP Rights": "#9063CD",
    "Risk Allocation": "#F16667",
    "Arbitration": "#4C8EDA",
    "Penalty": "#E8474C",
    "Obligations": "#F79767",
    "Data Protection": "#68BC00",
    "Force Majeure": "#06B6D4",
}

CONCEPT_ROLES = {
    'Termination': 'Governs exit conditions and contract end triggers. High in employment and MSA.',
    'Liability': 'Caps financial exposure. Central in MSA and EPC — anchor concept.',
    'Indemnification': 'Shifts loss between parties. Tightly coupled with Liability across archetypes.',
    'IP Rights': 'Defines ownership of created works. Dominant in NDA and SaaS.',
    'Risk Allocation': 'Distributes contract risk. Core to EPC construction contracts.',
    'Arbitration': 'Dispute resolution mechanism. Concentrated in high-value contracts.',
    'Penalty': 'Financial consequences for breach. EPC-dominant with force multipliers.',
    'Obligations': 'Party duties and performance standards. Strong in Employment and MSA.',
    'Data Protection': 'GDPR/privacy compliance. Rising importance in SaaS/digital contracts.',
    'Force Majeure': 'Unforeseeable event carve-outs. Amplified by EPC and global contracts.',
}

CONTRACT_ARCHETYPES = {
    "MSA": [0.82, 0.91, 0.76, 0.65, 0.71, 0.55, 0.60, 0.78, 0.50, 0.45],
    "SaaS": [0.70, 0.88, 0.69, 0.92, 0.64, 0.40, 0.30, 0.55, 0.85, 0.60],
    "NDA": [0.30, 0.40, 0.35, 0.95, 0.20, 0.10, 0.05, 0.15, 0.30, 0.10],
    "Employment": [0.75, 0.60, 0.55, 0.50, 0.45, 0.25, 0.20, 0.70, 0.40, 0.35],
    "EPC": [0.90, 0.95, 0.85, 0.40, 0.92, 0.75, 0.88, 0.60, 0.35, 0.80],
}

CONTRACT_TYPE_PROFILES = {
    "MSA": {
        "description": "Master Service Agreement — dense liability/indemnification cluster",
        "dominant_concepts": ["Liability", "Indemnification", "Termination", "Obligations"],
        "edge_density": "high",
    },
    "SaaS": {
        "description": "SaaS Agreement — IP and data protection focused",
        "dominant_concepts": ["IP Rights", "Data Protection", "Liability"],
        "edge_density": "medium",
    },
    "NDA": {
        "description": "Non-Disclosure Agreement — confidentiality/IP dominated, sparse network",
        "dominant_concepts": ["IP Rights", "Termination"],
        "edge_density": "low",
    },
    "Employment": {
        "description": "Employment Agreement — obligations and termination centric",
        "dominant_concepts": ["Obligations", "Termination", "Indemnification"],
        "edge_density": "medium",
    },
    "EPC": {
        "description": "EPC Construction Contract — maximum risk/penalty density",
        "dominant_concepts": ["Risk Allocation", "Penalty", "Liability", "Force Majeure"],
        "edge_density": "very_high",
    },
}


# Graph schema constraints and indices
SCHEMA_CYPHER = """
CREATE CONSTRAINT concept_id_unique IF NOT EXISTS
FOR (c:Concept) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT contract_type_id_unique IF NOT EXISTS
FOR (ct:ContractType) REQUIRE ct.id IS UNIQUE;

CREATE INDEX concept_name_idx IF NOT EXISTS
FOR (c:Concept) ON (c.name);

CREATE INDEX contract_type_name_idx IF NOT EXISTS
FOR (ct:ContractType) ON (ct.name);

CREATE INDEX concept_avg_strength_idx IF NOT EXISTS
FOR (c:Concept) ON (c.avg_strength);
"""


class ConceptGraphSchema:
    """
    Neo4j schema manager for concept correlation graph.
    Follows RiskGraphSchema pattern with singleton access.
    """

    def __init__(self):
        self.driver = None
        self.connected = False
        self._initialize()

    def _initialize(self):
        """Initialize Neo4j connection"""
        try:
            if check_neo4j_available():
                self.driver = get_neo4j_driver()
                if self.driver:
                    self.driver.verify_connectivity()
                    self.connected = True
                    logger.info("[CONCEPT-GRAPH] Connected to Neo4j")
                else:
                    logger.warning("[CONCEPT-GRAPH] Neo4j driver not available")
                    self.connected = False
            else:
                logger.warning("[CONCEPT-GRAPH] Neo4j not available")
                self.connected = False
        except Exception as e:
            logger.error(f"[CONCEPT-GRAPH] Initialization failed: {e}")
            self.connected = False

    def apply_schema(self) -> bool:
        """Apply graph schema (constraints and indices)"""
        if not self.connected:
            logger.warning("[CONCEPT-GRAPH] Cannot apply schema - not connected")
            return False

        try:
            with self.driver.session() as session:
                statements = [stmt.strip() for stmt in SCHEMA_CYPHER.strip().split(';') if stmt.strip()]

                for statement in statements:
                    if statement and not statement.startswith('--'):
                        try:
                            session.run(statement)
                            logger.debug(f"[CONCEPT-GRAPH] Applied: {statement[:50]}...")
                        except Exception as e:
                            logger.debug(f"[CONCEPT-GRAPH] Schema statement skipped (may exist): {e}")

            logger.info("[CONCEPT-GRAPH] Schema applied successfully")
            return True

        except Exception as e:
            logger.error(f"[CONCEPT-GRAPH] Schema application failed: {e}", exc_info=True)
            return False

    def seed_concept_nodes(self) -> bool:
        """Seed 10 concept nodes with colors and computed avg strength"""
        if not self.connected:
            logger.warning("[CONCEPT-GRAPH] Cannot seed concepts - not connected")
            return False

        try:
            # Compute average strength across all archetypes
            df = pd.DataFrame(CONTRACT_ARCHETYPES, index=CONCEPTS).T
            avg_strengths = df.mean().to_dict()

            with self.driver.session() as session:
                for concept in CONCEPTS:
                    concept_id = f"CONCEPT_{concept.replace(' ', '_').upper()}"
                    session.run("""
                        MERGE (c:Concept {id: $concept_id})
                        SET c.name = $name,
                            c.color = $color,
                            c.avg_strength = $avg_strength,
                            c.description = $description
                    """, concept_id=concept_id,
                         name=concept,
                         color=CONCEPT_COLORS.get(concept, "#4C8EDA"),
                         avg_strength=round(avg_strengths.get(concept, 0.5), 3),
                         description=CONCEPT_ROLES.get(concept, f"Legal concept: {concept}"))

            logger.info(f"[CONCEPT-GRAPH] Seeded {len(CONCEPTS)} concept nodes")
            return True

        except Exception as e:
            logger.error(f"[CONCEPT-GRAPH] Concept seeding failed: {e}", exc_info=True)
            return False

    def seed_contract_type_nodes(self) -> bool:
        """Seed 5 contract type nodes and HAS_CONCEPT relationships"""
        if not self.connected:
            logger.warning("[CONCEPT-GRAPH] Cannot seed contract types - not connected")
            return False

        try:
            with self.driver.session() as session:
                for contract_type, strengths in CONTRACT_ARCHETYPES.items():
                    profile = CONTRACT_TYPE_PROFILES.get(contract_type, {})
                    type_id = f"TYPE_{contract_type}"

                    # Create ContractType node
                    session.run("""
                        MERGE (ct:ContractType {id: $type_id})
                        SET ct.name = $name,
                            ct.description = $description,
                            ct.edge_density = $edge_density
                    """, type_id=type_id,
                         name=contract_type,
                         description=profile.get("description", ""),
                         edge_density=profile.get("edge_density", "medium"))

                    # Create HAS_CONCEPT relationships
                    for i, concept in enumerate(CONCEPTS):
                        strength = strengths[i]
                        concept_id = f"CONCEPT_{concept.replace(' ', '_').upper()}"

                        session.run("""
                            MATCH (ct:ContractType {id: $type_id})
                            MATCH (c:Concept {id: $concept_id})
                            MERGE (ct)-[r:HAS_CONCEPT]->(c)
                            SET r.strength = $strength
                        """, type_id=type_id,
                             concept_id=concept_id,
                             strength=round(strength, 3))

            logger.info(f"[CONCEPT-GRAPH] Seeded {len(CONTRACT_ARCHETYPES)} contract type nodes")
            return True

        except Exception as e:
            logger.error(f"[CONCEPT-GRAPH] Contract type seeding failed: {e}", exc_info=True)
            return False

    def seed_concept_correlations(self, corr_matrix: pd.DataFrame, threshold: float = 0.50) -> bool:
        """Create CORRELATES_WITH relationships using Pearson correlation"""
        if not self.connected:
            logger.warning("[CONCEPT-GRAPH] Cannot seed correlations - not connected")
            return False

        try:
            with self.driver.session() as session:
                seen = set()
                correlation_count = 0

                for c1 in CONCEPTS:
                    for c2 in CONCEPTS:
                        if c1 == c2:
                            continue

                        pair = tuple(sorted([c1, c2]))
                        if pair in seen:
                            continue
                        seen.add(pair)

                        weight = float(corr_matrix.loc[c1, c2])
                        if weight < threshold:
                            continue

                        c1_id = f"CONCEPT_{c1.replace(' ', '_').upper()}"
                        c2_id = f"CONCEPT_{c2.replace(' ', '_').upper()}"

                        session.run("""
                            MATCH (c1:Concept {id: $c1_id})
                            MATCH (c2:Concept {id: $c2_id})
                            MERGE (c1)-[r:CORRELATES_WITH]-(c2)
                            SET r.weight = $weight,
                                r.pearson = $weight
                        """, c1_id=c1_id,
                             c2_id=c2_id,
                             weight=round(weight, 3))

                        correlation_count += 1

            logger.info(f"[CONCEPT-GRAPH] Created {correlation_count} concept correlations (threshold={threshold})")
            return True

        except Exception as e:
            logger.error(f"[CONCEPT-GRAPH] Correlation seeding failed: {e}", exc_info=True)
            return False

    def query_concept_graph(self, contract_type: str = "ALL") -> Dict[str, Any]:
        """Query Neo4j for concept graph (nodes + edges)"""
        if not self.connected:
            return {"nodes": [], "edges": []}

        try:
            with self.driver.session() as session:
                if contract_type == "ALL":
                    # Global graph: all concepts with avg strength
                    nodes_result = session.run("""
                        MATCH (c:Concept)
                        RETURN c.id as id, c.name as name, c.color as color,
                               c.avg_strength as strength
                        ORDER BY c.name
                    """)
                else:
                    # Type-specific graph: concepts with archetype strength
                    nodes_result = session.run("""
                        MATCH (ct:ContractType {name: $contract_type})-[r:HAS_CONCEPT]->(c:Concept)
                        RETURN c.id as id, c.name as name, c.color as color,
                               r.strength as strength
                        ORDER BY c.name
                    """, contract_type=contract_type)

                nodes = []
                for record in nodes_result:
                    nodes.append({
                        "id": record["name"],  # Use name for React Flow compatibility
                        "name": record["name"],
                        "color": record["color"],
                        "strength": float(record["strength"] or 0.5)
                    })

                # Get correlations
                edges_result = session.run("""
                    MATCH (c1:Concept)-[r:CORRELATES_WITH]-(c2:Concept)
                    WHERE id(c1) < id(c2)
                    RETURN c1.name as source, c2.name as target,
                           r.weight as weight, r.pearson as pearson
                """)

                edges = []
                for record in edges_result:
                    edges.append({
                        "source": record["source"],
                        "target": record["target"],
                        "weight": float(record["weight"]),
                        "pearson": float(record["pearson"])
                    })

                return {"nodes": nodes, "edges": edges}

        except Exception as e:
            logger.error(f"[CONCEPT-GRAPH] Query failed: {e}", exc_info=True)
            return {"nodes": [], "edges": []}

    def create_contract_concept_profile(
        self,
        contract_id: str,
        contract_type: str,
        concept_strengths: Dict[str, float]
    ) -> bool:
        """Create contract node with EXHIBITS_CONCEPT relationships"""
        if not self.connected:
            return False

        try:
            contract_id_str = str(contract_id)

            with self.driver.session() as session:
                # Create Contract node
                session.run("""
                    MERGE (con:Contract {id: $contract_id})
                    SET con.created_at = datetime(),
                        con.updated_at = datetime()
                """, contract_id=contract_id_str)

                # Link to ContractType
                if contract_type and contract_type in CONTRACT_ARCHETYPES:
                    type_id = f"TYPE_{contract_type}"
                    session.run("""
                        MATCH (con:Contract {id: $contract_id})
                        MATCH (ct:ContractType {id: $type_id})
                        MERGE (con)-[:IS_TYPE]->(ct)
                    """, contract_id=contract_id_str, type_id=type_id)

                # Create EXHIBITS_CONCEPT relationships
                for concept, strength in concept_strengths.items():
                    if strength > 0.0:
                        concept_id = f"CONCEPT_{concept.replace(' ', '_').upper()}"
                        session.run("""
                            MATCH (con:Contract {id: $contract_id})
                            MATCH (c:Concept {id: $concept_id})
                            MERGE (con)-[r:EXHIBITS_CONCEPT]->(c)
                            SET r.strength = $strength,
                                r.updated_at = datetime()
                        """, contract_id=contract_id_str,
                             concept_id=concept_id,
                             strength=round(strength, 3))

            logger.info(f"[CONCEPT-GRAPH] Created concept profile for contract {contract_id_str}")
            return True

        except Exception as e:
            logger.error(f"[CONCEPT-GRAPH] Contract profile creation failed: {e}", exc_info=True)
            return False

    def get_contract_concept_profile(self, contract_id: str) -> Dict[str, float]:
        """Query contract's concept profile from Neo4j"""
        if not self.connected:
            return {}

        try:
            contract_id_str = str(contract_id)

            with self.driver.session() as session:
                result = session.run("""
                    MATCH (con:Contract {id: $contract_id})-[r:EXHIBITS_CONCEPT]->(c:Concept)
                    RETURN c.name as concept, r.strength as strength
                    ORDER BY r.strength DESC
                """, contract_id=contract_id_str)

                profile = {}
                for record in result:
                    profile[record["concept"]] = float(record["strength"])

                return profile

        except Exception as e:
            logger.error(f"[CONCEPT-GRAPH] Failed to retrieve contract profile: {e}", exc_info=True)
            return {}


# Singleton instance
_concept_graph_schema = None


def get_concept_graph_schema() -> ConceptGraphSchema:
    """Get singleton concept graph schema instance"""
    global _concept_graph_schema
    if _concept_graph_schema is None:
        _concept_graph_schema = ConceptGraphSchema()
    return _concept_graph_schema
