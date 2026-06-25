"""
Trust Score API Views

Provides RESTful endpoints for Clause Trust Score (CTS) functionality.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from core.models import Clause, ClauseEvent, ClauseHealthMetrics
from ai.trust_engine.trust_service import (
    calculate_clause_trust,
    bulk_calculate_trust,
    update_clause_health_with_trust,
    get_trust_statistics
)
from ai.trust_engine.badges import all_badges


class ClauseTrustScoreView(APIView):
    """
    Calculate Clause Trust Score (CTS) for a specific clause.

    GET /api/clauses/<clause_id>/trust/
    """

    def get(self, request, clause_id):
        """Get trust score for a clause."""
        try:
            clause = get_object_or_404(Clause, id=clause_id)

            # Get outcomes (ClauseEvents)
            # Note: ClauseEvent links to ClauseVersion, so we need to get through versions
            outcomes = ClauseEvent.objects.none()  # Start with empty queryset

            # If clause has versions with events
            if hasattr(clause, 'versions'):
                for version in clause.versions.all():
                    if hasattr(version, 'events'):
                        outcomes = outcomes | version.events.all()

            # Calculate trust
            trust_data = calculate_clause_trust(clause, outcomes)

            return Response(trust_data, status=status.HTTP_200_OK)

        except Clause.DoesNotExist:
            return Response(
                {"error": "Clause not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClauseTrustUpdateView(APIView):
    """
    Recalculate and update trust scores for a clause.

    POST /api/clauses/<clause_id>/trust/update/
    """

    def post(self, request, clause_id):
        """Recalculate trust score and update health metrics."""
        try:
            clause = get_object_or_404(Clause, id=clause_id)

            # Get or create health metrics
            health_metrics, created = ClauseHealthMetrics.objects.get_or_create(
                clause=clause,
                defaults={
                    'usage_count': 0,
                    'success_rate': 0.0,
                    'enforceability_score': 0.5,
                    'negotiation_score': 0.5,
                    'health_score': 0.5
                }
            )

            # Update with trust scores
            updated_metrics = update_clause_health_with_trust(clause, health_metrics)

            # Get full trust data
            outcomes = ClauseEvent.objects.none()
            if hasattr(clause, 'versions'):
                for version in clause.versions.all():
                    if hasattr(version, 'events'):
                        outcomes = outcomes | version.events.all()

            trust_data = calculate_clause_trust(clause, outcomes)

            return Response({
                "message": "Trust score updated successfully",
                "trust_data": trust_data,
                "created": created
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkTrustScoreView(APIView):
    """
    Calculate trust scores for multiple clauses.

    POST /api/clauses/trust/bulk/
    Body: {clause_ids: [id1, id2, ...]}
    """

    def post(self, request):
        """Bulk trust score calculation."""
        try:
            clause_ids = request.data.get('clause_ids', [])

            if not clause_ids:
                # Get all clauses
                clauses = Clause.objects.all()[:100]  # Limit to 100 for performance
            else:
                clauses = Clause.objects.filter(id__in=clause_ids)

            # Calculate trust scores
            trust_scores = bulk_calculate_trust(clauses)

            return Response({
                "count": len(trust_scores),
                "trust_scores": trust_scores
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TrustStatisticsView(APIView):
    """
    Get aggregate trust statistics across all clauses.

    GET /api/trust/statistics/
    """

    def get(self, request):
        """Get trust statistics."""
        try:
            # Optional filter by contract
            contract_id = request.query_params.get('contract_id')

            if contract_id:
                clauses = Clause.objects.filter(contract_id=contract_id)
            else:
                clauses = Clause.objects.all()[:500]  # Limit for performance

            stats = get_trust_statistics(clauses)

            return Response(stats, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TrustBadgesView(APIView):
    """
    Get all available trust badges and their definitions.

    GET /api/trust/badges/
    """

    def get(self, request):
        """List all trust badges."""
        try:
            badges = all_badges()

            return Response({
                "badges": badges,
                "count": len(badges)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClauseTrustCompareView(APIView):
    """
    Compare trust scores between two clauses.

    GET /api/trust/compare/?clause_a=<id>&clause_b=<id>
    """

    def get(self, request):
        """Compare two clauses by trust score."""
        try:
            clause_a_id = request.query_params.get('clause_a')
            clause_b_id = request.query_params.get('clause_b')

            if not clause_a_id or not clause_b_id:
                return Response(
                    {"error": "Both clause_a and clause_b parameters required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            clause_a = get_object_or_404(Clause, id=clause_a_id)
            clause_b = get_object_or_404(Clause, id=clause_b_id)

            # Get outcomes
            outcomes_a = ClauseEvent.objects.none()
            if hasattr(clause_a, 'versions'):
                for version in clause_a.versions.all():
                    if hasattr(version, 'events'):
                        outcomes_a = outcomes_a | version.events.all()

            outcomes_b = ClauseEvent.objects.none()
            if hasattr(clause_b, 'versions'):
                for version in clause_b.versions.all():
                    if hasattr(version, 'events'):
                        outcomes_b = outcomes_b | version.events.all()

            # Calculate trust for both
            trust_a = calculate_clause_trust(clause_a, outcomes_a)
            trust_b = calculate_clause_trust(clause_b, outcomes_b)

            # Compare
            diff = trust_a["trust_score"] - trust_b["trust_score"]
            diff_pct = (diff / trust_b["trust_score"] * 100) if trust_b["trust_score"] > 0 else 0

            if abs(diff) < 0.05:
                verdict = "EQUIVALENT"
            elif diff > 0:
                verdict = "A_BETTER"
            else:
                verdict = "B_BETTER"

            return Response({
                "clause_a": {
                    "id": clause_a.id,
                    "name": clause_a.clause_name,
                    "trust_data": trust_a
                },
                "clause_b": {
                    "id": clause_b.id,
                    "name": clause_b.clause_name,
                    "trust_data": trust_b
                },
                "comparison": {
                    "difference": round(diff, 3),
                    "difference_pct": round(diff_pct, 1),
                    "verdict": verdict
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContractTrustDashboardView(APIView):
    """
    Get trust dashboard for all clauses in a contract.

    GET /api/contracts/<contract_id>/trust/dashboard/
    """

    def get(self, request, contract_id):
        """Get contract-level trust dashboard."""
        try:
            clauses = Clause.objects.filter(contract_id=contract_id)

            if not clauses.exists():
                return Response(
                    {"error": "Contract not found or has no clauses"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Calculate trust for all clauses
            trust_scores = bulk_calculate_trust(clauses)

            # Get statistics
            stats = get_trust_statistics(clauses)

            # Find high-risk clauses
            high_risk = [t for t in trust_scores if t["trust_score"] < 0.4]
            excellent = [t for t in trust_scores if t["trust_score"] >= 0.85]

            return Response({
                "contract_id": contract_id,
                "total_clauses": len(trust_scores),
                "statistics": stats,
                "high_risk_clauses": high_risk,
                "excellent_clauses": excellent,
                "all_clauses": trust_scores
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
