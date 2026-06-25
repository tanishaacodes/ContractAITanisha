"""
What-If Simulation Engine
===========================
Simulates the impact of removing or modifying clauses on overall contract risk.

Features:
1. simulate_remove_clause - Temporarily remove clause and recalculate risk
2. simulate_modify_clause - Test impact of clause text changes
3. Before vs After risk comparison
4. Cascading impact analysis
5. Hotspot change detection

This is non-destructive - nothing is deleted in DB or Neo4j.
The simulation runs entirely in memory on graph copies.
"""

import copy
import logging
from typing import Dict, List, Any, Optional
import networkx as nx

from .clause_graph import ClauseGraphBuilder, build_interaction_graph, get_graph_summary
from .risk_propagation import RiskPropagationEngine, propagate_risk
from .graph_negotiation_advisor import NegotiationAdvisor, generate_negotiation_advice

logger = logging.getLogger(__name__)


class WhatIfSimulator:
    """
    Graph-based What-If scenario simulator.

    Allows executives to answer:
    - "What if we remove clause X?"
    - "What if we renegotiate clause Y?"
    - "What's the risk reduction from removing high-risk clauses?"
    """

    def __init__(self):
        self.graph_builder = ClauseGraphBuilder()
        self.risk_engine = RiskPropagationEngine()
        self.negotiation_advisor = NegotiationAdvisor()

    def simulate_remove_clause(
        self,
        graph: nx.DiGraph,
        clause_id: str
    ) -> Dict[str, Any]:
        """
        Simulate impact of removing a clause from the contract.

        Args:
            graph: NetworkX DiGraph with clause nodes
            clause_id: ID of clause to remove

        Returns:
            Dict containing before/after comparison
        """
        if graph.number_of_nodes() == 0:
            return self._empty_result("empty_graph")

        # Convert clause_id to string for comparison
        clause_id_str = str(clause_id)

        # Find the node (might be stored as str or UUID)
        target_node = None
        for node in graph.nodes():
            if str(node) == clause_id_str:
                target_node = node
                break

        if target_node is None:
            return self._empty_result("clause_not_found")

        # --- BASELINE (Before removal) ---
        baseline_risk = self._calculate_total_risk(graph)
        baseline_timeline = propagate_risk(graph)
        baseline_advice = generate_negotiation_advice(graph, baseline_timeline)

        # --- SIMULATE REMOVAL ---
        simulated_graph = copy.deepcopy(graph)

        # Get clause info before removal
        removed_node_data = dict(graph.nodes[target_node])
        removed_clause_risk = removed_node_data.get('risk_score', 0)
        removed_clause_type = removed_node_data.get('clause_type', 'general')

        # Get edges that will be removed
        removed_edges = []
        for pred in list(graph.predecessors(target_node)):
            edge_data = graph[pred][target_node]
            removed_edges.append({
                "from_clause": str(pred),
                "to_clause": clause_id_str,
                "weight": edge_data.get('weight', 0),
                "type": edge_data.get('interaction_type', '')
            })
        for succ in list(graph.successors(target_node)):
            edge_data = graph[target_node][succ]
            removed_edges.append({
                "from_clause": clause_id_str,
                "to_clause": str(succ),
                "weight": edge_data.get('weight', 0),
                "type": edge_data.get('interaction_type', '')
            })

        # Remove the node
        simulated_graph.remove_node(target_node)

        # --- AFTER REMOVAL ---
        post_risk = self._calculate_total_risk(simulated_graph)
        post_timeline = propagate_risk(simulated_graph)
        post_advice = generate_negotiation_advice(simulated_graph, post_timeline)

        # Calculate delta
        risk_before = baseline_timeline.get('total_risk', baseline_risk)
        risk_after = post_timeline.get('total_risk', post_risk)
        risk_delta = risk_before - risk_after
        risk_reduction_pct = (risk_delta / risk_before * 100) if risk_before > 0 else 0

        # Identify affected clauses (those connected to removed clause)
        affected_clauses = self._identify_affected_clauses(
            graph, simulated_graph, target_node, baseline_timeline, post_timeline
        )

        # Identify hotspot changes
        hotspot_changes = self._compare_hotspots(baseline_timeline, post_timeline)

        # Negotiation priority shifts
        negotiation_changes = self._compare_negotiation_priorities(
            baseline_advice, post_advice
        )

        return {
            "success": True,
            "simulation_type": "remove_clause",
            "removed_clause": {
                "id": clause_id_str,
                "type": removed_clause_type,
                "risk_score": round(removed_clause_risk, 3),
                "connections_removed": len(removed_edges)
            },
            "delta": {
                "risk_before": round(risk_before, 3),
                "risk_after": round(risk_after, 3),
                "risk_reduction": round(risk_delta, 3),
                "risk_reduction_pct": round(risk_reduction_pct, 1),
            },
            "timeline": {
                "before": baseline_timeline,
                "after": post_timeline
            },
            "negotiation": {
                "before": self._summarize_advice(baseline_advice),
                "after": self._summarize_advice(post_advice),
                "priority_shifts": negotiation_changes
            },
            "affected_clauses": affected_clauses,
            "hotspot_changes": hotspot_changes,
            "removed_edges": removed_edges,
            "graph_metrics": {
                "nodes_before": graph.number_of_nodes(),
                "nodes_after": simulated_graph.number_of_nodes(),
                "edges_before": graph.number_of_edges(),
                "edges_after": simulated_graph.number_of_edges(),
            }
        }

    def simulate_batch_removal(
        self,
        graph: nx.DiGraph,
        clause_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Simulate removing multiple clauses at once.

        Args:
            graph: NetworkX DiGraph
            clause_ids: List of clause IDs to remove

        Returns:
            Combined simulation result
        """
        if graph.number_of_nodes() == 0:
            return self._empty_result("empty_graph")

        # --- BASELINE ---
        baseline_risk = self._calculate_total_risk(graph)
        baseline_timeline = propagate_risk(graph)

        # --- SIMULATE BATCH REMOVAL ---
        simulated_graph = copy.deepcopy(graph)
        removed_clauses = []

        for clause_id in clause_ids:
            clause_id_str = str(clause_id)
            target_node = None

            for node in simulated_graph.nodes():
                if str(node) == clause_id_str:
                    target_node = node
                    break

            if target_node is not None:
                node_data = dict(simulated_graph.nodes[target_node])
                removed_clauses.append({
                    "id": clause_id_str,
                    "type": node_data.get('clause_type', 'general'),
                    "risk_score": round(node_data.get('risk_score', 0), 3)
                })
                simulated_graph.remove_node(target_node)

        # --- AFTER BATCH REMOVAL ---
        post_timeline = propagate_risk(simulated_graph)

        risk_before = baseline_timeline.get('total_risk', baseline_risk)
        risk_after = post_timeline.get('total_risk', 0)
        risk_delta = risk_before - risk_after
        risk_reduction_pct = (risk_delta / risk_before * 100) if risk_before > 0 else 0

        return {
            "success": True,
            "simulation_type": "batch_removal",
            "removed_clauses": removed_clauses,
            "delta": {
                "risk_before": round(risk_before, 3),
                "risk_after": round(risk_after, 3),
                "risk_reduction": round(risk_delta, 3),
                "risk_reduction_pct": round(risk_reduction_pct, 1),
            },
            "timeline": {
                "before": baseline_timeline,
                "after": post_timeline
            },
            "graph_metrics": {
                "nodes_before": graph.number_of_nodes(),
                "nodes_after": simulated_graph.number_of_nodes(),
                "clauses_removed": len(removed_clauses)
            }
        }

    def _calculate_total_risk(self, graph: nx.DiGraph) -> float:
        """Calculate total risk score from graph nodes"""
        if graph.number_of_nodes() == 0:
            return 0.0

        total = sum(
            graph.nodes[n].get('risk_score', 0)
            for n in graph.nodes()
        )
        return total / graph.number_of_nodes()

    def _identify_affected_clauses(
        self,
        original_graph: nx.DiGraph,
        simulated_graph: nx.DiGraph,
        removed_node: Any,
        baseline_timeline: Dict,
        post_timeline: Dict
    ) -> List[Dict]:
        """Identify clauses whose risk changed after removal"""
        affected = []

        baseline_risk_map = baseline_timeline.get('risk_map', {})
        post_risk_map = post_timeline.get('risk_map', {})

        # Get nodes connected to removed node
        connected_nodes = set()
        for pred in original_graph.predecessors(removed_node):
            connected_nodes.add(pred)
        for succ in original_graph.successors(removed_node):
            connected_nodes.add(succ)

        for node_id in connected_nodes:
            node_id_str = str(node_id)
            original_risk = baseline_risk_map.get(node_id_str, 0)
            new_risk = post_risk_map.get(node_id_str, 0)

            if abs(original_risk - new_risk) > 0.01:  # Significant change
                node_data = original_graph.nodes.get(node_id, {})
                affected.append({
                    "clause_id": node_id_str,
                    "clause_type": node_data.get('clause_type', 'general'),
                    "risk_before": round(original_risk, 3),
                    "risk_after": round(new_risk, 3),
                    "risk_change": round(new_risk - original_risk, 3),
                    "relationship": "directly_connected"
                })

        # Sort by absolute change
        affected.sort(key=lambda x: abs(x['risk_change']), reverse=True)

        return affected[:10]  # Top 10 most affected

    def _compare_hotspots(
        self,
        baseline_timeline: Dict,
        post_timeline: Dict
    ) -> Dict[str, List[Dict]]:
        """Compare hotspots before and after simulation"""
        baseline_hotspots = {
            h['clause_id']: h
            for h in baseline_timeline.get('hotspots', [])
        }
        post_hotspots = {
            h['clause_id']: h
            for h in post_timeline.get('hotspots', [])
        }

        baseline_ids = set(baseline_hotspots.keys())
        post_ids = set(post_hotspots.keys())

        removed_hotspots = [
            baseline_hotspots[cid]
            for cid in (baseline_ids - post_ids)
        ]
        new_hotspots = [
            post_hotspots[cid]
            for cid in (post_ids - baseline_ids)
        ]
        remaining_hotspots = []
        for cid in (baseline_ids & post_ids):
            before = baseline_hotspots[cid]
            after = post_hotspots[cid]
            remaining_hotspots.append({
                "clause_id": cid,
                "risk_before": before.get('total_risk', 0),
                "risk_after": after.get('total_risk', 0),
                "change": round(
                    after.get('total_risk', 0) - before.get('total_risk', 0),
                    3
                )
            })

        return {
            "removed_hotspots": removed_hotspots,
            "new_hotspots": new_hotspots,
            "remaining_hotspots": remaining_hotspots
        }

    def _compare_negotiation_priorities(
        self,
        baseline_advice: List[Dict],
        post_advice: List[Dict]
    ) -> List[Dict]:
        """Compare negotiation priority rankings"""
        baseline_map = {a['clause_id']: a for a in baseline_advice}
        post_map = {a['clause_id']: a for a in post_advice}

        shifts = []
        for clause_id, baseline in baseline_map.items():
            if clause_id in post_map:
                post = post_map[clause_id]
                if baseline['priority'] != post['priority']:
                    shifts.append({
                        "clause_id": clause_id,
                        "priority_before": baseline['priority'],
                        "priority_after": post['priority'],
                        "score_before": baseline.get('priority_score', 0),
                        "score_after": post.get('priority_score', 0)
                    })

        return shifts

    def _summarize_advice(self, advice: List[Dict]) -> List[Dict]:
        """Summarize negotiation advice for response"""
        return [
            {
                "clause_id": a['clause_id'],
                "priority": a['priority'],
                "priority_score": a.get('priority_score', 0),
                "clause_type": a.get('clause_type', 'general')
            }
            for a in advice[:10]  # Top 10
        ]

    def _empty_result(self, reason: str) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            "success": False,
            "error": reason,
            "simulation_type": None,
            "delta": {
                "risk_before": 0,
                "risk_after": 0,
                "risk_reduction": 0,
                "risk_reduction_pct": 0
            },
            "timeline": {"before": {}, "after": {}},
            "negotiation": {"before": [], "after": [], "priority_shifts": []},
            "affected_clauses": [],
            "hotspot_changes": {"removed_hotspots": [], "new_hotspots": [], "remaining_hotspots": []}
        }


def simulate_remove_clause(graph: nx.DiGraph, clause_id: str) -> Dict[str, Any]:
    """
    Convenience function to simulate clause removal.

    Args:
        graph: NetworkX DiGraph with clause nodes
        clause_id: ID of clause to remove

    Returns:
        Simulation result with before/after comparison
    """
    simulator = WhatIfSimulator()
    return simulator.simulate_remove_clause(graph, clause_id)


def simulate_batch_removal(graph: nx.DiGraph, clause_ids: List[str]) -> Dict[str, Any]:
    """
    Convenience function to simulate batch clause removal.

    Args:
        graph: NetworkX DiGraph
        clause_ids: List of clause IDs to remove

    Returns:
        Combined simulation result
    """
    simulator = WhatIfSimulator()
    return simulator.simulate_batch_removal(graph, clause_ids)
