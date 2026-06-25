"""
Neo4j-Based Risk Propagation Service
====================================

Performs risk propagation analysis using Neo4j graph database.
Falls back to NetworkX if Neo4j is unavailable.

Author: Contract AI System
"""

import logging
from typing import Dict, List, Optional, Tuple
from django.core.exceptions import ObjectDoesNotExist
from core.models import Contract, Clause
from .neo4j_graph_service import Neo4jGraphService

logger = logging.getLogger(__name__)


class Neo4jRiskPropagationService:
    """
    Service for performing risk propagation analysis using Neo4j.
    Provides advanced graph-based risk analysis with centrality and clustering.
    """

    def __init__(self):
        self.neo4j_service = Neo4jGraphService()
        self.using_neo4j = self.neo4j_service.is_connected

    def propagate_risk_for_contract(
        self,
        contract_id: int,
        initial_risks: Optional[Dict[int, float]] = None,
        iterations: int = 5,
        damping: float = 0.85
    ) -> Dict:
        """
        Propagate risk scores through the contract graph using Neo4j.

        Args:
            contract_id: ID of the contract to analyze
            initial_risks: Optional dict of {clause_id: risk_score} to seed propagation
            iterations: Number of propagation iterations (default: 5)
            damping: Damping factor for propagation (default: 0.85)

        Returns:
            Dict containing:
            - propagated_risks: Dict of {clause_id: propagated_risk}
            - risk_clusters: List of high-risk clause clusters
            - central_clauses: List of clauses with high centrality
            - using_neo4j: Boolean indicating if Neo4j was used
            - success: Boolean
            - error: Optional error message
        """
        try:
            # Get contract and clauses
            contract = Contract.objects.get(id=contract_id)
            clauses = list(Clause.objects.filter(contract=contract))

            if not clauses:
                return {
                    'success': False,
                    'error': 'No clauses found for contract',
                    'propagated_risks': {},
                    'risk_clusters': [],
                    'central_clauses': [],
                    'using_neo4j': self.using_neo4j
                }

            # Prepare initial risks if not provided
            if initial_risks is None:
                initial_risks = {
                    clause.id: clause.risk_score if clause.risk_score else 0.5
                    for clause in clauses
                }

            # Ensure graph exists in Neo4j
            if self.using_neo4j:
                graph_exists = self.neo4j_service.get_contract_graph(contract_id)
                if not graph_exists:
                    # Create graph from existing clauses
                    logger.info(f"Creating Neo4j graph for contract {contract_id}")
                    self._create_graph_from_clauses(contract_id, clauses)

            # Perform risk propagation
            propagated_risks = self.neo4j_service.propagate_risk(
                contract_id=contract_id,
                initial_risks=initial_risks,
                iterations=iterations,
                damping=damping
            )

            # Find risk clusters
            risk_clusters = self.neo4j_service.find_risk_clusters(
                contract_id=contract_id,
                risk_threshold=0.7
            )

            # Analyze centrality
            centrality_analysis = self.neo4j_service.analyze_centrality(contract_id)

            # Get top central clauses (high influence)
            central_clauses = self._get_central_clauses(
                centrality_analysis.get('betweenness', {}),
                clauses,
                top_n=5
            )

            # Update clause risk scores if requested
            self._update_clause_risks(propagated_risks)

            return {
                'success': True,
                'propagated_risks': propagated_risks,
                'risk_clusters': risk_clusters,
                'central_clauses': central_clauses,
                'centrality_analysis': centrality_analysis,
                'using_neo4j': self.using_neo4j,
                'iterations_performed': iterations,
                'total_clauses': len(clauses)
            }

        except ObjectDoesNotExist:
            logger.error(f"Contract {contract_id} not found")
            return {
                'success': False,
                'error': f'Contract {contract_id} not found',
                'propagated_risks': {},
                'risk_clusters': [],
                'central_clauses': [],
                'using_neo4j': self.using_neo4j
            }
        except Exception as e:
            logger.error(f"Error in risk propagation: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'propagated_risks': {},
                'risk_clusters': [],
                'central_clauses': [],
                'using_neo4j': self.using_neo4j
            }

    def _create_graph_from_clauses(self, contract_id: int, clauses: List[Clause]):
        """Create Neo4j graph from existing clauses."""
        # Build edges based on clause relationships
        edges = []
        clause_map = {c.id: c for c in clauses}

        for i, clause1 in enumerate(clauses):
            for clause2 in clauses[i+1:]:
                # Create edge if clauses are related (same type or references)
                if self._are_clauses_related(clause1, clause2):
                    weight = self._calculate_edge_weight(clause1, clause2)
                    edges.append((clause1.id, clause2.id, {'weight': weight}))

        # Create graph in Neo4j
        self.neo4j_service.create_contract_graph(
            contract_id=contract_id,
            clauses=clauses,
            edges=edges
        )

    def _are_clauses_related(self, clause1: Clause, clause2: Clause) -> bool:
        """Determine if two clauses are related."""
        # Same type
        if clause1.clause_type == clause2.clause_type:
            return True

        # Cross-reference in text
        if clause1.clause_name.lower() in (clause2.extracted_text or '').lower():
            return True
        if clause2.clause_name.lower() in (clause1.extracted_text or '').lower():
            return True

        return False

    def _calculate_edge_weight(self, clause1: Clause, clause2: Clause) -> float:
        """Calculate edge weight between two clauses."""
        weight = 0.5  # Base weight

        # Increase weight for same type
        if clause1.clause_type == clause2.clause_type:
            weight += 0.3

        # Increase weight for cross-references
        if clause1.clause_name.lower() in (clause2.extracted_text or '').lower():
            weight += 0.2
        if clause2.clause_name.lower() in (clause1.extracted_text or '').lower():
            weight += 0.2

        return min(weight, 1.0)

    def _get_central_clauses(
        self,
        centrality_scores: Dict[int, float],
        clauses: List[Clause],
        top_n: int = 5
    ) -> List[Dict]:
        """Get top N central clauses based on betweenness centrality."""
        if not centrality_scores:
            return []

        # Sort by centrality
        sorted_clauses = sorted(
            centrality_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        # Build result with clause details
        clause_map = {c.id: c for c in clauses}
        result = []

        for clause_id, centrality in sorted_clauses:
            if clause_id in clause_map:
                clause = clause_map[clause_id]
                result.append({
                    'clause_id': clause.id,
                    'clause_name': clause.clause_name,
                    'clause_type': clause.clause_type,
                    'risk_score': clause.risk_score,
                    'centrality': centrality,
                    'influence': 'HIGH' if centrality > 0.5 else 'MEDIUM' if centrality > 0.2 else 'LOW'
                })

        return result

    def _update_clause_risks(self, propagated_risks: Dict[int, float]):
        """Update clause risk scores in database (optional)."""
        # Only update if explicitly enabled
        # This can be made configurable via settings
        pass

    def analyze_risk_flow(self, contract_id: int) -> Dict:
        """
        Analyze how risk flows through the contract.

        Returns insights about risk propagation paths and bottlenecks.
        """
        try:
            # Get contract graph
            graph_data = self.neo4j_service.get_contract_graph(contract_id)
            if not graph_data:
                return {
                    'success': False,
                    'error': 'Contract graph not found'
                }

            # Perform centrality analysis
            centrality = self.neo4j_service.analyze_centrality(contract_id)

            # Find risk clusters
            clusters = self.neo4j_service.find_risk_clusters(
                contract_id=contract_id,
                risk_threshold=0.6
            )

            # Identify risk bottlenecks (high betweenness = risk flows through these)
            betweenness = centrality.get('betweenness', {})
            bottlenecks = [
                {'clause_id': cid, 'score': score}
                for cid, score in sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:5]
            ]

            # Identify risk amplifiers (high degree + high risk)
            degree = centrality.get('degree', {})
            amplifiers = []
            for clause_id in degree.keys():
                if degree[clause_id] >= 3:  # Highly connected
                    try:
                        clause = Clause.objects.get(id=clause_id)
                        if clause.risk_score and clause.risk_score > 0.7:
                            amplifiers.append({
                                'clause_id': clause_id,
                                'clause_name': clause.clause_name,
                                'connections': degree[clause_id],
                                'risk_score': clause.risk_score
                            })
                    except Clause.DoesNotExist:
                        pass

            return {
                'success': True,
                'bottlenecks': bottlenecks,
                'amplifiers': amplifiers,
                'risk_clusters': clusters,
                'centrality_analysis': centrality,
                'using_neo4j': self.using_neo4j
            }

        except Exception as e:
            logger.error(f"Error analyzing risk flow: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def simulate_clause_removal(self, contract_id: int, clause_id: int) -> Dict:
        """
        Simulate the impact of removing a clause on overall risk.

        Args:
            contract_id: Contract ID
            clause_id: Clause to remove

        Returns:
            Dict with before/after risk analysis
        """
        try:
            # Get current state
            current_analysis = self.propagate_risk_for_contract(contract_id)
            if not current_analysis['success']:
                return current_analysis

            current_risks = current_analysis['propagated_risks']
            current_avg_risk = sum(current_risks.values()) / len(current_risks) if current_risks else 0

            # Simulate removal by zeroing out the clause risk
            modified_risks = current_risks.copy()
            if clause_id in modified_risks:
                modified_risks[clause_id] = 0.0

            # Re-propagate with modified risks
            new_analysis = self.propagate_risk_for_contract(
                contract_id=contract_id,
                initial_risks=modified_risks
            )

            if not new_analysis['success']:
                return new_analysis

            new_risks = new_analysis['propagated_risks']
            new_avg_risk = sum(new_risks.values()) / len(new_risks) if new_risks else 0

            # Calculate impact
            risk_reduction = current_avg_risk - new_avg_risk
            impact_pct = (risk_reduction / current_avg_risk * 100) if current_avg_risk > 0 else 0

            return {
                'success': True,
                'clause_id': clause_id,
                'current_avg_risk': current_avg_risk,
                'new_avg_risk': new_avg_risk,
                'risk_reduction': risk_reduction,
                'impact_percentage': impact_pct,
                'recommendation': self._get_removal_recommendation(impact_pct),
                'using_neo4j': self.using_neo4j
            }

        except Exception as e:
            logger.error(f"Error simulating clause removal: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _get_removal_recommendation(self, impact_pct: float) -> str:
        """Get recommendation based on removal impact."""
        if impact_pct > 10:
            return "HIGH IMPACT: Removing this clause significantly reduces contract risk. Strong candidate for renegotiation."
        elif impact_pct > 5:
            return "MEDIUM IMPACT: This clause contributes moderately to contract risk. Consider negotiating modifications."
        elif impact_pct > 0:
            return "LOW IMPACT: Removing this clause has minimal effect on overall risk."
        else:
            return "NEGATIVE IMPACT: Removing this clause may increase risk elsewhere. Recommend keeping."
