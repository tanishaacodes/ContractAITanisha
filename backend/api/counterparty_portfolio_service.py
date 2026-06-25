"""
Portfolio-Level Counterparty Risk Heatmap Service
Aggregates counterparty-level risk metrics for CFO/CRO dashboards.
"""
from django.db.models import Sum, Avg, Count, Q, F
from django.db.models.functions import Cast
from django.db.models import DecimalField, FloatField
from negotiation.models import Counterparty, NegotiationHistory
from core.models import Contract
from typing import Dict, List
import logging
import re

logger = logging.getLogger(__name__)


class CounterpartyPortfolioService:
    """
    Portfolio-wide counterparty risk analysis.

    This provides CFO/CRO-level insights:
    - Counterparty reliability scoring (behavior-based)
    - Financial exposure aggregation
    - Failure probability (Bayesian)
    """

    def parse_contract_value(self, value_str: str) -> float:
        """
        Parse contract value from string format.
        Examples: "INR 22 Cr", "₹10.5 L", "$5M", "AED 3,300,000.00"
        Handles Indian (Cr/Crore, L/Lakh) and Western (M/Million, K/Thousand) formats
        """
        if not value_str:
            return 0.0

        try:
            # Convert to uppercase for case-insensitive matching
            value_upper = value_str.upper()

            # Extract numeric value (including decimals)
            numeric_match = re.search(r'([\d,]+\.?\d*)', value_str)
            if not numeric_match:
                return 0.0

            # Remove commas and convert to float
            base_value = float(numeric_match.group(1).replace(',', ''))

            # Detect multiplier suffix
            multiplier = 1.0

            # Indian formats (Crore = 10 million, Lakh = 100 thousand)
            if 'CR' in value_upper or 'CRORE' in value_upper:
                multiplier = 10000000  # 1 Crore = 10^7
            elif 'L' in value_upper or 'LAKH' in value_upper or 'LAC' in value_upper:
                multiplier = 100000  # 1 Lakh = 10^5
            # Western formats
            elif 'B' in value_upper or 'BILLION' in value_upper:
                multiplier = 1000000000  # 1 Billion = 10^9
            elif 'M' in value_upper or 'MILLION' in value_upper:
                multiplier = 1000000  # 1 Million = 10^6
            elif 'K' in value_upper or 'THOUSAND' in value_upper:
                multiplier = 1000  # 1 Thousand = 10^3

            return base_value * multiplier

        except (ValueError, TypeError):
            return 0.0

    def calculate_counterparty_reliability(self, counterparty: Counterparty) -> float:
        """
        Calculate reliability score from negotiation history.

        Reliability = weighted_average([
            acceptance_rate (40%),
            1 - stall_rate (30%),
            1 / avg_redline_rounds (20%),
            1 - avg_deviation (10%)
        ])

        Returns: 0-1 score (0=unreliable, 1=highly reliable)
        """
        history = NegotiationHistory.objects.filter(counterparty=counterparty)

        if history.count() == 0:
            return 0.5  # Neutral default for no history

        total = history.count()

        # Acceptance rate
        acceptance_rate = history.filter(accepted=True).count() / total

        # Stall rate
        stall_rate = history.filter(stalled=True).count() / total

        # Average redline rounds (normalize to 0-1, inverse)
        avg_redlines = history.aggregate(Avg('redline_rounds'))['redline_rounds__avg'] or 1
        redline_score = 1 / (1 + avg_redlines)  # More redlines = lower score

        # Average deviation (lower is better)
        avg_deviation = history.aggregate(Avg('deviation_score'))['deviation_score__avg'] or 0
        deviation_score = 1 - avg_deviation

        # Weighted calculation
        reliability = (
            acceptance_rate * 0.40 +
            (1 - stall_rate) * 0.30 +
            redline_score * 0.20 +
            deviation_score * 0.10
        )

        return round(reliability, 3)

    def calculate_financial_exposure(self, counterparty: Counterparty) -> float:
        """
        Calculate total financial exposure for this counterparty.

        Exposure = Σ(contract_value + total_liability + silent_risk_exposure)

        Returns: Total exposure in base currency
        """
        contracts = Contract.objects.filter(counterparty=counterparty)

        if contracts.count() == 0:
            return 0.0

        total_exposure = 0.0

        for contract in contracts:
            # Parse contract value
            contract_value = self.parse_contract_value(contract.contract_value or "")

            # Add total_liability
            total_liability = float(contract.total_liability or 0)

            # Add silent risk exposures
            silent_risk_exposure = contract.silent_risks.aggregate(
                total=Sum('financial_exposure')
            )['total'] or 0

            total_exposure += contract_value + total_liability + float(silent_risk_exposure)

        return round(total_exposure, 2)

    def calculate_failure_probability(self, counterparty: Counterparty, reliability: float) -> float:
        """
        Calculate Bayesian failure probability.

        P(failure) = (1 - reliability) * avg_contract_risk_score

        This combines:
        - Behavioral reliability (from negotiations)
        - Contract-level risk (from clause analysis)

        Returns: 0-1 probability
        """
        contracts = Contract.objects.filter(counterparty=counterparty)

        if contracts.count() == 0:
            return 1 - reliability  # Use pure behavioral score

        # Get average risk score across all clauses in all contracts
        from core.models import Clause
        avg_risk = Clause.objects.filter(
            contract__in=contracts,
            risk_score__isnull=False
        ).aggregate(Avg('risk_score'))['risk_score__avg']

        if avg_risk is None:
            return 1 - reliability

        # Combine behavioral and contract risk
        # Higher avg_risk + lower reliability = higher failure probability
        failure_prob = (1 - reliability) * 0.6 + avg_risk * 0.4

        return round(min(failure_prob, 1.0), 3)

    def get_portfolio_heatmap(self, user_id: str) -> Dict:
        """
        Generate portfolio-level contract risk heatmap.

        Returns contract-level data points (each bubble = one contract).
        """
        # Get all contracts with counterparties for this user
        contracts = Contract.objects.filter(
            user_id=user_id,
            counterparty__isnull=False
        ).select_related('counterparty')

        heatmap_data = []
        total_exposure = 0.0
        reliability_scores = []
        counterparty_cache = {}

        for contract in contracts:
            cp = contract.counterparty

            # Cache counterparty metrics to avoid recalculation
            if cp.id not in counterparty_cache:
                counterparty_cache[cp.id] = {
                    'reliability': self.calculate_counterparty_reliability(cp),
                    'failure_prob_base': None
                }

            reliability = counterparty_cache[cp.id]['reliability']

            # Calculate contract-specific exposure
            contract_value = self.parse_contract_value(contract.contract_value or "")
            total_liability = float(contract.total_liability or 0)
            silent_risk_exposure = contract.silent_risks.aggregate(
                total=Sum('financial_exposure')
            )['total'] or 0
            exposure = contract_value + total_liability + float(silent_risk_exposure)

            # Calculate failure probability for this contract
            from core.models import Clause
            avg_risk = Clause.objects.filter(
                contract=contract,
                risk_score__isnull=False
            ).aggregate(Avg('risk_score'))['risk_score__avg']

            if avg_risk is None:
                failure_prob = 1 - reliability
            else:
                failure_prob = (1 - reliability) * 0.6 + avg_risk * 0.4

            failure_prob = round(min(failure_prob, 1.0), 3)

            # Determine quadrant
            quadrant = self._determine_quadrant(reliability, exposure, failure_prob)

            # Use original_filename or filename as the contract name
            contract_name = contract.original_filename or contract.filename or f'Contract #{str(contract.id)[:8]}'

            heatmap_data.append({
                'contract_id': str(contract.id),
                'contract_name': contract_name,
                'counterparty_id': str(cp.id),
                'counterparty_name': cp.name,
                'reliability_score': reliability,
                'financial_exposure': round(exposure, 2),
                'failure_probability': failure_prob,
                'quadrant': quadrant,
                'industry': cp.industry or 'Unknown',
            })

            total_exposure += exposure
            if reliability not in reliability_scores:
                reliability_scores.append(reliability)

        # Sort by failure_probability descending (riskiest first)
        heatmap_data.sort(key=lambda x: x['failure_probability'], reverse=True)

        # Calculate summary metrics
        high_risk_count = len([d for d in heatmap_data if d['quadrant'] == 'IMMEDIATE_ACTION'])
        avg_reliability = sum(reliability_scores) / len(reliability_scores) if reliability_scores else 0

        unique_counterparties = len(set(d['counterparty_id'] for d in heatmap_data))

        summary = {
            'total_counterparties': unique_counterparties,
            'total_contracts': len(heatmap_data),
            'total_exposure': round(total_exposure, 2),
            'high_risk_count': high_risk_count,
            'avg_reliability': round(avg_reliability, 3),
            'contracts_with_counterparty': len(heatmap_data),
            'contracts_without_counterparty': Contract.objects.filter(
                user_id=user_id,
                counterparty__isnull=True
            ).count(),
        }

        return {
            'heatmap_data': heatmap_data,
            'summary': summary,
        }

    def _determine_quadrant(self, reliability: float, exposure: float, failure_prob: float) -> str:
        """
        Determine risk quadrant for portfolio visualization.

        Quadrants:
        - IMMEDIATE_ACTION: High failure prob + High exposure
        - MONITOR: Medium risk
        - SAFE: High reliability + Low failure prob
        - REVIEW: Low reliability but low exposure
        """
        if failure_prob >= 0.6:
            if exposure > 100000:  # Threshold for "high exposure"
                return 'IMMEDIATE_ACTION'
            else:
                return 'REVIEW'
        elif failure_prob >= 0.3:
            return 'MONITOR'
        else:
            return 'SAFE'

    def get_contract_risk_detail(self, contract_id: str) -> Dict:
        """
        Get detailed risk analysis for a specific contract with full portfolio context.

        This provides CFO/CRO-level intelligence for a single contract:
        - Counterparty profile & reliability breakdown
        - Financial exposure decomposition
        - Bayesian failure analysis
        - Portfolio positioning
        - Recommended actions

        Returns: Comprehensive risk intelligence dict
        """
        from core.models import Clause

        try:
            contract = Contract.objects.select_related('counterparty').get(id=contract_id)
        except Contract.DoesNotExist:
            raise ValueError(f"Contract {contract_id} not found")

        # If no counterparty, return minimal data
        if not contract.counterparty:
            return {
                'contract': {
                    'id': str(contract.id),
                    'name': contract.original_filename or contract.filename,
                    'value': contract.contract_value,
                    'has_counterparty': False
                },
                'message': 'No counterparty linked to this contract'
            }

        cp = contract.counterparty

        # 1. Calculate counterparty reliability with breakdown
        history = NegotiationHistory.objects.filter(counterparty=cp)
        total_history = history.count()

        if total_history > 0:
            acceptance_rate = history.filter(accepted=True).count() / total_history
            stall_rate = history.filter(stalled=True).count() / total_history
            avg_redlines = history.aggregate(Avg('redline_rounds'))['redline_rounds__avg'] or 1
            redline_score = 1 / (1 + avg_redlines)
            avg_deviation = history.aggregate(Avg('deviation_score'))['deviation_score__avg'] or 0
            deviation_score = 1 - avg_deviation
        else:
            acceptance_rate = 0.5
            stall_rate = 0.5
            redline_score = 0.5
            avg_redlines = 0
            deviation_score = 0.5
            avg_deviation = 0.5

        reliability = self.calculate_counterparty_reliability(cp)

        reliability_breakdown = {
            'overall_score': reliability,
            'acceptance_rate': round(acceptance_rate, 3),
            'stall_rate': round(stall_rate, 3),
            'redline_score': round(redline_score, 3),
            'avg_redline_rounds': round(avg_redlines, 1),
            'deviation_score': round(deviation_score, 3),
            'avg_deviation': round(avg_deviation, 3),
            'history_records': total_history
        }

        # 2. Calculate financial exposure with breakdown
        contract_value = self.parse_contract_value(contract.contract_value or "")
        total_liability = float(contract.total_liability or 0)
        silent_risk_exposure = contract.silent_risks.aggregate(
            total=Sum('financial_exposure')
        )['total'] or 0
        total_exposure = contract_value + total_liability + float(silent_risk_exposure)

        financial_exposure = {
            'total': round(total_exposure, 2),
            'contract_value': round(contract_value, 2),
            'total_liability': round(total_liability, 2),
            'silent_risk_exposure': round(float(silent_risk_exposure), 2)
        }

        # 3. Calculate failure probability with explanation
        avg_risk = Clause.objects.filter(
            contract=contract,
            risk_score__isnull=False
        ).aggregate(Avg('risk_score'))['risk_score__avg']

        if avg_risk is None:
            failure_prob = 1 - reliability
            failure_explanation = "Based on counterparty reliability only (no clause risk data)"
        else:
            failure_prob = (1 - reliability) * 0.6 + avg_risk * 0.4
            failure_explanation = f"Bayesian: (1 - reliability) * 0.6 + avg_clause_risk * 0.4 = {round(failure_prob, 3)}"

        failure_prob = round(min(failure_prob, 1.0), 3)

        failure_analysis = {
            'probability': failure_prob,
            'avg_clause_risk': round(avg_risk, 3) if avg_risk else None,
            'explanation': failure_explanation,
            'risk_level': 'HIGH' if failure_prob >= 0.6 else 'MEDIUM' if failure_prob >= 0.3 else 'LOW'
        }

        # 4. Portfolio context
        counterparty_contracts = Contract.objects.filter(counterparty=cp, user_id=contract.user_id)
        counterparty_total_exposure = sum(
            self.calculate_financial_exposure(cp) for cp in [contract.counterparty]
        )

        user_total_exposure = 0.0
        all_user_contracts = Contract.objects.filter(user_id=contract.user_id, counterparty__isnull=False)
        for c in all_user_contracts:
            cv = self.parse_contract_value(c.contract_value or "")
            tl = float(c.total_liability or 0)
            sre = c.silent_risks.aggregate(total=Sum('financial_exposure'))['total'] or 0
            user_total_exposure += cv + tl + float(sre)

        portfolio_percentage = (total_exposure / user_total_exposure * 100) if user_total_exposure > 0 else 0

        portfolio_context = {
            'counterparty_total_exposure': round(counterparty_total_exposure, 2),
            'related_contracts_count': counterparty_contracts.count(),
            'portfolio_percentage': round(portfolio_percentage, 2),
            'user_total_exposure': round(user_total_exposure, 2)
        }

        # 5. Determine quadrant and recommended actions
        quadrant = self._determine_quadrant(reliability, total_exposure, failure_prob)
        recommended_actions = self._get_recommended_actions(quadrant, reliability, failure_prob, total_exposure)

        # 6. Get counterparty profile
        counterparty_profile = {
            'id': str(cp.id),
            'name': cp.name,
            'industry': cp.industry or 'Unknown',
            'reliability_score': reliability,
            'risk_profile': cp.risk_profile or 'Unknown',
            'total_contracts': counterparty_contracts.count()
        }

        return {
            'contract': {
                'id': str(contract.id),
                'name': contract.original_filename or contract.filename,
                'value': contract.contract_value,
                'status': contract.status,
                'has_counterparty': True
            },
            'counterparty_profile': counterparty_profile,
            'reliability_breakdown': reliability_breakdown,
            'financial_exposure': financial_exposure,
            'failure_analysis': failure_analysis,
            'portfolio_context': portfolio_context,
            'risk_quadrant': quadrant,
            'recommended_actions': recommended_actions
        }

    def _get_recommended_actions(self, quadrant: str, reliability: float, failure_prob: float, exposure: float) -> List[Dict]:
        """
        Generate context-specific recommended actions based on risk quadrant.
        """
        actions = []

        if quadrant == 'IMMEDIATE_ACTION':
            actions = [
                {
                    'priority': 'CRITICAL',
                    'action': 'Schedule immediate risk review meeting with CFO/CRO',
                    'rationale': f'High failure probability ({failure_prob:.1%}) with significant exposure (Rs {exposure/10000000:.1f} Cr)'
                },
                {
                    'priority': 'HIGH',
                    'action': 'Renegotiate key terms or request additional guarantees',
                    'rationale': f'Counterparty reliability is low ({reliability:.1%})'
                },
                {
                    'priority': 'HIGH',
                    'action': 'Consider hedging strategies or insurance',
                    'rationale': 'Mitigate potential financial impact'
                }
            ]
        elif quadrant == 'MONITOR':
            actions = [
                {
                    'priority': 'MEDIUM',
                    'action': 'Add to monthly risk monitoring dashboard',
                    'rationale': f'Moderate failure probability ({failure_prob:.1%}) requires ongoing tracking'
                },
                {
                    'priority': 'MEDIUM',
                    'action': 'Review counterparty performance quarterly',
                    'rationale': f'Current reliability at {reliability:.1%} - track trend'
                },
                {
                    'priority': 'LOW',
                    'action': 'Document escalation triggers for executive review',
                    'rationale': 'Prepare contingency if risk profile deteriorates'
                }
            ]
        elif quadrant == 'REVIEW':
            actions = [
                {
                    'priority': 'MEDIUM',
                    'action': 'Assess counterparty relationship value',
                    'rationale': f'Low reliability ({reliability:.1%}) but limited exposure'
                },
                {
                    'priority': 'LOW',
                    'action': 'Consider vendor rationalization',
                    'rationale': 'Consolidate to more reliable counterparties'
                }
            ]
        else:  # SAFE
            actions = [
                {
                    'priority': 'LOW',
                    'action': 'Maintain standard monitoring protocols',
                    'rationale': f'Strong reliability ({reliability:.1%}) and low failure risk'
                },
                {
                    'priority': 'INFO',
                    'action': 'Use as benchmark for other counterparty relationships',
                    'rationale': 'This represents a healthy risk profile'
                }
            ]

        return actions


# Global service instance
counterparty_portfolio_service = CounterpartyPortfolioService()
