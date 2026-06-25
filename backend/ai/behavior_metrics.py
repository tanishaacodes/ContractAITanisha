"""
Counterparty Behavior Metrics Engine
Analyzes historical negotiation patterns to profile counterparty behavior
"""
import numpy as np
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


def compute_behavior_metrics(negotiation_history_qs):
    """
    Compute comprehensive behavior metrics from negotiation history

    Args:
        negotiation_history_qs: Django QuerySet of NegotiationHistory objects

    Returns:
        dict: {
            "acceptance_rate": float,
            "avg_redlines": float,
            "stall_rate": float,
            "aggressiveness": float,
            "elasticity": float,
            "total_negotiations": int
        }
    """
    if not negotiation_history_qs.exists():
        return None

    # Collect metrics
    acceptance = []
    redlines = []
    stalled = []

    for record in negotiation_history_qs:
        acceptance.append(1 if record.accepted else 0)
        redlines.append(record.redline_rounds)
        stalled.append(1 if record.stalled else 0)

    # Calculate core metrics
    acceptance_rate = np.mean(acceptance)
    avg_redlines = np.mean(redlines)
    stall_rate = np.mean(stalled)

    # Derived metrics
    # Aggressiveness: inverse of acceptance rate
    aggressiveness = round(1 - acceptance_rate, 2)

    # Elasticity: willingness to accept after redlines
    # Higher elasticity = more flexible despite initial resistance
    elasticity = round(acceptance_rate / (avg_redlines + 1), 2)

    return {
        "acceptance_rate": round(float(acceptance_rate), 2),
        "avg_redlines": round(float(avg_redlines), 1),
        "stall_rate": round(float(stall_rate), 2),
        "aggressiveness": aggressiveness,
        "elasticity": elasticity,
        "total_negotiations": len(acceptance)
    }


def clause_acceptance_matrix(negotiation_history_qs):
    """
    Generate clause-type acceptance matrix for a counterparty

    Args:
        negotiation_history_qs: Django QuerySet of NegotiationHistory objects

    Returns:
        dict: {clause_type: acceptance_rate}
    """
    if not negotiation_history_qs.exists():
        return {}

    matrix = defaultdict(lambda: {"accepted": 0, "total": 0})

    for record in negotiation_history_qs:
        clause_type = record.clause_type
        matrix[clause_type]["total"] += 1
        if record.accepted:
            matrix[clause_type]["accepted"] += 1

    # Calculate acceptance rates
    result = {}
    for clause_type, stats in matrix.items():
        if stats["total"] > 0:
            result[clause_type] = round(stats["accepted"] / stats["total"], 2)
        else:
            result[clause_type] = 0.0

    return result


def identify_stall_clauses(negotiation_history_qs, stall_threshold=0.6):
    """
    Identify clause types that frequently cause stalls

    Args:
        negotiation_history_qs: Django QuerySet of NegotiationHistory objects
        stall_threshold: Stall rate above this is considered problematic

    Returns:
        List of dicts with clause_type and stall_rate
    """
    if not negotiation_history_qs.exists():
        return []

    stall_stats = defaultdict(lambda: {"stalled": 0, "total": 0})

    for record in negotiation_history_qs:
        clause_type = record.clause_type
        stall_stats[clause_type]["total"] += 1
        if record.stalled:
            stall_stats[clause_type]["stalled"] += 1

    # Calculate stall rates
    stall_clauses = []
    for clause_type, stats in stall_stats.items():
        if stats["total"] >= 2:  # Only consider if at least 2 negotiations
            stall_rate = stats["stalled"] / stats["total"]
            if stall_rate >= stall_threshold:
                stall_clauses.append({
                    "clause_type": clause_type,
                    "stall_rate": round(stall_rate, 2),
                    "occurrences": stats["total"]
                })

    # Sort by stall rate descending
    stall_clauses.sort(key=lambda x: x["stall_rate"], reverse=True)

    return stall_clauses


