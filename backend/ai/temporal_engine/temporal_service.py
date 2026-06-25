"""
Temporal Clause Evolution Service

Main service for temporal analysis of clause performance over time.
"""
import numpy as np
from datetime import datetime


def calculate_usage_trend(usage_history):
    """
    Calculate usage trend using linear regression.

    Args:
        usage_history: List of (year, usage_count) tuples

    Returns:
        dict: Trend analysis
    """
    if not usage_history or len(usage_history) < 2:
        return {
            "trend": "STABLE",
            "slope": 0,
            "direction": "NEUTRAL"
        }

    years = [h[0] for h in usage_history]
    counts = [h[1] for h in usage_history]

    # Linear regression
    slope = np.polyfit(years, counts, 1)[0]

    if slope < -0.2:
        trend = "DECLINING"
        direction = "DOWN"
    elif slope > 0.2:
        trend = "GROWING"
        direction = "UP"
    else:
        trend = "STABLE"
        direction = "NEUTRAL"

    return {
        "trend": trend,
        "slope": float(slope),
        "direction": direction
    }


def calculate_risk_trend(risk_timeline):
    """
    Calculate risk score trend over time.

    Args:
        risk_timeline: List of (year, risk_score) tuples

    Returns:
        dict: Risk trend analysis
    """
    if not risk_timeline or len(risk_timeline) < 2:
        return {
            "trend": "STABLE",
            "slope": 0,
            "increasing": False
        }

    years = [r[0] for r in risk_timeline]
    scores = [r[1] for r in risk_timeline]

    # Linear regression
    slope = np.polyfit(years, scores, 1)[0]

    increasing = slope > 0.15

    if slope > 0.15:
        trend = "INCREASING"
    elif slope < -0.15:
        trend = "DECREASING"
    else:
        trend = "STABLE"

    return {
        "trend": trend,
        "slope": float(slope),
        "increasing": increasing
    }


def calculate_aging_score(usage_trend, risk_trend, trust_trend=None):
    """
    Calculate clause aging score.

    Aging happens when:
    - Usage declining
    - Risk increasing
    - Trust declining

    Args:
        usage_trend: Usage trend dict
        risk_trend: Risk trend dict
        trust_trend: Optional trust trend dict

    Returns:
        dict: Aging analysis
    """
    # Usage decline factor (0-1)
    usage_decline = max(0, -usage_trend["slope"])
    usage_factor = min(1.0, usage_decline / 5.0)  # Normalize

    # Risk increase factor (0-1)
    risk_increase = max(0, risk_trend["slope"])
    risk_factor = min(1.0, risk_increase / 0.5)  # Normalize

    # Trust decline factor (optional)
    if trust_trend:
        trust_decline = max(0, -trust_trend["slope"])
        trust_factor = min(1.0, trust_decline / 0.3)
    else:
        trust_factor = 0

    # Composite aging score
    if trust_trend:
        aging = (
            0.4 * usage_factor +
            0.3 * risk_factor +
            0.3 * trust_factor
        )
    else:
        aging = (
            0.6 * usage_factor +
            0.4 * risk_factor
        )

    # Classify aging level
    if aging > 0.75:
        level = "COMMERCIALLY_EXTINCT"
    elif aging > 0.5:
        level = "AGING"
    elif aging > 0.3:
        level = "DECLINING"
    else:
        level = "ACTIVE"

    return {
        "aging_score": round(aging, 3),
        "aging_level": level,
        "usage_decline_factor": round(usage_factor, 3),
        "risk_increase_factor": round(risk_factor, 3),
        "trust_decline_factor": round(trust_factor, 3) if trust_trend else None
    }


def detect_regulatory_drift(clause_id, legal_events, jurisdiction=None):
    """
    Detect if clause is affected by regulatory changes.

    Args:
        clause_id: Clause ID
        legal_events: List of LegalEvent objects
        jurisdiction: Optional jurisdiction filter

    Returns:
        dict: Regulatory drift analysis
    """
    if jurisdiction:
        events = [e for e in legal_events if e.jurisdiction == jurisdiction]
    else:
        events = legal_events

    if not events:
        return {
            "has_drift": False,
            "affected_events": []
        }

    # Events by severity
    critical = [e for e in events if e.impact_severity == "CRITICAL"]
    high = [e for e in events if e.impact_severity == "HIGH"]
    medium = [e for e in events if e.impact_severity == "MEDIUM"]

    has_drift = len(critical) > 0 or len(high) > 0

    return {
        "has_drift": has_drift,
        "total_events": len(events),
        "critical_count": len(critical),
        "high_count": len(high),
        "medium_count": len(medium),
        "affected_events": [
            {
                "year": e.year,
                "title": e.title,
                "severity": e.impact_severity,
                "type": e.event_type
            }
            for e in sorted(events, key=lambda x: (x.impact_severity == "CRITICAL", x.year), reverse=True)[:5]
        ]
    }


