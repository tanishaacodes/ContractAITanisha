"""
Clause Addition Service
========================
Add new clauses to contracts with automatic risk assessment and what-if analysis.

Features:
1. Add custom clauses to contracts
2. Automatic risk scoring
3. Graph integration (add node + edges)
4. What-if simulation (before vs after)
5. Exposure impact analysis
"""

import logging
from typing import Dict, Any, Optional, List
import networkx as nx
from datetime import datetime

logger = logging.getLogger(__name__)


class ClauseAdditionService:
    """
    Service for adding new clauses to contracts with risk assessment.
    """

    # Clause type risk baselines
    CLAUSE_TYPE_RISKS = {
        'indemnity': 0.85,
        'liability': 0.75,
        'termination': 0.60,
        'payment': 0.55,
        'warranty': 0.50,
        'confidentiality': 0.45,
        'intellectual_property': 0.70,
        'force_majeure': 0.40,
        'dispute_resolution': 0.35,
        'general': 0.30,
    }

    # Risk keywords and their weights
    RISK_KEYWORDS = {
        'unlimited': 0.3,
        'shall indemnify': 0.25,
        'without limitation': 0.25,
        'consequential damages': 0.20,
        'indirect damages': 0.20,
        'lost profits': 0.15,
        'punitive damages': 0.25,
        'strict liability': 0.25,
        'joint and several': 0.20,
        'breach': 0.15,
        'default': 0.15,
        'penalty': 0.20,
        'liquidated damages': 0.15,
        'gross negligence': 0.20,
        'willful misconduct': 0.20,
        'perpetual': 0.15,
        'irrevocable': 0.15,
        'exclusive': 0.10,
        'non-compete': 0.15,
        'terminate immediately': 0.15,
    }

    def __init__(self):
        """Initialize clause addition service"""
        self.logger = logger

    def add_clause_to_contract(
        self,
        clause_text: str,
        clause_name: str,
        clause_type: str,
        contract_model: Any,
        suggested_risk_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Add a new clause to a contract with risk assessment.

        Args:
            clause_text: Text of the new clause
            clause_name: Name/title of the clause
            clause_type: Type of clause (indemnity, payment, etc.)
            contract_model: Contract model instance
            suggested_risk_score: Optional pre-computed risk score

        Returns:
            Dict with new clause info and risk assessment
        """
        try:
            # Calculate risk score if not provided
            if suggested_risk_score is None:
                risk_score = self._assess_clause_risk(clause_text, clause_type)
            else:
                risk_score = suggested_risk_score

            # Determine risk level
            risk_level = self._classify_risk_level(risk_score)

            # Extract risk factors
            risk_factors = self._extract_risk_factors(clause_text, clause_type)

            # Create clause data
            clause_data = {
                'clause_name': clause_name,
                'clause_type': clause_type,
                'extracted_text': clause_text,
                'text_spans': clause_text,
                'context_sentences': clause_text,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'found': True,
                'confidence': 1.0,  # User-added, so full confidence
                'enriched_at': datetime.now()
            }

            self.logger.info(
                f"[CLAUSE-ADD] Prepared new clause '{clause_name}' "
                f"with risk score {risk_score:.2f}"
            )

            return {
                'success': True,
                'clause_data': clause_data,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'risk_factors': risk_factors
            }

        except Exception as e:
            self.logger.error(f"[CLAUSE-ADD] Error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _assess_clause_risk(self, clause_text: str, clause_type: str) -> float:
        """
        Assess risk score for a clause based on content and type.

        Risk scoring:
        - Base risk from clause type (0-1)
        - Additional risk from keywords (+0-0.3)
        - Cap at 1.0
        """
        clause_text_lower = clause_text.lower()
        clause_type_lower = clause_type.lower()

        # Start with base risk for clause type
        base_risk = self.CLAUSE_TYPE_RISKS.get(clause_type_lower, 0.3)

        # Add risk from keywords
        keyword_risk = 0.0
        matched_keywords = []

        for keyword, weight in self.RISK_KEYWORDS.items():
            if keyword in clause_text_lower:
                keyword_risk += weight
                matched_keywords.append(keyword)

        # Combine risks (cap at 1.0)
        total_risk = min(base_risk + keyword_risk, 1.0)

        self.logger.debug(
            f"[CLAUSE-RISK] Base: {base_risk:.2f}, "
            f"Keywords: {keyword_risk:.2f}, Total: {total_risk:.2f}"
        )

        return total_risk

    def _classify_risk_level(self, risk_score: float) -> str:
        """Classify risk level based on score"""
        if risk_score >= 0.7:
            return 'HIGH'
        elif risk_score >= 0.4:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _extract_risk_factors(self, clause_text: str, clause_type: str) -> Dict[str, Any]:
        """Extract detailed risk factors from clause"""
        clause_text_lower = clause_text.lower()

        factors = {
            'clause_type': clause_type,
            'keywords_found': [],
            'risk_indicators': []
        }

        # Find matched keywords
        for keyword in self.RISK_KEYWORDS.keys():
            if keyword in clause_text_lower:
                factors['keywords_found'].append(keyword)

        # Identify specific risk indicators
        if 'unlimited' in clause_text_lower or 'without limitation' in clause_text_lower:
            factors['risk_indicators'].append('Unlimited liability exposure')

        if 'indemnif' in clause_text_lower:
            factors['risk_indicators'].append('Indemnification obligation')

        if 'consequential' in clause_text_lower or 'indirect' in clause_text_lower:
            factors['risk_indicators'].append('Broad damages coverage')

        if 'terminate' in clause_text_lower:
            factors['risk_indicators'].append('Termination provisions')

        if 'penalty' in clause_text_lower or 'liquidated damages' in clause_text_lower:
            factors['risk_indicators'].append('Financial penalties')

        return factors

    def add_clause_to_graph(
        self,
        graph: nx.DiGraph,
        clause_id: str,
        clause_name: str,
        clause_type: str,
        risk_score: float,
        risk_level: str
    ) -> nx.DiGraph:
        """
        Add new clause as a node to the contract graph.

        Args:
            graph: Existing contract graph
            clause_id: ID of new clause
            clause_name: Name of clause
            clause_type: Type of clause
            risk_score: Risk score (0-1)
            risk_level: Risk level (LOW/MEDIUM/HIGH)

        Returns:
            Updated graph with new clause node
        """
        try:
            # Add node
            graph.add_node(
                clause_id,
                clause_name=clause_name,
                clause_type=clause_type,
                risk_score=risk_score,
                risk_level=risk_level,
                added_by_user=True
            )

            # Identify potential edges based on clause type similarity
            self._add_potential_edges(graph, clause_id, clause_type, risk_score)

            self.logger.info(
                f"[CLAUSE-GRAPH] Added node {clause_id} to graph "
                f"with {graph.degree(clause_id)} connections"
            )

            return graph

        except Exception as e:
            self.logger.error(f"[CLAUSE-GRAPH] Error: {e}", exc_info=True)
            return graph

    def _add_potential_edges(
        self,
        graph: nx.DiGraph,
        new_clause_id: str,
        clause_type: str,
        risk_score: float
    ):
        """
        Add edges between new clause and related existing clauses.

        Edge creation rules:
        - Connect to clauses of same type
        - Connect high-risk clauses together
        - Connect termination → all obligations
        - Connect payment → liability
        """
        clause_type_lower = clause_type.lower()

        for node_id, node_data in graph.nodes(data=True):
            if node_id == new_clause_id:
                continue

            existing_type = node_data.get('clause_type', '').lower()
            existing_risk = node_data.get('risk_score', 0.0)

            # Rule 1: Same type clauses interact
            if existing_type == clause_type_lower:
                graph.add_edge(
                    new_clause_id,
                    node_id,
                    interaction_type='same_type',
                    weight=0.5
                )

            # Rule 2: High risk clauses interact
            if risk_score >= 0.7 and existing_risk >= 0.7:
                graph.add_edge(
                    new_clause_id,
                    node_id,
                    interaction_type='high_risk_interaction',
                    weight=0.6
                )

            # Rule 3: Termination affects all obligations
            if 'termination' in clause_type_lower:
                if existing_type in ['payment', 'indemnity', 'liability', 'warranty']:
                    graph.add_edge(
                        new_clause_id,
                        node_id,
                        interaction_type='termination_impact',
                        weight=0.7
                    )

            # Rule 4: Payment affects liability
            if 'payment' in clause_type_lower and 'liability' in existing_type:
                graph.add_edge(
                    new_clause_id,
                    node_id,
                    interaction_type='payment_liability',
                    weight=0.5
                )

            # Rule 5: Indemnity affects many clauses
            if 'indemnit' in clause_type_lower:
                if existing_type in ['liability', 'warranty', 'intellectual_property']:
                    graph.add_edge(
                        new_clause_id,
                        node_id,
                        interaction_type='indemnity_coverage',
                        weight=0.8
                    )

    def simulate_clause_addition_impact(
        self,
        original_clauses: List[Any],
        new_clause_data: Dict[str, Any],
        original_graph: nx.DiGraph,
        contract_value: float
    ) -> Dict[str, Any]:
        """
        Simulate the impact of adding a new clause using what-if analysis.

        Args:
            original_clauses: Existing contract clauses
            new_clause_data: Data for new clause
            original_graph: Existing contract graph
            contract_value: Contract value for exposure calculation

        Returns:
            Dict with before/after comparison
        """
        try:
            from .exposure_engine import ExposureEngine

            exposure_engine = ExposureEngine()

            # Calculate current exposure
            current_exposure = exposure_engine.calculate_exposure(
                original_clauses,
                original_graph,
                contract_value
            )

            # Create temporary clause object for simulation
            class TempClause:
                def __init__(self, data):
                    self.id = 'temp_new_clause'
                    for key, value in data.items():
                        setattr(self, key, value)

            temp_clause = TempClause(new_clause_data)

            # Create updated clause list
            updated_clauses = list(original_clauses) + [temp_clause]

            # Create updated graph
            updated_graph = original_graph.copy()
            updated_graph = self.add_clause_to_graph(
                updated_graph,
                'temp_new_clause',
                new_clause_data['clause_name'],
                new_clause_data['clause_type'],
                new_clause_data['risk_score'],
                new_clause_data['risk_level']
            )

            # Calculate new exposure
            new_exposure = exposure_engine.calculate_exposure(
                updated_clauses,
                updated_graph,
                contract_value
            )

            # Calculate delta
            exposure_delta = new_exposure - current_exposure
            risk_increase_pct = (exposure_delta / current_exposure * 100) if current_exposure > 0 else 0

            return {
                'success': True,
                'current_exposure': round(current_exposure, 2),
                'new_exposure': round(new_exposure, 2),
                'exposure_delta': round(exposure_delta, 2),
                'risk_increase_pct': round(risk_increase_pct, 1),
                'recommendation': self._generate_addition_recommendation(
                    new_clause_data['risk_level'],
                    exposure_delta,
                    risk_increase_pct
                )
            }

        except Exception as e:
            self.logger.error(f"[CLAUSE-ADD-SIMULATION] Error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_addition_recommendation(
        self,
        risk_level: str,
        exposure_delta: float,
        risk_increase_pct: float
    ) -> str:
        """Generate recommendation for clause addition"""
        if risk_level == 'HIGH' and risk_increase_pct > 20:
            return (
                f"⚠️ HIGH RISK: Adding this clause increases exposure by "
                f"{risk_increase_pct:.1f}%. Recommend legal review before proceeding."
            )
        elif risk_level == 'MEDIUM' and risk_increase_pct > 10:
            return (
                f"⚠️ MODERATE RISK: Adding this clause increases exposure by "
                f"{risk_increase_pct:.1f}%. Review recommended."
            )
        else:
            return (
                f"✅ LOW RISK: Adding this clause increases exposure by "
                f"{risk_increase_pct:.1f}%. Impact is acceptable."
            )


# Convenience function
def add_clause_with_assessment(
    clause_text: str,
    clause_name: str,
    clause_type: str,
    contract_model: Any,
    original_clauses: List[Any],
    original_graph: nx.DiGraph,
    contract_value: float
) -> Dict[str, Any]:
    """
    Add clause with full risk assessment and what-if simulation.
    """
    service = ClauseAdditionService()

    # Assess risk
    assessment = service.add_clause_to_contract(
        clause_text, clause_name, clause_type, contract_model
    )

    if not assessment['success']:
        return assessment

    # Simulate impact
    impact = service.simulate_clause_addition_impact(
        original_clauses,
        assessment['clause_data'],
        original_graph,
        contract_value
    )

    return {
        'success': True,
        'assessment': assessment,
        'impact': impact
    }