def calculate_negotiation_style(behavior_metrics):
    """
    Determine negotiation style from behavior metrics

    Args:
        behavior_metrics: Dict from compute_behavior_metrics

    Returns:
        dict: {
            "style": str (e.g., "Aggressive", "Balanced", "Flexible"),
            "description": str
        }
    """
    if not behavior_metrics:
        return {
            "style": "Unknown",
            "description": "Insufficient data to determine negotiation style"
        }

    aggressiveness = behavior_metrics.get("aggressiveness", 0.5)
    elasticity = behavior_metrics.get("elasticity", 0.5)
    stall_rate = behavior_metrics.get("stall_rate", 0.3)

    # Classify based on metrics
    if aggressiveness > 0.7 and stall_rate > 0.4:
        style = "Highly Aggressive"
        description = "Frequently rejects clauses and causes deal stalls. Expect extended negotiations."

    elif aggressiveness > 0.55 and elasticity < 0.15:
        style = "Aggressive"
        description = "Resistant to initial proposals with low flexibility. Escalation may be required."

    elif aggressiveness > 0.4 and elasticity > 0.25:
        style = "Firm but Fair"
        description = "Negotiates firmly but willing to compromise. Standard redline process expected."

    elif aggressiveness < 0.3 and elasticity > 0.35:
        style = "Flexible"
        description = "Generally accepting of standard terms with minor redlines."

    else:
        style = "Balanced"
        description = "Shows typical negotiation patterns. Moderate redlines expected."

    return {
        "style": style,
        "description": description
    }


def compare_counterparties(counterparty_metrics_list):
    """
    Compare multiple counterparties

    Args:
        counterparty_metrics_list: List of dicts with 'name' and 'metrics'

    Returns:
        dict: Comparative analysis with rankings
    """
    if not counterparty_metrics_list:
        return {}

    # Rank by aggressiveness
    aggressive_ranking = sorted(
        counterparty_metrics_list,
        key=lambda x: x['metrics'].get('aggressiveness', 0),
        reverse=True
    )

    # Rank by flexibility (elasticity)
    flexible_ranking = sorted(
        counterparty_metrics_list,
        key=lambda x: x['metrics'].get('elasticity', 0),
        reverse=True
    )

    # Rank by stall risk
    stall_risk_ranking = sorted(
        counterparty_metrics_list,
        key=lambda x: x['metrics'].get('stall_rate', 0),
        reverse=True
    )

    return {
        "most_aggressive": [x['name'] for x in aggressive_ranking[:3]],
        "most_flexible": [x['name'] for x in flexible_ranking[:3]],
        "highest_stall_risk": [x['name'] for x in stall_risk_ranking[:3]],
        "total_compared": len(counterparty_metrics_list)
    }


def trend_analysis(snapshots_qs):
    """
    Analyze trends in counterparty behavior over time

    Args:
        snapshots_qs: Django QuerySet of CounterpartyBehaviorSnapshot objects

    Returns:
        dict: Trend indicators
    """
    if not snapshots_qs.exists() or snapshots_qs.count() < 2:
        return {
            "trend": "STABLE",
            "description": "Insufficient data for trend analysis"
        }

    # Order by date
    snapshots = list(snapshots_qs.order_by('snapshot_date'))

    # Compare first half vs second half
    mid_point = len(snapshots) // 2
    first_half = snapshots[:mid_point]
    second_half = snapshots[mid_point:]

    avg_aggress_first = np.mean([s.aggressiveness_score for s in first_half])
    avg_aggress_second = np.mean([s.aggressiveness_score for s in second_half])

    change = avg_aggress_second - avg_aggress_first

    if change > 0.15:
        trend = "GETTING_TOUGHER"
        description = "Counterparty is becoming more aggressive in negotiations"
    elif change < -0.15:
        trend = "GETTING_SOFTER"
        description = "Counterparty is becoming more flexible in negotiations"
    else:
        trend = "STABLE"
        description = "Negotiation behavior remains consistent"

    return {
        "trend": trend,
        "description": description,
        "change": round(float(change), 2)
    }
