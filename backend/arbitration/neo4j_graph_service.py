"""
Neo4j Arbitration Knowledge Graph Service
==========================================
Persists arbitration clause graphs to Neo4j for advanced querying and analytics.

Graph Schema:
- Nodes: Contract, ArbitrationClause, RiskCategory
- Relationships: HAS_CLAUSE, INFLUENCES, DEPENDS_ON, SEMANTICALLY_SIMILAR

Capabilities:
- Store/retrieve arbitration graphs
- Find critical risk paths
- Clause similarity queries
- Risk propagation analysis
"""

import logging
from typing import List, Dict, Optional, Any
import os

try:
    from neo4j import GraphDatabase, Driver
    _NEO4J_AVAILABLE = True
except ImportError:
    _NEO4J_AVAILABLE = False

logger = logging.getLogger(__name__)


class Neo4jArbitrationGraphService:
    """
    Service for managing arbitration knowledge graphs in Neo4j.
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize Neo4j connection.

        Args:
            uri: Neo4j URI (default from env: NEO4J_URI)
            user: Neo4j username (default from env: NEO4J_USER)
            password: Neo4j password (default from env: NEO4J_PASSWORD)
        """
        if not _NEO4J_AVAILABLE:
            logger.warning("neo4j library not available. Graph persistence disabled.")
            self.driver = None
            return

        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password123")

        try:
            self.driver: Optional[Driver] = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
            logger.info(f"Connected to Neo4j at {self.uri}")

            # Create indexes and constraints
            self._initialize_schema()

        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.driver = None

    def _initialize_schema(self):
        """Create indexes and constraints for arbitration graph."""
        if not self.driver:
            return

        with self.driver.session() as session:
            try:
                # Contract uniqueness
                session.run("""
                    CREATE CONSTRAINT contract_id_unique IF NOT EXISTS
                    FOR (c:Contract) REQUIRE c.id IS UNIQUE
                """)

                # Clause uniqueness
                session.run("""
                    CREATE CONSTRAINT clause_id_unique IF NOT EXISTS
                    FOR (cl:ArbitrationClause) REQUIRE cl.id IS UNIQUE
                """)

                # Index on risk scores for fast filtering
                session.run("""
                    CREATE INDEX clause_risk_idx IF NOT EXISTS
                    FOR (cl:ArbitrationClause) ON (cl.compositeRisk)
                """)

                # Index on canonical nodes
                session.run("""
                    CREATE INDEX canonical_node_idx IF NOT EXISTS
                    FOR (cn:CanonicalNode) ON (cn.canonicalId)
                """)

                logger.info("Neo4j schema initialized successfully")

            except Exception as e:
                logger.error(f"Schema initialization failed: {e}")

    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    def is_available(self) -> bool:
        """Check if Neo4j is connected."""
        return self.driver is not None

    # ───────────────────────────────────────
    # CREATE OPERATIONS
    # ───────────────────────────────────────

    def create_contract_node(
        self, contract_id: str, contract_name: str, analysis_data: Dict
    ) -> bool:
        """
        Create a Contract node in Neo4j.

        Args:
            contract_id: UUID of contract
            contract_name: Contract filename
            analysis_data: ArbitrationAnalysis summary data

        Returns:
            Success boolean
        """
        if not self.driver:
            return False

        with self.driver.session() as session:
            try:
                session.run(
                    """
                    MERGE (c:Contract {id: $cid})
                    SET c.name = $name,
                        c.totalClauses = $total,
                        c.highRiskClauses = $high,
                        c.avgRisk = $avg,
                        c.disputeProbability = $prob,
                        c.expectedLoss = $loss,
                        c.createdAt = datetime()
                    """,
                    cid=contract_id,
                    name=contract_name,
                    total=analysis_data.get("total_clauses", 0),
                    high=analysis_data.get("high_risk_clauses", 0),
                    avg=analysis_data.get("avg_composite_risk", 0.0),
                    prob=analysis_data.get("dispute_probability", 0.0),
                    loss=float(analysis_data.get("expected_loss", 0)),
                )
                return True
            except Exception as e:
                logger.error(f"Failed to create contract node: {e}")
                return False

    def create_clause_nodes(
        self, contract_id: str, clauses: List[Dict]
    ) -> bool:
        """
        Create ArbitrationClause nodes and link to Contract.

        Args:
            contract_id: Parent contract UUID
            clauses: List of clause dicts with risk vectors

        Returns:
            Success boolean
        """
        if not self.driver:
            return False

        with self.driver.session() as session:
            try:
                for clause in clauses:
                    # Create clause node
                    session.run(
                        """
                        CREATE (cl:ArbitrationClause {
                            id: $id,
                            index: $index,
                            text: $text,
                            compositeRisk: $composite,
                            jurisdictionRisk: $jurisdiction,
                            costExposure: $cost,
                            institutionalRisk: $institutional,
                            tribunalStructure: $tribunal,
                            proceduralRisk: $procedural,
                            enforcementRisk: $enforcement,
                            delayDisputeRisk: $delay,
                            subcontractorPassThrough: $subcontractor,
                            riskLevel: $level
                        })
                        """,
                        id=clause["id"],
                        index=clause.get("clause_index", 0),
                        text=clause.get("clause_text", "")[:500],  # truncate
                        composite=clause.get("composite_risk", 0.0),
                        jurisdiction=clause.get("jurisdiction_risk", 0.0),
                        cost=clause.get("cost_exposure", 0.0),
                        institutional=clause.get("institutional_risk", 0.0),
                        tribunal=clause.get("tribunal_structure", 0.0),
                        procedural=clause.get("procedural_risk", 0.0),
                        enforcement=clause.get("enforcement_risk", 0.0),
                        delay=clause.get("delay_dispute_risk", 0.0),
                        subcontractor=clause.get("subcontractor_pass_through", 0.0),
                        level=clause.get("risk_level", "MEDIUM"),
                    )

                    # Link to contract
                    session.run(
                        """
                        MATCH (c:Contract {id: $cid})
                        MATCH (cl:ArbitrationClause {id: $clid})
                        MERGE (c)-[:HAS_CLAUSE {index: $index}]->(cl)
                        """,
                        cid=contract_id,
                        clid=clause["id"],
                        index=clause.get("clause_index", 0),
                    )

                return True

            except Exception as e:
                logger.error(f"Failed to create clause nodes: {e}")
                return False

    def create_canonical_graph(self, canonical_nodes: List[Dict], canonical_edges: List[tuple]) -> bool:
        """
        Create the 32-node canonical arbitration ontology in Neo4j.

        Args:
            canonical_nodes: List of canonical clause definitions
            canonical_edges: List of (source, target, type, weight) tuples

        Returns:
            Success boolean
        """
        if not self.driver:
            return False

        with self.driver.session() as session:
            try:
                # Create canonical nodes
                for node in canonical_nodes:
                    session.run(
                        """
                        MERGE (cn:CanonicalNode {canonicalId: $cid})
                        SET cn.name = $name,
                            cn.category = $category,
                            cn.baseRisk = $risk
                        """,
                        cid=node["id"],
                        name=node["name"],
                        category=node["category"],
                        risk=node["base_risk"],
                    )

                # Create edges
                for (src, tgt, rel_type, weight) in canonical_edges:
                    session.run(
                        f"""
                        MATCH (a:CanonicalNode {{canonicalId: $src}})
                        MATCH (b:CanonicalNode {{canonicalId: $tgt}})
                        MERGE (a)-[r:{rel_type}]->(b)
                        SET r.weight = $weight
                        """,
                        src=src,
                        tgt=tgt,
                        weight=weight,
                    )

                logger.info("Canonical arbitration graph created successfully")
                return True

            except Exception as e:
                logger.error(f"Failed to create canonical graph: {e}")
                return False

    def create_clause_relationships(
        self, relationships: List[Dict]
    ) -> bool:
        """
        Create SEMANTICALLY_SIMILAR or INFLUENCES relationships between clauses.

        Args:
            relationships: List of {from_id, to_id, type, weight} dicts

        Returns:
            Success boolean
        """
        if not self.driver:
            return False

        with self.driver.session() as session:
            try:
                for rel in relationships:
                    session.run(
                        f"""
                        MATCH (a:ArbitrationClause {{id: $from}})
                        MATCH (b:ArbitrationClause {{id: $to}})
                        MERGE (a)-[r:{rel['type']}]->(b)
                        SET r.weight = $weight
                        """,
                        **{"from": rel["from_id"], "to": rel["to_id"], "weight": rel["weight"]},
                    )
                return True
            except Exception as e:
                logger.error(f"Failed to create clause relationships: {e}")
                return False

    # ───────────────────────────────────────
    # QUERY OPERATIONS
    # ───────────────────────────────────────

    def get_contract_graph(self, contract_id: str) -> Optional[Dict]:
        """
        Retrieve full arbitration graph for a contract.

        Args:
            contract_id: Contract UUID

        Returns:
            Dict with nodes and edges for visualization
        """
        if not self.driver:
            return None

        with self.driver.session() as session:
            try:
                # Get contract node
                contract_result = session.run(
                    """
                    MATCH (c:Contract {id: $cid})
                    RETURN c
                    """,
                    cid=contract_id,
                )
                contract_record = contract_result.single()

                if not contract_record:
                    return None

                # Get all clauses
                clauses_result = session.run(
                    """
                    MATCH (c:Contract {id: $cid})-[:HAS_CLAUSE]->(cl:ArbitrationClause)
                    RETURN cl
                    ORDER BY cl.index
                    """,
                    cid=contract_id,
                )

                nodes = []
                for record in clauses_result:
                    cl = record["cl"]
                    nodes.append({
                        "id": cl["id"],
                        "type": "clause",
                        "text": cl.get("text", "")[:100],
                        "riskLevel": cl.get("riskLevel", "MEDIUM"),
                        "compositeRisk": cl.get("compositeRisk", 0.0),
                    })

                # Get relationships
                edges_result = session.run(
                    """
                    MATCH (c:Contract {id: $cid})-[:HAS_CLAUSE]->(cl1:ArbitrationClause)
                    MATCH (cl1)-[r]->(cl2:ArbitrationClause)
                    RETURN cl1.id AS source, cl2.id AS target, type(r) AS relType, r.weight AS weight
                    """,
                    cid=contract_id,
                )

                edges = []
                for record in edges_result:
                    edges.append({
                        "source": record["source"],
                        "target": record["target"],
                        "type": record["relType"],
                        "weight": record.get("weight", 1.0),
                    })

                return {"nodes": nodes, "edges": edges}

            except Exception as e:
                logger.error(f"Failed to get contract graph: {e}")
                return None

    def find_critical_risk_paths(
        self, contract_id: str, min_risk: float = 0.60
    ) -> List[List[str]]:
        """
        Find paths of connected high-risk clauses using graph traversal.

        Args:
            contract_id: Contract UUID
            min_risk: Minimum risk threshold

        Returns:
            List of paths (list of clause IDs)
        """
        if not self.driver:
            return []

        with self.driver.session() as session:
            try:
                result = session.run(
                    """
                    MATCH (c:Contract {id: $cid})-[:HAS_CLAUSE]->(start:ArbitrationClause)
                    WHERE start.compositeRisk >= $minRisk
                    MATCH path = (start)-[:INFLUENCES|DEPENDS_ON*1..3]->(end:ArbitrationClause)
                    WHERE end.compositeRisk >= $minRisk
                    RETURN [node IN nodes(path) | node.id] AS pathIds
                    LIMIT 20
                    """,
                    cid=contract_id,
                    minRisk=min_risk,
                )

                paths = [record["pathIds"] for record in result]
                return paths

            except Exception as e:
                logger.error(f"Failed to find critical paths: {e}")
                return []

    def find_similar_clauses_graph(
        self, clause_id: str, min_similarity: float = 0.70, limit: int = 5
    ) -> List[Dict]:
        """
        Find semantically similar clauses using graph relationships.

        Args:
            clause_id: Source clause ID
            min_similarity: Minimum similarity weight
            limit: Max results

        Returns:
            List of {clauseId, similarity, text} dicts
        """
        if not self.driver:
            return []

        with self.driver.session() as session:
            try:
                result = session.run(
                    """
                    MATCH (cl1:ArbitrationClause {id: $clid})-[r:SEMANTICALLY_SIMILAR]->(cl2:ArbitrationClause)
                    WHERE r.weight >= $minSim
                    RETURN cl2.id AS clauseId, r.weight AS similarity, cl2.text AS text
                    ORDER BY r.weight DESC
                    LIMIT $limit
                    """,
                    clid=clause_id,
                    minSim=min_similarity,
                    limit=limit,
                )

                return [
                    {
                        "clauseId": record["clauseId"],
                        "similarity": round(record["similarity"], 4),
                        "text": record["text"],
                    }
                    for record in result
                ]

            except Exception as e:
                logger.error(f"Failed to find similar clauses: {e}")
                return []

    def compute_centrality_scores(self, contract_id: str) -> Dict[str, float]:
        """
        Compute degree centrality for all clauses in a contract graph.
        Identifies most influential clauses.

        Args:
            contract_id: Contract UUID

        Returns:
            Dict mapping clause_id -> centrality score
        """
        if not self.driver:
            return {}

        with self.driver.session() as session:
            try:
                # Use Neo4j Graph Data Science if available, else simple degree count
                result = session.run(
                    """
                    MATCH (c:Contract {id: $cid})-[:HAS_CLAUSE]->(cl:ArbitrationClause)
                    OPTIONAL MATCH (cl)-[r]-(other:ArbitrationClause)
                    WITH cl.id AS clauseId, count(r) AS degree
                    RETURN clauseId, degree
                    ORDER BY degree DESC
                    """,
                    cid=contract_id,
                )

                # Normalize to 0-1
                scores = {record["clauseId"]: record["degree"] for record in result}
                max_degree = max(scores.values()) if scores else 1
                normalized = {k: v / max_degree for k, v in scores.items()}

                return normalized

            except Exception as e:
                logger.error(f"Failed to compute centrality: {e}")
                return {}

    # ───────────────────────────────────────
    # DELETE OPERATIONS
    # ───────────────────────────────────────

    def delete_contract_graph(self, contract_id: str) -> bool:
        """
        Delete a contract and all its clauses from Neo4j.

        Args:
            contract_id: Contract UUID

        Returns:
            Success boolean
        """
        if not self.driver:
            return False

        with self.driver.session() as session:
            try:
                # Detach delete removes node and all relationships
                session.run(
                    """
                    MATCH (c:Contract {id: $cid})
                    OPTIONAL MATCH (c)-[:HAS_CLAUSE]->(cl:ArbitrationClause)
                    DETACH DELETE c, cl
                    """,
                    cid=contract_id,
                )
                return True
            except Exception as e:
                logger.error(f"Failed to delete contract graph: {e}")
                return False

    def get_full_arbitration_graph(self) -> Optional[Dict]:
        """
        Retrieve the complete arbitration knowledge graph from Neo4j.

        Returns:
            Dict with 'nodes' and 'edges' arrays for ReactFlow visualization
        """
        if not self.driver:
            logger.warning("Neo4j driver not available")
            return None

        with self.driver.session() as session:
            try:
                # Query all nodes and relationships
                result = session.run("""
                    MATCH (n)
                    OPTIONAL MATCH (n)-[r]->(m)
                    RETURN n, r, m
                """)

                nodes_dict = {}
                edges = []

                for record in result:
                    # Process source node
                    n = record['n']
                    if n:
                        node_id = n.element_id
                        if node_id not in nodes_dict:
                            labels = list(n.labels)
                            props = dict(n.items())
                            nodes_dict[node_id] = {
                                'id': node_id,
                                'data': {
                                    'label': props.get('name', props.get('text', props.get('canonicalId', labels[0] if labels else 'Node')))[:50],
                                    'type': labels[0] if labels else 'Unknown',
                                    **props
                                },
                                'position': {'x': 0, 'y': 0},  # Will be set by dagre layout
                                'style': self._get_node_style(labels[0] if labels else 'Unknown', props)
                            }

                    # Process target node and relationship
                    m = record['m']
                    r = record['r']
                    if m and r:
                        target_id = m.element_id
                        if target_id not in nodes_dict:
                            labels = list(m.labels)
                            props = dict(m.items())
                            nodes_dict[target_id] = {
                                'id': target_id,
                                'data': {
                                    'label': props.get('name', props.get('text', props.get('canonicalId', labels[0] if labels else 'Node')))[:50],
                                    'type': labels[0] if labels else 'Unknown',
                                    **props
                                },
                                'position': {'x': 0, 'y': 0},
                                'style': self._get_node_style(labels[0] if labels else 'Unknown', props)
                            }

                        edges.append({
                            'id': f'{n.element_id}-{m.element_id}',
                            'source': n.element_id,
                            'target': m.element_id,
                            'label': r.type,
                            'type': 'smoothstep'
                        })

                logger.info(f"Retrieved {len(nodes_dict)} nodes and {len(edges)} edges from Neo4j")

                return {
                    'nodes': list(nodes_dict.values()),
                    'edges': edges
                }

            except Exception as e:
                logger.error(f"Failed to retrieve full graph: {e}")
                return None

    def _get_node_style(self, node_type: str, props: Dict) -> Dict:
        """Get ReactFlow node style based on type."""
        color_map = {
            'Contract': '#9333ea',
            'ArbitrationClause': '#06b6d4',
            'CanonicalNode': '#10b981',
            'RiskCategory': '#f59e0b',
        }

        bg_color = color_map.get(node_type, '#64748b')
        border_color = bg_color

        # Highlight high-risk nodes
        if props.get('compositeRisk', 0) > 0.6 or props.get('baseRisk', 0) > 0.6:
            border_color = '#dc2626'

        return {
            'background': bg_color,
            'color': 'white',
            'border': f'2px solid {border_color}',
            'padding': 10,
            'borderRadius': 8,
        }


# Global singleton instance
_neo4j_service = None


def get_neo4j_graph_service() -> Neo4jArbitrationGraphService:
    """Get or create the global Neo4j graph service instance."""
    global _neo4j_service
    if _neo4j_service is None:
        _neo4j_service = Neo4jArbitrationGraphService()
    return _neo4j_service
