"""
Clause Optimization Engine
Multi-objective optimization for Force Majeure clause improvement
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ClauseScore:
    """Scoring metrics for an FM clause"""
    coverage_score: float  # 0-1, how many FM events are covered
    clarity_score: float  # 0-1, how clear and unambiguous
    enforceability_score: float  # 0-1, legal enforceability
    balance_score: float  # 0-1, fairness between parties
    risk_reduction: float  # 0-1, estimated risk mitigation
    compliance_score: float  # 0-1, standard compliance (FIDIC, ICC, etc.)
    overall_score: float  # Weighted average


@dataclass
class OptimizationObjective:
    """Optimization objective with weight"""
    name: str
    weight: float
    target: str  # 'maximize' or 'minimize'
    current_value: float
    optimized_value: float


class ClauseOptimizationEngine:
    """
    Multi-objective optimization engine for FM clauses

    Optimizes clauses across multiple dimensions:
    - Event coverage (maximize)
    - Legal clarity (maximize)
    - Enforceability (maximize)
    - Party balance (maximize fairness)
    - Risk reduction (maximize)
    - Standard compliance (maximize)
    """

    def __init__(self):
        self.fm_events = [
            'war', 'terrorism', 'cyber_warfare', 'pandemic', 'earthquake',
            'flood', 'sanctions', 'embargo', 'supply_chain_disruption',
            'port_closure', 'civil_war', 'military_invasion', 'border_conflict',
            'military_coup', 'drone_strikes', 'naval_blockade',
            'government_expropriation', 'martial_law', 'energy_shortages',
            'commodity_shock', 'satellite_disruption', 'airspace_closure'
        ]

        self.critical_terms = [
            'notice_period', 'documentation_requirements', 'mitigation_obligations',
            'suspension_rights', 'termination_rights', 'cost_allocation',
            'time_extensions', 'force_majeure_duration'
        ]

        self.standard_templates = {
            'FIDIC': {
                'coverage_baseline': 0.75,
                'clarity_baseline': 0.85,
                'balance_baseline': 0.80
            },
            'ICC': {
                'coverage_baseline': 0.70,
                'clarity_baseline': 0.80,
                'balance_baseline': 0.75
            },
            'NEC': {
                'coverage_baseline': 0.72,
                'clarity_baseline': 0.82,
                'balance_baseline': 0.78
            }
        }

    def optimize_clause(
        self,
        current_clause: str,
        optimization_objectives: Optional[Dict[str, float]] = None,
        constraints: Optional[Dict] = None,
        party_preferences: Optional[Dict] = None
    ) -> Dict:
        """
        Optimize FM clause using multi-objective optimization

        Args:
            current_clause: Current FM clause text
            optimization_objectives: Objectives with weights {objective: weight}
            constraints: Hard constraints (e.g., {'max_length': 500})
            party_preferences: Party-specific preferences

        Returns:
            Optimized clause with improvement metrics
        """

        if optimization_objectives is None:
            # Default equal weights
            optimization_objectives = {
                'coverage': 0.25,
                'clarity': 0.20,
                'enforceability': 0.20,
                'balance': 0.15,
                'risk_reduction': 0.15,
                'compliance': 0.05
            }

        if constraints is None:
            constraints = {
                'max_length_words': 500,
                'min_coverage_events': 15,
                'require_notice_period': True,
                'require_mitigation': True
            }

        # Step 1: Score current clause
        current_score = self._score_clause(current_clause)

        # Step 2: Identify improvement opportunities
        improvement_areas = self._identify_improvement_areas(
            current_clause,
            current_score,
            optimization_objectives
        )

        # Step 3: Generate optimized clause variants
        variants = self._generate_clause_variants(
            current_clause,
            improvement_areas,
            constraints,
            n_variants=10
        )

        # Step 4: Evaluate variants
        variant_scores = []
        for variant in variants:
            score = self._score_clause(variant)
            objective_score = self._calculate_objective_score(score, optimization_objectives)
            variant_scores.append({
                'clause': variant,
                'score': score,
                'objective_score': objective_score
            })

        # Step 5: Select best variant (Pareto optimal)
        best_variant = max(variant_scores, key=lambda x: x['objective_score'])

        # Step 6: Apply party preferences if provided
        if party_preferences:
            best_variant = self._apply_party_preferences(
                best_variant,
                party_preferences
            )

        # Calculate improvements
        improvements = self._calculate_improvements(
            current_score,
            best_variant['score']
        )

        return {
            'optimized_clause': best_variant['clause'],
            'current_score': self._score_to_dict(current_score),
            'optimized_score': self._score_to_dict(best_variant['score']),
            'improvements': improvements,
            'improvement_areas': improvement_areas,
            'optimization_objectives': optimization_objectives,
            'pareto_optimal': self._is_pareto_optimal(best_variant, variant_scores),
            'alternatives': [
                {
                    'clause': v['clause'][:200] + '...' if len(v['clause']) > 200 else v['clause'],
                    'score': self._score_to_dict(v['score']),
                    'objective_score': round(v['objective_score'], 3)
                }
                for v in sorted(variant_scores, key=lambda x: x['objective_score'], reverse=True)[:3]
            ],
            'recommendations': self._generate_optimization_recommendations(
                current_score,
                best_variant['score'],
                improvement_areas
            )
        }

    def multi_party_negotiation_optimize(
        self,
        current_clause: str,
        buyer_preferences: Dict,
        seller_preferences: Dict,
        neutral_arbitrator: bool = True
    ) -> Dict:
        """
        Optimize clause balancing multiple party interests

        Args:
            current_clause: Current clause text
            buyer_preferences: Buyer's optimization preferences
            seller_preferences: Seller's optimization preferences
            neutral_arbitrator: Use neutral arbitration for conflicts

        Returns:
            Balanced optimized clause
        """

        # Score from each party's perspective
        buyer_optimal = self.optimize_clause(
            current_clause,
            optimization_objectives=buyer_preferences
        )

        seller_optimal = self.optimize_clause(
            current_clause,
            optimization_objectives=seller_preferences
        )

        # Find Nash equilibrium point (balanced solution)
        if neutral_arbitrator:
            # Neutral weighting
            balanced_objectives = self._calculate_balanced_objectives(
                buyer_preferences,
                seller_preferences
            )

            balanced_optimal = self.optimize_clause(
                current_clause,
                optimization_objectives=balanced_objectives
            )

            return {
                'balanced_clause': balanced_optimal['optimized_clause'],
                'balanced_score': balanced_optimal['optimized_score'],
                'buyer_perspective': {
                    'optimal_clause': buyer_optimal['optimized_clause'],
                    'score': buyer_optimal['optimized_score']
                },
                'seller_perspective': {
                    'optimal_clause': seller_optimal['optimized_clause'],
                    'score': seller_optimal['optimized_score']
                },
                'fairness_analysis': self._analyze_fairness(
                    balanced_optimal,
                    buyer_optimal,
                    seller_optimal
                ),
                'negotiation_points': self._identify_negotiation_points(
                    buyer_preferences,
                    seller_preferences
                )
            }
        else:
            # Return both perspectives for manual negotiation
            return {
                'buyer_optimal': buyer_optimal,
                'seller_optimal': seller_optimal,
                'conflict_areas': self._identify_conflicts(
                    buyer_optimal,
                    seller_optimal
                )
            }

    def _score_clause(self, clause_text: str) -> ClauseScore:
        """Score clause across multiple dimensions"""

        # Coverage score: How many FM events are explicitly covered
        coverage_score = self._calculate_coverage_score(clause_text)

        # Clarity score: Linguistic clarity and specificity
        clarity_score = self._calculate_clarity_score(clause_text)

        # Enforceability score: Legal enforceability indicators
        enforceability_score = self._calculate_enforceability_score(clause_text)

        # Balance score: Fairness between parties
        balance_score = self._calculate_balance_score(clause_text)

        # Risk reduction: Estimated risk mitigation value
        risk_reduction = self._calculate_risk_reduction(clause_text, coverage_score)

        # Compliance score: Alignment with industry standards
        compliance_score = self._calculate_compliance_score(clause_text)

        # Overall weighted score
        overall_score = (
            coverage_score * 0.25 +
            clarity_score * 0.20 +
            enforceability_score * 0.20 +
            balance_score * 0.15 +
            risk_reduction * 0.15 +
            compliance_score * 0.05
        )

        return ClauseScore(
            coverage_score=coverage_score,
            clarity_score=clarity_score,
            enforceability_score=enforceability_score,
            balance_score=balance_score,
            risk_reduction=risk_reduction,
            compliance_score=compliance_score,
            overall_score=overall_score
        )

    def _calculate_coverage_score(self, clause: str) -> float:
        """Calculate FM event coverage score"""

        clause_lower = clause.lower()

        # Count how many FM events are covered
        covered_events = 0
        for event in self.fm_events:
            event_keywords = event.replace('_', ' ').split()
            if any(keyword in clause_lower for keyword in event_keywords):
                covered_events += 1

        coverage_score = covered_events / len(self.fm_events)

        # Bonus for catch-all phrases
        catch_all_phrases = ['acts of god', 'beyond reasonable control', 'unforeseeable', 'unavoidable']
        if any(phrase in clause_lower for phrase in catch_all_phrases):
            coverage_score = min(1.0, coverage_score + 0.10)

        return min(1.0, coverage_score)

    def _calculate_clarity_score(self, clause: str) -> float:
        """Calculate linguistic clarity score"""

        score = 0.5  # Baseline

        # Positive indicators
        if 'shall' in clause.lower():
            score += 0.10  # Clear obligations

        if any(term in clause.lower() for term in ['written notice', 'days', 'business days']):
            score += 0.10  # Specific timeframes

        if 'mitigation' in clause.lower() or 'mitigate' in clause.lower():
            score += 0.10  # Mitigation duties

        # Negative indicators
        if 'may' in clause.lower():
            score -= 0.05  # Ambiguous

        if len(clause.split('.')) == 1 and len(clause) > 300:
            score -= 0.10  # Run-on sentence

        # Word count check
        word_count = len(clause.split())
        if 150 <= word_count <= 400:
            score += 0.15  # Appropriate length
        elif word_count < 100:
            score -= 0.10  # Too brief
        elif word_count > 500:
            score -= 0.10  # Too verbose

        return max(0.0, min(1.0, score))

    def _calculate_enforceability_score(self, clause: str) -> float:
        """Calculate legal enforceability score"""

        score = 0.5

        clause_lower = clause.lower()

        # Positive indicators
        enforceable_terms = [
            'notice', 'documentation', 'evidence', 'written',
            'reasonable', 'timely', 'immediately', 'suspend', 'terminate'
        ]

        for term in enforceable_terms:
            if term in clause_lower:
                score += 0.05

        # Negative indicators (vague terms)
        vague_terms = ['appropriate', 'as soon as possible', 'promptly']
        for term in vague_terms:
            if term in clause_lower:
                score -= 0.05

        return max(0.0, min(1.0, score))

    def _calculate_balance_score(self, clause: str) -> float:
        """Calculate fairness/balance score between parties"""

        clause_lower = clause.lower()

        score = 0.5

        # Check for mutual obligations
        if 'both parties' in clause_lower or 'either party' in clause_lower:
            score += 0.15

        # Check for one-sided terms
        if 'contractor shall' in clause_lower and 'employer shall' not in clause_lower:
            score -= 0.10  # One-sided obligation

        if 'termination' in clause_lower:
            if 'mutual' in clause_lower:
                score += 0.10
            else:
                score -= 0.05  # Unilateral termination

        # Cost allocation
        if 'cost' in clause_lower or 'expense' in clause_lower:
            if 'shared' in clause_lower or 'equitable' in clause_lower:
                score += 0.10
            elif 'contractor' in clause_lower and 'employer' not in clause_lower:
                score -= 0.10

        return max(0.0, min(1.0, score))

    def _calculate_risk_reduction(self, clause: str, coverage_score: float) -> float:
        """Estimate risk reduction potential"""

        # Base risk reduction on coverage
        risk_reduction = coverage_score * 0.6

        clause_lower = clause.lower()

        # Additional risk reduction factors
        if 'insurance' in clause_lower:
            risk_reduction += 0.10

        if 'mitigation' in clause_lower or 'minimize' in clause_lower:
            risk_reduction += 0.10

        if 'extension of time' in clause_lower or 'time extension' in clause_lower:
            risk_reduction += 0.10

        if 'suspend' in clause_lower or 'suspension' in clause_lower:
            risk_reduction += 0.10

        return min(1.0, risk_reduction)

    def _calculate_compliance_score(self, clause: str) -> float:
        """Calculate compliance with industry standards"""

        clause_lower = clause.lower()

        score = 0.5

        # FIDIC compliance indicators
        fidic_terms = ['extension of time', 'reasonable', 'unforeseeable', 'beyond control']
        fidic_matches = sum(1 for term in fidic_terms if term in clause_lower)
        score += (fidic_matches / len(fidic_terms)) * 0.25

        # ICC compliance
        icc_terms = ['impediment', 'prevent', 'control', 'reasonable']
        icc_matches = sum(1 for term in icc_terms if term in clause_lower)
        score += (icc_matches / len(icc_terms)) * 0.25

        return min(1.0, score)

    def _identify_improvement_areas(
        self,
        clause: str,
        score: ClauseScore,
        objectives: Dict[str, float]
    ) -> List[Dict]:
        """Identify areas for improvement based on scores and objectives"""

        improvements = []

        # Coverage improvements
        if score.coverage_score < 0.70 and objectives.get('coverage', 0) > 0.15:
            missing_events = self._find_missing_events(clause)
            improvements.append({
                'area': 'coverage',
                'current_score': score.coverage_score,
                'target_score': 0.85,
                'action': 'Add missing FM events',
                'missing_events': missing_events[:8]  # Top 8
            })

        # Clarity improvements
        if score.clarity_score < 0.70 and objectives.get('clarity', 0) > 0.10:
            improvements.append({
                'area': 'clarity',
                'current_score': score.clarity_score,
                'target_score': 0.85,
                'action': 'Improve clarity with specific terms and timeframes'
            })

        # Balance improvements
        if score.balance_score < 0.60 and objectives.get('balance', 0) > 0.10:
            improvements.append({
                'area': 'balance',
                'current_score': score.balance_score,
                'target_score': 0.75,
                'action': 'Add mutual obligations and balanced cost allocation'
            })

        return improvements

    def _find_missing_events(self, clause: str) -> List[str]:
        """Find FM events not covered in clause"""

        clause_lower = clause.lower()
        missing = []

        for event in self.fm_events:
            event_keywords = event.replace('_', ' ').split()
            if not any(keyword in clause_lower for keyword in event_keywords):
                missing.append(event)

        return missing

    def _generate_clause_variants(
        self,
        current_clause: str,
        improvement_areas: List[Dict],
        constraints: Dict,
        n_variants: int = 10
    ) -> List[str]:
        """Generate optimized clause variants"""

        variants = []

        # Variant 1: Enhanced coverage
        variant1 = self._enhance_coverage(current_clause, improvement_areas)
        variants.append(variant1)

        # Variant 2: Improved clarity
        variant2 = self._improve_clarity(current_clause)
        variants.append(variant2)

        # Variant 3: Better balance
        variant3 = self._improve_balance(current_clause)
        variants.append(variant3)

        # Variant 4: FIDIC-compliant
        variant4 = self._align_to_standard(current_clause, 'FIDIC')
        variants.append(variant4)

        # Variant 5: Comprehensive (all improvements)
        variant5 = self._apply_all_improvements(current_clause, improvement_areas)
        variants.append(variant5)

        # Fill remaining with random combinations
        while len(variants) < n_variants:
            variant = self._random_improvement_combination(current_clause, improvement_areas)
            variants.append(variant)

        return variants

    def _enhance_coverage(self, clause: str, improvements: List[Dict]) -> str:
        """Enhance FM event coverage"""

        enhanced = clause

        # Find coverage improvement
        coverage_imp = next((imp for imp in improvements if imp['area'] == 'coverage'), None)

        if coverage_imp and 'missing_events' in coverage_imp:
            missing = coverage_imp['missing_events']

            # Add missing events to clause
            events_text = ', '.join(missing[:8]).replace('_', ' ')
            enhanced += f" The Contractor shall also be entitled to relief for: {events_text}."

        return enhanced

    def _improve_clarity(self, clause: str) -> str:
        """Improve clause clarity"""

        improved = clause

        # Add specific timeframes if missing
        if 'days' not in clause.lower():
            improved += " The affected party shall provide written notice within 14 days of the Force Majeure event."

        # Add mitigation language
        if 'mitigation' not in clause.lower():
            improved += " Both parties shall use reasonable efforts to mitigate the effects of the Force Majeure event."

        return improved

    def _improve_balance(self, clause: str) -> str:
        """Improve balance between parties"""

        improved = clause

        # Add mutual obligations
        if 'both parties' not in clause.lower():
            improved += " Both parties shall have equal rights to suspend performance during Force Majeure."

        # Add cost sharing
        if 'cost' not in clause.lower():
            improved += " Costs incurred during Force Majeure shall be borne by the party incurring them."

        return improved

    def _align_to_standard(self, clause: str, standard: str) -> str:
        """Align clause to industry standard"""

        aligned = clause

        if standard == 'FIDIC':
            if 'extension of time' not in clause.lower():
                aligned += " The Contractor shall be entitled to an extension of time for any delays caused."

        return aligned

    def _apply_all_improvements(self, clause: str, improvements: List[Dict]) -> str:
        """Apply all identified improvements"""

        improved = clause

        for improvement in improvements:
            if improvement['area'] == 'coverage':
                improved = self._enhance_coverage(improved, [improvement])
            elif improvement['area'] == 'clarity':
                improved = self._improve_clarity(improved)
            elif improvement['area'] == 'balance':
                improved = self._improve_balance(improved)

        return improved

    def _random_improvement_combination(self, clause: str, improvements: List[Dict]) -> str:
        """Generate random combination of improvements"""

        variant = clause

        for improvement in improvements:
            if np.random.random() < 0.7:  # 70% chance to apply each
                if improvement['area'] == 'coverage':
                    variant = self._enhance_coverage(variant, [improvement])
                elif improvement['area'] == 'clarity':
                    variant = self._improve_clarity(variant)
                elif improvement['area'] == 'balance':
                    variant = self._improve_balance(variant)

        return variant

    def _calculate_objective_score(
        self,
        score: ClauseScore,
        objectives: Dict[str, float]
    ) -> float:
        """Calculate weighted objective score"""

        weighted_score = 0.0

        weighted_score += score.coverage_score * objectives.get('coverage', 0)
        weighted_score += score.clarity_score * objectives.get('clarity', 0)
        weighted_score += score.enforceability_score * objectives.get('enforceability', 0)
        weighted_score += score.balance_score * objectives.get('balance', 0)
        weighted_score += score.risk_reduction * objectives.get('risk_reduction', 0)
        weighted_score += score.compliance_score * objectives.get('compliance', 0)

        return weighted_score

    def _is_pareto_optimal(
        self,
        candidate: Dict,
        all_variants: List[Dict]
    ) -> bool:
        """Check if candidate is Pareto optimal"""

        candidate_score = candidate['score']

        for variant in all_variants:
            if variant == candidate:
                continue

            var_score = variant['score']

            # Check if variant dominates candidate
            dominates = (
                var_score.coverage_score >= candidate_score.coverage_score and
                var_score.clarity_score >= candidate_score.clarity_score and
                var_score.enforceability_score >= candidate_score.enforceability_score and
                var_score.balance_score >= candidate_score.balance_score
            )

            if dominates:
                return False

        return True

    def _score_to_dict(self, score: ClauseScore) -> Dict:
        """Convert ClauseScore to dictionary"""
        return {
            'coverage': round(score.coverage_score, 3),
            'clarity': round(score.clarity_score, 3),
            'enforceability': round(score.enforceability_score, 3),
            'balance': round(score.balance_score, 3),
            'risk_reduction': round(score.risk_reduction, 3),
            'compliance': round(score.compliance_score, 3),
            'overall': round(score.overall_score, 3)
        }

    def _calculate_improvements(
        self,
        current: ClauseScore,
        optimized: ClauseScore
    ) -> Dict:
        """Calculate improvements from optimization"""

        return {
            'coverage': {
                'before': round(current.coverage_score, 3),
                'after': round(optimized.coverage_score, 3),
                'improvement': round(optimized.coverage_score - current.coverage_score, 3),
                'improvement_pct': round((optimized.coverage_score - current.coverage_score) / current.coverage_score * 100, 1) if current.coverage_score > 0 else 0
            },
            'clarity': {
                'before': round(current.clarity_score, 3),
                'after': round(optimized.clarity_score, 3),
                'improvement': round(optimized.clarity_score - current.clarity_score, 3)
            },
            'overall': {
                'before': round(current.overall_score, 3),
                'after': round(optimized.overall_score, 3),
                'improvement': round(optimized.overall_score - current.overall_score, 3)
            }
        }

    def _apply_party_preferences(self, variant: Dict, preferences: Dict) -> Dict:
        """Apply party-specific preferences"""
        # Simplified - in full implementation would modify clause
        return variant

    def _calculate_balanced_objectives(
        self,
        buyer_prefs: Dict,
        seller_prefs: Dict
    ) -> Dict:
        """Calculate balanced objectives between parties"""

        balanced = {}
        all_keys = set(buyer_prefs.keys()) | set(seller_prefs.keys())

        for key in all_keys:
            buyer_weight = buyer_prefs.get(key, 0)
            seller_weight = seller_prefs.get(key, 0)
            balanced[key] = (buyer_weight + seller_weight) / 2

        return balanced

    def _analyze_fairness(
        self,
        balanced: Dict,
        buyer: Dict,
        seller: Dict
    ) -> Dict:
        """Analyze fairness of balanced solution"""

        buyer_satisfaction = buyer['optimized_score']['overall']
        seller_satisfaction = seller['optimized_score']['overall']
        balanced_score = balanced['optimized_score']['overall']

        return {
            'buyer_satisfaction': round(buyer_satisfaction, 3),
            'seller_satisfaction': round(seller_satisfaction, 3),
            'balanced_score': round(balanced_score, 3),
            'fairness_index': round(min(buyer_satisfaction, seller_satisfaction) / max(buyer_satisfaction, seller_satisfaction), 3) if max(buyer_satisfaction, seller_satisfaction) > 0 else 1.0
        }

    def _identify_negotiation_points(
        self,
        buyer_prefs: Dict,
        seller_prefs: Dict
    ) -> List[str]:
        """Identify key negotiation points"""

        conflicts = []

        for key in set(buyer_prefs.keys()) & set(seller_prefs.keys()):
            buyer_weight = buyer_prefs[key]
            seller_weight = seller_prefs[key]

            if abs(buyer_weight - seller_weight) > 0.20:
                conflicts.append(f"{key}: buyer={buyer_weight:.2f}, seller={seller_weight:.2f}")

        return conflicts

    def _identify_conflicts(self, buyer: Dict, seller: Dict) -> List[str]:
        """Identify conflicts between buyer and seller optimizations"""

        conflicts = []

        buyer_clause = buyer['optimized_clause']
        seller_clause = seller['optimized_clause']

        if buyer_clause != seller_clause:
            conflicts.append("Optimized clauses differ significantly between parties")

        return conflicts

    def _generate_optimization_recommendations(
        self,
        current: ClauseScore,
        optimized: ClauseScore,
        improvement_areas: List[Dict]
    ) -> List[str]:
        """Generate optimization recommendations"""

        recommendations = []

        if optimized.coverage_score - current.coverage_score > 0.10:
            recommendations.append(f"Coverage improved by {(optimized.coverage_score - current.coverage_score):.1%}")

        if optimized.clarity_score - current.clarity_score > 0.10:
            recommendations.append("Clarity significantly improved with specific terms")

        if optimized.balance_score > 0.75:
            recommendations.append("Clause achieves good balance between parties")
        elif optimized.balance_score < 0.60:
            recommendations.append("Consider further balance improvements")

        if optimized.overall_score > 0.80:
            recommendations.append("Clause meets high-quality standards")

        return recommendations


# Global instance
clause_optimization_engine = ClauseOptimizationEngine()


# Convenience functions
def optimize_fm_clause(
    current_clause: str,
    objectives: Optional[Dict[str, float]] = None
) -> Dict:
    """Optimize FM clause"""
    return clause_optimization_engine.optimize_clause(current_clause, objectives)


def multi_party_optimize(
    current_clause: str,
    buyer_preferences: Dict,
    seller_preferences: Dict
) -> Dict:
    """Multi-party negotiation optimization"""
    return clause_optimization_engine.multi_party_negotiation_optimize(
        current_clause,
        buyer_preferences,
        seller_preferences
    )
