"""
War Loss Prediction Engine
Predicts financial losses from war events considering multiple cost factors
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class WarLossComponents:
    """Components of war-related losses"""
    idle_labor_cost: float
    equipment_rental_cost: float
    demobilization_cost: float
    remobilization_cost: float
    commodity_price_increase: float
    currency_volatility_loss: float
    insurance_premium_increase: float
    supply_chain_rerouting: float
    project_delay_penalties: float
    contract_termination_risk: float


class WarLossPredictionEngine:
    """Engine for predicting financial losses from war events"""

    def __init__(self):
        self.loss_models = {}

    def predict_war_losses(
        self,
        contract_value: float,
        war_event: Dict,
        project_data: Dict,
        duration_estimate_days: int = 180
    ) -> Dict:
        """
        Predict total financial losses from war event

        Args:
            contract_value: Total contract value in USD
            war_event: War event details (type, location, severity)
            project_data: Project details (location, phase, workforce, etc.)
            duration_estimate_days: Expected war duration

        Returns:
            Comprehensive loss prediction with breakdown
        """
        # Extract project parameters
        workforce_size = project_data.get("workforce_size", 500)
        equipment_count = project_data.get("equipment_count", 50)
        daily_burn_rate = project_data.get("daily_burn_rate", contract_value / 730)  # 2 years default
        project_phase = project_data.get("phase", "execution")  # planning, execution, completion
        location_risk = project_data.get("location_risk", 0.5)

        # Calculate individual loss components
        loss_components = self._calculate_loss_components(
            contract_value=contract_value,
            workforce_size=workforce_size,
            equipment_count=equipment_count,
            daily_burn_rate=daily_burn_rate,
            duration_days=duration_estimate_days,
            war_severity=war_event.get("severity", 0.7),
            location_risk=location_risk
        )

        # Run Monte Carlo simulation for loss distribution
        loss_distribution = self._monte_carlo_loss_simulation(
            loss_components,
            duration_estimate_days,
            n_simulations=10000
        )

        # Calculate expected loss and percentiles
        expected_loss = np.mean(loss_distribution)
        p50_loss = np.percentile(loss_distribution, 50)
        p95_loss = np.percentile(loss_distribution, 95)
        p99_loss = np.percentile(loss_distribution, 99)
        worst_case = np.max(loss_distribution)

        # Calculate loss as percentage of contract value
        loss_percentage = (expected_loss / contract_value) * 100

        # Determine loss severity category
        if loss_percentage > 50:
            severity_category = "catastrophic"
        elif loss_percentage > 25:
            severity_category = "major"
        elif loss_percentage > 10:
            severity_category = "significant"
        else:
            severity_category = "moderate"

        return {
            "contract_value_usd": contract_value,
            "war_event": war_event.get("type", "war"),
            "duration_estimate_days": duration_estimate_days,
            "expected_loss_usd": expected_loss,
            "p50_loss_usd": p50_loss,
            "p95_loss_usd": p95_loss,
            "p99_loss_usd": p99_loss,
            "worst_case_loss_usd": worst_case,
            "loss_percentage": loss_percentage,
            "severity_category": severity_category,
            "loss_breakdown": {
                "idle_labor_cost": loss_components.idle_labor_cost,
                "equipment_rental_cost": loss_components.equipment_rental_cost,
                "demobilization_cost": loss_components.demobilization_cost,
                "remobilization_cost": loss_components.remobilization_cost,
                "commodity_price_increase": loss_components.commodity_price_increase,
                "currency_volatility_loss": loss_components.currency_volatility_loss,
                "insurance_premium_increase": loss_components.insurance_premium_increase,
                "supply_chain_rerouting": loss_components.supply_chain_rerouting,
                "project_delay_penalties": loss_components.project_delay_penalties,
                "contract_termination_risk": loss_components.contract_termination_risk
            },
            "mitigation_potential_usd": expected_loss * 0.30,  # Can mitigate up to 30%
            "insurance_recovery_potential_usd": expected_loss * 0.50,  # Insurance may cover 50%
            "net_loss_after_mitigation_usd": expected_loss * 0.50  # Net after mitigation + insurance
        }

    def _calculate_loss_components(
        self,
        contract_value: float,
        workforce_size: int,
        equipment_count: int,
        daily_burn_rate: float,
        duration_days: int,
        war_severity: float,
        location_risk: float
    ) -> WarLossComponents:
        """Calculate individual loss components"""

        # 1. Idle Labor Costs
        # Average labor cost per worker per day * days * retention rate
        avg_daily_labor_cost = 150  # USD per worker per day
        retention_rate = 0.70  # Keep 70% of workforce on standby
        idle_labor = workforce_size * avg_daily_labor_cost * duration_days * retention_rate

        # 2. Equipment Rental/Idle Costs
        # Equipment rental continues even when idle
        avg_equipment_cost_daily = 1000  # USD per equipment per day
        equipment_cost = equipment_count * avg_equipment_cost_daily * duration_days * 0.80

        # 3. Demobilization Costs
        # Cost to demobilize workforce and equipment
        demobilization = (workforce_size * 500) + (equipment_count * 5000)

        # 4. Remobilization Costs
        # Cost to remobilize when war ends
        remobilization = demobilization * 1.2  # 20% more expensive to remobilize

        # 5. Commodity Price Increases
        # War drives up steel, fuel, materials costs
        commodity_exposure = contract_value * 0.30  # 30% of contract is materials
        price_increase_factor = war_severity * 0.40  # Up to 40% increase
        commodity_increase = commodity_exposure * price_increase_factor

        # 6. Currency Volatility Losses
        # Currency fluctuations during war
        currency_exposure = contract_value * 0.60  # 60% in foreign currency
        volatility_loss_factor = war_severity * 0.15  # Up to 15% loss
        currency_loss = currency_exposure * volatility_loss_factor

        # 7. Insurance Premium Increases
        # War risk insurance becomes more expensive or unavailable
        current_insurance_cost = contract_value * 0.02  # 2% of contract value
        premium_increase_factor = war_severity * 5.0  # Can increase 5x
        insurance_increase = current_insurance_cost * premium_increase_factor * (duration_days / 365)

        # 8. Supply Chain Rerouting Costs
        # Cost to find alternate suppliers/routes
        supply_chain_value = contract_value * 0.40  # 40% dependent on supply chains
        rerouting_cost_factor = war_severity * 0.25  # Up to 25% cost increase
        rerouting_cost = supply_chain_value * rerouting_cost_factor

        # 9. Project Delay Penalties
        # Liquidated damages and penalties
        daily_penalty_rate = daily_burn_rate * 0.10  # 10% of daily burn as penalty
        delay_days = min(duration_days, 365)  # Cap at 1 year
        delay_penalties = daily_penalty_rate * delay_days * 0.70  # 70% chance of penalties

        # 10. Contract Termination Risk
        # Risk of contract termination if war continues too long
        if duration_days > 365:
            termination_probability = 0.50
        elif duration_days > 180:
            termination_probability = 0.25
        else:
            termination_probability = 0.10

        remaining_contract_value = contract_value * 0.60  # 40% completed
        termination_loss = remaining_contract_value * termination_probability * 0.30  # 30% termination penalty

        return WarLossComponents(
            idle_labor_cost=idle_labor,
            equipment_rental_cost=equipment_cost,
            demobilization_cost=demobilization,
            remobilization_cost=remobilization,
            commodity_price_increase=commodity_increase,
            currency_volatility_loss=currency_loss,
            insurance_premium_increase=insurance_increase,
            supply_chain_rerouting=rerouting_cost,
            project_delay_penalties=delay_penalties,
            contract_termination_risk=termination_loss
        )

    def _monte_carlo_loss_simulation(
        self,
        loss_components: WarLossComponents,
        duration_days: int,
        n_simulations: int = 10000
    ) -> np.ndarray:
        """
        Run Monte Carlo simulation to model loss distribution

        Returns:
            Array of simulated total losses
        """
        np.random.seed(42)  # For reproducibility

        losses = []

        for _ in range(n_simulations):
            # Add uncertainty to each component
            simulated_loss = 0

            # Idle labor (Normal distribution, ±20%)
            simulated_loss += np.random.normal(
                loss_components.idle_labor_cost,
                loss_components.idle_labor_cost * 0.20
            )

            # Equipment costs (Normal distribution, ±15%)
            simulated_loss += np.random.normal(
                loss_components.equipment_rental_cost,
                loss_components.equipment_rental_cost * 0.15
            )

            # Mobilization costs (Uniform distribution)
            demob_remob = loss_components.demobilization_cost + loss_components.remobilization_cost
            simulated_loss += np.random.uniform(
                demob_remob * 0.80,
                demob_remob * 1.20
            )

            # Commodity prices (Log-normal distribution - can spike dramatically)
            simulated_loss += np.random.lognormal(
                np.log(loss_components.commodity_price_increase),
                0.30
            )

            # Currency losses (Normal distribution, ±30%)
            simulated_loss += np.random.normal(
                loss_components.currency_volatility_loss,
                loss_components.currency_volatility_loss * 0.30
            )

            # Insurance (Normal distribution, ±25%)
            simulated_loss += np.random.normal(
                loss_components.insurance_premium_increase,
                loss_components.insurance_premium_increase * 0.25
            )

            # Supply chain (Exponential distribution - sudden shocks possible)
            simulated_loss += np.random.exponential(
                loss_components.supply_chain_rerouting
            )

            # Delay penalties (Uniform distribution)
            simulated_loss += np.random.uniform(
                loss_components.project_delay_penalties * 0.50,
                loss_components.project_delay_penalties * 1.50
            )

            # Termination risk (Binary outcome with probability)
            termination_draw = np.random.random()
            termination_threshold = 0.20 if duration_days > 180 else 0.10
            if termination_draw < termination_threshold:
                simulated_loss += loss_components.contract_termination_risk

            losses.append(max(0, simulated_loss))  # Ensure non-negative

        return np.array(losses)

    def calculate_war_insurance_premium(
        self,
        contract_value: float,
        location_risk: float,
        war_probability: float,
        coverage_percentage: float = 80.0
    ) -> Dict:
        """
        Calculate appropriate war risk insurance premium

        Args:
            contract_value: Contract value
            location_risk: Risk score for location (0-1)
            war_probability: Probability of war occurring (0-1)
            coverage_percentage: Percentage of contract value to insure

        Returns:
            Insurance premium calculation
        """
        # Base premium rate
        base_rate = 0.015  # 1.5% for low-risk areas

        # Adjust for location risk
        location_multiplier = 1 + (location_risk * 4)  # Up to 5x for high-risk

        # Adjust for war probability
        probability_multiplier = 1 + (war_probability * 6)  # Up to 7x if war is likely

        # Calculate final premium rate
        final_rate = base_rate * location_multiplier * probability_multiplier

        # Calculate premium
        insured_value = contract_value * (coverage_percentage / 100)
        annual_premium = insured_value * final_rate

        return {
            "insured_value_usd": insured_value,
            "coverage_percentage": coverage_percentage,
            "annual_premium_usd": annual_premium,
            "premium_rate_pct": final_rate * 100,
            "base_rate_pct": base_rate * 100,
            "location_multiplier": location_multiplier,
            "war_probability_multiplier": probability_multiplier,
            "policy_terms": {
                "deductible_pct": 5.0,
                "waiting_period_days": 30,
                "max_claim_pct": 90.0,
                "exclusions": [
                    "Nuclear war",
                    "Chemical/biological weapons",
                    "Deliberate acts by insured"
                ]
            }
        }

    def estimate_recovery_time(
        self,
        war_duration_days: int,
        project_phase: str,
        damage_severity: str
    ) -> Dict:
        """
        Estimate time to recover and resume project after war

        Args:
            war_duration_days: Duration of war/conflict
            project_phase: Current project phase
            damage_severity: "none", "minor", "moderate", "severe", "destroyed"

        Returns:
            Recovery time estimate
        """
        # Base recovery times by damage severity (days)
        recovery_times = {
            "none": 30,  # Just remobilization
            "minor": 60,  # Minor repairs
            "moderate": 120,  # Significant repairs
            "severe": 240,  # Major reconstruction
            "destroyed": 365  # Complete rebuild
        }

        base_recovery = recovery_times.get(damage_severity, 90)

        # Adjust for project phase
        phase_factors = {
            "planning": 0.5,  # Less to recover
            "mobilization": 0.7,
            "execution": 1.0,
            "completion": 1.2  # More complex to restart near completion
        }

        phase_factor = phase_factors.get(project_phase, 1.0)

        # Adjust for war duration (longer wars = longer recovery)
        duration_factor = 1 + (war_duration_days / 365) * 0.30  # +30% per year

        total_recovery_days = int(base_recovery * phase_factor * duration_factor)

        return {
            "base_recovery_days": base_recovery,
            "phase_adjustment_factor": phase_factor,
            "duration_adjustment_factor": duration_factor,
            "total_recovery_days": total_recovery_days,
            "recovery_cost_usd": total_recovery_days * 50000,  # $50k per day
            "recovery_phases": [
                {"phase": "Security assessment", "duration_days": int(total_recovery_days * 0.1)},
                {"phase": "Damage assessment", "duration_days": int(total_recovery_days * 0.1)},
                {"phase": "Repairs/reconstruction", "duration_days": int(total_recovery_days * 0.50)},
                {"phase": "Remobilization", "duration_days": int(total_recovery_days * 0.20)},
                {"phase": "Resume operations", "duration_days": int(total_recovery_days * 0.10)}
            ]
        }


# Global instance
war_loss_engine = WarLossPredictionEngine()


# Convenience function
def predict_war_financial_impact(contract_data: Dict, war_scenario: Dict) -> Dict:
    """Convenience function to predict war financial impact"""
    contract_value = contract_data.get("value", 100_000_000)
    duration_days = war_scenario.get("duration_days", 180)

    project_data = {
        "workforce_size": contract_data.get("workforce_size", 500),
        "equipment_count": contract_data.get("equipment_count", 50),
        "phase": contract_data.get("phase", "execution"),
        "location_risk": war_scenario.get("location_risk", 0.7)
    }

    return war_loss_engine.predict_war_losses(
        contract_value,
        war_scenario,
        project_data,
        duration_days
    )
