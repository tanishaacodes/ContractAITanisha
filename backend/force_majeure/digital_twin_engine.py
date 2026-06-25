"""
Contract Digital Twin Engine
Creates virtual replicas of contracts with real-time state tracking and scenario simulation
"""

import uuid
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class ContractState:
    """Contract state at a point in time"""
    timestamp: datetime
    phase: str  # planning, execution, delay, suspended, terminated, completed
    completion_percentage: float
    budget_spent: float
    remaining_budget: float
    days_elapsed: int
    days_remaining: int
    active_risks: List[str]
    fm_events_occurred: List[Dict]
    performance_score: float
    health_status: str  # green, yellow, red


@dataclass
class ContractDigitalTwin:
    """Digital twin of a contract"""
    twin_id: str
    contract_id: str
    contract_name: str
    contract_value: float
    start_date: datetime
    planned_end_date: datetime
    current_state: ContractState
    state_history: List[ContractState] = field(default_factory=list)
    fm_clause_text: str = ""
    risk_profile: Dict = field(default_factory=dict)
    dependencies: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class DigitalTwinEngine:
    """
    Contract Digital Twin Engine

    Creates and manages virtual replicas of contracts with:
    - Real-time state synchronization
    - Historical state tracking
    - What-if scenario simulation
    - Risk impact modeling
    - Performance prediction
    """

    def __init__(self):
        self.twins: Dict[str, ContractDigitalTwin] = {}
        self.simulation_results = {}

    def create_twin(
        self,
        contract_id: str,
        contract_data: Dict
    ) -> str:
        """
        Create a digital twin for a contract

        Args:
            contract_id: Unique contract identifier
            contract_data: Contract details and current state

        Returns:
            twin_id: Unique digital twin identifier
        """

        twin_id = f"twin_{uuid.uuid4().hex[:12]}"

        # Parse contract data
        contract_value = float(contract_data.get('contract_value', 0))
        start_date_str = contract_data.get('start_date')
        end_date_str = contract_data.get('end_date')

        if isinstance(start_date_str, str):
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        else:
            start_date = datetime.now()

        if isinstance(end_date_str, str):
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        else:
            end_date = start_date + timedelta(days=365)

        # Calculate current state
        now = datetime.now()
        days_elapsed = max(0, (now - start_date).days)
        total_days = max(1, (end_date - start_date).days)
        days_remaining = max(0, (end_date - now).days)

        completion_pct = contract_data.get('completion_percentage', min(100, (days_elapsed / total_days) * 100))
        budget_spent = contract_data.get('budget_spent', contract_value * (completion_pct / 100))
        remaining_budget = contract_value - budget_spent

        # Initialize current state
        current_state = ContractState(
            timestamp=now,
            phase=contract_data.get('phase', 'execution'),
            completion_percentage=round(completion_pct, 2),
            budget_spent=budget_spent,
            remaining_budget=remaining_budget,
            days_elapsed=days_elapsed,
            days_remaining=days_remaining,
            active_risks=contract_data.get('active_risks', []),
            fm_events_occurred=contract_data.get('fm_events', []),
            performance_score=contract_data.get('performance_score', 0.80),
            health_status=self._calculate_health_status(completion_pct, days_elapsed, total_days)
        )

        # Create twin
        twin = ContractDigitalTwin(
            twin_id=twin_id,
            contract_id=contract_id,
            contract_name=contract_data.get('contract_name', f'Contract {contract_id}'),
            contract_value=contract_value,
            start_date=start_date,
            planned_end_date=end_date,
            current_state=current_state,
            state_history=[current_state],
            fm_clause_text=contract_data.get('fm_clause', ''),
            risk_profile=contract_data.get('risk_profile', {}),
            dependencies=contract_data.get('dependencies', []),
            metadata=contract_data.get('metadata', {})
        )

        self.twins[twin_id] = twin

        logger.info(f"Created digital twin {twin_id} for contract {contract_id}")

        return twin_id

    def update_twin_state(
        self,
        twin_id: str,
        state_update: Dict
    ) -> Dict:
        """
        Update digital twin state with new information

        Args:
            twin_id: Digital twin identifier
            state_update: State changes to apply

        Returns:
            Updated state summary
        """

        if twin_id not in self.twins:
            return {'error': f'Twin {twin_id} not found'}

        twin = self.twins[twin_id]
        current = twin.current_state

        # Apply updates
        new_state = ContractState(
            timestamp=datetime.now(),
            phase=state_update.get('phase', current.phase),
            completion_percentage=state_update.get('completion_percentage', current.completion_percentage),
            budget_spent=state_update.get('budget_spent', current.budget_spent),
            remaining_budget=state_update.get('remaining_budget', current.remaining_budget),
            days_elapsed=state_update.get('days_elapsed', current.days_elapsed),
            days_remaining=state_update.get('days_remaining', current.days_remaining),
            active_risks=state_update.get('active_risks', current.active_risks),
            fm_events_occurred=state_update.get('fm_events_occurred', current.fm_events_occurred),
            performance_score=state_update.get('performance_score', current.performance_score),
            health_status=state_update.get('health_status', current.health_status)
        )

        # Update twin
        twin.current_state = new_state
        twin.state_history.append(new_state)

        return {
            'twin_id': twin_id,
            'updated_at': new_state.timestamp.isoformat(),
            'current_state': self._state_to_dict(new_state),
            'state_changes': self._detect_state_changes(current, new_state)
        }

    def simulate_fm_scenario(
        self,
        twin_id: str,
        fm_scenario: Dict,
        simulation_params: Optional[Dict] = None
    ) -> Dict:
        """
        Simulate FM event impact on contract digital twin

        Args:
            twin_id: Digital twin identifier
            fm_scenario: FM event details {type, severity, duration, start_day}
            simulation_params: Simulation configuration

        Returns:
            Scenario simulation results
        """

        if twin_id not in self.twins:
            return {'error': f'Twin {twin_id} not found'}

        twin = self.twins[twin_id]

        if simulation_params is None:
            simulation_params = {
                'monte_carlo_runs': 1000,
                'forecast_days': 365
            }

        # Run Monte Carlo simulation
        simulation_id = f"sim_{uuid.uuid4().hex[:8]}"

        results = self._run_monte_carlo_simulation(
            twin,
            fm_scenario,
            simulation_params
        )

        # Store simulation results
        self.simulation_results[simulation_id] = {
            'twin_id': twin_id,
            'scenario': fm_scenario,
            'params': simulation_params,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }

        return {
            'simulation_id': simulation_id,
            'twin_id': twin_id,
            'scenario': fm_scenario,
            'results': results
        }

    def _run_monte_carlo_simulation(
        self,
        twin: ContractDigitalTwin,
        fm_scenario: Dict,
        params: Dict
    ) -> Dict:
        """Run Monte Carlo simulation of FM impact"""

        n_runs = params.get('monte_carlo_runs', 1000)
        forecast_days = params.get('forecast_days', 365)

        # FM event parameters
        fm_type = fm_scenario.get('type', 'war')
        fm_severity = fm_scenario.get('severity', 0.70)
        fm_duration_days = fm_scenario.get('duration_days', 90)
        fm_start_day = fm_scenario.get('start_day', 30)

        # Current state
        current_completion = twin.current_state.completion_percentage
        current_budget_spent = twin.current_state.budget_spent
        remaining_value = twin.contract_value - current_budget_spent

        # Simulation results storage
        final_completion = []
        final_costs = []
        delay_days_list = []
        fm_triggered_count = 0

        np.random.seed(42)

        for _ in range(n_runs):
            # Simulate contract progression
            sim_completion = current_completion
            sim_cost = current_budget_spent
            sim_day = 0
            fm_triggered = False
            delay_days = 0

            while sim_day < forecast_days and sim_completion < 100:
                # Check if FM event occurs
                if sim_day == fm_start_day and not fm_triggered:
                    fm_triggered = True
                    fm_triggered_count += 1

                    # FM event causes delay
                    delay_days = fm_duration_days + np.random.randint(0, 30)

                    # Cost increase during FM period
                    idle_cost_rate = remaining_value * 0.002  # 0.2% per day idle
                    fm_cost_increase = idle_cost_rate * delay_days * fm_severity

                    # Add remobilization costs
                    remob_cost = remaining_value * 0.05 * fm_severity

                    sim_cost += fm_cost_increase + remob_cost

                    # Skip ahead by delay period
                    sim_day += delay_days

                # Normal progression
                if sim_completion < 100:
                    # Daily progress rate
                    base_progress_rate = (100 - current_completion) / max(1, (forecast_days - sim_day))

                    # Add noise
                    progress = base_progress_rate * np.random.uniform(0.8, 1.2)
                    sim_completion += progress

                    # Daily cost burn rate
                    daily_cost = remaining_value / max(1, (forecast_days - sim_day))
                    sim_cost += daily_cost * np.random.uniform(0.9, 1.1)

                sim_day += 1

            final_completion.append(min(100, sim_completion))
            final_costs.append(sim_cost)
            delay_days_list.append(delay_days)

        final_completion = np.array(final_completion)
        final_costs = np.array(final_costs)
        delay_days_list = np.array(delay_days_list)

        # Calculate statistics
        expected_completion = np.mean(final_completion)
        expected_cost = np.mean(final_costs)
        expected_delay = np.mean(delay_days_list)

        cost_overrun = expected_cost - twin.contract_value
        cost_overrun_pct = (cost_overrun / twin.contract_value) * 100 if twin.contract_value > 0 else 0

        # Probabilities
        prob_complete_on_time = np.mean(final_completion >= 100) * (1 - fm_severity * 0.5)
        prob_fm_invocation = fm_triggered_count / n_runs
        prob_cost_overrun = np.mean(final_costs > twin.contract_value)

        return {
            'expected_outcomes': {
                'completion_percentage': round(expected_completion, 2),
                'total_cost_usd': round(expected_cost, 2),
                'cost_overrun_usd': round(cost_overrun, 2),
                'cost_overrun_pct': round(cost_overrun_pct, 2),
                'delay_days': round(expected_delay, 1)
            },
            'probabilities': {
                'complete_on_time': round(prob_complete_on_time, 3),
                'fm_invocation': round(prob_fm_invocation, 3),
                'cost_overrun': round(prob_cost_overrun, 3)
            },
            'percentiles': {
                'completion': {
                    'p50': round(np.percentile(final_completion, 50), 2),
                    'p90': round(np.percentile(final_completion, 90), 2),
                    'p10': round(np.percentile(final_completion, 10), 2)
                },
                'cost': {
                    'p50': round(np.percentile(final_costs, 50), 2),
                    'p90': round(np.percentile(final_costs, 90), 2),
                    'p10': round(np.percentile(final_costs, 10), 2)
                },
                'delay_days': {
                    'p50': round(np.percentile(delay_days_list, 50), 1),
                    'p90': round(np.percentile(delay_days_list, 90), 1),
                    'p10': round(np.percentile(delay_days_list, 10), 1)
                }
            },
            'simulation_params': {
                'runs': n_runs,
                'forecast_days': forecast_days
            },
            'risk_assessment': self._assess_simulation_risk(
                expected_completion,
                cost_overrun_pct,
                expected_delay,
                prob_fm_invocation
            )
        }

    def compare_scenarios(
        self,
        twin_id: str,
        scenarios: List[Dict]
    ) -> Dict:
        """
        Compare multiple FM scenarios on the same digital twin

        Args:
            twin_id: Digital twin identifier
            scenarios: List of FM scenarios to compare

        Returns:
            Comparative analysis of scenarios
        """

        if twin_id not in self.twins:
            return {'error': f'Twin {twin_id} not found'}

        scenario_results = []

        for i, scenario in enumerate(scenarios):
            result = self.simulate_fm_scenario(twin_id, scenario)
            scenario_results.append({
                'scenario_id': i + 1,
                'scenario': scenario,
                'simulation_id': result.get('simulation_id'),
                'results': result.get('results', {})
            })

        # Comparative analysis
        comparison = self._compare_scenario_results(scenario_results)

        return {
            'twin_id': twin_id,
            'scenarios_compared': len(scenarios),
            'scenario_results': scenario_results,
            'comparison': comparison,
            'recommendations': self._generate_comparison_recommendations(comparison)
        }

    def get_twin_status(self, twin_id: str) -> Dict:
        """Get current status of digital twin"""

        if twin_id not in self.twins:
            return {'error': f'Twin {twin_id} not found'}

        twin = self.twins[twin_id]
        state = twin.current_state

        return {
            'twin_id': twin_id,
            'contract_id': twin.contract_id,
            'contract_name': twin.contract_name,
            'current_state': self._state_to_dict(state),
            'health_status': state.health_status,
            'performance_score': state.performance_score,
            'state_history_length': len(twin.state_history),
            'last_updated': state.timestamp.isoformat()
        }

    def get_state_history(
        self,
        twin_id: str,
        limit: Optional[int] = None
    ) -> Dict:
        """Get historical states of digital twin"""

        if twin_id not in self.twins:
            return {'error': f'Twin {twin_id} not found'}

        twin = self.twins[twin_id]
        history = twin.state_history

        if limit:
            history = history[-limit:]

        return {
            'twin_id': twin_id,
            'total_states': len(twin.state_history),
            'returned_states': len(history),
            'history': [self._state_to_dict(s) for s in history]
        }

    def _calculate_health_status(
        self,
        completion_pct: float,
        days_elapsed: int,
        total_days: int
    ) -> str:
        """Calculate contract health status"""

        expected_completion = (days_elapsed / total_days) * 100 if total_days > 0 else 0

        deviation = completion_pct - expected_completion

        if deviation >= 5:
            return 'green'  # Ahead of schedule
        elif deviation >= -10:
            return 'yellow'  # On track or slightly behind
        else:
            return 'red'  # Significantly behind

    def _state_to_dict(self, state: ContractState) -> Dict:
        """Convert ContractState to dictionary"""
        return {
            'timestamp': state.timestamp.isoformat(),
            'phase': state.phase,
            'completion_percentage': state.completion_percentage,
            'budget_spent': state.budget_spent,
            'remaining_budget': state.remaining_budget,
            'days_elapsed': state.days_elapsed,
            'days_remaining': state.days_remaining,
            'active_risks': state.active_risks,
            'fm_events_occurred': state.fm_events_occurred,
            'performance_score': state.performance_score,
            'health_status': state.health_status
        }

    def _detect_state_changes(
        self,
        old_state: ContractState,
        new_state: ContractState
    ) -> List[str]:
        """Detect significant changes between states"""

        changes = []

        if old_state.phase != new_state.phase:
            changes.append(f"Phase changed from {old_state.phase} to {new_state.phase}")

        if abs(old_state.completion_percentage - new_state.completion_percentage) > 5:
            changes.append(
                f"Completion changed by {new_state.completion_percentage - old_state.completion_percentage:.1f}%"
            )

        if old_state.health_status != new_state.health_status:
            changes.append(f"Health status changed from {old_state.health_status} to {new_state.health_status}")

        if len(new_state.active_risks) > len(old_state.active_risks):
            changes.append(f"{len(new_state.active_risks) - len(old_state.active_risks)} new risks detected")

        return changes

    def _assess_simulation_risk(
        self,
        expected_completion: float,
        cost_overrun_pct: float,
        expected_delay: float,
        prob_fm: float
    ) -> Dict:
        """Assess overall risk from simulation"""

        risk_score = 0.0

        # Completion risk
        if expected_completion < 80:
            risk_score += 0.30
        elif expected_completion < 95:
            risk_score += 0.15

        # Cost risk
        if cost_overrun_pct > 20:
            risk_score += 0.30
        elif cost_overrun_pct > 10:
            risk_score += 0.15

        # Delay risk
        if expected_delay > 90:
            risk_score += 0.20
        elif expected_delay > 30:
            risk_score += 0.10

        # FM invocation risk
        risk_score += prob_fm * 0.20

        # Categorize
        if risk_score >= 0.70:
            category = 'CRITICAL'
            color = 'red'
        elif risk_score >= 0.50:
            category = 'HIGH'
            color = 'orange'
        elif risk_score >= 0.30:
            category = 'MEDIUM'
            color = 'yellow'
        else:
            category = 'LOW'
            color = 'green'

        return {
            'risk_score': round(risk_score, 3),
            'risk_category': category,
            'risk_color': color
        }

    def _compare_scenario_results(self, scenario_results: List[Dict]) -> Dict:
        """Compare results across scenarios"""

        comparison = {
            'best_case': None,
            'worst_case': None,
            'risk_metrics': []
        }

        best_score = float('inf')
        worst_score = float('-inf')

        for scenario in scenario_results:
            results = scenario['results']
            expected = results['expected_outcomes']

            # Calculate composite risk score
            risk_score = (
                expected['cost_overrun_pct'] +
                (100 - expected['completion_percentage']) +
                expected['delay_days'] / 365 * 100
            )

            if risk_score < best_score:
                best_score = risk_score
                comparison['best_case'] = scenario

            if risk_score > worst_score:
                worst_score = risk_score
                comparison['worst_case'] = scenario

            comparison['risk_metrics'].append({
                'scenario_id': scenario['scenario_id'],
                'risk_score': round(risk_score, 2),
                'cost_overrun_pct': expected['cost_overrun_pct'],
                'completion_pct': expected['completion_percentage'],
                'delay_days': expected['delay_days']
            })

        return comparison

    def _generate_comparison_recommendations(self, comparison: Dict) -> List[str]:
        """Generate recommendations from scenario comparison"""

        recommendations = []

        best = comparison['best_case']
        worst = comparison['worst_case']

        if best and worst:
            best_results = best['results']['expected_outcomes']
            worst_results = worst['results']['expected_outcomes']

            cost_range = worst_results['cost_overrun_pct'] - best_results['cost_overrun_pct']

            if cost_range > 30:
                recommendations.append(
                    f"Wide cost variance ({cost_range:.1f}%) across scenarios - implement scenario-specific contingencies"
                )

            if worst_results['delay_days'] > 90:
                recommendations.append(
                    f"Worst case delays exceed 90 days - establish critical path mitigation"
                )

            recommendations.append(
                f"Best scenario: {best['scenario']['type']} with {best_results['cost_overrun_pct']:.1f}% overrun"
            )
            recommendations.append(
                f"Prepare for worst scenario: {worst['scenario']['type']} with {worst_results['delay_days']:.0f} day delay"
            )

        recommendations.append("Use digital twin for continuous monitoring and early warning")
        recommendations.append("Update twin state monthly with actual performance data")

        return recommendations


# Global instance
digital_twin_engine = DigitalTwinEngine()


# Convenience functions
def create_contract_twin(contract_id: str, contract_data: Dict) -> str:
    """Create digital twin for contract"""
    return digital_twin_engine.create_twin(contract_id, contract_data)


def simulate_fm_impact(twin_id: str, fm_scenario: Dict) -> Dict:
    """Simulate FM event impact on contract twin"""
    return digital_twin_engine.simulate_fm_scenario(twin_id, fm_scenario)
