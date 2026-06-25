"""
Portfolio Exposure Rollup Engine
=================================
Aggregates exposure across all contracts for portfolio-level risk analysis.

Features:
1. Total portfolio exposure calculation
2. Counterparty concentration risk
3. Exposure by contract type
4. Top risk contributors
5. Time-based exposure trends
6. Currency-normalized exposure

Perfect for CFO/CRO portfolio reviews and risk committee meetings.
"""

import logging
from typing import Dict, List, Any, Optional
from decimal import Decimal
from collections import defaultdict

logger = logging.getLogger(__name__)


class PortfolioExposureEngine:
    """
    Portfolio-level exposure aggregation and analytics.

    Combines individual contract exposures into portfolio view.
    """

    def __init__(self):
        """Initialize portfolio engine"""
        pass

    def calculate_portfolio_exposure(
        self,
        user,
        currency: str = 'INR'
    ) -> Dict[str, Any]:
        """
        Calculate total exposure across all user's contracts.

        Args:
            user: User instance
            currency: Target currency for normalization

        Returns:
            Dict with portfolio exposure metrics
        """
        from core.models import Contract, Clause, ContractGraphMeta
        from .exposure_engine import ExposureEngine
        from .clause_graph import build_interaction_graph
        from .currency_converter import get_converter

        try:
            # Get all user contracts
            contracts = Contract.objects.filter(user=user).order_by('-uploaded_at')

            if not contracts.exists():
                return self._empty_portfolio()

            exposure_engine = ExposureEngine()
            converter = get_converter()

            # Aggregate metrics
            total_exposure = 0.0
            contract_exposures = []
            counterparty_exposure = defaultdict(float)
            type_exposure = defaultdict(float)
            currency_breakdown = defaultdict(float)

            for contract in contracts:
                try:
                    # Get contract value
                    contract_value = exposure_engine.parse_contract_value(
                        contract.contract_value or "0"
                    )

                    if contract_value == 0:
                        continue

                    # Get clauses
                    clauses = list(Clause.objects.filter(contract=contract, found=True))

                    if not clauses:
                        continue

                    # Build graph
                    graph = build_interaction_graph(clauses)

                    # Calculate exposure
                    exposure, breakdown = exposure_engine.calculate_total_exposure(
                        clauses,
                        graph,
                        contract_value
                    )

                    # Convert to target currency
                    contract_currency = self._detect_currency(contract)
                    if contract_currency != currency:
                        exposure = converter.convert(exposure, contract_currency, currency)

                    # Accumulate
                    total_exposure += exposure

                    # Track by counterparty
                    counterparty = contract.counterparty or contract.party_name or 'Unknown'
                    counterparty_exposure[counterparty] += exposure

                    # Track by type
                    contract_type = contract.contract_type or 'General'
                    type_exposure[contract_type] += exposure

                    # Track by currency
                    currency_breakdown[contract_currency] += exposure

                    # Store individual contract
                    contract_exposures.append({
                        'contract_id': str(contract.id),
                        'contract_name': contract.name or contract.original_filename,
                        'counterparty': counterparty,
                        'contract_type': contract_type,
                        'exposure': round(exposure, 2),
                        'exposure_formatted': converter.format_amount(exposure, currency),
                        'contract_value': contract_value,
                        'uploaded_at': contract.uploaded_at.isoformat()
                    })

                except Exception as e:
                    logger.warning(f"Failed to process contract {contract.id}: {e}")
                    continue

            # Sort contracts by exposure
            contract_exposures.sort(key=lambda x: x['exposure'], reverse=True)

            # Top counterparties
            top_counterparties = [
                {
                    'counterparty': cp,
                    'exposure': round(exp, 2),
                    'exposure_formatted': converter.format_amount(exp, currency),
                    'percentage': round((exp / total_exposure * 100) if total_exposure > 0 else 0, 1)
                }
                for cp, exp in sorted(
                    counterparty_exposure.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            ]

            # Top contract types
            top_types = [
                {
                    'contract_type': ct,
                    'exposure': round(exp, 2),
                    'exposure_formatted': converter.format_amount(exp, currency),
                    'percentage': round((exp / total_exposure * 100) if total_exposure > 0 else 0, 1)
                }
                for ct, exp in sorted(
                    type_exposure.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            ]

            # Concentration risk (Herfindahl index)
            concentration_index = sum(
                (exp / total_exposure) ** 2
                for exp in counterparty_exposure.values()
            ) if total_exposure > 0 else 0

            # Risk rating based on concentration
            if concentration_index > 0.25:
                concentration_risk = 'HIGH'
            elif concentration_index > 0.15:
                concentration_risk = 'MEDIUM'
            else:
                concentration_risk = 'LOW'

            return {
                'success': True,
                'currency': currency,
                'total_exposure': round(total_exposure, 2),
                'total_exposure_formatted': converter.format_amount(total_exposure, currency),
                'total_contracts': len(contract_exposures),
                'contracts': contract_exposures[:50],  # Limit to top 50
                'counterparty_breakdown': top_counterparties,
                'type_breakdown': top_types,
                'currency_breakdown': [
                    {
                        'currency': curr,
                        'exposure': round(exp, 2),
                        'exposure_formatted': converter.format_amount(exp, curr)
                    }
                    for curr, exp in sorted(
                        currency_breakdown.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )
                ],
                'concentration': {
                    'index': round(concentration_index, 3),
                    'risk_level': concentration_risk,
                    'interpretation': self._interpret_concentration(concentration_risk)
                },
                'top_risk_contributors': contract_exposures[:10]
            }

        except Exception as e:
            logger.error(f"Portfolio exposure calculation failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def calculate_portfolio_trends(
        self,
        user,
        currency: str = 'INR',
        months: int = 12
    ) -> Dict[str, Any]:
        """
        Calculate portfolio exposure trends over time.

        Args:
            user: User instance
            currency: Target currency
            months: Number of months to analyze

        Returns:
            Dict with time-series exposure data
        """
        from core.models import Contract
        from datetime import datetime, timedelta
        from django.db.models import Q
        from .currency_converter import get_converter

        try:
            converter = get_converter()
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months * 30)

            # Get contracts in date range
            contracts = Contract.objects.filter(
                user=user,
                uploaded_at__gte=start_date
            ).order_by('uploaded_at')

            # Group by month
            monthly_exposure = []
            current_date = start_date

            while current_date <= end_date:
                month_start = current_date.replace(day=1)
                next_month = (month_start + timedelta(days=32)).replace(day=1)

                month_contracts = contracts.filter(
                    uploaded_at__gte=month_start,
                    uploaded_at__lt=next_month
                )

                month_data = {
                    'month': month_start.strftime('%Y-%m'),
                    'contracts_added': month_contracts.count(),
                    'exposure': 0.0
                }

                monthly_exposure.append(month_data)
                current_date = next_month

            return {
                'success': True,
                'currency': currency,
                'period': f'{months} months',
                'monthly_data': monthly_exposure
            }

        except Exception as e:
            logger.error(f"Portfolio trends calculation failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _detect_currency(self, contract) -> str:
        """Detect currency from contract value string"""
        value_str = str(contract.contract_value or '').upper()

        if 'USD' in value_str or '$' in value_str:
            return 'USD'
        elif 'EUR' in value_str or '€' in value_str:
            return 'EUR'
        elif 'GBP' in value_str or '£' in value_str:
            return 'GBP'
        elif 'AED' in value_str:
            return 'AED'
        else:
            return 'INR'  # Default

    def _interpret_concentration(self, risk_level: str) -> str:
        """Interpret concentration risk level"""
        interpretations = {
            'HIGH': 'Portfolio heavily concentrated in few counterparties. Consider diversification.',
            'MEDIUM': 'Moderate concentration. Monitor top counterparties closely.',
            'LOW': 'Well-diversified portfolio across counterparties.'
        }
        return interpretations.get(risk_level, '')

    def _empty_portfolio(self) -> Dict[str, Any]:
        """Return empty portfolio structure"""
        return {
            'success': True,
            'total_exposure': 0.0,
            'total_exposure_formatted': '₹0',
            'total_contracts': 0,
            'contracts': [],
            'counterparty_breakdown': [],
            'type_breakdown': [],
            'concentration': {
                'index': 0,
                'risk_level': 'N/A',
                'interpretation': 'No contracts in portfolio'
            },
            'top_risk_contributors': []
        }
