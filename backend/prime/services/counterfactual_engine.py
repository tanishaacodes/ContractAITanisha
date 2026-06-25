"""
PrimeContractAI - Counterfactual AI Engine
Generate alternative contract scenarios and optimize terms
"""

from typing import Dict, List
import numpy as np


class CounterfactualEngine:
    """
    AI-powered counterfactual scenario generator
    Simulates "what-if" contract modifications and their impact
    """

    def __init__(self):
        self.modification_templates = {
            "cap_liability": {
                "description": "Cap liability at multiple of annual fees",
                "risk_reduction_factor": 0.28,
                "margin_improvement_factor": 0.042,
                "feasibility": "high",
                "impact": "high"
            },
            "add_force_majeure": {
                "description": "Add Force Majeure clause",
                "risk_reduction_factor": 0.15,
                "margin_improvement_factor": 0.021,
                "feasibility": "high",
                "impact": "medium"
            },
            "reduce_penalty": {
                "description": "Reduce penalty from 10% to 5%",
                "risk_reduction_factor": 0.22,
                "margin_improvement_factor": 0.038,
                "feasibility": "medium",
                "impact": "high"
            },
            "limit_indemnity": {
                "description": "Limit indemnity scope to direct damages",
                "risk_reduction_factor": 0.20,
                "margin_improvement_factor": 0.035,
                "feasibility": "medium",
                "impact": "high"
            },
            "extend_notice_period": {
                "description": "Extend termination notice to 90 days",
                "risk_reduction_factor": 0.12,
                "margin_improvement_factor": 0.015,
                "feasibility": "high",
                "impact": "medium"
            }
        }

    def generate_counterfactual(
        self,
        contract: Dict,
        modification_type: str
    ) -> Dict:
        """
        Generate counterfactual scenario for specific modification

        Args:
            contract: Original contract data
            modification_type: Type of modification to simulate

        Returns:
            Counterfactual scenario with projected impact
        """
        template = self.modification_templates.get(modification_type)

        if not template:
            raise ValueError(f"Unknown modification type: {modification_type}")

        current_risk = contract.get("risk_score", 50)
        current_profit = contract.get("profit_margin", 0.15)

        # Add contract-specific variance to modification factors
        contract_id = contract.get("contract_id", "default")
        import hashlib
        contract_hash = int(hashlib.md5(str(contract_id).encode()).hexdigest()[:8], 16)
        variance = (contract_hash % 100) / 100.0  # 0.0 to 0.99

        # Adjust risk reduction factor (±15% variance)
        risk_factor = template["risk_reduction_factor"]
        risk_factor_adjusted = risk_factor * (0.85 + variance * 0.3)  # 85% to 115% of base

        # Adjust margin improvement factor (±20% variance)
        margin_factor = template["margin_improvement_factor"]
        margin_factor_adjusted = margin_factor * (0.80 + variance * 0.4)  # 80% to 120% of base

        # Calculate new risk and profit
        risk_reduction = current_risk * risk_factor_adjusted
        new_risk = max(0, current_risk - risk_reduction)

        margin_improvement = margin_factor_adjusted
        new_profit = current_profit + margin_improvement

        return {
            "modification_type": modification_type,
            "description": template["description"],
            "current_state": {
                "risk_score": current_risk,
                "profit_margin": current_profit * 100,
                "contract_value": contract.get("value", 0)
            },
            "projected_state": {
                "risk_score": round(new_risk, 2),
                "profit_margin": round(new_profit * 100, 2),
                "contract_value": contract.get("value", 0)
            },
            "impact": {
                "risk_reduction": round(risk_reduction, 2),
                "risk_reduction_percent": round(risk_reduction / current_risk * 100, 2),
                "margin_improvement": round(margin_improvement * 100, 2),
                "margin_improvement_percent": round(margin_improvement / current_profit * 100, 2) if current_profit > 0 else 0
            },
            "feasibility": template["feasibility"],
            "impact_level": template["impact"],
            "recommendation_priority": self._calculate_priority(
                risk_reduction / current_risk,
                margin_improvement,
                template["feasibility"],
                template["impact"]
            )
        }

    def generate_optimal_suggestions(
        self,
        contract: Dict,
        max_suggestions: int = 5
    ) -> List[Dict]:
        """
        Generate top counterfactual suggestions ranked by impact and feasibility

        Args:
            contract: Contract data
            max_suggestions: Maximum number of suggestions to return

        Returns:
            Ranked list of counterfactual suggestions
        """
        suggestions = []

        for mod_type in self.modification_templates.keys():
            try:
                counterfactual = self.generate_counterfactual(contract, mod_type)
                suggestions.append(counterfactual)
            except Exception as e:
                print(f"Error generating {mod_type}: {e}")
                continue

        # Rank by priority score
        suggestions.sort(key=lambda x: x["recommendation_priority"], reverse=True)

        return suggestions[:max_suggestions]

    def simulate_combined_modifications(
        self,
        contract: Dict,
        modification_types: List[str]
    ) -> Dict:
        """
        Simulate multiple modifications applied together
        Note: Assumes independent effects (actual synergies may vary)

        Args:
            contract: Contract data
            modification_types: List of modifications to combine

        Returns:
            Combined counterfactual scenario
        """
        current_risk = contract.get("risk_score", 50)
        current_profit = contract.get("profit_margin", 0.15)

        cumulative_risk_reduction = 0
        cumulative_margin_improvement = 0
        modifications = []

        for mod_type in modification_types:
            template = self.modification_templates.get(mod_type)
            if not template:
                continue

            # Apply diminishing returns for combined modifications
            diminish_factor = 1.0 - (len(modifications) * 0.1)  # 10% reduction per additional mod
            diminish_factor = max(diminish_factor, 0.5)  # Floor at 50%

            risk_reduction = current_risk * template["risk_reduction_factor"] * diminish_factor
            margin_improvement = template["margin_improvement_factor"] * diminish_factor

            cumulative_risk_reduction += risk_reduction
            cumulative_margin_improvement += margin_improvement

            modifications.append({
                "type": mod_type,
                "description": template["description"],
                "risk_reduction": risk_reduction,
                "margin_improvement": margin_improvement
            })

        new_risk = max(0, current_risk - cumulative_risk_reduction)
        new_profit = current_profit + cumulative_margin_improvement

        return {
            "modification_count": len(modifications),
            "modifications": modifications,
            "current_state": {
                "risk_score": current_risk,
                "profit_margin": current_profit * 100
            },
            "projected_state": {
                "risk_score": round(new_risk, 2),
                "profit_margin": round(new_profit * 100, 2)
            },
            "cumulative_impact": {
                "total_risk_reduction": round(cumulative_risk_reduction, 2),
                "total_margin_improvement": round(cumulative_margin_improvement * 100, 2),
                "risk_reduction_percent": round(cumulative_risk_reduction / current_risk * 100, 2),
                "margin_improvement_percent": round(cumulative_margin_improvement / current_profit * 100, 2) if current_profit > 0 else 0
            }
        }

    def _calculate_priority(
        self,
        risk_reduction_ratio: float,
        margin_improvement: float,
        feasibility: str,
        impact: str
    ) -> float:
        """
        Calculate recommendation priority score (0-100)

        Higher scores = higher priority recommendations
        """
        # Base score from quantitative impact
        risk_score = risk_reduction_ratio * 40  # Up to 40 points
        margin_score = margin_improvement * 200  # Up to 20 points (assuming max 0.1 margin improvement)

        # Feasibility multiplier
        feasibility_map = {"high": 1.5, "medium": 1.0, "low": 0.6}
        feasibility_multiplier = feasibility_map.get(feasibility, 1.0)

        # Impact bonus
        impact_map = {"high": 20, "medium": 10, "low": 5}
        impact_bonus = impact_map.get(impact, 0)

        priority = (risk_score + margin_score) * feasibility_multiplier + impact_bonus

        return min(priority, 100)  # Cap at 100
