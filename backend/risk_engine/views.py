"""Risk Scoring Engine API Views"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .risk_service import compute_risk_score, compute_clause_risk, score_multiple_clauses

logger = logging.getLogger(__name__)


class RiskScoreView(APIView):
    """POST /api/risk-engine/score/ — score a contract or clause text"""
    permission_classes = [AllowAny]

    def post(self, request):
        text = request.data.get("text", "").strip()
        if not text:
            return Response({"error": "text is required"}, status=status.HTTP_400_BAD_REQUEST)

        contract_value = float(request.data.get("contract_value", 0) or 0)
        clause_count = int(request.data.get("clause_count", 0) or 0)

        result = compute_risk_score(text, contract_value=contract_value, clause_count=clause_count)
        return Response(result)


class ClauseRiskView(APIView):
    """POST /api/risk-engine/clause/ — score a single clause"""
    permission_classes = [AllowAny]

    def post(self, request):
        text = request.data.get("text", "").strip()
        if not text:
            return Response({"error": "text is required"}, status=status.HTTP_400_BAD_REQUEST)
        result = compute_clause_risk(text)
        return Response(result)


class BatchClauseRiskView(APIView):
    """POST /api/risk-engine/batch/ — score multiple clauses"""
    permission_classes = [AllowAny]

    def post(self, request):
        clauses = request.data.get("clauses", [])
        if not clauses or not isinstance(clauses, list):
            return Response({"error": "clauses must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)
        if len(clauses) > 200:
            return Response({"error": "Maximum 200 clauses per batch"}, status=status.HTTP_400_BAD_REQUEST)
        result = score_multiple_clauses(clauses)
        return Response(result)
