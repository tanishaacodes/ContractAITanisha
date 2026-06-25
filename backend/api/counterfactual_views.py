"""
Counterfactual & What-If Simulation API
Provides endpoints for contract scenario analysis
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from core.models import Contract
import sys
import os

# Add ai directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ai'))

try:
    from counterfactual_engine import simulate_counterfactual
except ImportError:
    # Fallback if numpy not available
    def simulate_counterfactual(contract, actions):
        return {
            "risk_delta": 0.0,
            "avg_loss": 0,
            "percentile_95": 0,
            "percentile_99": 0,
            "negotiation_shift": 0.0,
            "loss_distribution": [],
            "confidence_interval": {"lower": 0, "upper": 0}
        }


class CounterfactualSimulationView(APIView):
    """
    POST /api/counterfactual/simulate
    Run counterfactual simulation for contract modifications

    Request body:
    {
        "contract_id": 123,
        "actions": {
            "remove_clause": true,
            "add_indemnity": false,
            "liability_cap": 3,
            "governing_law": "UK",
            "add_arbitration": true,
            "termination_rights": false
        }
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        contract_id = request.data.get('contract_id')
        actions = request.data.get('actions', {})

        if not contract_id:
            return Response({"error": "contract_id is required"}, status=400)

        # Get contract (ensure user owns it)
        contract = get_object_or_404(Contract, id=contract_id, user=user)

        # Calculate base exposure from contract
        base_exposure = 500_000_000  # Default

        # Try to calculate from contract value if available
        if hasattr(contract, 'contract_value') and contract.contract_value:
            try:
                base_exposure = float(contract.contract_value)
            except (ValueError, TypeError):
                pass

        # Prepare contract data for simulation
        contract_data = {
            "id": contract.id,
            "exposure": base_exposure,
            "name": contract.original_filename or contract.filename
        }

        # Run simulation
        try:
            result = simulate_counterfactual(contract_data, actions)

            # Convert to INR and USD
            avg_loss_inr = result["avg_loss"]
            avg_loss_usd = round(result["avg_loss"] / 83, 2)

            percentile_95_inr = result["percentile_95"]
            percentile_95_usd = round(result["percentile_95"] / 83, 2)

            return Response({
                "contract_id": contract.id,
                "contract_name": contract_data["name"],
                "base_exposure_inr": int(base_exposure),
                "base_exposure_usd": round(base_exposure / 83, 2),
                "risk_delta": result["risk_delta"],
                "risk_delta_percentage": round(result["risk_delta"] * 100, 1),
                "avg_loss_inr": avg_loss_inr,
                "avg_loss_usd": avg_loss_usd,
                "percentile_95_inr": percentile_95_inr,
                "percentile_95_usd": percentile_95_usd,
                "percentile_99_inr": result["percentile_99"],
                "percentile_99_usd": round(result["percentile_99"] / 83, 2),
                "negotiation_shift": result["negotiation_shift"],
                "loss_distribution": result["loss_distribution"],
                "confidence_interval_inr": result["confidence_interval"],
                "confidence_interval_usd": {
                    "lower": round(result["confidence_interval"]["lower"] / 83, 2),
                    "upper": round(result["confidence_interval"]["upper"] / 83, 2)
                },
                "actions_applied": actions
            })

        except Exception as e:
            return Response({
                "error": "Simulation failed",
                "message": str(e)
            }, status=500)


class ContractListForSimulationView(APIView):
    """
    GET /api/counterfactual/contracts
    Get list of user's contracts for simulation
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        contracts = Contract.objects.filter(user=user).order_by('-uploaded_at')[:100]

        contract_list = []
        for c in contracts:
            contract_list.append({
                "id": c.id,
                "name": c.original_filename or c.filename,
                "uploaded_at": c.uploaded_at.isoformat() if c.uploaded_at else None,
                "business_unit": c.business_unit,
                "jurisdiction": c.jurisdiction,
                "contract_type": c.contract_type
            })

        return Response({
            "contracts": contract_list,
            "total": len(contract_list)
        })
