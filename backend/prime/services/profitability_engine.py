"""
PrimeContractAI - Profitability Engine
Calculate contract profitability metrics and risk-adjusted margins
"""

from typing import Dict
import hashlib


class ProfitabilityEngine:
    """
    Profitability calculation engine for contract analysis
    Calculates gross margin, risk-adjusted margin, and profitability score
    """

    def calculate_profitability(
        self,
        contract_value: float,
        estimated_cost: float,
        risk_score: float,
        contract_id: str = None
    ) -> Dict:
        """
        Calculate comprehensive profitability metrics for a contract

        Args:
            contract_value: Total contract value in dollars
            estimated_cost: Estimated cost to deliver
            risk_score: Risk score (0-100)
            contract_id: Optional contract ID for variance

        Returns:
            Dictionary with profitability metrics
        """
        # Add contract-specific variance if contract_id provided
        if contract_id:
            contract_hash = int(hashlib.md5(str(contract_id).encode()).hexdigest()[:8], 16)
            variance = (contract_hash % 100) / 1000.0  # 0.000 to 0.099

            # Adjust cost with variance (±5%)
            cost_variance = 1.0 - 0.05 + (variance * 0.1)  # 0.95 to 1.05
            estimated_cost = estimated_cost * cost_variance

        # Basic margin calculations
        gross_profit = contract_value - estimated_cost
        gross_margin_percent = (gross_profit / contract_value * 100) if contract_value > 0 else 0

        # Risk adjustment factor (higher risk = more reserve needed)
        risk_adjustment = risk_score / 100.0  # Convert to 0-1
        risk_reserve_percent = risk_adjustment * 20  # Up to 20% reserve

        # Risk-adjusted metrics
        risk_reserve = contract_value * (risk_reserve_percent / 100)
        risk_adjusted_profit = gross_profit - risk_reserve
        risk_adjusted_margin = (risk_adjusted_profit / contract_value * 100) if contract_value > 0 else 0

        # Profitability score (0-100, higher is better)
        profitability_score = self._calculate_profitability_score(
            gross_margin_percent,
            risk_score,
            contract_value
        )

        # Break-even analysis
        break_even_value = estimated_cost / (1 - (risk_reserve_percent / 100)) if risk_reserve_percent < 100 else 0

        return {
            "contract_value": round(contract_value, 2),
            "estimated_cost": round(estimated_cost, 2),
            "gross_profit": round(gross_profit, 2),
            "gross_margin_percent": round(gross_margin_percent, 2),
            "risk_score": round(risk_score, 2),
            "risk_reserve": round(risk_reserve, 2),
            "risk_reserve_percent": round(risk_reserve_percent, 2),
            "risk_adjusted_profit": round(risk_adjusted_profit, 2),
            "risk_adjusted_margin": round(risk_adjusted_margin, 2),
            "profitability_score": round(profitability_score, 2),
            "break_even_value": round(break_even_value, 2),
            "category": self._get_profitability_category(profitability_score)
        }

    def calculate_portfolio_profitability(
        self,
        contracts: list
    ) -> Dict:
        """
        Calculate aggregate profitability metrics for a portfolio

        Args:
            contracts: List of contracts with profitability data

        Returns:
            Portfolio-level profitability metrics
        """
        if not contracts:
            return {
                "total_value": 0,
                "total_cost": 0,
                "total_profit": 0,
                "average_margin": 0,
                "average_risk_adjusted_margin": 0,
                "average_profitability_score": 0,
                "high_profit_contracts": 0,
                "low_profit_contracts": 0
            }

        total_value = sum(c.get("contract_value", 0) for c in contracts)
        total_cost = sum(c.get("estimated_cost", 0) for c in contracts)
        total_profit = total_value - total_cost

        margins = [c.get("gross_margin_percent", 0) for c in contracts if c.get("gross_margin_percent")]
        risk_adjusted_margins = [c.get("risk_adjusted_margin", 0) for c in contracts if c.get("risk_adjusted_margin")]
        profitability_scores = [c.get("profitability_score", 0) for c in contracts if c.get("profitability_score")]

        avg_margin = sum(margins) / len(margins) if margins else 0
        avg_risk_adjusted_margin = sum(risk_adjusted_margins) / len(risk_adjusted_margins) if risk_adjusted_margins else 0
        avg_profitability_score = sum(profitability_scores) / len(profitability_scores) if profitability_scores else 0

        high_profit = len([s for s in profitability_scores if s >= 70])
        low_profit = len([s for s in profitability_scores if s < 50])

        return {
            "total_value": round(total_value, 2),
            "total_cost": round(total_cost, 2),
            "total_profit": round(total_profit, 2),
            "average_margin": round(avg_margin, 2),
            "average_risk_adjusted_margin": round(avg_risk_adjusted_margin, 2),
            "average_profitability_score": round(avg_profitability_score, 2),
            "high_profit_contracts": high_profit,
            "low_profit_contracts": low_profit,
            "total_contracts": len(contracts)
        }

    def _calculate_profitability_score(
        self,
        gross_margin: float,
        risk_score: float,
        contract_value: float
    ) -> float:
        """
        Calculate composite profitability score (0-100)

        Weights:
        - Gross margin: 50%
        - Risk (inverse): 30%
        - Contract size: 20%
        """
        # Margin score (0-100, normalized from 0-30% margin)
        margin_score = min(gross_margin / 30 * 100, 100) * 0.5

        # Risk score (inverse - lower risk is better)
        risk_score_component = (100 - risk_score) * 0.3

        # Size score (logarithmic scaling, larger contracts score higher)
        import math
        size_score = min(math.log10(max(contract_value, 1)) / 7 * 100, 100) * 0.2  # Normalized to $10M

        profitability_score = margin_score + risk_score_component + size_score

        return min(max(profitability_score, 0), 100)  # Clamp to 0-100

    def _get_profitability_category(self, score: float) -> str:
        """Categorize profitability score"""
        if score >= 80:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 50:
            return "fair"
        elif score >= 30:
            return "poor"
        else:
            return "critical"
