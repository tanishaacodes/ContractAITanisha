"""
Negotiation Heat Engine API Views

RESTful endpoints for negotiation heat analysis.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ai.heat_engine.heat_service import (
    analyze_negotiation_heat,
    compare_heat,
    recommend_cooling_strategy,
    bulk_heat_analysis
)
from negotiation.models import NegotiationHistory


class ClauseHeatAnalysisView(APIView):
    """
    Analyze negotiation heat for a specific clause.

    GET /api/clauses/<clause_id>/heat/
    """

    def get(self, request, clause_id):
        """Get heat analysis for clause"""
        try:
            # Get negotiation history for this clause
            history = NegotiationHistory.objects.filter(clause_id=clause_id).order_by('created_at')

            if not history.exists():
                return Response({
                    "heat_score": 0.3,
                    "heat_level": "UNTESTED",
                    "message": "No negotiation history available for this clause"
                }, status=status.HTTP_200_OK)

            # Extract redlines
            redlines = [h.counterparty_redline or h.our_redline for h in history if h.counterparty_redline or h.our_redline]

            if not redlines:
                return Response({
                    "heat_score": 0.3,
                    "heat_level": "MINIMAL",
                    "message": "No redlines found in negotiation history"
                }, status=status.HTTP_200_OK)

            # Analyze heat
            heat_analysis = analyze_negotiation_heat(redlines)

            # Get cooling strategies
            cooling = recommend_cooling_strategy(heat_analysis)

            return Response({
                **heat_analysis,
                "cooling_strategies": cooling,
                "clause_id": clause_id
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContractHeatMapView(APIView):
    """
    Get heat map for all clauses in a contract.

    GET /api/contracts/<contract_id>/heat-map/
    """

    def get(self, request, contract_id):
        """Get contract heat map"""
        try:
            # Get all negotiation history for this contract
            history = NegotiationHistory.objects.filter(
                contract_negotiation__contract_id=contract_id
            ).select_related('clause')

            # Group by clause
            clause_redlines = {}
            for h in history:
                clause_id = h.clause_id
                if clause_id not in clause_redlines:
                    clause_redlines[clause_id] = []

                redline = h.counterparty_redline or h.our_redline
                if redline:
                    clause_redlines[clause_id].append(redline)

            # Analyze heat for each clause
            heat_analyses = []
            for clause_id, redlines in clause_redlines.items():
                if redlines:
                    heat = analyze_negotiation_heat(redlines)
                    heat["clause_id"] = clause_id
                    heat_analyses.append(heat)

            # Sort by heat (hottest first)
            heat_analyses.sort(key=lambda x: x["heat_score"], reverse=True)

            # Calculate stats
            if heat_analyses:
                avg_heat = sum(h["heat_score"] for h in heat_analyses) / len(heat_analyses)
                max_heat = max(h["heat_score"] for h in heat_analyses)
                hot_clauses = sum(1 for h in heat_analyses if h["heat_score"] > 0.6)
            else:
                avg_heat = 0
                max_heat = 0
                hot_clauses = 0

            return Response({
                "contract_id": contract_id,
                "total_clauses": len(heat_analyses),
                "avg_heat": round(avg_heat, 3),
                "max_heat": round(max_heat, 3),
                "hot_clause_count": hot_clauses,
                "clauses": heat_analyses
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HeatComparisonView(APIView):
    """
    Compare heat between two clauses.

    GET /api/heat/compare/?clause_a=<id>&clause_b=<id>
    """

    def get(self, request):
        """Compare clause heat"""
        try:
            clause_a_id = request.query_params.get('clause_a')
            clause_b_id = request.query_params.get('clause_b')

            if not clause_a_id or not clause_b_id:
                return Response(
                    {"error": "Both clause_a and clause_b parameters required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get redlines for clause A
            history_a = NegotiationHistory.objects.filter(clause_id=clause_a_id).order_by('created_at')
            redlines_a = [h.counterparty_redline or h.our_redline for h in history_a if h.counterparty_redline or h.our_redline]

            # Get redlines for clause B
            history_b = NegotiationHistory.objects.filter(clause_id=clause_b_id).order_by('created_at')
            redlines_b = [h.counterparty_redline or h.our_redline for h in history_b if h.counterparty_redline or h.our_redline]

            # Compare
            comparison = compare_heat(redlines_a, redlines_b)

            return Response({
                "clause_a": clause_a_id,
                "clause_b": clause_b_id,
                **comparison
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CoolingStrategyView(APIView):
    """
    Get cooling strategies for a hot clause.

    GET /api/clauses/<clause_id>/heat/cooling-strategies/
    """

    def get(self, request, clause_id):
        """Get cooling strategies"""
        try:
            # Get negotiation history
            history = NegotiationHistory.objects.filter(clause_id=clause_id).order_by('created_at')

            if not history.exists():
                return Response({
                    "message": "No negotiation history available",
                    "strategies": []
                }, status=status.HTTP_200_OK)

            redlines = [h.counterparty_redline or h.our_redline for h in history if h.counterparty_redline or h.our_redline]

            if not redlines:
                return Response({
                    "message": "No redlines found",
                    "strategies": []
                }, status=status.HTTP_200_OK)

            # Analyze heat
            heat_analysis = analyze_negotiation_heat(redlines)

            # Get strategies
            strategies = recommend_cooling_strategy(heat_analysis)

            return Response({
                "clause_id": clause_id,
                "current_heat": heat_analysis["heat_score"],
                "heat_level": heat_analysis["heat_level"],
                "strategies": strategies
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PortfolioHeatStatsView(APIView):
    """
    Get portfolio-wide heat statistics.

    GET /api/heat/portfolio-stats/
    """

    def get(self, request):
        """Get portfolio heat stats"""
        try:
            # Get all negotiation history
            all_history = NegotiationHistory.objects.all().select_related('clause')

            # Group by clause
            clause_redlines = {}
            for h in all_history:
                clause_id = h.clause_id
                if clause_id not in clause_redlines:
                    clause_redlines[clause_id] = []

                redline = h.counterparty_redline or h.our_redline
                if redline:
                    clause_redlines[clause_id].append(redline)

            # Analyze
            clauses_data = [(cid, redlines) for cid, redlines in clause_redlines.items()]
            heat_analyses = bulk_heat_analysis(clauses_data)

            # Calculate stats
            if heat_analyses:
                avg_heat = sum(h["heat_score"] for h in heat_analyses) / len(heat_analyses)
                critical = sum(1 for h in heat_analyses if h["heat_score"] > 0.8)
                high = sum(1 for h in heat_analyses if 0.6 <= h["heat_score"] <= 0.8)
                medium = sum(1 for h in heat_analyses if 0.4 <= h["heat_score"] < 0.6)
                low = sum(1 for h in heat_analyses if h["heat_score"] < 0.4)
            else:
                avg_heat = 0
                critical = high = medium = low = 0

            return Response({
                "total_clauses": len(heat_analyses),
                "avg_heat": round(avg_heat, 3),
                "distribution": {
                    "critical": critical,
                    "high": high,
                    "medium": medium,
                    "low": low
                },
                "hottest_clauses": heat_analyses[:10] if heat_analyses else []
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
