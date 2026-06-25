"""
Clause Interaction Graph Builder
==================================
Builds a NetworkX graph representing semantic relationships between contract clauses.

Graph Structure:
- Nodes: Clauses (with risk score, type, text attributes)
- Edges: Semantic connections (e.g., indemnity → liability, termination → payment)
- Weights: Strength of interaction (0-1)

This graph powers:
- Risk propagation simulation
- Negotiation priority ranking
- What-If scenario analysis
"""

import networkx as nx
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ClauseGraphBuilder:
    """Builds interaction graphs from contract clauses"""

    # Semantic interaction patterns - these define how clauses affect each other
    INTERACTION_PATTERNS = [
        # (clause_type_1, clause_type_2, weight, rationale)
        ("indemnity", "liability", 0.9, "Indemnity directly triggers liability caps"),
        ("indemnity", "insurance", 0.8, "Indemnity requires insurance backing"),
        ("liability", "termination", 0.7, "Liability breaches can cause termination"),
        ("termination", "payment", 0.8, "Termination affects payment obligations"),
        ("payment", "late_fees", 0.9, "Payment defaults trigger penalties"),
        ("confidentiality", "termination", 0.6, "Confidentiality breaches enable termination"),
        ("warranty", "indemnity", 0.8, "Warranty breaches trigger indemnity"),
        ("intellectual_property", "indemnity", 0.7, "IP violations trigger indemnity"),
        ("force_majeure", "termination", 0.6, "Force majeure enables termination"),
        ("dispute_resolution", "termination", 0.5, "Dispute process delays termination"),
        ("limitation_of_liability", "indemnity", 0.9, "Liability caps limit indemnity exposure"),
        ("service_level", "payment", 0.7, "SLA failures affect payment/penalties"),
        ("audit", "termination", 0.5, "Audit violations can cause termination"),
        ("non_compete", "termination", 0.6, "Non-compete enforced post-termination"),
        ("assignment", "termination", 0.4, "Unauthorized assignment enables termination"),
    ]

    def __init__(self):
        self.graph = None

    def _infer_risk_score(self, clause_type: str, clause_text: str) -> float:
        """
        Infer risk score from clause type if not explicitly set.

        Args:
            clause_type: Clause type or name
            clause_text: Clause text content

        Returns:
            Risk score between 0.0 and 1.0
        """
        clause_type_lower = clause_type.lower()

        # High-risk clause types
        high_risk_keywords = [
            'indemnity', 'indemnification', 'liability', 'termination',
            'penalty', 'damages', 'breach', 'warranty', 'guarantee'
        ]

        # Medium-risk clause types
        medium_risk_keywords = [
            'payment', 'fee', 'insurance', 'confidentiality', 'intellectual property',
            'ip', 'non-compete', 'non-disclosure', 'assignment', 'force majeure'
        ]

        # Check for high-risk keywords
        for keyword in high_risk_keywords:
            if keyword in clause_type_lower:
                return 0.75  # High risk

        # Check for medium-risk keywords
        for keyword in medium_risk_keywords:
            if keyword in clause_type_lower:
                return 0.55  # Medium risk

        # Default to moderate risk
        return 0.35

    def build_interaction_graph(self, clauses: List[Any]) -> nx.DiGraph:
        """
        Build a directed graph from clauses.

        Args:
            clauses: List of Clause model instances

        Returns:
            NetworkX DiGraph with nodes and weighted edges
        """
        self.graph = nx.DiGraph()

        # Add clause nodes
        for clause in clauses:
            # Get clause text from available fields (extracted_text or context_sentences or text_spans)
            clause_text = ""
            if hasattr(clause, 'extracted_text') and clause.extracted_text:
                clause_text = clause.extracted_text
            elif hasattr(clause, 'context_sentences') and clause.context_sentences:
                clause_text = clause.context_sentences
            elif hasattr(clause, 'text_spans') and clause.text_spans:
                clause_text = clause.text_spans

            # Use clause_name as type if clause_type is not set
            clause_type = clause.clause_type or clause.clause_name or "general"

            # Calculate default risk score if not present
            risk_score = clause.risk_score
            if risk_score is None:
                # Infer risk from clause type
                risk_score = self._infer_risk_score(clause_type, clause_text)

            self.graph.add_node(
                clause.id,
                clause_id=clause.id,
                clause_text=clause_text[:200] if clause_text else "",  # Truncate for memory
                clause_type=clause_type,
                risk_score=float(risk_score),
                contract_id=str(clause.contract.id)
            )

        # Add interaction edges based on semantic patterns
        self._add_semantic_edges(clauses)

        # Calculate graph metrics
        self._calculate_node_metrics()

        logger.info(f"Built clause graph: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")

        return self.graph

    def _add_semantic_edges(self, clauses: List[Any]):
        """Add edges based on clause type interactions"""
        clause_map = {c.id: c for c in clauses}

        for clause_a in clauses:
            # Get clause type from node data (already processed)
            type_a = self.graph.nodes[clause_a.id]['clause_type'].lower()

            for clause_b in clauses:
                if clause_a.id == clause_b.id:
                    continue

                type_b = self.graph.nodes[clause_b.id]['clause_type'].lower()

                # Check if there's a semantic connection
                weight = self._get_interaction_weight(type_a, type_b)

                if weight > 0:
                    self.graph.add_edge(
                        clause_a.id,
                        clause_b.id,
                        weight=weight,
                        interaction_type=f"{type_a}_affects_{type_b}"
                    )

        # Add risk-based connections (high-risk clauses affect connected clauses)
        self._add_risk_propagation_edges(clauses)

    def _get_interaction_weight(self, type_a: str, type_b: str) -> float:
        """Get interaction weight between two clause types"""
        # Normalize clause names to match common patterns
        type_a_normalized = self._normalize_clause_type(type_a)
        type_b_normalized = self._normalize_clause_type(type_b)

        for pattern_a, pattern_b, weight, _ in self.INTERACTION_PATTERNS:
            # Match if either direction matches
            if (pattern_a in type_a_normalized and pattern_b in type_b_normalized) or \
               (pattern_b in type_a_normalized and pattern_a in type_b_normalized):
                return weight

        # Weak connection for all clauses (everything is somewhat related)
        return 0.2 if type_a != type_b else 0.0

    def _normalize_clause_type(self, clause_type: str) -> str:
        """
        Normalize clause type names to match interaction patterns.
        E.g., "Payment Terms" -> "payment", "Indemnification Clause" -> "indemnity"
        """
        clause_lower = clause_type.lower()

        # Mapping common variations to canonical names
        if 'payment' in clause_lower or 'fee' in clause_lower:
            return 'payment'
        if 'terminat' in clause_lower:  # Matches "termination", "terminate"
            return 'termination'
        if 'indemn' in clause_lower:
            return 'indemnity'
        if 'liabilit' in clause_lower:
            return 'liability'
        if 'warrant' in clause_lower:
            return 'warranty'
        if 'confident' in clause_lower or 'nda' in clause_lower:
            return 'confidentiality'
        if 'intellectual' in clause_lower or ' ip' in clause_lower:
            return 'intellectual_property'
        if 'insurance' in clause_lower:
            return 'insurance'
        if 'force' in clause_lower and 'majeure' in clause_lower:
            return 'force_majeure'
        if 'dispute' in clause_lower:
            return 'dispute_resolution'
        if 'late' in clause_lower and ('fee' in clause_lower or 'penalty' in clause_lower):
            return 'late_fees'
        if 'service' in clause_lower and 'level' in clause_lower:
            return 'service_level'
        if 'audit' in clause_lower:
            return 'audit'
        if 'non' in clause_lower and 'compete' in clause_lower:
            return 'non_compete'
        if 'assign' in clause_lower:
            return 'assignment'
        if 'limitation' in clause_lower and 'liability' in clause_lower:
            return 'limitation_of_liability'

        # Return original if no match
        return clause_lower

    def _add_risk_propagation_edges(self, clauses: List[Any]):
        """
        Add edges from high-risk clauses to related clauses.
        High-risk clauses have amplified impact on the contract.
        """
        high_risk_clauses = [c for c in clauses if (c.risk_score or 0) >= 0.7]

        for hr_clause in high_risk_clauses:
            for other_clause in clauses:
                if hr_clause.id == other_clause.id:
                    continue

                # If edge already exists, amplify it
                if self.graph.has_edge(hr_clause.id, other_clause.id):
                    edge_data = self.graph[hr_clause.id][other_clause.id]
                    # Amplify existing edge weight
                    edge_data['weight'] = min(1.0, edge_data['weight'] * 1.3)
                    edge_data['risk_amplified'] = True

    def _calculate_node_metrics(self):
        """Calculate centrality and importance metrics for each node"""
        if self.graph.number_of_nodes() == 0:
            return

        try:
            # Degree centrality - how connected is this clause?
            degree_centrality = nx.degree_centrality(self.graph)

            # Betweenness centrality - does this clause connect risk clusters?
            betweenness_centrality = nx.betweenness_centrality(self.graph)

            # PageRank - overall importance in risk propagation
            pagerank = nx.pagerank(self.graph, weight='weight')

            # Add metrics to nodes
            for node in self.graph.nodes():
                self.graph.nodes[node]['degree_centrality'] = degree_centrality.get(node, 0)
                self.graph.nodes[node]['betweenness_centrality'] = betweenness_centrality.get(node, 0)
                self.graph.nodes[node]['pagerank'] = pagerank.get(node, 0)

                # Overall importance score (weighted combination)
                importance = (
                    0.4 * degree_centrality.get(node, 0) +
                    0.3 * betweenness_centrality.get(node, 0) +
                    0.3 * pagerank.get(node, 0)
                )
                self.graph.nodes[node]['importance'] = importance

        except Exception as e:
            logger.warning(f"Could not calculate centrality metrics: {e}")

    def get_graph_summary(self) -> Dict[str, Any]:
        """
        Get a JSON-serializable summary of the graph for frontend.

        Returns:
            Dict with nodes, edges, and metrics
        """
        if not self.graph:
            return {"nodes": [], "edges": []}

        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            nodes.append({
                "id": str(node_id),
                "clause_id": str(data.get("clause_id")),
                "clause_type": data.get("clause_type"),
                "risk_score": data.get("risk_score", 0),
                "importance": data.get("importance", 0),
                "degree_centrality": data.get("degree_centrality", 0),
            })

        edges = []
        for source, target, data in self.graph.edges(data=True):
            edges.append({
                "source": str(source),
                "target": str(target),
                "weight": data.get("weight", 0),
                "interaction_type": data.get("interaction_type", ""),
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "metrics": {
                "total_nodes": self.graph.number_of_nodes(),
                "total_edges": self.graph.number_of_edges(),
                "density": nx.density(self.graph) if self.graph.number_of_nodes() > 0 else 0,
            }
        }


def build_interaction_graph(clauses: List[Any]) -> nx.DiGraph:
    """
    Convenience function to build clause interaction graph.

    Args:
        clauses: List of Clause model instances

    Returns:
        NetworkX DiGraph
    """
    builder = ClauseGraphBuilder()
    return builder.build_interaction_graph(clauses)


def get_graph_summary(graph: nx.DiGraph) -> Dict[str, Any]:
    """
    Get JSON-serializable graph summary.

    Args:
        graph: NetworkX DiGraph

    Returns:
        Dict with nodes, edges, metrics
    """
    builder = ClauseGraphBuilder()
    builder.graph = graph
    return builder.get_graph_summary()
