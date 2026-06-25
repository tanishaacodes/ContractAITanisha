"""
API Views for Autonomous Contract Drift Detection.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import logging

from .engine import (
    detect_drift,
    analyze_drift_patterns,
    get_user_drifts,
    update_drift_status,
    get_unread_alerts,
    batch_detect_drift_from_logs
)
from .models import ContractDrift, DriftAlert, BehaviorLog
from django.utils import timezone

logger = logging.getLogger(__name__)


class DriftDetectionAPIView(APIView):
    """
    API endpoint for detecting contract drift.

    POST /api/drift/detect/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Detect drift between contract terms and observed behavior.

        Request body:
        {
            "contract_id": "CONTRACT_001",
            "contract_terms": "Original contract terms...",
            "observed_behavior": "Actual behavior observed...",
            "behavior_context": {  // optional
                "source": "support_ticket",
                "ticket_id": "TICKET-123",
                "date": "2025-01-10"
            },
            "data_source": "support"  // optional: crm, billing, support, email, slack, manual
        }
        """
        try:
            data = request.data

            # Validate required fields
            required_fields = ['contract_id', 'contract_terms', 'observed_behavior']
            for field in required_fields:
                if field not in data:
                    return Response(
                        {"error": f"Missing required field: {field}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Run drift detection
            logger.info(f"Running drift detection for user {request.user.email}")
            result = detect_drift(
                contract_id=data['contract_id'],
                contract_terms=data['contract_terms'],
                observed_behavior=data['observed_behavior'],
                user=request.user,
                behavior_context=data.get('behavior_context'),
                data_source=data.get('data_source', 'manual')
            )

            if 'error' in result:
                return Response(
                    {"error": result['error']},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in drift detection: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DriftAnalysisAPIView(APIView):
    """
    API endpoint for analyzing drift patterns over time.

    GET /api/drift/analysis/?contract_id=CONTRACT_001&lookback_days=90
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Analyze drift patterns for a contract.

        Query params:
        - contract_id (required): Contract to analyze
        - lookback_days (optional): Days to look back (default: 90)
        """
        try:
            contract_id = request.query_params.get('contract_id')
            if not contract_id:
                return Response(
                    {"error": "contract_id parameter is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            lookback_days = int(request.query_params.get('lookback_days', 90))

            result = analyze_drift_patterns(
                contract_id=contract_id,
                user=request.user,
                lookback_days=lookback_days
            )

            if 'error' in result:
                return Response(
                    {"error": result['error']},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error analyzing drift patterns: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DriftListAPIView(APIView):
    """
    API endpoint for retrieving drift records.

    GET /api/drift/list/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get drift records with optional filters.

        Query params:
        - contract_id (optional): Filter by contract
        - status (optional): Filter by status (detected, acknowledged, resolved, etc.)
        - min_severity (optional): Minimum severity (1-10)
        - limit (optional): Maximum number of results (default: 20)
        """
        try:
            contract_id = request.query_params.get('contract_id') or None
            status_filter = request.query_params.get('status') or None
            min_severity = request.query_params.get('min_severity')
            limit = int(request.query_params.get('limit', 20))

            # Convert min_severity to int or None
            if min_severity and min_severity.strip():
                min_severity = int(min_severity)
            else:
                min_severity = None

            drifts = get_user_drifts(
                user=request.user,
                contract_id=contract_id,
                status=status_filter,
                min_severity=min_severity,
                limit=limit
            )

            return Response(
                {
                    "count": len(drifts),
                    "drifts": drifts
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error retrieving drift list: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DriftDetailAPIView(APIView):
    """
    API endpoint for retrieving detailed information about a specific drift.

    GET /api/drift/<drift_id>/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, drift_id):
        """
        Get detailed information about a drift record.
        """
        try:
            drift = ContractDrift.objects.get(id=drift_id, user=request.user)

            # Get associated behavior logs
            behavior_logs = drift.behavior_logs.all()[:10]

            result = {
                "id": drift.id,
                "contract_id": drift.contract_id,
                "drift_type": drift.drift_type,
                "contract_terms": drift.contract_terms,
                "detected_behavior": drift.detected_behavior,
                "behavior_context": drift.behavior_context,
                "legal_risk": drift.legal_risk,
                "business_impact": drift.business_impact,
                "severity": drift.severity,
                "status": drift.status,
                "legal_doctrines": drift.legal_doctrines,
                "remediation_recommendations": drift.remediation_recommendations,
                "remediation_taken": drift.remediation_taken,
                "detected_at": drift.detected_at.isoformat(),
                "acknowledged_at": drift.acknowledged_at.isoformat() if drift.acknowledged_at else None,
                "resolved_at": drift.resolved_at.isoformat() if drift.resolved_at else None,
                "updated_at": drift.updated_at.isoformat(),
                "drift_duration_days": drift.drift_duration_days,
                "frequency_count": drift.frequency_count,
                "behavior_logs": [
                    {
                        "id": log.id,
                        "data_source": log.data_source,
                        "behavior_description": log.behavior_description,
                        "behavior_date": log.behavior_date.isoformat(),
                    }
                    for log in behavior_logs
                ]
            }

            return Response(result, status=status.HTTP_200_OK)

        except ContractDrift.DoesNotExist:
            return Response(
                {"error": "Drift not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error retrieving drift details: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DriftUpdateStatusAPIView(APIView):
    """
    API endpoint for updating drift status.

    PUT /api/drift/<drift_id>/status/
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, drift_id):
        """
        Update the status of a drift record.

        Request body:
        {
            "status": "acknowledged",  // detected, acknowledged, remediation_planned, remediation_in_progress, resolved, accepted
            "remediation_taken": "Sent amendment to customer for signature"  // optional
        }
        """
        try:
            data = request.data

            if 'status' not in data:
                return Response(
                    {"error": "Missing required field: status"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            result = update_drift_status(
                drift_id=drift_id,
                user=request.user,
                new_status=data['status'],
                remediation_taken=data.get('remediation_taken')
            )

            if not result.get('success'):
                return Response(
                    {"error": result.get('error')},
                    status=status.HTTP_404_NOT_FOUND if 'not found' in result.get('error', '') else status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error updating drift status: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DriftAlertsAPIView(APIView):
    """
    API endpoint for managing drift alerts.

    GET /api/drift/alerts/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get unread drift alerts for the user.

        Query params:
        - limit (optional): Maximum number of alerts (default: 10)
        """
        try:
            limit = int(request.query_params.get('limit', 10))

            alerts = get_unread_alerts(user=request.user, limit=limit)

            return Response(
                {
                    "count": len(alerts),
                    "alerts": alerts
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error retrieving alerts: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DriftAlertMarkReadAPIView(APIView):
    """
    API endpoint for marking alerts as read.

    PUT /api/drift/alerts/<alert_id>/read/
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, alert_id):
        """
        Mark an alert as read.
        """
        try:
            alert = DriftAlert.objects.get(
                id=alert_id,
                drift__user=request.user
            )

            alert.is_read = True
            alert.read_at = timezone.now()
            alert.save()

            return Response(
                {
                    "success": True,
                    "alert_id": alert_id,
                    "read_at": alert.read_at.isoformat()
                },
                status=status.HTTP_200_OK
            )

        except DriftAlert.DoesNotExist:
            return Response(
                {"error": "Alert not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error marking alert as read: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DriftBatchDetectionAPIView(APIView):
    """
    API endpoint for batch drift detection from behavior logs.

    POST /api/drift/batch-detect/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Batch process behavior logs to detect drift.

        Request body:
        {
            "contract_id": "CONTRACT_001",
            "behavior_logs": [
                {
                    "description": "Customer granted extended payment terms",
                    "date": "2025-01-10",
                    "source": "crm",
                    "raw_data": {"ticket_id": "123"}
                },
                ...
            ]
        }
        """
        try:
            data = request.data

            if 'contract_id' not in data or 'behavior_logs' not in data:
                return Response(
                    {"error": "Missing required fields: contract_id and behavior_logs"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not isinstance(data['behavior_logs'], list):
                return Response(
                    {"error": "behavior_logs must be a list"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            result = batch_detect_drift_from_logs(
                contract_id=data['contract_id'],
                user=request.user,
                behavior_logs=data['behavior_logs']
            )

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in batch drift detection: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DriftDashboardAPIView(APIView):
    """
    API endpoint for drift detection dashboard summary.

    GET /api/drift/dashboard/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get dashboard summary of drift detection metrics.
        """
        try:
            # Get counts by status
            total_drifts = ContractDrift.objects.filter(user=request.user).count()
            critical_drifts = ContractDrift.objects.filter(
                user=request.user,
                severity__gte=7,
                status__in=['detected', 'acknowledged']
            ).count()

            unread_alerts_count = DriftAlert.objects.filter(
                drift__user=request.user,
                is_read=False,
                is_dismissed=False
            ).count()

            # Get recent high-severity drifts
            recent_critical = ContractDrift.objects.filter(
                user=request.user,
                severity__gte=7
            ).order_by('-detected_at')[:5]

            result = {
                "total_drifts": total_drifts,
                "critical_unresolved": critical_drifts,
                "unread_alerts": unread_alerts_count,
                "recent_critical_drifts": [
                    {
                        "id": d.id,
                        "contract_id": d.contract_id,
                        "drift_type": d.drift_type,
                        "severity": d.severity,
                        "status": d.status,
                        "detected_at": d.detected_at.isoformat()
                    }
                    for d in recent_critical
                ]
            }

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
