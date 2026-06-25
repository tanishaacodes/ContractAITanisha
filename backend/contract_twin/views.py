"""
Contract Twin API Views
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from core.models import Contract
from .twin_engine import simulate_supplier_failure, simulate_force_majeure, simulate_payment_default

logger = logging.getLogger(__name__)


class ContractTwinView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, contract_id):
        try:
            contract = get_object_or_404(Contract, id=contract_id)
            scenario = request.query_params.get('scenario', 'all')

            # Allow frontend to pass an override value when DB has NULL
            override_value = request.query_params.get('override_value')
            if override_value:
                try:
                    contract.contract_value = str(float(override_value.replace(',', '')))
                except (ValueError, TypeError):
                    pass

            if scenario == 'supplier_failure':
                result = simulate_supplier_failure(contract)
            elif scenario == 'force_majeure':
                result = simulate_force_majeure(contract)
            elif scenario == 'payment_default':
                result = simulate_payment_default(contract)
            else:
                result = {
                    "contract_id": str(contract.id),
                    "contract_title": getattr(contract, 'filename', 'Unknown'),
                    "simulations": {
                        "supplier_failure": simulate_supplier_failure(contract),
                        "force_majeure": simulate_force_majeure(contract),
                        "payment_default": simulate_payment_default(contract),
                    }
                }
            return Response(result)
        except Exception as e:
            logger.error(f"Contract twin view error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
