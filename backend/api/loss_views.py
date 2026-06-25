"""
Loss Prediction & Liability Sentinel API
Provides endpoints for loss forecasting and tail risk analysis
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.models import Contract
import sys
import os

# Add ai directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ai'))

try:
    from loss_predictor import (
        forecast_losses,
        calculate_exposure_percentage,
        tail_risk_distribution,
        calculate_var_cvar,
        attribute_loss_to_clauses
    )
except ImportError:
    # Fallback implementations
    def forecast_losses(exposure, risk_multiplier=1.0):
        return {"12m": 0, "24m": 0, "36m": 0}

    def calculate_exposure_percentage(contracts):
        return 0

    def tail_risk_distribution(exposure, risk_profile="medium", runs=2000):
        return []

    def calculate_var_cvar(exposure, confidence=0.95):
        return {"var_95": 0, "cvar_95": 0, "var_99": 0, "expected_shortfall": 0}

    def attribute_loss_to_clauses(contracts):
        return []


class LossSentinelDashboardView(APIView):
    """
    GET /api/loss-sentinel/dashboard
    Main dashboard data for Loss Prediction & Liability Sentinel
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        contracts = Contract.objects.filter(user=user)

        # Prepare contract data for analysis
        contract_data = []
        total_value = 0

        for contract in contracts:
            # Calculate contract value (use default if not available)
            try:
                value = float(contract.contract_value) if hasattr(contract, 'contract_value') and contract.contract_value else 50_000_000
            except (ValueError, TypeError):
                value = 50_000_000

            total_value += value

            # Calculate risk score
            risk_score = 50  # Default medium risk
            if contract.liability_level == 'HIGH':
                risk_score = 80
            elif contract.liability_level == 'MEDIUM':
                risk_score = 60
            elif contract.liability_level == 'LOW':
                risk_score = 30

            # Check for unlimited liability (multiple detection methods)
            has_unlimited_liability = False

            # Method 1: Check full_text for specific unlimited liability keywords
            if hasattr(contract, 'full_text') and contract.full_text:
                text_lower = contract.full_text.lower()
                has_unlimited_liability = (
                    'unlimited liability' in text_lower or
                    'unlimited indemnity' in text_lower or
                    ('unlimited' in text_lower and 'liability' in text_lower and 'cap' not in text_lower)
                )

            # Method 2: Fallback — only if model field explicitly says no cap
            if not has_unlimited_liability:
                has_liability_cap = getattr(contract, 'has_liability_cap', None)
                has_unlimited_liability = (
                    contract.liability_level == 'HIGH' and
                    has_liability_cap is False  # Only True when field exists and is explicitly False
                )

            contract_data.append({
                "id": contract.id,
                "name": contract.original_filename or contract.filename,
                "value": value,
                "risk_score": risk_score,
                "has_unlimited_liability": has_unlimited_liability,
                "broad_indemnity": risk_score > 70,
                "unilateral_termination": False,  # Would need clause analysis
                "has_liability_cap": hasattr(contract, 'has_liability_cap') and contract.has_liability_cap,
                "has_warranties": True,  # Default assumption
                "has_force_majeure": True  # Default assumption
            })

        # Calculate base exposure
        base_exposure = total_value if total_value > 0 else 500_000_000

        # Calculate exposure percentage
        exposure_pct = calculate_exposure_percentage(contract_data)

        # Forecast losses
        risk_multiplier = 1.2 if exposure_pct > 70 else 1.0 if exposure_pct > 40 else 0.8
        loss_forecast = forecast_losses(base_exposure, risk_multiplier)

        # Calculate tail risk
        risk_profile = "high" if exposure_pct > 70 else "medium" if exposure_pct > 40 else "low"
        tail_risk = tail_risk_distribution(base_exposure, risk_profile)

        # Calculate VaR/CVaR
        var_cvar = calculate_var_cvar(base_exposure)

        # Get unlimited liability contracts
        unlimited_contracts = [
            {
                "id": c["id"],
                "name": c["name"],
                "value_inr": c["value"],
                "value_usd": round(c["value"] / 83, 2),
                "risk_score": c["risk_score"]
            }
            for c in contract_data
            if c["has_unlimited_liability"]
        ][:10]  # Top 10

        # Attribute losses to clauses
        clause_attribution = attribute_loss_to_clauses(contract_data)

        return Response({
            "exposure_percentage": exposure_pct,
            "total_exposure_inr": int(base_exposure),
            "total_exposure_usd": round(base_exposure / 83, 2),
            "loss_forecast": loss_forecast,
            "tail_risk_distribution": tail_risk,
            "var_cvar": var_cvar,
            "unlimited_liability_watchlist": unlimited_contracts,
            "clause_loss_attribution": clause_attribution,
            "total_contracts": len(contract_data),
            "high_risk_contracts": sum(1 for c in contract_data if c["risk_score"] >= 70)
        })


class UnlimitedLiabilityWatchlistView(APIView):
    """
    GET /api/loss-sentinel/unlimited-watchlist
    Detailed view of contracts with unlimited liability
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        contracts = Contract.objects.filter(user=user).order_by('-uploaded_at')

        watchlist = []
        for contract in contracts:
            # Check for unlimited liability
            has_unlimited = False
            if hasattr(contract, 'full_text') and contract.full_text:
                text_lower = contract.full_text.lower()
                has_unlimited = (
                    'unlimited liability' in text_lower or
                    'unlimited indemnity' in text_lower or
                    ('unlimited' in text_lower and 'liability' in text_lower and 'cap' not in text_lower)
                )

            # Fallback to HIGH liability — only when field explicitly says no cap
            if not has_unlimited:
                has_liability_cap = getattr(contract, 'has_liability_cap', None)
                has_unlimited = (
                    contract.liability_level == 'HIGH' and
                    has_liability_cap is False
                )

            # Only add if has unlimited liability
            if has_unlimited:
                try:
                    value = float(contract.contract_value) if hasattr(contract, 'contract_value') and contract.contract_value else 50_000_000
                except (ValueError, TypeError):
                    value = 50_000_000

                watchlist.append({
                    "id": contract.id,
                    "name": contract.original_filename or contract.filename,
                    "value_inr": int(value),
                    "value_usd": round(value / 83, 2),
                    "risk_score": 80 if contract.liability_level == 'HIGH' else 60,
                    "business_unit": contract.business_unit or "Unknown",
                    "jurisdiction": contract.jurisdiction or "Unknown",
                    "uploaded_at": contract.uploaded_at.isoformat() if contract.uploaded_at else None,
                    "counterparty": contract.counterparty.name if contract.counterparty else "Unknown"
                })

        # Sort by value descending
        watchlist.sort(key=lambda x: x["value_inr"], reverse=True)

        return Response({
            "watchlist": watchlist,
            "total_unlimited": len(watchlist),
            "total_exposure": sum(c["value_inr"] for c in watchlist)
        })
