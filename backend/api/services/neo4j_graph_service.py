"""
Neo4j Graph Service
===================
Graph database operations using Neo4j for contract risk analysis.

Features:
- Store contract graphs in Neo4j
- Advanced graph queries (Cypher)
- Risk propagation analysis
- Clause relationship discovery
- Performance optimized for large graphs
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import networkx as nx
from contractai.neo4j_config import get_neo4j_driver, check_neo4j_available

logger = logging.getLogger(__name__)


class Neo4jGraphService:
    """
    Neo4j-based graph operations for contract analysis.
    Falls back to NetworkX if Neo4j unavailable.
    """

    def __init__(self):
        self.driver = None
        self.neo4j_available = False
        self._initialize()

    def _initialize(self):
        """Initialize Neo4j connection"""
        try:
            if check_neo4j_available():
                self.driver = get_neo4j_driver()
                self.neo4j_available = True
                logger.info("[NEO4J-SERVICE] Neo4j available")
            else:
                logger.warning("[NEO4J-SERVICE] Neo4j not available, using NetworkX fallback")
        except Exception as e:
            logger.error(f"[NEO4J-SERVICE] Initialization failed: {e}")
            self.neo4j_available = False

    def create_contract_graph(
        self,
        contract_id: str,
        clauses: List[Any],
        edges: List[Tuple[str, str, Dict[str, Any]]]
    ) -> bool:
        """
        Create contract graph in Neo4j.

        Args:
            contract_id: Contract UUID
            clauses: List of clause objects/dicts
            edges: List of (source, target, properties) tuples

        Returns:
            Success boolean
        """
        if not self.neo4j_available:
            logger.warning("[NEO4J] Not available, skipping graph creation")
            return False

        try:
            with self.driver.session() as session:
                # Clear existing graph for contract
                session.run("""
                    MATCH (c:Clause {contract_id: $contract_id})
                    DETACH DELETE c
                """, contract_id=contract_id)

                # Create clause nodes
                for clause in clauses:
                    clause_id = clause.id if hasattr(clause, 'id') else clause.get('id')
                    clause_name = clause.clause_name if hasattr(clause, 'clause_name') else clause.get('clause_name', '')
                    clause_type = clause.clause_type if hasattr(clause, 'clause_type') else clause.get('clause_type', 'general')
                    risk_score = float(clause.risk_score or 0) if hasattr(clause, 'risk_score') else clause.get('risk_score', 0)
                    risk_level = clause.risk_level if hasattr(clause, 'risk_level') else clause.get('risk_level', 'LOW')

                    session.run("""
                        CREATE (c:Clause {
                            id: $id,
                            contract_id: $contract_id,
                            clause_name: $clause_name,
                            clause_type: $clause_type,
                            risk_score: $risk_score,
                            risk_level: $risk_level
                        })
                    """, id=clause_id, contract_id=contract_id, clause_name=clause_name,
                        clause_type=clause_type, risk_score=risk_score, risk_level=risk_level)

                # Create relationships
                for source, target, props in edges:
                    interaction_type = props.get('interaction_type', 'RELATES_TO')
                    weight = props.get('weight', 0.5)

                    session.run("""
                        MATCH (source:Clause {id: $source_id, contract_id: $contract_id})
                        MATCH (target:Clause {id: $target_id, contract_id: $contract_id})
                        CREATE (source)-[r:RELATES_TO {
                            interaction_type: $interaction_type,
                            weight: $weight
                        }]->(target)
                    """, source_id=source, target_id=target, contract_id=contract_id,
                        interaction_type=interaction_type, weight=weight)

                logger.info(f"[NEO4J] Created graph for contract {contract_id}")
                return True

        except Exception as e:
            logger.error(f"[NEO4J] Error creating graph: {e}", exc_info=True)
            return False

    def get_contract_graph(self, contract_id: str) -> Optional[nx.DiGraph]:
        """
        Retrieve contract graph from Neo4j as NetworkX graph.

        Args:
            contract_id: Contract UUID

        Returns:
            NetworkX DiGraph or None
        """
        if not self.neo4j_available:
            return None

        try:
            graph = nx.DiGraph()

            with self.driver.session() as session:
                # Get nodes
                result = session.run("""
                    MATCH (c:Clause {contract_id: $contract_id})
                    RETURN c.id as id, c.clause_name as name, c.clause_type as type,
                           c.risk_score as risk_score, c.risk_level as risk_level
                """, contract_id=contract_id)

                for record in result:
                    graph.add_node(
                        record['id'],
                        clause_name=record['name'],
                        clause_type=record['type'],
                        risk_score=record['risk_score'],
                        risk_level=record['risk_level']
                    )

                # Get edges
                result = session.run("""
                    MATCH (source:Clause {contract_id: $contract_id})-[r:RELATES_TO]->(target:Clause)
                    RETURN source.id as source, target.id as target,
                           r.interaction_type as interaction_type, r.weight as weight
                """, contract_id=contract_id)

                for record in result:
                    graph.add_edge(
                        record['source'],
                        record['target'],
                        interaction_type=record['interaction_type'],
                        weight=record['weight']
                    )

            logger.info(f"[NEO4J] Retrieved graph for contract {contract_id}: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
            return graph

        except Exception as e:
            logger.error(f"[NEO4J] Error retrieving graph: {e}", exc_info=True)
            return None

    def propagate_risk(self, contract_id: str, source_clause_id: str) -> Dict[str, float]:
        """
        Propagate risk from a source clause through the graph.

        Args:
            contract_id: Contract UUID
            source_clause_id: Starting clause ID

        Returns:
            Dict of {clause_id: propagated_risk_score}
        """
        if not self.neo4j_available:
            return {}

        try:
            with self.driver.session() as session:
                # Use Cypher for risk propagation
                result = session.run("""
                    MATCH path = (source:Clause {id: $source_id, contract_id: $contract_id})
                                 -[r:RELATES_TO*1..3]->(target:Clause)
                    WITH target,
                         source.risk_score as source_risk,
                         reduce(weight = 1.0, rel in relationships(path) | weight * rel.weight) as path_weight
                    RETURN target.id as clause_id,
                           source_risk * path_weight as propagated_risk
                    ORDER BY propagated_risk DESC
                """, source_id=source_clause_id, contract_id=contract_id)

                risk_scores = {}
                for record in result:
                    risk_scores[record['clause_id']] = record['propagated_risk']

                return risk_scores

        except Exception as e:
            logger.error(f"[NEO4J] Error propagating risk: {e}", exc_info=True)
            return {}

    def find_risk_clusters(self, contract_id: str) -> List[List[str]]:
        """
        Find clusters of highly connected risky clauses.

        Args:
            contract_id: Contract UUID

        Returns:
            List of clause ID lists (clusters)
        """
        if not self.neo4j_available:
            return []

        try:
            with self.driver.session() as session:
                # Find densely connected high-risk clauses
                result = session.run("""
                    MATCH (c:Clause {contract_id: $contract_id})
                    WHERE c.risk_score >= 0.6
                    CALL {
                        WITH c
                        MATCH (c)-[r:RELATES_TO]-(connected:Clause)
                        WHERE connected.risk_score >= 0.6
                        RETURN collect(DISTINCT connected.id) as cluster_members
                    }
                    RETURN c.id as clause_id, cluster_members
                    ORDER BY size(cluster_members) DESC
                    LIMIT 10
                """, contract_id=contract_id)

                clusters = []
                seen = set()

                for record in result:
                    clause_id = record['clause_id']
                    members = record['cluster_members']

                    if clause_id not in seen:
                        cluster = [clause_id] + members
                        clusters.append(list(set(cluster)))
                        seen.update(cluster)

                return clusters

        except Exception as e:
            logger.error(f"[NEO4J] Error finding clusters: {e}", exc_info=True)
            return []

    def analyze_centrality(self, contract_id: str) -> Dict[str, Dict[str, float]]:
        """
        Analyze clause centrality (importance in graph).

        Args:
            contract_id: Contract UUID

        Returns:
            Dict of {clause_id: {degree: X, betweenness: Y}}
        """
        if not self.neo4j_available:
            return {}

        try:
            # Get graph and use NetworkX algorithms
            graph = self.get_contract_graph(contract_id)
            if not graph:
                return {}

            degree_centrality = nx.degree_centrality(graph)
            betweenness_centrality = nx.betweenness_centrality(graph)

            centrality = {}
            for node in graph.nodes():
                centrality[node] = {
                    'degree': degree_centrality.get(node, 0),
                    'betweenness': betweenness_centrality.get(node, 0)
                }

            return centrality

        except Exception as e:
            logger.error(f"[NEO4J] Error analyzing centrality: {e}", exc_info=True)
            return {}

    def delete_contract_graph(self, contract_id: str) -> bool:
        """
        Delete contract graph from Neo4j.

        Args:
            contract_id: Contract UUID

        Returns:
            Success boolean
        """
        if not self.neo4j_available:
            return False

        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (c:Clause {contract_id: $contract_id})
                    DETACH DELETE c
                """, contract_id=contract_id)

                logger.info(f"[NEO4J] Deleted graph for contract {contract_id}")
                return True

        except Exception as e:
            logger.error(f"[NEO4J] Error deleting graph: {e}", exc_info=True)
            return False


# Convenience functions
def create_graph_in_neo4j(contract_id: str, clauses: List[Any], edges: List[Tuple]) -> bool:
    """Create contract graph in Neo4j"""
    service = Neo4jGraphService()
    return service.create_contract_graph(contract_id, clauses, edges)


def get_graph_from_neo4j(contract_id: str) -> Optional[nx.DiGraph]:
    """Get contract graph from Neo4j"""
    service = Neo4jGraphService()
    return service.get_contract_graph(contract_id)
