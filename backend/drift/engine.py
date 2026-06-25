"""
Drift Detection Engine - Autonomous detection of contract-reality divergence.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .models import ContractDrift, BehaviorLog, DriftAlert
from counterfactual.llm_client import get_llm_client
from django.utils import timezone

logger = logging.getLogger(__name__)


def detect_drift(
    contract_id: str,
    contract_terms: str,
    observed_behavior: str,
    user,
    behavior_context: Optional[Dict] = None,
    data_source: str = 'manual'
) -> Dict:
    """
    Detect drift between contract terms and observed behavior.

    Args:
        contract_id: Contract identifier
        contract_terms: Original contract terms
        observed_behavior: Description of actual behavior observed
        user: Django User object
        behavior_context: Additional context (CRM data, support tickets, etc.)
        data_source: Source of the behavior data

    Returns:
        Dict containing drift analysis and saved drift object
    """
    logger.info(f"Detecting drift for contract {contract_id}")

    try:
        # Step 1: Use LLM to assess drift
        llm_client = get_llm_client()
        drift_analysis = llm_client.assess_contract_drift(
            contract_terms=contract_terms,
            observed_behavior=observed_behavior,
            behavior_context=behavior_context
        )

        logger.info(f"Drift analysis completed. Severity: {drift_analysis.get('severity')}")

        # Step 2: Extract drift types
        drift_types = drift_analysis.get('drift_types', ['general_drift'])
        primary_drift_type = drift_types[0] if drift_types else 'general_drift'

        # Step 3: Save drift record
        drift = ContractDrift.objects.create(
            contract_id=contract_id,
            user=user,
            drift_type=primary_drift_type,
            contract_terms=contract_terms,
            detected_behavior=observed_behavior,
            behavior_context=behavior_context or {},
            legal_risk=drift_analysis.get('legal_risk', ''),
            business_impact=drift_analysis.get('business_impact', ''),
            severity=drift_analysis.get('severity', 5),
            legal_doctrines=drift_types,
            remediation_recommendations=drift_analysis.get('remediation', ''),
        )

        logger.info(f"Created drift record {drift.id}")

        # Step 4: Create behavior log
        behavior_log = BehaviorLog.objects.create(
            contract_id=contract_id,
            drift=drift,
            data_source=data_source,
            behavior_description=observed_behavior,
            behavior_date=timezone.now().date(),
            raw_data=behavior_context or {}
        )

        # Step 5: Create alerts for high-severity drift
        if drift.severity >= 7:
            _create_drift_alert(
                drift=drift,
                alert_type='critical_severity',
                message=f"Critical drift detected (Severity: {drift.severity})"
            )

        # Step 6: Format response
        result = {
            "drift_id": drift.id,
            "contract_id": contract_id,
            "drift_type": primary_drift_type,
            "severity": drift.severity,
            "analysis": drift_analysis,
            "status": drift.status,
            "detected_at": drift.detected_at.isoformat(),
            "behavior_log_id": behavior_log.id
        }

        return result

    except Exception as e:
        logger.error(f"Error detecting drift: {e}")
        return {
            "error": str(e),
            "contract_id": contract_id,
            "status": "failed"
        }


def analyze_drift_patterns(contract_id: str, user, lookback_days: int = 90) -> Dict:
    """
    Analyze drift patterns over time for a contract.

    Args:
        contract_id: Contract identifier
        user: Django User object
        lookback_days: Number of days to look back

    Returns:
        Dict containing drift pattern analysis
    """
    logger.info(f"Analyzing drift patterns for contract {contract_id}")

    try:
        # Get all drift records for this contract
        since_date = timezone.now() - timedelta(days=lookback_days)
        drifts = ContractDrift.objects.filter(
            contract_id=contract_id,
            user=user,
            detected_at__gte=since_date
        ).order_by('-detected_at')

        if not drifts.exists():
            return {
                "contract_id": contract_id,
                "drift_count": 0,
                "message": "No drift detected in the specified period"
            }

        # Calculate statistics
        drift_count = drifts.count()
        avg_severity = sum(d.severity for d in drifts) / drift_count
        drift_types_distribution = {}
        status_distribution = {}

        for drift in drifts:
            drift_types_distribution[drift.drift_type] = drift_types_distribution.get(drift.drift_type, 0) + 1
            status_distribution[drift.status] = status_distribution.get(drift.status, 0) + 1

        # Identify trends
        recent_drifts = drifts[:30]  # Last 30 records
        trend = _calculate_drift_trend(recent_drifts)

        # Get most critical unresolved drift
        critical_drifts = drifts.filter(
            severity__gte=7,
            status__in=['detected', 'acknowledged']
        ).order_by('-severity')[:5]

        result = {
            "contract_id": contract_id,
            "analysis_period_days": lookback_days,
            "total_drift_count": drift_count,
            "average_severity": round(avg_severity, 2),
            "drift_types_distribution": drift_types_distribution,
            "status_distribution": status_distribution,
            "trend": trend,
            "critical_unresolved": [
                {
                    "id": d.id,
                    "drift_type": d.drift_type,
                    "severity": d.severity,
                    "detected_at": d.detected_at.isoformat()
                }
                for d in critical_drifts
            ]
        }

        return result

    except Exception as e:
        logger.error(f"Error analyzing drift patterns: {e}")
        return {
            "error": str(e),
            "contract_id": contract_id
        }


def get_user_drifts(
    user,
    contract_id: Optional[str] = None,
    status: Optional[str] = None,
    min_severity: Optional[int] = None,
    limit: int = 20
) -> List[Dict]:
    """
    Get drift records for a user with optional filters.

    Args:
        user: Django User object
        contract_id: Optional contract ID filter
        status: Optional status filter
        min_severity: Optional minimum severity filter
        limit: Maximum number of results

    Returns:
        List of drift dicts
    """
    try:
        queryset = ContractDrift.objects.filter(user=user).order_by('-detected_at')

        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)

        if status:
            queryset = queryset.filter(status=status)

        if min_severity is not None:
            queryset = queryset.filter(severity__gte=min_severity)

        drifts = queryset[:limit]

        return [
            {
                "id": d.id,
                "contract_id": d.contract_id,
                "drift_type": d.drift_type,
                "severity": d.severity,
                "status": d.status,
                "detected_behavior": d.detected_behavior[:200] + "..." if len(d.detected_behavior) > 200 else d.detected_behavior,
                "detected_at": d.detected_at.isoformat(),
                "updated_at": d.updated_at.isoformat(),
            }
            for d in drifts
        ]

    except Exception as e:
        logger.error(f"Error retrieving user drifts: {e}")
        return []


def update_drift_status(drift_id: int, user, new_status: str, remediation_taken: Optional[str] = None) -> Dict:
    """
    Update the status of a drift record.

    Args:
        drift_id: Drift record ID
        user: Django User object
        new_status: New status value
        remediation_taken: Optional description of remediation actions

    Returns:
        Dict with update result
    """
    try:
        drift = ContractDrift.objects.get(id=drift_id, user=user)

        old_status = drift.status
        drift.status = new_status

        if new_status == 'acknowledged' and not drift.acknowledged_at:
            drift.acknowledged_at = timezone.now()

        if new_status == 'resolved' and not drift.resolved_at:
            drift.resolved_at = timezone.now()

        if remediation_taken:
            drift.remediation_taken = remediation_taken

        drift.save()

        logger.info(f"Updated drift {drift_id} status from {old_status} to {new_status}")

        return {
            "success": True,
            "drift_id": drift_id,
            "old_status": old_status,
            "new_status": new_status,
            "updated_at": drift.updated_at.isoformat()
        }

    except ContractDrift.DoesNotExist:
        return {
            "success": False,
            "error": "Drift not found"
        }
    except Exception as e:
        logger.error(f"Error updating drift status: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def get_unread_alerts(user, limit: int = 10) -> List[Dict]:
    """
    Get unread drift alerts for a user.

    Args:
        user: Django User object
        limit: Maximum number of alerts to return

    Returns:
        List of alert dicts
    """
    try:
        alerts = DriftAlert.objects.filter(
            drift__user=user,
            is_read=False,
            is_dismissed=False
        ).select_related('drift')[:limit]

        return [
            {
                "id": a.id,
                "drift_id": a.drift.id,
                "contract_id": a.drift.contract_id,
                "alert_type": a.alert_type,
                "alert_message": a.alert_message,
                "severity": a.drift.severity,
                "created_at": a.created_at.isoformat()
            }
            for a in alerts
        ]

    except Exception as e:
        logger.error(f"Error retrieving unread alerts: {e}")
        return []


def _create_drift_alert(drift: ContractDrift, alert_type: str, message: str):
    """
    Create a drift alert.

    Args:
        drift: ContractDrift instance
        alert_type: Type of alert
        message: Alert message
    """
    try:
        alert = DriftAlert.objects.create(
            drift=drift,
            alert_type=alert_type,
            alert_message=message
        )
        logger.info(f"Created drift alert {alert.id} for drift {drift.id}")
        return alert
    except Exception as e:
        logger.error(f"Error creating drift alert: {e}")
        return None


def _calculate_drift_trend(drifts) -> str:
    """
    Calculate drift trend (increasing, stable, decreasing).

    Args:
        drifts: QuerySet of drift records

    Returns:
        str: 'increasing', 'stable', or 'decreasing'
    """
    if drifts.count() < 5:
        return 'insufficient_data'

    # Split into first half and second half
    drift_list = list(drifts)
    mid_point = len(drift_list) // 2

    first_half_avg = sum(d.severity for d in drift_list[:mid_point]) / mid_point
    second_half_avg = sum(d.severity for d in drift_list[mid_point:]) / (len(drift_list) - mid_point)

    if second_half_avg > first_half_avg + 1:
        return 'increasing'
    elif second_half_avg < first_half_avg - 1:
        return 'decreasing'
    else:
        return 'stable'


def batch_detect_drift_from_logs(contract_id: str, user, behavior_logs: List[Dict]) -> Dict:
    """
    Batch process behavior logs to detect drift patterns.

    Args:
        contract_id: Contract identifier
        user: Django User object
        behavior_logs: List of behavior log dicts with 'description', 'date', 'source', etc.

    Returns:
        Dict with batch processing results
    """
    logger.info(f"Batch processing {len(behavior_logs)} behavior logs for contract {contract_id}")

    results = {
        "contract_id": contract_id,
        "total_logs": len(behavior_logs),
        "drifts_detected": 0,
        "high_severity_count": 0,
        "drift_ids": []
    }

    try:
        for log_data in behavior_logs:
            # Create behavior log
            behavior_log = BehaviorLog.objects.create(
                contract_id=contract_id,
                data_source=log_data.get('source', 'manual'),
                behavior_description=log_data.get('description', ''),
                behavior_date=log_data.get('date', timezone.now().date()),
                raw_data=log_data.get('raw_data', {})
            )

            logger.debug(f"Created behavior log {behavior_log.id}")

        # Aggregate behavior patterns and detect drift
        # This is a simplified version - in production, you'd analyze patterns across all logs
        aggregated_behavior = "\n".join([log.get('description', '') for log in behavior_logs[:5]])

        # Detect drift based on aggregated behavior
        # You would get contract terms from your contract storage
        # For now, this is a placeholder
        logger.info("Aggregated behavior analysis completed")

        results['status'] = 'completed'
        return results

    except Exception as e:
        logger.error(f"Error in batch drift detection: {e}")
        results['status'] = 'failed'
        results['error'] = str(e)
        return results
