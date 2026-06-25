"""
Risk Propagation Engine
========================
Simulates how risk cascades through a contract's clause network over time.

Algorithm:
1. Identify initial high-risk clauses (risk_score >= threshold)
2. Propagate risk through graph edges with dampening
3. Generate timeline showing risk activation at each step (T0, T1, T2...)
4. Track cumulative risk and hotspots

Output:
- Timeline: List of propagation steps with affected clauses
- Hotspots: Clauses that accumulate most risk
- Total risk: Aggregate risk score for the contract
"""

import networkx as nx
import logging
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)


class RiskPropagationEngine:
    """Simulates risk cascading through clause dependency graph"""

    def __init__(self, dampening_factor: float = 0.7, max_steps: int = 5):
        """
        Args:
            dampening_factor: Risk reduction per hop (0-1). Lower = faster decay.
            max_steps: Maximum propagation steps to simulate
        """
        self.dampening_factor = dampening_factor
        self.max_steps = max_steps

    def propagate_risk(self, graph: nx.DiGraph) -> Dict[str, Any]:
        """
        Simulate risk propagation through the clause graph.

        Args:
            graph: NetworkX DiGraph with clause nodes and interaction edges

        Returns:
            Dict containing:
            - timeline: List of propagation steps
            - total_risk: Cumulative risk score
            - hotspots: High-risk accumulation nodes
            - risk_map: Final risk distribution
        """
        if graph.number_of_nodes() == 0:
            return self._empty_result()

        # Initialize risk levels
        risk_map = {}
        for node in graph.nodes():
            risk_map[node] = graph.nodes[node].get('risk_score', 0.0)

        # Track risk accumulation (separate from base risk)
        accumulated_risk = {node: 0.0 for node in graph.nodes()}

        # Timeline of propagation steps
        timeline = []

        # Step 0: Initial state
        initial_high_risk = self._get_high_risk_nodes(risk_map, threshold=0.6)
        timeline.append({
            "step": 0,
            "description": "Initial high-risk clauses identified",
            "activated_clauses": [
                {
                    "clause_id": str(node),
                    "risk_score": risk_map[node],
                    "clause_type": graph.nodes[node].get('clause_type', 'general')
                }
                for node in initial_high_risk
            ],
            "total_active": len(initial_high_risk)
        })

        # Propagation steps
        active_nodes = set(initial_high_risk)

        for step in range(1, self.max_steps + 1):
            if not active_nodes:
                break

            newly_activated = set()
            step_propagations = []

            # Propagate from each active node
            for source_node in list(active_nodes):
                source_risk = risk_map[source_node]

                # Get outgoing edges
                for target_node in graph.successors(source_node):
                    edge_data = graph[source_node][target_node]
                    edge_weight = edge_data.get('weight', 0.5)

                    # Calculate propagated risk with dampening
                    propagated_risk = source_risk * edge_weight * (self.dampening_factor ** step)

                    # Only propagate if significant
                    if propagated_risk > 0.05:
                        accumulated_risk[target_node] += propagated_risk

                        # If target node crosses risk threshold, mark as newly activated
                        total_risk = risk_map[target_node] + accumulated_risk[target_node]
                        if total_risk >= 0.4 and target_node not in active_nodes:
                            newly_activated.add(target_node)

                        step_propagations.append({
                            "from_clause": str(source_node),
                            "to_clause": str(target_node),
                            "risk_transferred": round(propagated_risk, 3),
                            "edge_type": edge_data.get('interaction_type', 'interaction')
                        })

            # Update active nodes
            active_nodes = newly_activated

            if step_propagations:
                timeline.append({
                    "step": step,
                    "description": f"Risk propagation wave {step}",
                    "propagations": step_propagations,
                    "newly_activated": [
                        {
                            "clause_id": str(node),
                            "accumulated_risk": round(accumulated_risk[node], 3),
                            "total_risk": round(risk_map[node] + accumulated_risk[node], 3),
                            "clause_type": graph.nodes[node].get('clause_type', 'general')
                        }
                        for node in newly_activated
                    ],
                    "total_active": len(active_nodes)
                })

        # Calculate final risk distribution
        final_risk_map = {
            node: risk_map[node] + accumulated_risk[node]
            for node in graph.nodes()
        }

        # Identify hotspots (top risk accumulation points)
        hotspots = self._identify_hotspots(graph, accumulated_risk, top_n=5)

        # Calculate total contract risk
        total_risk = sum(final_risk_map.values()) / len(final_risk_map) if final_risk_map else 0

        return {
            "timeline": timeline,
            "total_risk": round(total_risk, 3),
            "hotspots": hotspots,
            "risk_map": {str(k): round(v, 3) for k, v in final_risk_map.items()},
            "propagation_steps": len(timeline) - 1,  # Exclude initial step
        }

    def _get_high_risk_nodes(self, risk_map: Dict, threshold: float = 0.6) -> List:
        """Get nodes with risk above threshold"""
        return [node for node, risk in risk_map.items() if risk >= threshold]

    def _identify_hotspots(self, graph: nx.DiGraph, accumulated_risk: Dict, top_n: int = 5) -> List[Dict]:
        """
        Identify clauses that accumulated the most risk from propagation.

        Args:
            graph: Clause graph
            accumulated_risk: Risk accumulated at each node
            top_n: Number of top hotspots to return

        Returns:
            List of hotspot dicts with clause info
        """
        # Sort by accumulated risk
        sorted_nodes = sorted(
            accumulated_risk.items(),
            key=lambda x: x[1],
            reverse=True
        )

        hotspots = []
        for node, acc_risk in sorted_nodes[:top_n]:
            if acc_risk > 0.1:  # Only include significant accumulation
                hotspots.append({
                    "clause_id": str(node),
                    "accumulated_risk": round(acc_risk, 3),
                    "base_risk": round(graph.nodes[node].get('risk_score', 0), 3),
                    "total_risk": round(graph.nodes[node].get('risk_score', 0) + acc_risk, 3),
                    "clause_type": graph.nodes[node].get('clause_type', 'general'),
                    "in_degree": graph.in_degree(node),  # How many clauses feed risk into this
                })

        return hotspots

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            "timeline": [],
            "total_risk": 0.0,
            "hotspots": [],
            "risk_map": {},
            "propagation_steps": 0,
        }


def propagate_risk(graph: nx.DiGraph, dampening_factor: float = 0.7, max_steps: int = 5) -> Dict[str, Any]:
    """
    Convenience function to run risk propagation.

    Args:
        graph: NetworkX DiGraph with clause nodes
        dampening_factor: Risk decay per hop (default 0.7)
        max_steps: Max propagation steps (default 5)

    Returns:
        Propagation result with timeline, hotspots, total risk
    """
    engine = RiskPropagationEngine(dampening_factor=dampening_factor, max_steps=max_steps)
    return engine.propagate_risk(graph)