def analyze_temporal_evolution(clause_id, usage_history, risk_timeline, trust_timeline=None, legal_events=None):
    """
    Complete temporal evolution analysis for a clause.

    Args:
        clause_id: Clause ID
        usage_history: List of (year, usage_count, industry, geography) tuples
        risk_timeline: List of (year, risk_score) tuples
        trust_timeline: Optional list of (year, trust_score) tuples
        legal_events: Optional list of LegalEvent objects

    Returns:
        dict: Complete temporal analysis
    """
    current_year = datetime.now().year

    # 1. Usage trend
    usage_data = [(h[0], h[1]) for h in usage_history]
    usage_trend = calculate_usage_trend(usage_data)

    # 2. Risk trend
    risk_data = [(r[0], r[1]) for r in risk_timeline]
    risk_trend = calculate_risk_trend(risk_data)

    # 3. Trust trend (if available)
    if trust_timeline:
        trust_data = [(t[0], t[1]) for t in trust_timeline]
        trust_trend = calculate_risk_trend(trust_data)  # Same logic
    else:
        trust_trend = None

    # 4. Aging score
    aging = calculate_aging_score(usage_trend, risk_trend, trust_trend)

    # 5. Regulatory drift (if events provided)
    if legal_events:
        reg_drift = detect_regulatory_drift(clause_id, legal_events)
    else:
        reg_drift = {"has_drift": False, "total_events": 0}

    # 6. Industry adoption analysis
    if usage_history:
        industries = {}
        for year, count, industry, geo in usage_history:
            if industry:
                industries[industry] = industries.get(industry, 0) + count

        top_industries = sorted(industries.items(), key=lambda x: x[1], reverse=True)[:3]
    else:
        top_industries = []

    # 7. Calculate years in use
    if usage_history:
        first_year = min(h[0] for h in usage_history)
        years_in_use = current_year - first_year
    else:
        years_in_use = 0

    # 8. Recent performance
    recent_usage = [h[1] for h in sorted(usage_history, key=lambda x: x[0], reverse=True)[:3]]
    recent_risk = [r[1] for r in sorted(risk_timeline, key=lambda x: x[0], reverse=True)[:3]]

    return {
        "clause_id": clause_id,
        "current_year": current_year,
        "years_in_use": years_in_use,

        # Trends
        "usage_trend": usage_trend,
        "risk_trend": risk_trend,
        "trust_trend": trust_trend,

        # Aging
        "aging": aging,

        # Regulatory
        "regulatory_drift": reg_drift,

        # Industry
        "top_industries": top_industries,

        # Recent performance
        "recent_usage": recent_usage,
        "recent_risk": recent_risk,
        "recent_risk_avg": round(sum(recent_risk) / len(recent_risk), 3) if recent_risk else 0,

        # Historical data points
        "usage_history_count": len(usage_history),
        "risk_timeline_count": len(risk_timeline),
        "trust_timeline_count": len(trust_timeline) if trust_timeline else 0
    }


def recommend_temporal_action(temporal_analysis):
    """
    Recommend actions based on temporal analysis.

    Args:
        temporal_analysis: Temporal analysis dict

    Returns:
        list: Action recommendations
    """
    recommendations = []

    aging = temporal_analysis["aging"]
    usage_trend = temporal_analysis["usage_trend"]
    risk_trend = temporal_analysis["risk_trend"]
    reg_drift = temporal_analysis["regulatory_drift"]

    # Aging recommendations
    if aging["aging_level"] == "COMMERCIALLY_EXTINCT":
        recommendations.append({
            "priority": "CRITICAL",
            "action": "Retire Clause",
            "reason": "Clause is commercially extinct. Usage has dropped to near-zero.",
            "category": "AGING"
        })

    elif aging["aging_level"] == "AGING":
        recommendations.append({
            "priority": "HIGH",
            "action": "Review & Modernize",
            "reason": "Clause is aging. Consider updating language to current standards.",
            "category": "AGING"
        })

    # Usage trend recommendations
    if usage_trend["trend"] == "DECLINING":
        recommendations.append({
            "priority": "MEDIUM",
            "action": "Investigate Usage Decline",
            "reason": f"Usage declining at {abs(usage_trend['slope']):.1f} per year. Understand why.",
            "category": "USAGE"
        })

    # Risk trend recommendations
    if risk_trend["increasing"]:
        recommendations.append({
            "priority": "HIGH",
            "action": "Address Risk Increase",
            "reason": f"Risk score increasing over time. Identify and mitigate new risk factors.",
            "category": "RISK"
        })

    # Regulatory drift recommendations
    if reg_drift["has_drift"]:
        if reg_drift.get("critical_count", 0) > 0:
            recommendations.append({
                "priority": "CRITICAL",
                "action": "Urgent Regulatory Update",
                "reason": f"{reg_drift['critical_count']} critical regulatory changes affect this clause.",
                "category": "REGULATORY"
            })
        elif reg_drift.get("high_count", 0) > 0:
            recommendations.append({
                "priority": "HIGH",
                "action": "Regulatory Compliance Review",
                "reason": f"{reg_drift['high_count']} significant regulatory changes may require updates.",
                "category": "REGULATORY"
            })

    # No issues
    if not recommendations:
        recommendations.append({
            "priority": "LOW",
            "action": "Continue Monitoring",
            "reason": "Clause performance is stable. No immediate action needed.",
            "category": "MAINTENANCE"
        })

    return recommendations
