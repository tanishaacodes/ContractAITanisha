"""
Graph-Based Negotiation Advisor
=================================
Uses graph analysis to prioritize clauses for negotiation.

Ranking Factors:
1. Risk Score (40%) - Inherent clause risk
2. Network Centrality (30%) - How connected/influential the clause is
3. Downstream Impact (20%) - How many other clauses it affects
4. Risk Amplification (10%) - Does it amplify risk to others?

Output:
- Priority ranking (HIGH/MEDIUM/LOW)
- Negotiation rationale
- Suggested modifications
"""

import networkx as nx
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class NegotiationAdvisor:
    """Analyzes graph to determine negotiation priorities"""

    # Priority thresholds
    HIGH_PRIORITY_THRESHOLD = 0.7
    MEDIUM_PRIORITY_THRESHOLD = 0.4

    def __init__(self):
        pass

    def generate_negotiation_advice(self, graph: nx.DiGraph, risk_propagation_data: Dict = None) -> List[Dict[str, Any]]:
        """
        Generate prioritized negotiation recommendations.

        Args:
            graph: NetworkX DiGraph with clause nodes and edges
            risk_propagation_data: Optional risk propagation results for context

        Returns:
            List of negotiation advice dicts, sorted by priority
        """
        if graph.number_of_nodes() == 0:
            return []

        advice_list = []

        for node in graph.nodes():
            node_data = graph.nodes[node]

            # Calculate negotiation priority score
            priority_score = self._calculate_priority_score(graph, node, node_data, risk_propagation_data)

            # Determine priority level
            if priority_score >= self.HIGH_PRIORITY_THRESHOLD:
                priority = "HIGH"
                color = "#dc2626"  # red-600
            elif priority_score >= self.MEDIUM_PRIORITY_THRESHOLD:
                priority = "MEDIUM"
                color = "#f59e0b"  # amber-500
            else:
                priority = "LOW"
                color = "#10b981"  # green-500

            # Generate rationale
            rationale = self._generate_rationale(graph, node, node_data, priority_score, risk_propagation_data)

            # Get suggested actions
            suggestions = self._generate_suggestions(graph, node, node_data, priority)

            advice_list.append({
                "clause_id": str(node),
                "clause_type": node_data.get('clause_type', 'general'),
                "priority": priority,
                "priority_score": round(priority_score, 3),
                "priority_color": color,
                "rationale": rationale,
                "suggestions": suggestions,
                "risk_score": node_data.get('risk_score', 0),
                "importance": node_data.get('importance', 0),
                "affects_clauses": list(graph.successors(node)),
                "affected_by_clauses": list(graph.predecessors(node)),
            })

        # Sort by priority score (highest first)
        advice_list.sort(key=lambda x: x['priority_score'], reverse=True)

        return advice_list

    def _calculate_priority_score(
        self,
        graph: nx.DiGraph,
        node: Any,
        node_data: Dict,
        risk_propagation_data: Dict = None
    ) -> float:
        """
        Calculate negotiation priority score (0-1).

        Weighted formula:
        - 40% base risk score
        - 30% network centrality (importance)
        - 20% downstream impact (out-degree)
        - 10% risk amplification
        """
        # Factor 1: Base risk score (40%)
        risk_score = node_data.get('risk_score', 0.0)
        risk_factor = risk_score * 0.4

        # Factor 2: Network centrality (30%)
        importance = node_data.get('importance', 0.0)
        centrality_factor = importance * 0.3

        # Factor 3: Downstream impact (20%)
        out_degree = graph.out_degree(node)
        max_out_degree = max(dict(graph.out_degree()).values()) if graph.number_of_nodes() > 1 else 1
        downstream_factor = (out_degree / max(max_out_degree, 1)) * 0.2

        # Factor 4: Risk amplification (10%)
        # Check if this clause has risk-amplified edges
        amplification = 0.0
        for _, _, edge_data in graph.out_edges(node, data=True):
            if edge_data.get('risk_amplified', False):
                amplification = 1.0
                break
        amplification_factor = amplification * 0.1

        # Check if it's a hotspot from risk propagation
        hotspot_bonus = 0.0
        if risk_propagation_data and 'hotspots' in risk_propagation_data:
            hotspot_ids = [h['clause_id'] for h in risk_propagation_data['hotspots']]
            if str(node) in hotspot_ids:
                hotspot_bonus = 0.1

        total_score = risk_factor + centrality_factor + downstream_factor + amplification_factor + hotspot_bonus

        return min(total_score, 1.0)  # Cap at 1.0

    def _generate_rationale(
        self,
        graph: nx.DiGraph,
        node: Any,
        node_data: Dict,
        priority_score: float,
        risk_propagation_data: Dict = None
    ) -> str:
        """Generate human-readable negotiation rationale"""
        clause_type = node_data.get('clause_type', 'general')
        risk_score = node_data.get('risk_score', 0)
        out_degree = graph.out_degree(node)

        reasons = []

        # Risk-based reasoning
        if risk_score >= 0.7:
            reasons.append(f"This {clause_type} clause carries high inherent risk (score: {risk_score:.2f})")
        elif risk_score >= 0.5:
            reasons.append(f"This clause has moderate risk (score: {risk_score:.2f})")

        # Network impact reasoning
        if out_degree >= 3:
            reasons.append(f"It directly impacts {out_degree} other contractual provisions")
        elif out_degree > 0:
            reasons.append(f"It affects {out_degree} related clause(s)")

        # Hotspot reasoning
        if risk_propagation_data and 'hotspots' in risk_propagation_data:
            hotspot_ids = [h['clause_id'] for h in risk_propagation_data['hotspots']]
            if str(node) in hotspot_ids:
                reasons.append("It accumulates risk from multiple upstream clauses")

        # Centrality reasoning
        importance = node_data.get('importance', 0)
        if importance >= 0.6:
            reasons.append("It is a central node in the contract's risk network")

        if not reasons:
            reasons.append("Standard clause with limited cross-dependencies")

        return ". ".join(reasons) + "."

    def _generate_suggestions(
        self,
        graph: nx.DiGraph,
        node: Any,
        node_data: Dict,
        priority: str
    ) -> List[str]:
        """Generate negotiation suggestions based on clause type and priority"""
        clause_type = node_data.get('clause_type', 'general').lower()
        suggestions = []

        if priority == "HIGH":
            # High-priority negotiation tactics
            if "indemnity" in clause_type:
                suggestions.extend([
                    "Negotiate liability cap specific to indemnity obligations",
                    "Add carve-outs for third-party IP claims",
                    "Require insurance backing for indemnity obligations"
                ])
            elif "liability" in clause_type or "limitation" in clause_type:
                suggestions.extend([
                    "Reduce liability cap to 1x annual contract value",
                    "Add exceptions for gross negligence only",
                    "Exclude consequential damages from liability"
                ])
            elif "termination" in clause_type:
                suggestions.extend([
                    "Extend notice period for termination for convenience",
                    "Add mutual termination rights",
                    "Negotiate wind-down provisions"
                ])
            elif "payment" in clause_type:
                suggestions.extend([
                    "Extend payment terms (Net 60 → Net 90)",
                    "Add early payment discounts",
                    "Negotiate late fee caps"
                ])
            else:
                suggestions.append("Seek material revisions or removal of this clause")

        elif priority == "MEDIUM":
            # Medium-priority suggestions
            suggestions.extend([
                "Request clarifying language to reduce ambiguity",
                "Negotiate specific performance metrics or timelines",
                "Add mutual obligations or reciprocal language"
            ])

        else:
            # Low-priority suggestions
            suggestions.append("Acceptable as-is or minor wording improvements")

        return suggestions


def generate_negotiation_advice(graph: nx.DiGraph, risk_propagation_data: Dict = None) -> List[Dict[str, Any]]:
    """
    Convenience function to generate negotiation advice.

    Args:
        graph: NetworkX DiGraph with clause nodes
        risk_propagation_data: Optional risk propagation results

    Returns:
        List of negotiation advice dicts
    """
    advisor = NegotiationAdvisor()
    return advisor.generate_negotiation_advice(graph, risk_propagation_data)
