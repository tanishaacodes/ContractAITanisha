"""
Strategic Radar API Views
=========================
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .radar_engine import run_strategic_radar
from .models import StrategicAlert, ContractExposure

logger = logging.getLogger(__name__)


class StrategicRadarView(APIView):
    """
    GET /api/strategic-radar/<contract_id>/
    Runs the full Strategic Intelligence Radar for a contract.
    """
    permission_classes = [AllowAny]

    def get(self, request, contract_id):
        try:
            result = run_strategic_radar(contract_id)

            # Persist alerts to DB
            for alert in result.get('alerts', []):
                StrategicAlert.objects.create(
                    contract_id=contract_id,
                    alert_type=alert.get('alert_type', 'cost_risk'),
                    exposure_type=alert.get('exposure_type', ''),
                    message=alert.get('message', ''),
                    estimated_value=alert.get('estimated_value', 0),
                )

            # Persist exposures to DB
            for exp in result.get('exposures', []):
                impact = exp.get('estimated_impact') or exp.get('annual_financing_impact', 0) or 0
                ContractExposure.objects.create(
                    contract_id=contract_id,
                    exposure_type=exp.get('exposure_type', ''),
                    signal_name=exp.get('message', '')[:255],
                    estimated_impact=impact,
                    is_protected=exp.get('protected', False),
                )

            return Response(result)

        except Exception as e:
            logger.error(f"Strategic radar error for {contract_id}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StrategicAlertHistoryView(APIView):
    """
    GET /api/strategic-radar/alerts/?contract_id=<id>
    Returns alert history for a contract.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        contract_id = request.query_params.get('contract_id')
        qs = StrategicAlert.objects.all()[:100]
        if contract_id:
            qs = StrategicAlert.objects.filter(contract_id=contract_id)[:50]

        data = list(qs.values(
            'id', 'contract_id', 'alert_type', 'exposure_type',
            'message', 'estimated_value', 'is_actioned', 'created_at'
        ))
        return Response({"alerts": data, "count": len(data)})
