"""
Trust Engine - Composite Trust Scoring

Combines enforceability, negotiability, ambiguity, and litigation survival
into a single Clause Trust Score (CTS).
"""


def compute_trust_score(enforceability, negotiability, ambiguity, litigation_survival):
    """
    Calculate composite Clause Trust Score (CTS).

    Formula:
        CTS = 0.35 * enforceability +
              0.25 * negotiability +
              0.20 * (1 - ambiguity) +
              0.20 * litigation_survival

    Args:
        enforceability: Court enforceability score (0-1)
        negotiability: Deal closure success rate (0-1)
        ambiguity: Legal ambiguity score (0-1, lower is better)
        litigation_survival: Financial survival score (0-1)

    Returns:
        float: Trust score (0-1)
    """
    trust = (
        0.35 * enforceability +
        0.25 * negotiability +
        0.20 * (1.0 - ambiguity) +
        0.20 * litigation_survival
    )

    return round(trust, 3)


def trust_level(trust_score):
    """
    Convert numeric trust score to categorical level.

    Args:
        trust_score: Trust score (0-1)

    Returns:
        str: Trust level
    """
    if trust_score >= 0.85:
        return "EXCELLENT"
    elif trust_score >= 0.70:
        return "GOOD"
    elif trust_score >= 0.50:
        return "FAIR"
    elif trust_score >= 0.30:
        return "POOR"
    else:
        return "CRITICAL"


def trust_grade(trust_score):
    """
    Convert trust score to letter grade.

    Args:
        trust_score: Trust score (0-1)

    Returns:
        str: Letter grade (A+ to F)
    """
    if trust_score >= 0.95:
        return "A+"
    elif trust_score >= 0.90:
        return "A"
    elif trust_score >= 0.85:
        return "A-"
    elif trust_score >= 0.80:
        return "B+"
    elif trust_score >= 0.75:
        return "B"
    elif trust_score >= 0.70:
        return "B-"
    elif trust_score >= 0.65:
        return "C+"
    elif trust_score >= 0.60:
        return "C"
    elif trust_score >= 0.55:
        return "C-"
    elif trust_score >= 0.50:
        return "D+"
    elif trust_score >= 0.40:
        return "D"
    else:
        return "F"


def trust_color(trust_score):
    """
    Get color code for trust score visualization.

    Args:
        trust_score: Trust score (0-1)

    Returns:
        str: Hex color code
    """
    if trust_score >= 0.80:
        return "#10b981"  # Green
    elif trust_score >= 0.60:
        return "#f59e0b"  # Amber
    elif trust_score >= 0.40:
        return "#ef4444"  # Red
    else:
        return "#991b1b"  # Dark red


def trust_breakdown(enforceability, negotiability, ambiguity, litigation_survival):
    """
    Provide detailed breakdown of trust score components.

    Args:
        enforceability: Court enforceability score (0-1)
        negotiability: Deal closure success rate (0-1)
        ambiguity: Legal ambiguity score (0-1)
        litigation_survival: Financial survival score (0-1)

    Returns:
        dict: Breakdown with weights and contributions
    """
    trust = compute_trust_score(enforceability, negotiability, ambiguity, litigation_survival)

    return {
        "trust_score": trust,
        "trust_level": trust_level(trust),
        "trust_grade": trust_grade(trust),
        "color": trust_color(trust),
        "components": {
            "enforceability": {
                "score": enforceability,
                "weight": 0.35,
                "contribution": round(0.35 * enforceability, 3)
            },
            "negotiability": {
                "score": negotiability,
                "weight": 0.25,
                "contribution": round(0.25 * negotiability, 3)
            },
            "clarity": {
                "score": round(1.0 - ambiguity, 3),  # Inverted for readability
                "weight": 0.20,
                "contribution": round(0.20 * (1.0 - ambiguity), 3)
            },
            "litigation_survival": {
                "score": litigation_survival,
                "weight": 0.20,
                "contribution": round(0.20 * litigation_survival, 3)
            }
        }
    }


def compare_trust_scores(score_a, score_b):
    """
    Compare two trust scores and explain the difference.

    Args:
        score_a: First trust score
        score_b: Second trust score

    Returns:
        dict: Comparison result
    """
    diff = score_a - score_b
    diff_pct = (diff / score_b * 100) if score_b > 0 else 0

    if abs(diff) < 0.05:
        verdict = "EQUIVALENT"
    elif diff > 0:
        verdict = "A_BETTER"
    else:
        verdict = "B_BETTER"

    return {
        "score_a": score_a,
        "score_b": score_b,
        "difference": round(diff, 3),
        "difference_pct": round(diff_pct, 1),
        "verdict": verdict
    }
