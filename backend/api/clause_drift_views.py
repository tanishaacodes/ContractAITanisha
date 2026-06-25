"""
Clause Drift Intelligence API Views
Provides endpoints for clause-level drift analysis and prediction.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from core.models import Clause, ClauseVersion
from api.services.drift_predictor import get_drift_predictor
import logging

logger = logging.getLogger(__name__)


class ClauseDriftView(APIView):
    """
    GET /api/clauses/<clause_id>/drift

    Returns drift intelligence for a specific clause:
    - Original vs current text
    - Predicted future clause
    - Drift probability
    - Volatility index
    - Historical deviation
    - Counterparty bias
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, clause_id):
        try:
            clause = get_object_or_404(Clause, id=clause_id)
            drift_service = get_drift_predictor()

            # Get clause versions
            versions = ClauseVersion.objects.filter(clause=clause).order_by('version_number')

            # Determine original and current text
            if versions.exists():
                original_text = versions.first().original_text or clause.extracted_text or ""
                current_text = versions.last().modified_text or clause.extracted_text or ""

                # Collect all version texts for volatility calculation
                version_texts = []
                if versions.first().original_text:
                    version_texts.append(versions.first().original_text)
                for v in versions:
                    if v.modified_text:
                        version_texts.append(v.modified_text)
            else:
                # No versions - use extracted text as both
                original_text = clause.extracted_text or ""
                current_text = clause.extracted_text or ""
                version_texts = [original_text] if original_text else []

            # Calculate metrics
            drift_prob = drift_service.predict_drift(original_text, current_text)

            volatility = drift_service.calculate_volatility_index(version_texts) if len(version_texts) >= 2 else 0.0

            historical_deviation_pct = drift_service.calculate_historical_deviation(original_text, current_text)

            counterparty_bias = drift_service.estimate_counterparty_bias(version_texts)

            # Predict future clause evolution
            predicted_text = drift_service.predict_future_clause(
                current_text,
                clause_type=clause.clause_name,
                context=f"Contract: {clause.contract.original_filename}"
            )

            # Check if this is a pristine clause (no modifications)
            is_pristine = not versions.exists() or (original_text == current_text)

            # For demo purposes: if pristine and no real drift, show simulated risk
            # based on clause type (you can remove this in production)
            simulated_drift = 0.0
            if is_pristine and clause.risk_score:
                # Simulate potential drift based on risk score
                # High-risk clauses are more likely to drift during negotiation
                simulated_drift = min(0.85, clause.risk_score * 0.7)

            display_drift = drift_prob if not is_pristine else simulated_drift

            return Response({
                "clause_id": str(clause.id),
                "clause_name": clause.clause_name,
                "clause_type": clause.clause_type or "Unknown",

                # Texts
                "original_text": original_text[:1000],  # Truncate for display
                "current_text": current_text[:1000],
                "predicted_text": predicted_text[:1000] if predicted_text else "Prediction unavailable",

                # Metrics
                "drift_probability": display_drift,
                "volatility_index": volatility,
                "historical_deviation_pct": historical_deviation_pct if not is_pristine else 0,
                "counterparty_bias": counterparty_bias,

                # Meta
                "version_count": versions.count(),
                "risk_score": clause.risk_score,
                "risk_level": clause.risk_level,
                "is_pristine": is_pristine,
                "message": "This clause has no modification history. Drift metrics show potential negotiation risk." if is_pristine else None
            })

        except Exception as e:
            logger.error(f"Error fetching clause drift: {e}")
            return Response(
                {"error": "Failed to analyze clause drift", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContractClauseDriftSummaryView(APIView):
    """
    GET /api/contracts/<contract_id>/clause-drift-summary

    Returns drift summary for all clauses in a contract.
    Useful for showing which clauses are drifting most.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, contract_id):
        try:
            clauses = Clause.objects.filter(contract_id=contract_id)
            drift_service = get_drift_predictor()

            drift_summary = []

            for clause in clauses:
                versions = ClauseVersion.objects.filter(clause=clause).order_by('version_number')

                if versions.exists():
                    original_text = versions.first().original_text or clause.extracted_text or ""
                    current_text = versions.last().modified_text or clause.extracted_text or ""
                else:
                    original_text = clause.extracted_text or ""
                    current_text = clause.extracted_text or ""

                drift_prob = drift_service.predict_drift(original_text, current_text)

                drift_summary.append({
                    "clause_id": str(clause.id),
                    "clause_name": clause.clause_name,
                    "drift_probability": drift_prob,
                    "risk_level": clause.risk_level,
                    "version_count": versions.count()
                })

            # Sort by drift probability (highest first)
            drift_summary.sort(key=lambda x: x['drift_probability'], reverse=True)

            return Response({
                "contract_id": str(contract_id),
                "total_clauses": len(drift_summary),
                "high_drift_clauses": len([c for c in drift_summary if c['drift_probability'] > 0.7]),
                "clauses": drift_summary
            })

        except Exception as e:
            logger.error(f"Error fetching contract drift summary: {e}")
            return Response(
                {"error": "Failed to analyze contract drift", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClauseDriftHistoryView(APIView):
    """
    GET /api/clauses/<clause_id>/drift-history

    Returns version-to-version drift progression.
    Shows how clause evolved over time.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, clause_id):
        try:
            clause = get_object_or_404(Clause, id=clause_id)
            versions = ClauseVersion.objects.filter(clause=clause).order_by('version_number')

            if not versions.exists():
                return Response({
                    "clause_id": str(clause_id),
                    "clause_name": clause.clause_name,
                    "history": [],
                    "message": "No version history available"
                })

            drift_service = get_drift_predictor()
            history = []

            # Get base text (original)
            base_text = versions.first().original_text or clause.extracted_text or ""

            for i, version in enumerate(versions):
                # Calculate drift from base
                current_text = version.modified_text or base_text
                drift_from_base = drift_service.predict_drift(base_text, current_text)

                # Calculate drift from previous version
                if i > 0:
                    prev_version = versions[i-1]
                    prev_text = prev_version.modified_text or base_text
                    drift_from_prev = drift_service.predict_drift(prev_text, current_text)
                else:
                    drift_from_prev = 0.0

                history.append({
                    "version_number": version.version_number,
                    "modified_at": version.modified_at.isoformat(),
                    "modified_by": version.modified_by.email if hasattr(version.modified_by, 'email') else "Unknown",
                    "drift_from_original": drift_from_base,
                    "drift_from_previous": drift_from_prev,
                    "text_preview": current_text[:200] + "..." if len(current_text) > 200 else current_text,
                    "new_risk_score": version.new_risk_score,
                    "new_risk_level": version.new_risk_level
                })

            return Response({
                "clause_id": str(clause_id),
                "clause_name": clause.clause_name,
                "total_versions": len(history),
                "history": history
            })

        except Exception as e:
            logger.error(f"Error fetching drift history: {e}")
            return Response(
                {"error": "Failed to fetch drift history", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CrossContractDriftView(APIView):
    """
    GET /api/clause-library/drift/summary/
    Cross-contract drift summary: compares all clause types across contracts.
    Identifies which clause types drift the most from your standard templates.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from .clause_drift_detection import get_drift_detector
            detector = get_drift_detector()
            summary = detector.get_drift_summary(user=request.user)
            return Response({
                'summary': summary,
                'total_types': len(summary),
                'critical_types': [s for s in summary if s['status'] == 'critical'],
            })
        except Exception as e:
            logger.error(f"Cross-contract drift summary failed: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DriftByTypeView(APIView):
    """
    GET /api/clause-library/drift/type/?clause_type=<type>
    Detailed drift for all clauses of a given type vs standard template.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        clause_type = request.query_params.get('clause_type', '').strip()
        if not clause_type:
            return Response({'error': 'clause_type query param required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from .clause_drift_detection import get_drift_detector
            detector = get_drift_detector()
            result = detector.compute_drift_for_type(clause_type, user=request.user)
            return Response(result)
        except Exception as e:
            logger.error(f"Drift by type failed: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DriftTimelineView(APIView):
    """
    GET /api/clause-library/drift/timeline/?clause_type=<type>
    Drift score over time (per contract creation date).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        clause_type = request.query_params.get('clause_type', '').strip()
        if not clause_type:
            return Response({'error': 'clause_type query param required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from .clause_drift_detection import get_drift_detector
            detector = get_drift_detector()
            timeline = detector.get_drift_timeline(clause_type, user=request.user)
            return Response({'clause_type': clause_type, 'timeline': timeline})
        except Exception as e:
            logger.error(f"Drift timeline failed: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DriftMatrixView(APIView):
    """
    GET /api/clause-library/drift/matrix/<clause_type>/
    Cross-contract similarity matrix for a clause type.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        clause_type = request.query_params.get('clause_type', '').strip()
        if not clause_type:
            return Response({'error': 'clause_type query param required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from .clause_drift_detection import get_drift_detector
            max_contracts = int(request.query_params.get('max', 10))
            detector = get_drift_detector()
            matrix = detector.get_cross_contract_matrix(
                clause_type, user=request.user, max_contracts=max_contracts
            )
            return Response(matrix)
        except Exception as e:
            logger.error(f"Drift matrix failed: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
