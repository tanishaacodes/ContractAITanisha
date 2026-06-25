"""
Dynamic Bayesian Network for Temporal Force Majeure Risk Modeling
Extends static Bayesian network with temporal dependencies for time-series predictions
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from .expanded_bayesian_engine import ExpandedBayesianEngine

logger = logging.getLogger(__name__)


class DynamicBayesianNetwork(ExpandedBayesianEngine):
    """
    Dynamic Bayesian Network for temporal FM risk modeling

    Models risk evolution over time with:
    - Temporal dependencies between time slices
    - State persistence (e.g., war continues from t to t+1)
    - Evidence propagation across time
    - Risk trajectory forecasting
    """

    def __init__(self):
        super().__init__()
        self.time_slices = []
        self.temporal_transitions = {}
        self._initialize_temporal_structure()

    def _initialize_temporal_structure(self):
        """Initialize temporal transition probabilities"""

        # Temporal transition probabilities P(X_t+1 | X_t)
        # Format: {node_name: {(prev_state, curr_evidence): probability}}

        # Events tend to persist (wars don't end immediately)
        self.temporal_transitions = {
            'war': {
                (True, True): 0.90,   # War continues if already at war
                (True, False): 0.10,  # War ends
                (False, True): 0.02,  # New war starts
                (False, False): 0.98  # Peace continues
            },
            'pandemic': {
                (True, True): 0.85,
                (True, False): 0.15,
                (False, True): 0.01,
                (False, False): 0.99
            },
            'sanctions': {
                (True, True): 0.95,   # Sanctions very persistent
                (True, False): 0.05,
                (False, True): 0.03,
                (False, False): 0.97
            },
            'civil_war': {
                (True, True): 0.88,
                (True, False): 0.12,
                (False, True): 0.01,
                (False, False): 0.99
            },
            'earthquake': {
                (True, True): 0.20,   # Earthquakes are discrete events
                (True, False): 0.80,
                (False, True): 0.001,
                (False, False): 0.999
            },
            'cyber_warfare': {
                (True, True): 0.70,
                (True, False): 0.30,
                (False, True): 0.05,
                (False, False): 0.95
            },
            'port_closure': {
                (True, True): 0.75,
                (True, False): 0.25,
                (False, True): 0.02,
                (False, False): 0.98
            },
            'supply_chain_disruption': {
                (True, True): 0.80,
                (True, False): 0.20,
                (False, True): 0.05,
                (False, False): 0.95
            },
            'project_delay': {
                (True, True): 0.85,   # Delays tend to compound
                (True, False): 0.15,
                (False, True): 0.10,
                (False, False): 0.90
            },
            'cost_overrun': {
                (True, True): 0.90,
                (True, False): 0.10,
                (False, True): 0.15,
                (False, False): 0.85
            }
        }

        # Momentum factors (how fast situations escalate/de-escalate)
        self.momentum_factors = {
            'war': 0.15,              # Slow to escalate, slow to resolve
            'pandemic': 0.25,         # Can escalate quickly
            'sanctions': 0.10,        # Very slow to change
            'cyber_warfare': 0.40,    # Rapid escalation possible
            'supply_chain_disruption': 0.30
        }

    def forecast_temporal_risk(
        self,
        initial_evidence: Dict[str, bool],
        time_steps: int = 12,
        time_unit: str = 'months',
        target_outcomes: Optional[List[str]] = None
    ) -> Dict:
        """
        Forecast FM risk evolution over time

        Args:
            initial_evidence: Current state {node_name: True/False}
            time_steps: Number of time periods to forecast
            time_unit: 'days', 'weeks', 'months', 'quarters', 'years'
            target_outcomes: Specific outcomes to track

        Returns:
            Time series of risk probabilities with trajectory analysis
        """

        if target_outcomes is None:
            target_outcomes = [
                'fm_invocation', 'project_delay', 'cost_overrun',
                'contract_suspension', 'contract_termination'
            ]

        # Initialize trajectories
        trajectories = {outcome: [] for outcome in target_outcomes}
        evidence_history = [initial_evidence.copy()]

        current_evidence = initial_evidence.copy()

        # Simulate forward through time
        for t in range(time_steps):
            # Infer probabilities at current time step
            current_probs = self.infer_risk(current_evidence)

            # Record target outcome probabilities
            for outcome in target_outcomes:
                prob = current_probs['probabilities'].get(outcome, 0.0)
                trajectories[outcome].append({
                    'time_step': t,
                    'probability': prob,
                    'evidence': current_evidence.copy()
                })

            # Transition to next time step using temporal transitions
            next_evidence = self._transition_to_next_timestep(
                current_evidence,
                current_probs['probabilities']
            )

            evidence_history.append(next_evidence.copy())
            current_evidence = next_evidence

        # Analyze trajectories
        trajectory_analysis = self._analyze_trajectories(trajectories, time_steps)

        # Calculate risk momentum (acceleration/deceleration)
        momentum_analysis = self._calculate_risk_momentum(trajectories)

        # Identify critical time windows
        critical_windows = self._identify_critical_windows(trajectories, threshold=0.60)

        return {
            'forecast_horizon': {
                'time_steps': time_steps,
                'time_unit': time_unit,
                'start_date': datetime.now().isoformat(),
                'end_date': self._calculate_end_date(time_steps, time_unit).isoformat()
            },
            'trajectories': trajectories,
            'trajectory_analysis': trajectory_analysis,
            'momentum_analysis': momentum_analysis,
            'critical_windows': critical_windows,
            'evidence_history': evidence_history,
            'recommendations': self._generate_temporal_recommendations(
                trajectory_analysis,
                momentum_analysis,
                critical_windows
            )
        }

    def _transition_to_next_timestep(
        self,
        current_evidence: Dict[str, bool],
        current_probabilities: Dict[str, float]
    ) -> Dict[str, bool]:
        """Transition evidence from time t to t+1 using temporal model"""

        next_evidence = {}

        for node, current_state in current_evidence.items():
            if node in self.temporal_transitions:
                # Use temporal transition probability
                transition_probs = self.temporal_transitions[node]

                # Get P(node_t+1=True | node_t=current_state)
                stay_prob = transition_probs.get((current_state, True), 0.5)

                # Sample next state
                next_state = np.random.random() < stay_prob
                next_evidence[node] = next_state
            else:
                # For nodes without explicit temporal model, use current probability
                node_prob = current_probabilities.get(node, 0.5)
                next_evidence[node] = np.random.random() < node_prob

        # Add temporal persistence effects
        next_evidence = self._apply_persistence_effects(current_evidence, next_evidence)

        return next_evidence

    def _apply_persistence_effects(
        self,
        prev_evidence: Dict[str, bool],
        next_evidence: Dict[str, bool]
    ) -> Dict[str, bool]:
        """Apply persistence effects (e.g., delays persist, outcomes compound)"""

        # If project_delay was True, it likely stays True
        if prev_evidence.get('project_delay', False):
            if np.random.random() < 0.85:  # 85% persistence
                next_evidence['project_delay'] = True

        # Cost overruns tend to persist and compound
        if prev_evidence.get('cost_overrun', False):
            if np.random.random() < 0.90:  # 90% persistence
                next_evidence['cost_overrun'] = True

        # FM invocation has lasting effects
        if prev_evidence.get('fm_invocation', False):
            if np.random.random() < 0.70:
                next_evidence['fm_invocation'] = True

        return next_evidence

    def _analyze_trajectories(
        self,
        trajectories: Dict[str, List[Dict]],
        time_steps: int
    ) -> Dict:
        """Analyze trajectory patterns"""

        analysis = {}

        for outcome, trajectory in trajectories.items():
            probs = [step['probability'] for step in trajectory]

            # Trend analysis
            if len(probs) > 1:
                trend = 'increasing' if probs[-1] > probs[0] else 'decreasing'
                trend_magnitude = abs(probs[-1] - probs[0])
            else:
                trend = 'stable'
                trend_magnitude = 0

            # Peak analysis
            max_prob = max(probs)
            max_time = probs.index(max_prob)

            # Volatility
            volatility = np.std(probs) if len(probs) > 1 else 0

            analysis[outcome] = {
                'initial_probability': probs[0],
                'final_probability': probs[-1],
                'peak_probability': max_prob,
                'peak_time_step': max_time,
                'trend': trend,
                'trend_magnitude': round(trend_magnitude, 3),
                'volatility': round(volatility, 3),
                'average_probability': round(np.mean(probs), 3),
                'time_above_50pct': sum(1 for p in probs if p > 0.50)
            }

        return analysis

    def _calculate_risk_momentum(
        self,
        trajectories: Dict[str, List[Dict]]
    ) -> Dict:
        """Calculate risk momentum (rate of change)"""

        momentum = {}

        for outcome, trajectory in trajectories.items():
            probs = [step['probability'] for step in trajectory]

            if len(probs) < 2:
                momentum[outcome] = {'momentum': 0, 'acceleration': 0}
                continue

            # Calculate first derivative (velocity)
            velocities = np.diff(probs)
            avg_velocity = np.mean(velocities)

            # Calculate second derivative (acceleration)
            if len(velocities) > 1:
                accelerations = np.diff(velocities)
                avg_acceleration = np.mean(accelerations)
            else:
                avg_acceleration = 0

            # Momentum classification
            if avg_velocity > 0.02:
                momentum_class = 'accelerating_risk'
            elif avg_velocity < -0.02:
                momentum_class = 'decelerating_risk'
            else:
                momentum_class = 'stable_risk'

            momentum[outcome] = {
                'average_velocity': round(avg_velocity, 4),
                'average_acceleration': round(avg_acceleration, 4),
                'momentum_class': momentum_class,
                'current_velocity': round(velocities[-1], 4) if len(velocities) > 0 else 0
            }

        return momentum

    def _identify_critical_windows(
        self,
        trajectories: Dict[str, List[Dict]],
        threshold: float = 0.60
    ) -> List[Dict]:
        """Identify time windows where risk exceeds threshold"""

        critical_windows = []

        for outcome, trajectory in trajectories.items():
            in_critical = False
            window_start = None

            for step in trajectory:
                t = step['time_step']
                prob = step['probability']

                if prob >= threshold and not in_critical:
                    # Start of critical window
                    in_critical = True
                    window_start = t

                elif prob < threshold and in_critical:
                    # End of critical window
                    in_critical = False
                    critical_windows.append({
                        'outcome': outcome,
                        'start_time': window_start,
                        'end_time': t - 1,
                        'duration': t - window_start,
                        'max_probability': max(
                            trajectory[i]['probability']
                            for i in range(window_start, t)
                        )
                    })

            # Handle window that extends to end
            if in_critical:
                critical_windows.append({
                    'outcome': outcome,
                    'start_time': window_start,
                    'end_time': len(trajectory) - 1,
                    'duration': len(trajectory) - window_start,
                    'max_probability': max(
                        trajectory[i]['probability']
                        for i in range(window_start, len(trajectory))
                    )
                })

        # Sort by start time
        critical_windows.sort(key=lambda x: x['start_time'])

        return critical_windows

    def _calculate_end_date(self, time_steps: int, time_unit: str) -> datetime:
        """Calculate end date based on time steps and unit"""

        now = datetime.now()

        if time_unit == 'days':
            return now + timedelta(days=time_steps)
        elif time_unit == 'weeks':
            return now + timedelta(weeks=time_steps)
        elif time_unit == 'months':
            return now + timedelta(days=time_steps * 30)  # Approximate
        elif time_unit == 'quarters':
            return now + timedelta(days=time_steps * 90)
        elif time_unit == 'years':
            return now + timedelta(days=time_steps * 365)
        else:
            return now + timedelta(days=time_steps * 30)  # Default to months

    def _generate_temporal_recommendations(
        self,
        trajectory_analysis: Dict,
        momentum_analysis: Dict,
        critical_windows: List[Dict]
    ) -> List[str]:
        """Generate recommendations based on temporal analysis"""

        recommendations = []

        # Check for accelerating risks
        accelerating = [
            outcome for outcome, data in momentum_analysis.items()
            if data['momentum_class'] == 'accelerating_risk'
        ]

        if accelerating:
            recommendations.append(
                f"URGENT: {len(accelerating)} risk(s) accelerating: {', '.join(accelerating[:3])}"
            )
            recommendations.append(
                "Implement immediate mitigation measures to reverse risk momentum"
            )

        # Check for high-probability outcomes
        high_risk_outcomes = [
            outcome for outcome, data in trajectory_analysis.items()
            if data['final_probability'] > 0.60
        ]

        if high_risk_outcomes:
            recommendations.append(
                f"High risk outcomes in forecast: {', '.join(high_risk_outcomes)}"
            )

        # Check for critical windows
        if len(critical_windows) > 0:
            earliest_window = critical_windows[0]
            recommendations.append(
                f"Critical risk window begins at time step {earliest_window['start_time']} "
                f"for {earliest_window['outcome']}"
            )
            recommendations.append(
                "Schedule risk mitigation actions before critical window"
            )

        # Check volatility
        volatile_outcomes = [
            outcome for outcome, data in trajectory_analysis.items()
            if data['volatility'] > 0.15
        ]

        if volatile_outcomes:
            recommendations.append(
                f"High volatility detected in: {', '.join(volatile_outcomes[:3])}"
            )
            recommendations.append(
                "Implement continuous monitoring for volatile risk factors"
            )

        # General recommendations
        recommendations.append("Conduct scenario planning for critical time windows")
        recommendations.append("Update risk assessment as new evidence emerges")
        recommendations.append("Establish trigger points for escalation procedures")

        return recommendations

    def compare_scenarios(
        self,
        baseline_evidence: Dict[str, bool],
        alternative_scenarios: List[Dict],
        time_steps: int = 12
    ) -> Dict:
        """
        Compare risk trajectories across multiple scenarios

        Args:
            baseline_evidence: Baseline scenario evidence
            alternative_scenarios: List of alternative scenario evidence dicts
            time_steps: Forecast horizon

        Returns:
            Comparative analysis of scenario trajectories
        """

        # Forecast baseline
        baseline_forecast = self.forecast_temporal_risk(
            baseline_evidence,
            time_steps=time_steps
        )

        # Forecast alternatives
        alternative_forecasts = []
        for i, alt_evidence in enumerate(alternative_scenarios):
            alt_forecast = self.forecast_temporal_risk(
                alt_evidence,
                time_steps=time_steps
            )
            alternative_forecasts.append({
                'scenario_id': i + 1,
                'evidence': alt_evidence,
                'forecast': alt_forecast
            })

        # Compare outcomes
        comparison = self._compare_scenario_outcomes(
            baseline_forecast,
            alternative_forecasts
        )

        return {
            'baseline_scenario': {
                'evidence': baseline_evidence,
                'forecast': baseline_forecast
            },
            'alternative_scenarios': alternative_forecasts,
            'comparison': comparison,
            'best_scenario': self._identify_best_scenario(
                baseline_forecast,
                alternative_forecasts
            )
        }

    def _compare_scenario_outcomes(
        self,
        baseline: Dict,
        alternatives: List[Dict]
    ) -> Dict:
        """Compare risk outcomes across scenarios"""

        comparison = {}

        baseline_trajectories = baseline['trajectories']

        for outcome in baseline_trajectories.keys():
            baseline_final = baseline['trajectory_analysis'][outcome]['final_probability']

            alt_finals = []
            for alt in alternatives:
                alt_final = alt['forecast']['trajectory_analysis'][outcome]['final_probability']
                alt_finals.append(alt_final)

            best_alt_idx = np.argmin(alt_finals) if alt_finals else None
            best_alt_prob = min(alt_finals) if alt_finals else baseline_final

            comparison[outcome] = {
                'baseline_final_probability': baseline_final,
                'best_alternative_probability': best_alt_prob,
                'best_alternative_scenario': best_alt_idx + 1 if best_alt_idx is not None else None,
                'risk_reduction': round(baseline_final - best_alt_prob, 3),
                'risk_reduction_pct': round((baseline_final - best_alt_prob) / baseline_final * 100, 1) if baseline_final > 0 else 0
            }

        return comparison

    def _identify_best_scenario(
        self,
        baseline: Dict,
        alternatives: List[Dict]
    ) -> Dict:
        """Identify overall best scenario"""

        # Score scenarios based on weighted risk outcomes
        weights = {
            'fm_invocation': 0.30,
            'contract_termination': 0.25,
            'contract_suspension': 0.20,
            'cost_overrun': 0.15,
            'project_delay': 0.10
        }

        baseline_score = self._calculate_scenario_score(baseline, weights)

        alt_scores = []
        for i, alt in enumerate(alternatives):
            score = self._calculate_scenario_score(alt['forecast'], weights)
            alt_scores.append({
                'scenario_id': i + 1,
                'score': score,
                'evidence': alt['evidence']
            })

        # Find minimum risk score (best scenario)
        best_alt = min(alt_scores, key=lambda x: x['score']) if alt_scores else None

        if best_alt and best_alt['score'] < baseline_score:
            return {
                'is_baseline': False,
                'scenario_id': best_alt['scenario_id'],
                'risk_score': round(best_alt['score'], 3),
                'baseline_risk_score': round(baseline_score, 3),
                'improvement': round(baseline_score - best_alt['score'], 3),
                'evidence': best_alt['evidence']
            }
        else:
            return {
                'is_baseline': True,
                'risk_score': round(baseline_score, 3),
                'message': 'Baseline scenario is optimal'
            }

    def _calculate_scenario_score(
        self,
        forecast: Dict,
        weights: Dict[str, float]
    ) -> float:
        """Calculate weighted risk score for scenario"""

        score = 0.0

        for outcome, weight in weights.items():
            if outcome in forecast['trajectory_analysis']:
                final_prob = forecast['trajectory_analysis'][outcome]['final_probability']
                score += weight * final_prob

        return score


# Global instance
dynamic_bayesian_network = DynamicBayesianNetwork()


# Convenience functions
def forecast_risk_trajectory(
    initial_evidence: Dict[str, bool],
    time_steps: int = 12,
    time_unit: str = 'months'
) -> Dict:
    """Forecast FM risk evolution over time"""
    return dynamic_bayesian_network.forecast_temporal_risk(
        initial_evidence,
        time_steps,
        time_unit
    )


def compare_risk_scenarios(
    baseline_evidence: Dict[str, bool],
    alternative_scenarios: List[Dict],
    time_steps: int = 12
) -> Dict:
    """Compare risk trajectories across scenarios"""
    return dynamic_bayesian_network.compare_scenarios(
        baseline_evidence,
        alternative_scenarios,
        time_steps
    )
