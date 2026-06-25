"""
CFO Financial Risk Metrics Engine
Converts legal risk scores into financial impact estimates for C-suite decision making
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from decimal import Decimal


class CFOFinancialRiskEngine:
    """
    Translates legal risk into financial metrics for CFO dashboards.
    Calculates Expected Loss, Value at Risk, and Portfolio Risk Exposure.
    """

    # Industry benchmarks for loss multipliers by contract type
    LOSS_MULTIPLIERS = {
        'NDA': 0.05,                    # 5% of contract value
        'MSA': 0.15,                    # 15% of contract value
        'SLA': 0.20,                    # 20% of contract value
        'Supplier Agreement': 0.25,     # 25% of contract value
        'Partnership Agreement': 0.30,  # 30% of contract value
        'Joint Venture': 0.40,          # 40% of contract value
        'default': 0.15                 # Default 15%
    }

    # Risk level to probability of materialization
    RISK_PROBABILITY = {
        'LOW': 0.05,        # 5% chance
        'MEDIUM': 0.15,     # 15% chance
        'HIGH': 0.35,       # 35% chance
        'CRITICAL': 0.60    # 60% chance
    }

    def __init__(self):
        """Initialize CFO Financial Risk Engine."""
        self.portfolio_cache = {}

    def calculate_expected_loss(
        self,
        contract_value: float,
        risk_score: float,
        contract_type: str = 'default',
        liability_level: str = 'MEDIUM'
    ) -> Dict[str, float]:
        """
        Calculate Expected Loss (EL) = Exposure × Probability × Loss Given Default

        Args:
            contract_value: Contract value in USD
            risk_score: Risk score (0-1)
            contract_type: Type of contract
            liability_level: Liability level (LOW/MEDIUM/HIGH/CRITICAL)

        Returns:
            Dict with expected loss metrics
        """
        # Exposure at Default (EAD)
        multiplier = self.LOSS_MULTIPLIERS.get(contract_type, self.LOSS_MULTIPLIERS['default'])
        exposure = contract_value * multiplier

        # Probability of Default (PD)
        probability = self._risk_score_to_probability(risk_score, liability_level)

        # Loss Given Default (LGD) - percentage of exposure lost if risk materializes
        lgd = min(0.9, risk_score * 1.2)  # Cap at 90%

        # Expected Loss
        expected_loss = exposure * probability * lgd

        return {
            'expected_loss': round(expected_loss, 2),
            'exposure_at_default': round(exposure, 2),
            'probability_of_default': round(probability, 4),
            'loss_given_default': round(lgd, 4),
            'contract_value': contract_value,
            'risk_score': risk_score,
            'severity': self._get_severity(expected_loss, contract_value)
        }

    def calculate_portfolio_var(
        self,
        contracts: List[Dict],
        confidence_level: float = 0.95
    ) -> Dict[str, float]:
        """
        Calculate Portfolio Value at Risk (VaR) at given confidence level.

        Args:
            contracts: List of contract dicts with value and risk_score
            confidence_level: Confidence level (default 95%)

        Returns:
            Dict with VaR metrics
        """
        if not contracts:
            return {'var': 0, 'expected_shortfall': 0, 'total_exposure': 0}

        # Calculate expected loss for each contract
        losses = []
        total_value = 0

        for contract in contracts:
            value = contract.get('contract_value', 0) or 0
            risk = contract.get('risk_score', 0) or 0
            contract_type = contract.get('contract_type', 'default')
            liability = contract.get('liability_level', 'MEDIUM')

            total_value += value

            el_data = self.calculate_expected_loss(value, risk, contract_type, liability)
            losses.append(el_data['expected_loss'])

        # Convert to numpy array for calculations
        losses_array = np.array(losses)

        # VaR at confidence level (e.g., 95th percentile)
        var = np.percentile(losses_array, confidence_level * 100)

        # Expected Shortfall (CVaR) - average of losses above VaR threshold
        threshold_losses = losses_array[losses_array >= var]
        expected_shortfall = np.mean(threshold_losses) if len(threshold_losses) > 0 else var

        # Total expected loss
        total_expected_loss = np.sum(losses_array)

        return {
            'var': round(float(var), 2),
            'expected_shortfall': round(float(expected_shortfall), 2),
            'total_expected_loss': round(float(total_expected_loss), 2),
            'total_exposure': round(total_value, 2),
            'confidence_level': confidence_level,
            'num_contracts': len(contracts),
            'avg_loss_per_contract': round(float(np.mean(losses_array)), 2),
            'max_single_loss': round(float(np.max(losses_array)), 2)
        }

    def calculate_risk_adjusted_contract_value(
        self,
        contract_value: float,
        risk_score: float,
        contract_type: str = 'default'
    ) -> Dict[str, float]:
        """
        Calculate risk-adjusted contract value (RACV).
        RACV = Contract Value - Expected Loss

        Args:
            contract_value: Contract value in USD
            risk_score: Risk score (0-1)
            contract_type: Type of contract

        Returns:
            Dict with RACV metrics
        """
        el_data = self.calculate_expected_loss(contract_value, risk_score, contract_type)

        racv = contract_value - el_data['expected_loss']
        discount_rate = el_data['expected_loss'] / contract_value if contract_value > 0 else 0

        return {
            'original_value': contract_value,
            'expected_loss': el_data['expected_loss'],
            'risk_adjusted_value': round(racv, 2),
            'discount_rate': round(discount_rate, 4),
            'risk_score': risk_score,
            'recommendation': self._get_racv_recommendation(discount_rate)
        }

    def calculate_cash_flow_impact(
        self,
        contract_value: float,
        risk_score: float,
        payment_terms_days: int = 30,
        force_majeure_risk: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate potential cash flow impact from contract risks.

        Args:
            contract_value: Contract value in USD
            risk_score: Risk score (0-1)
            payment_terms_days: Payment terms in days
            force_majeure_risk: FM risk score (0-1)

        Returns:
            Dict with cash flow impact metrics
        """
        # Baseline expected payment
        expected_payment = contract_value

        # Probability of payment delay
        delay_prob = risk_score * 0.4  # 40% max chance of delay

        # Average delay in days (proportional to risk)
        avg_delay_days = payment_terms_days * risk_score * 2  # Can double payment terms

        # Cost of delay (time value of money at 5% annual rate)
        daily_rate = 0.05 / 365
        delay_cost = expected_payment * daily_rate * avg_delay_days * delay_prob

        # Probability of non-payment (default)
        default_prob = risk_score * 0.2  # 20% max chance of default

        # Expected loss from default
        default_loss = contract_value * default_prob * 0.7  # 70% loss given default

        # Force majeure impact
        fm_impact = contract_value * force_majeure_risk * 0.5  # 50% reduction if FM triggered

        # Total cash flow at risk
        total_cfar = delay_cost + default_loss + fm_impact

        return {
            'expected_payment': round(expected_payment, 2),
            'cash_flow_at_risk': round(total_cfar, 2),
            'delay_cost': round(delay_cost, 2),
            'default_risk_cost': round(default_loss, 2),
            'force_majeure_impact': round(fm_impact, 2),
            'probability_of_delay': round(delay_prob, 4),
            'expected_delay_days': round(avg_delay_days, 1),
            'net_expected_cash_flow': round(expected_payment - total_cfar, 2),
            'cash_flow_confidence': round((1 - (total_cfar / expected_payment)) * 100, 2) if expected_payment > 0 else 0
        }

    def generate_cfo_risk_report(
        self,
        contracts: List[Dict],
        portfolio_value: float = None
    ) -> Dict:
        """
        Generate comprehensive CFO risk report for portfolio.

        Args:
            contracts: List of contract dicts
            portfolio_value: Total portfolio value (calculated if not provided)

        Returns:
            Comprehensive risk report dict
        """
        if not contracts:
            return {'error': 'No contracts provided'}

        # Calculate portfolio metrics
        var_95 = self.calculate_portfolio_var(contracts, 0.95)
        var_99 = self.calculate_portfolio_var(contracts, 0.99)

        # Calculate total portfolio value if not provided
        if portfolio_value is None:
            portfolio_value = sum(c.get('contract_value', 0) or 0 for c in contracts)

        # Calculate total expected loss
        total_el = var_95['total_expected_loss']

        # Risk-weighted assets
        rwa = sum(
            (c.get('contract_value', 0) or 0) * (c.get('risk_score', 0) or 0)
            for c in contracts
        )

        # Top risk contributors
        top_risks = sorted(
            [
                {
                    'contract_id': c.get('id'),
                    'title': c.get('title', 'Unknown'),
                    'value': c.get('contract_value', 0),
                    'risk_score': c.get('risk_score', 0),
                    'expected_loss': self.calculate_expected_loss(
                        c.get('contract_value', 0) or 0,
                        c.get('risk_score', 0) or 0,
                        c.get('contract_type', 'default')
                    )['expected_loss']
                }
                for c in contracts
            ],
            key=lambda x: x['expected_loss'],
            reverse=True
        )[:10]

        # Risk concentration by contract type
        type_concentration = {}
        for c in contracts:
            ctype = c.get('contract_type', 'Unknown')
            value = c.get('contract_value', 0) or 0
            type_concentration[ctype] = type_concentration.get(ctype, 0) + value

        return {
            'portfolio_summary': {
                'total_contracts': len(contracts),
                'total_portfolio_value': round(portfolio_value, 2),
                'total_expected_loss': round(total_el, 2),
                'risk_adjusted_portfolio_value': round(portfolio_value - total_el, 2),
                'portfolio_discount_rate': round(total_el / portfolio_value * 100, 2) if portfolio_value > 0 else 0
            },
            'value_at_risk': {
                'var_95': var_95,
                'var_99': var_99
            },
            'risk_metrics': {
                'risk_weighted_assets': round(rwa, 2),
                'average_risk_score': round(np.mean([c.get('risk_score', 0) for c in contracts]), 4),
                'high_risk_contracts': len([c for c in contracts if c.get('risk_level') in ('HIGH', 'CRITICAL') or (c.get('risk_score', 0) or 0) >= 0.4]),
                'high_risk_exposure': round(sum(
                    c.get('contract_value', 0) or 0
                    for c in contracts
                    if c.get('risk_level') in ('HIGH', 'CRITICAL') or (c.get('risk_score', 0) or 0) >= 0.4
                ), 2)
            },
            'top_risk_contributors': top_risks,
            'concentration_by_type': type_concentration,
            'recommendations': self._generate_recommendations(var_95, portfolio_value, len(contracts))
        }

    # Helper methods

    def _risk_score_to_probability(self, risk_score: float, liability_level: str) -> float:
        """Convert risk score and liability level to probability of materialization."""
        base_prob = self.RISK_PROBABILITY.get(liability_level, 0.15)
        # Adjust by risk score
        adjusted_prob = base_prob * (1 + risk_score)
        return min(0.95, adjusted_prob)  # Cap at 95%

    def _get_severity(self, expected_loss: float, contract_value: float) -> str:
        """Determine severity level based on expected loss ratio."""
        if contract_value == 0:
            return 'UNKNOWN'
        ratio = expected_loss / contract_value
        if ratio >= 0.20:
            return 'CRITICAL'
        elif ratio >= 0.10:
            return 'HIGH'
        elif ratio >= 0.05:
            return 'MEDIUM'
        return 'LOW'

    def _get_racv_recommendation(self, discount_rate: float) -> str:
        """Get recommendation based on discount rate."""
        if discount_rate >= 0.20:
            return 'REJECT - Excessive risk relative to value'
        elif discount_rate >= 0.10:
            return 'RENEGOTIATE - Seek better terms to reduce risk'
        elif discount_rate >= 0.05:
            return 'PROCEED WITH CAUTION - Monitor closely'
        return 'APPROVE - Acceptable risk-return profile'

    def _generate_recommendations(self, var_data: Dict, portfolio_value: float, num_contracts: int) -> List[str]:
        """Generate CFO recommendations based on portfolio metrics."""
        recommendations = []

        # VaR recommendations
        var_ratio = var_data['var'] / portfolio_value if portfolio_value > 0 else 0
        if var_ratio > 0.05:
            recommendations.append(f"High VaR detected ({var_ratio*100:.1f}% of portfolio) - Consider hedging strategies")

        # Expected loss recommendations
        el_ratio = var_data['total_expected_loss'] / portfolio_value if portfolio_value > 0 else 0
        if el_ratio > 0.03:
            recommendations.append(f"Expected losses exceed 3% of portfolio ({el_ratio*100:.1f}%) - Review high-risk contracts")

        # Concentration recommendations
        avg_value = portfolio_value / num_contracts if num_contracts > 0 else 0
        if var_data['max_single_loss'] > avg_value * 10:
            recommendations.append("Single contract concentration risk - Diversify portfolio")

        if not recommendations:
            recommendations.append("Portfolio risk levels are within acceptable ranges")

        return recommendations


# Singleton instance
_cfo_engine = None

def get_cfo_engine() -> CFOFinancialRiskEngine:
    """Get or create CFO engine singleton."""
    global _cfo_engine
    if _cfo_engine is None:
        _cfo_engine = CFOFinancialRiskEngine()
    return _cfo_engine
