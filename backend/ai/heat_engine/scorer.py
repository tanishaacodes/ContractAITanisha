"""
Heat Scoring Engine

Combines emotion, loops, and historical patterns into a heat score.
"""


def compute_heat_score(avg_rounds, emotion, loops, friction_trend="STABLE"):
    """
    Calculate negotiation heat score.

    Formula:
        Heat = 0.4 × (avg_rounds / 5) +
               0.4 × emotion +
               0.2 × (loops / 3)

    Args:
        avg_rounds: Average negotiation rounds
        emotion: Emotional friction score (0-1)
        loops: Number of loops detected
        friction_trend: Trend direction (ESCALATING, STABLE, DE-ESCALATING)

    Returns:
        float: Heat score (0-1)
    """
    # Normalize rounds (5 rounds = 1.0)
    rounds_normalized = min(1.0, avg_rounds / 5.0)

    # Normalize loops (3 loops = 1.0)
    loops_normalized = min(1.0, loops / 3.0)

    # Base heat score
    heat = (
        0.4 * rounds_normalized +
        0.4 * emotion +
        0.2 * loops_normalized
    )

    # Adjust for friction trend
    if friction_trend == "ESCALATING":
        heat = min(1.0, heat * 1.2)  # Boost by 20%
    elif friction_trend == "DE-ESCALATING":
        heat = heat * 0.8  # Reduce by 20%

    return round(heat, 3)


def heat_level(heat_score):
    """
    Convert numeric heat score to categorical level.

    Args:
        heat_score: Heat score (0-1)

    Returns:
        str: Heat level
    """
    if heat_score >= 0.80:
        return "CRITICAL"
    elif heat_score >= 0.60:
        return "HIGH"
    elif heat_score >= 0.40:
        return "MEDIUM"
    elif heat_score >= 0.20:
        return "LOW"
    else:
        return "MINIMAL"


def heat_color(heat_score):
    """
    Get color for heat visualization.

    Args:
        heat_score: Heat score (0-1)

    Returns:
        str: Hex color code
    """
    if heat_score >= 0.80:
        return "#dc2626"  # Dark red
    elif heat_score >= 0.60:
        return "#ef4444"  # Red
    elif heat_score >= 0.40:
        return "#f59e0b"  # Amber
    elif heat_score >= 0.20:
        return "#fbbf24"  # Yellow
    else:
        return "#10b981"  # Green


def explosion_risk(heat_score, stall_probability):
    """
    Calculate deal explosion risk.

    Args:
        heat_score: Heat score (0-1)
        stall_probability: Probability of stall (0-1)

    Returns:
        dict: Explosion risk analysis
    """
    # Explosion = high heat + high stall probability
    explosion_score = (heat_score * 0.6) + (stall_probability * 0.4)

    if explosion_score > 0.75:
        risk_level = "CRITICAL"
        recommendation = "URGENT: Consider executive escalation or walk away"
    elif explosion_score > 0.55:
        risk_level = "HIGH"
        recommendation = "High risk of deal failure. Adjust strategy immediately."
    elif explosion_score > 0.35:
        risk_level = "MEDIUM"
        recommendation = "Monitor closely. Be prepared with fallback positions."
    else:
        risk_level = "LOW"
        recommendation = "Normal negotiation friction. Continue as planned."

    return {
        "explosion_score": round(explosion_score, 3),
        "risk_level": risk_level,
        "recommendation": recommendation
    }


def heat_breakdown(avg_rounds, emotion, loops):
    """
    Detailed breakdown of heat components.

    Args:
        avg_rounds: Average negotiation rounds
        emotion: Emotional friction score
        loops: Number of loops

    Returns:
        dict: Component breakdown
    """
    rounds_normalized = min(1.0, avg_rounds / 5.0)
    loops_normalized = min(1.0, loops / 3.0)

    heat = compute_heat_score(avg_rounds, emotion, loops)

    return {
        "heat_score": heat,
        "heat_level": heat_level(heat),
        "color": heat_color(heat),
        "components": {
            "rounds": {
                "value": avg_rounds,
                "normalized": rounds_normalized,
                "weight": 0.4,
                "contribution": round(0.4 * rounds_normalized, 3)
            },
            "emotion": {
                "value": emotion,
                "normalized": emotion,
                "weight": 0.4,
                "contribution": round(0.4 * emotion, 3)
            },
            "loops": {
                "value": loops,
                "normalized": loops_normalized,
                "weight": 0.2,
                "contribution": round(0.2 * loops_normalized, 3)
            }
        }
    }


def predict_deal_velocity(heat_score, trust_score=None):
    """
    Predict time to deal closure.

    Args:
        heat_score: Negotiation heat score
        trust_score: Optional clause trust score

    Returns:
        dict: Deal velocity prediction
    """
    # Base estimate: low heat = fast, high heat = slow
    base_days = 7  # Baseline for minimal friction

    # Heat multiplier
    heat_multiplier = 1 + (heat_score * 3)  # Up to 4x slower at max heat

    # Trust adjustment (if available)
    if trust_score is not None:
        trust_multiplier = 2 - trust_score  # High trust = faster
        estimated_days = base_days * heat_multiplier * trust_multiplier
    else:
        estimated_days = base_days * heat_multiplier

    # Classify velocity
    if estimated_days < 10:
        velocity = "FAST"
    elif estimated_days < 20:
        velocity = "NORMAL"
    elif estimated_days < 30:
        velocity = "SLOW"
    else:
        velocity = "CRITICAL_DELAY"

    return {
        "estimated_days": round(estimated_days, 1),
        "velocity": velocity,
        "heat_impact": f"{((heat_multiplier - 1) * 100):.0f}% slowdown from heat",
        "confidence": "MEDIUM" if heat_score < 0.7 else "LOW"
    }
