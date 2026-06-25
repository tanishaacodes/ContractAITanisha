"""
Predictive Risk Engine Views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import logging

from .predictive_risk_engine import get_predictive_risk_engine

logger = logging.getLogger(__name__)


class PredictiveRiskAllView(APIView):
    """
    GET /api/analytics/predictive-risk/
    Forecast risk for all clause types.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            horizon = int(request.query_params.get('horizon', 6))
            engine = get_predictive_risk_engine()
            results = engine.forecast_all_types(user=request.user, horizon=horizon)
            return Response({'forecasts': results, 'horizon_months': horizon})
        except Exception as e:
            logger.error(f"Predictive risk all failed: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PredictiveRiskByTypeView(APIView):
    """
    GET /api/analytics/predictive-risk/<clause_type>/
    Forecast risk for a specific clause type with full history + forecast.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, clause_type):
        try:
            horizon = int(request.query_params.get('horizon', 6))
            engine = get_predictive_risk_engine()
            result = engine.forecast_clause_type(clause_type, user=request.user, horizon=horizon)
            return Response(result)
        except Exception as e:
            logger.error(f"Predictive risk by type failed: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
