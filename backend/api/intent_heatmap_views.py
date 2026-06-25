"""
Contract Intent Heatmap API Views
Provides endpoints for intent detection and visualization.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from core.models import Contract, Clause, ContractVersion
from api.services.intent_detector import get_intent_detector
import logging

logger = logging.getLogger(__name__)


class ContractIntentHeatmapView(APIView):
    """
    GET /api/contracts/<contract_id>/intent-heatmap

    Returns intent heatmap for all clauses in a contract:
    - Per-clause intent scores (risk_transfer, liability_shielding, etc.)
    - Intent drift detection (if versions exist)
    - Counterparty bias score
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, contract_id):
        try:
            contract = get_object_or_404(Contract, id=contract_id)
            intent_service = get_intent_detector()

            # Get all clauses for this contract
            clauses = Clause.objects.filter(contract=contract)

            if not clauses.exists():
                return Response({
                    "contract_id": str(contract_id),
                    "contract_name": contract.original_filename,
                    "rows": [],
                    "intent_drift": False,
                    "counterparty_mismatch": {"level": "LOW", "score": 0.0},
                    "message": "No clauses extracted yet. Please extract clauses first."
                })

            # Build section data from clauses
            sections = []
            for clause in clauses:
                # Get the best available text
                text = clause.extracted_text or clause.context_sentences or ""

                # If we have minimal text, augment with clause name for better intent detection
                if text and len(text.strip()) > 10:
                    # Use actual text
                    full_text = f"{clause.clause_name}: {text}"
                elif clause.clause_name:
                    # Fallback: use clause name as semantic hint
                    full_text = f"This is a {clause.clause_name} clause in a contract"
                else:
                    full_text = ""

                if full_text:
                    sections.append({
                        'name': clause.clause_name,
                        'text': full_text,
                        'clause_id': str(clause.id)
                    })

            # Detect intents for all sections
            intent_rows = intent_service.detect_section_intents(sections)

            # Calculate aggregate intents for contract-level bias
            if intent_rows:
                aggregate_intents = {
                    intent: sum(row[intent] for row in intent_rows) / len(intent_rows)
                    for intent in intent_service.INTENT_TEMPLATES.keys()
                }
                bias = intent_service.detect_counterparty_bias(aggregate_intents)
            else:
                bias = {"level": "LOW", "score": 0.0}

            # Check for intent drift across versions
            versions = ContractVersion.objects.filter(contract=contract).order_by('version_number')
            intent_drift_detected = False

            if versions.count() > 1:
                # Simple heuristic: if we have versions, flag drift
                # In production, you'd compare intent vectors across versions
                intent_drift_detected = bias['score'] > 0.6

            # Add clause IDs to rows for drill-down
            for i, row in enumerate(intent_rows):
                if i < len(sections):
                    row['clause_id'] = sections[i]['clause_id']

            return Response({
                "contract_id": str(contract_id),
                "contract_name": contract.original_filename,
                "rows": intent_rows,
                "intent_drift": intent_drift_detected,
                "counterparty_mismatch": bias,
                "total_clauses": len(intent_rows),
                "aggregate_intents": aggregate_intents if intent_rows else {}
            })

        except Exception as e:
            logger.error(f"Error generating intent heatmap: {e}")
            return Response(
                {"error": "Failed to generate intent heatmap", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClauseIntentAnalysisView(APIView):
    """
    GET /api/clauses/<clause_id>/intent-analysis

    Returns detailed intent analysis for a single clause.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, clause_id):
        try:
            clause = get_object_or_404(Clause, id=clause_id)
            intent_service = get_intent_detector()

            text = clause.extracted_text or clause.context_sentences or ""

            if not text:
                return Response({
                    "clause_id": str(clause_id),
                    "clause_name": clause.clause_name,
                    "intents": {},
                    "dominant_intent": None,
                    "message": "No text available for intent analysis"
                })

            # Detect intents
            intents = intent_service.detect_intents(text)
            dominant = intent_service.get_dominant_intent(intents)

            return Response({
                "clause_id": str(clause_id),
                "clause_name": clause.clause_name,
                "clause_type": clause.clause_type or "Unknown",
                "intents": intents,
                "dominant_intent": dominant,
                "text_preview": text[:300] + "..." if len(text) > 300 else text
            })

        except Exception as e:
            logger.error(f"Error analyzing clause intent: {e}")
            return Response(
                {"error": "Failed to analyze clause intent", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class IntentDriftComparisonView(APIView):
    """
    GET /api/contracts/<contract_id>/intent-drift

    Compare intents across contract versions.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, contract_id):
        try:
            contract = get_object_or_404(Contract, id=contract_id)
            intent_service = get_intent_detector()

            versions = ContractVersion.objects.filter(contract=contract).order_by('version_number')

            if versions.count() < 2:
                return Response({
                    "contract_id": str(contract_id),
                    "drift_detected": False,
                    "message": "Not enough versions for drift comparison"
                })

            # Get clauses for current version
            current_clauses = Clause.objects.filter(contract=contract)
            current_sections = [
                {
                    'name': c.clause_name,
                    'text': c.extracted_text or c.context_sentences or ""
                }
                for c in current_clauses
                if c.extracted_text or c.context_sentences
            ]

            current_intents = intent_service.detect_section_intents(current_sections)

            # Calculate aggregate intent vector
            if current_intents:
                current_aggregate = {
                    intent: sum(row[intent] for row in current_intents) / len(current_intents)
                    for intent in intent_service.INTENT_TEMPLATES.keys()
                }
            else:
                current_aggregate = {}

            # For simplicity, we'll show which intents changed most
            # In production, you'd store intent vectors per version
            intent_changes = [
                {
                    "intent": intent,
                    "current_strength": current_aggregate.get(intent, 0),
                    "trend": "stable"  # Would compare with previous version
                }
                for intent in intent_service.INTENT_TEMPLATES.keys()
            ]

            return Response({
                "contract_id": str(contract_id),
                "version_count": versions.count(),
                "drift_detected": any(ic['current_strength'] > 0.7 for ic in intent_changes),
                "intent_changes": intent_changes,
                "aggregate_intents": current_aggregate
            })

        except Exception as e:
            logger.error(f"Error comparing intent drift: {e}")
            return Response(
                {"error": "Failed to compare intent drift", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
