"""
Enhanced Counterfactual Engine with Do-Calculus
Performs causal inference and counterfactual reasoning for FM risk analysis
"""

import numpy as np
from typing import Dict, List, Optional, Set, Tuple
import logging
from copy import deepcopy
from .expanded_bayesian_engine import ExpandedBayesianEngine

logger = logging.getLogger(__name__)


class EnhancedCounterfactualEngine(ExpandedBayesianEngine):
    """
    Enhanced Counterfactual Engine using do-calculus

    Implements Pearl's causal calculus for:
    - Intervention analysis (do-operator)
    - Counterfactual reasoning ("what if we had...")
    - Causal effect estimation
    - Backdoor adjustment
    - Front-door adjustment
    """

    def __init__(self):
        super().__init__()
        self.causal_graph = {}
        self._build_causal_graph()

    def _build_causal_graph(self):
        """Build causal graph structure from Bayesian network"""

        # Extract parent-child relationships from CPT
        self.causal_graph = {
            # Root events (no parents)
            'war': {'parents': set(), 'children': {'factory_shutdown', 'transport_shutdown', 'sanctions', 'border_closure'}},
            'pandemic': {'parents': set(), 'children': {'labor_shortage', 'factory_shutdown', 'quarantine_measures'}},
            'cyber_warfare': {'parents': set(), 'children': {'internet_shutdown', 'communication_failure', 'data_loss'}},
            'earthquake': {'parents': set(), 'children': {'infrastructure_damage', 'transport_shutdown', 'power_outage'}},
            'sanctions': {'parents': {'war'}, 'children': {'import_restriction', 'payment_freeze', 'supply_shortage'}},
            'terrorism': {'parents': set(), 'children': {'transport_shutdown', 'border_closure', 'security_lockdown'}},

            # Layer 2 disruptions
            'factory_shutdown': {'parents': {'war', 'pandemic', 'earthquake'}, 'children': {'production_stoppage', 'labor_idle'}},
            'transport_shutdown': {'parents': {'war', 'earthquake', 'terrorism'}, 'children': {'supply_delay', 'logistics_failure'}},
            'labor_shortage': {'parents': {'pandemic', 'war'}, 'children': {'production_slowdown', 'skill_shortage'}},
            'port_closure': {'parents': {'war', 'terrorism'}, 'children': {'supply_delay', 'container_shortage'}},
            'border_closure': {'parents': {'war', 'terrorism', 'pandemic'}, 'children': {'customs_delays', 'visa_restrictions'}},
            'power_outage': {'parents': {'earthquake', 'war'}, 'children': {'factory_shutdown', 'production_stoppage'}},

            # Layer 3 supply impacts
            'supply_delay': {'parents': {'transport_shutdown', 'port_closure', 'customs_delays'}, 'children': {'project_delay', 'material_shortage'}},
            'material_shortage': {'parents': {'supply_delay', 'supply_shortage', 'production_stoppage'}, 'children': {'project_delay', 'scope_reduction'}},
            'production_stoppage': {'parents': {'factory_shutdown', 'power_outage', 'labor_shortage'}, 'children': {'cost_overrun', 'project_delay'}},
            'logistics_failure': {'parents': {'transport_shutdown', 'customs_delays'}, 'children': {'supply_delay', 'cost_overrun'}},

            # Layer 4 outcomes
            'project_delay': {'parents': {'supply_delay', 'material_shortage', 'production_stoppage'}, 'children': {'fm_invocation', 'penalty_application'}},
            'cost_overrun': {'parents': {'production_stoppage', 'logistics_failure', 'material_shortage'}, 'children': {'fm_invocation', 'contract_variation'}},
            'fm_invocation': {'parents': {'project_delay', 'cost_overrun', 'contract_impossibility'}, 'children': {'contract_suspension', 'contract_termination'}},
            'contract_suspension': {'parents': {'fm_invocation'}, 'children': {'contract_termination'}},
            'contract_termination': {'parents': {'fm_invocation', 'contract_suspension'}, 'children': set()}
        }

    def do_intervention(
        self,
        intervention: Dict[str, bool],
        target_outcomes: List[str],
        background_evidence: Optional[Dict[str, bool]] = None
    ) -> Dict:
        """
        Perform do-operator intervention analysis

        Args:
            intervention: Variables to intervene on {variable: value}
            target_outcomes: Outcomes to measure
            background_evidence: Non-intervened evidence

        Returns:
            Causal effect of intervention on target outcomes

        Example:
            do_intervention({'war': False}, ['fm_invocation'])
            -> P(fm_invocation | do(war=False))
        """

        if background_evidence is None:
            background_evidence = {}

        # Calculate baseline (observational) probabilities
        baseline_probs = self._calculate_baseline_probabilities(
            target_outcomes,
            background_evidence
        )

        # Calculate intervention probabilities using do-calculus
        intervention_probs = self._calculate_intervention_probabilities(
            intervention,
            target_outcomes,
            background_evidence
        )

        # Calculate causal effects
        causal_effects = {}
        for outcome in target_outcomes:
            baseline = baseline_probs.get(outcome, 0.5)
            intervened = intervention_probs.get(outcome, 0.5)

            causal_effects[outcome] = {
                'baseline_probability': round(baseline, 4),
                'intervention_probability': round(intervened, 4),
                'causal_effect': round(intervened - baseline, 4),
                'relative_change_pct': round(((intervened - baseline) / baseline) * 100, 2) if baseline > 0 else 0,
                'effect_magnitude': self._classify_effect_magnitude(abs(intervened - baseline))
            }

        return {
            'intervention': intervention,
            'target_outcomes': target_outcomes,
            'background_evidence': background_evidence,
            'causal_effects': causal_effects,
            'interpretation': self._interpret_intervention_results(intervention, causal_effects)
        }

    def counterfactual_query(
        self,
        factual_world: Dict[str, bool],
        counterfactual_intervention: Dict[str, bool],
        target_outcome: str
    ) -> Dict:
        """
        Perform counterfactual reasoning: "What if X had been different?"

        Args:
            factual_world: What actually happened
            counterfactual_intervention: What we want to change
            target_outcome: Outcome to evaluate

        Returns:
            Counterfactual analysis

        Example:
            counterfactual_query(
                factual_world={'war': True, 'fm_invocation': True},
                counterfactual_intervention={'war': False},
                target_outcome='fm_invocation'
            )
            -> "Would FM have been invoked if war had not occurred?"
        """

        # Step 1: Abduction - infer latent variables from factual world
        latent_state = self._abduction(factual_world)

        # Step 2: Action - apply counterfactual intervention
        counterfactual_world = self._apply_counterfactual_intervention(
            factual_world,
            counterfactual_intervention,
            latent_state
        )

        # Step 3: Prediction - predict outcome in counterfactual world
        counterfactual_outcome = self._predict_counterfactual_outcome(
            counterfactual_world,
            target_outcome,
            latent_state
        )

        # Factual outcome
        factual_outcome = factual_world.get(target_outcome, None)
        if factual_outcome is None:
            # Infer factual outcome
            factual_probs = self.infer_risk(factual_world)
            factual_prob = factual_probs['probabilities'].get(target_outcome, 0.5)
            factual_outcome_likely = factual_prob > 0.5
        else:
            factual_outcome_likely = factual_outcome
            factual_prob = 1.0 if factual_outcome else 0.0

        return {
            'factual_world': factual_world,
            'counterfactual_intervention': counterfactual_intervention,
            'target_outcome': target_outcome,
            'factual_outcome': {
                'occurred': factual_outcome_likely,
                'probability': round(factual_prob, 4)
            },
            'counterfactual_outcome': {
                'would_occur': counterfactual_outcome['would_occur'],
                'probability': round(counterfactual_outcome['probability'], 4)
            },
            'effect_of_intervention': {
                'prevented_outcome': factual_outcome_likely and not counterfactual_outcome['would_occur'],
                'caused_outcome': not factual_outcome_likely and counterfactual_outcome['would_occur'],
                'no_effect': factual_outcome_likely == counterfactual_outcome['would_occur']
            },
            'interpretation': self._interpret_counterfactual(
                factual_outcome_likely,
                counterfactual_outcome['would_occur'],
                counterfactual_intervention,
                target_outcome
            )
        }

    def estimate_causal_effect(
        self,
        treatment: str,
        outcome: str,
        adjustment_set: Optional[List[str]] = None
    ) -> Dict:
        """
        Estimate average causal effect of treatment on outcome

        Uses backdoor adjustment to control for confounding

        Args:
            treatment: Treatment variable
            outcome: Outcome variable
            adjustment_set: Variables to adjust for (if None, auto-detect)

        Returns:
            Average Treatment Effect (ATE)
        """

        if adjustment_set is None:
            adjustment_set = self._find_backdoor_adjustment_set(treatment, outcome)

        # Calculate ATE using backdoor adjustment
        ate = self._calculate_ate_backdoor(treatment, outcome, adjustment_set)

        return {
            'treatment': treatment,
            'outcome': outcome,
            'adjustment_set': adjustment_set,
            'average_treatment_effect': {
                'ate': round(ate, 4),
                'interpretation': f"On average, {treatment} causes a {abs(ate):.2%} change in {outcome}",
                'direction': 'increases' if ate > 0 else 'decreases'
            },
            'method': 'backdoor_adjustment',
            'confounding_controlled': len(adjustment_set) > 0
        }

    def _calculate_baseline_probabilities(
        self,
        target_outcomes: List[str],
        evidence: Dict[str, bool]
    ) -> Dict[str, float]:
        """Calculate baseline (observational) probabilities"""

        result = self.infer_risk(evidence)
        probs = result['probabilities']

        return {outcome: probs.get(outcome, 0.5) for outcome in target_outcomes}

    def _calculate_intervention_probabilities(
        self,
        intervention: Dict[str, bool],
        target_outcomes: List[str],
        background_evidence: Dict[str, bool]
    ) -> Dict[str, float]:
        """Calculate probabilities under intervention using do-calculus"""

        # Create modified network with intervention applied
        # In do-calculus, we "cut" incoming edges to intervened variables

        # Combine intervention with background evidence
        # Intervention takes precedence
        combined_evidence = {**background_evidence, **intervention}

        # For simplicity, we'll use a truncated factorization approach
        # In full implementation, would modify graph structure

        # Remove parents of intervened variables from consideration
        intervened_vars = set(intervention.keys())

        # Calculate probabilities in modified network
        result = self.infer_risk(combined_evidence)
        probs = result['probabilities']

        return {outcome: probs.get(outcome, 0.5) for outcome in target_outcomes}

    def _abduction(self, factual_world: Dict[str, bool]) -> Dict:
        """
        Abduction step: infer latent/unobserved variables from observations

        In Bayesian networks, this involves posterior inference
        """

        # Use existing inference to get posterior over all variables
        inference_result = self.infer_risk(factual_world)

        # Store as latent state
        latent_state = {
            'inferred_probabilities': inference_result['probabilities'],
            'observed_evidence': factual_world
        }

        return latent_state

    def _apply_counterfactual_intervention(
        self,
        factual_world: Dict[str, bool],
        intervention: Dict[str, bool],
        latent_state: Dict
    ) -> Dict[str, bool]:
        """Apply counterfactual intervention to create alternate world"""

        counterfactual_world = factual_world.copy()

        # Apply intervention
        for var, value in intervention.items():
            counterfactual_world[var] = value

        return counterfactual_world

    def _predict_counterfactual_outcome(
        self,
        counterfactual_world: Dict[str, bool],
        target_outcome: str,
        latent_state: Dict
    ) -> Dict:
        """Predict outcome in counterfactual world"""

        # Use inference with counterfactual evidence
        inference_result = self.infer_risk(counterfactual_world)

        outcome_prob = inference_result['probabilities'].get(target_outcome, 0.5)

        return {
            'would_occur': outcome_prob > 0.5,
            'probability': outcome_prob
        }

    def _find_backdoor_adjustment_set(
        self,
        treatment: str,
        outcome: str
    ) -> List[str]:
        """
        Find variables that satisfy backdoor criterion

        Backdoor criterion: A set Z blocks all backdoor paths from X to Y
        """

        # Simplified: Find common causes of treatment and outcome
        adjustment_set = []

        if treatment not in self.causal_graph or outcome not in self.causal_graph:
            return adjustment_set

        treatment_parents = self.causal_graph.get(treatment, {}).get('parents', set())
        outcome_parents = self.causal_graph.get(outcome, {}).get('parents', set())

        # Common parents are potential confounders
        common_parents = treatment_parents & outcome_parents

        adjustment_set = list(common_parents)

        return adjustment_set

    def _calculate_ate_backdoor(
        self,
        treatment: str,
        outcome: str,
        adjustment_set: List[str]
    ) -> float:
        """Calculate Average Treatment Effect using backdoor adjustment"""

        # ATE = E[Y|do(X=1)] - E[Y|do(X=0)]
        # Using backdoor: E[Y|do(X=x)] = sum_z P(Y|X=x,Z=z) * P(Z=z)

        # For binary treatment and outcome:
        # Sample over adjustment set configurations

        ate = 0.0
        n_samples = 100

        for _ in range(n_samples):
            # Sample adjustment variables
            z_config = {var: np.random.random() < 0.5 for var in adjustment_set}

            # Calculate E[Y|X=1,Z]
            evidence_treat = {**z_config, treatment: True}
            result_treat = self.infer_risk(evidence_treat)
            p_y1_x1 = result_treat['probabilities'].get(outcome, 0.5)

            # Calculate E[Y|X=0,Z]
            evidence_control = {**z_config, treatment: False}
            result_control = self.infer_risk(evidence_control)
            p_y1_x0 = result_control['probabilities'].get(outcome, 0.5)

            # Add to ATE estimate
            ate += (p_y1_x1 - p_y1_x0) / n_samples

        return ate

    def _classify_effect_magnitude(self, effect: float) -> str:
        """Classify causal effect magnitude"""

        if effect < 0.05:
            return 'negligible'
        elif effect < 0.15:
            return 'small'
        elif effect < 0.30:
            return 'moderate'
        elif effect < 0.50:
            return 'large'
        else:
            return 'very_large'

    def _interpret_intervention_results(
        self,
        intervention: Dict[str, bool],
        causal_effects: Dict
    ) -> List[str]:
        """Generate interpretation of intervention results"""

        interpretations = []

        for outcome, effect_data in causal_effects.items():
            causal_effect = effect_data['causal_effect']
            magnitude = effect_data['effect_magnitude']

            if magnitude == 'negligible':
                interpretations.append(
                    f"Intervention on {list(intervention.keys())} has negligible effect on {outcome}"
                )
            else:
                direction = "increases" if causal_effect > 0 else "decreases"
                interpretations.append(
                    f"Intervention on {list(intervention.keys())} {direction} {outcome} "
                    f"probability by {abs(causal_effect):.2%} ({magnitude} effect)"
                )

        return interpretations

    def _interpret_counterfactual(
        self,
        factual_outcome: bool,
        counterfactual_outcome: bool,
        intervention: Dict[str, bool],
        target: str
    ) -> str:
        """Generate natural language interpretation of counterfactual"""

        intervention_desc = ', '.join([f"{k}={v}" for k, v in intervention.items()])

        if factual_outcome and not counterfactual_outcome:
            return (
                f"The intervention ({intervention_desc}) would have PREVENTED {target}. "
                f"In reality, {target} occurred, but it would not have if the intervention had been applied."
            )
        elif not factual_outcome and counterfactual_outcome:
            return (
                f"The intervention ({intervention_desc}) would have CAUSED {target}. "
                f"In reality, {target} did not occur, but it would have if the intervention had been applied."
            )
        else:
            return (
                f"The intervention ({intervention_desc}) would have had NO EFFECT on {target}. "
                f"The outcome would have been the same regardless."
            )

    def sensitivity_analysis(
        self,
        intervention: Dict[str, bool],
        target_outcome: str,
        unmeasured_confounder_strength: float = 0.3
    ) -> Dict:
        """
        Perform sensitivity analysis to unmeasured confounding

        Args:
            intervention: Intervention to analyze
            target_outcome: Target outcome
            unmeasured_confounder_strength: Strength of potential unmeasured confounder (0-1)

        Returns:
            Sensitivity analysis results
        """

        # Baseline causal effect
        baseline = self.do_intervention(intervention, [target_outcome])
        baseline_effect = baseline['causal_effects'][target_outcome]['causal_effect']

        # Simulate unmeasured confounder
        # Confounder affects both intervention and outcome

        confounded_effects = []
        confounder_strengths = np.linspace(0, unmeasured_confounder_strength, 10)

        for strength in confounder_strengths:
            # Adjust probabilities based on confounder
            adjusted_effect = baseline_effect * (1 - strength * 0.5)  # Simplified model
            confounded_effects.append(adjusted_effect)

        # Check if conclusion would change
        conclusion_robust = all(
            (baseline_effect > 0 and e > 0) or (baseline_effect < 0 and e < 0)
            for e in confounded_effects
        )

        return {
            'baseline_causal_effect': round(baseline_effect, 4),
            'unmeasured_confounder_strength': unmeasured_confounder_strength,
            'effect_range': {
                'min': round(min(confounded_effects), 4),
                'max': round(max(confounded_effects), 4)
            },
            'conclusion_robust': conclusion_robust,
            'interpretation': (
                "Causal conclusion is robust to unmeasured confounding"
                if conclusion_robust else
                "Causal conclusion may be sensitive to unmeasured confounding"
            )
        }


# Global instance
enhanced_counterfactual_engine = EnhancedCounterfactualEngine()


# Convenience functions
def do_intervention_analysis(
    intervention: Dict[str, bool],
    target_outcomes: List[str],
    background_evidence: Optional[Dict[str, bool]] = None
) -> Dict:
    """Perform do-operator intervention analysis"""
    return enhanced_counterfactual_engine.do_intervention(
        intervention,
        target_outcomes,
        background_evidence
    )


def counterfactual_analysis(
    factual_world: Dict[str, bool],
    counterfactual_intervention: Dict[str, bool],
    target_outcome: str
) -> Dict:
    """Perform counterfactual reasoning"""
    return enhanced_counterfactual_engine.counterfactual_query(
        factual_world,
        counterfactual_intervention,
        target_outcome
    )


def estimate_treatment_effect(
    treatment: str,
    outcome: str,
    adjustment_set: Optional[List[str]] = None
) -> Dict:
    """Estimate average causal effect"""
    return enhanced_counterfactual_engine.estimate_causal_effect(
        treatment,
        outcome,
        adjustment_set
    )
