"""
Risk Identification Engine
Rule-based + embedding hybrid approach (no LLM hallucination)
"""

# Risk patterns with weights (deterministic, auditable)
RISK_PATTERNS = [
    ("unlimited liability", 0.9),
    ("indemnify", 0.7),
    ("indemnification", 0.7),
    ("termination without cause", 0.6),
    ("penalty", 0.65),
    ("liquidated damages", 0.7),
    ("governing law", 0.4),
    ("force majeure", 0.5),
    ("arbitration", 0.45),
    ("confidentiality", 0.4),
    ("non-compete", 0.6),
    ("exclusive rights", 0.65),
    ("waive", 0.8),
    ("waiver", 0.8),
    ("irrevocable", 0.75),
    ("perpetual", 0.7),
    ("unlimited duration", 0.8),
    ("automatic renewal", 0.5),
]

def score_clause_risk(text: str):
    """
    Calculate risk score for a clause based on keywords

    Args:
        text: Clause text to analyze

    Returns:
        Tuple of (risk_score, reason_string)
    """
    score = 0
    reasons = []

    text_lower = text.lower()

    for keyword, weight in RISK_PATTERNS:
        if keyword in text_lower:
            score += weight
            reasons.append(f"Contains '{keyword}'")

    # Cap at 1.0 and normalize
    final_score = min(score, 1.0)
    reason_string = ", ".join(reasons) if reasons else "No risk patterns detected"

    return round(final_score, 2), reason_string

def calculate_overall_risk(clauses_data: list):
    """
    Calculate overall contract risk from multiple clauses

    Args:
        clauses_data: List of clause dictionaries with risk scores

    Returns:
        Overall risk score (0-100)
    """
    if not clauses_data:
        return 0

    risk_scores = [c.get('risk_score', 0) for c in clauses_data]

    # Weighted average with emphasis on high-risk clauses
    max_risk = max(risk_scores) if risk_scores else 0
    avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0

    # 70% weight to max risk, 30% to average
    overall = (max_risk * 0.7 + avg_risk * 0.3) * 100

    return round(overall, 2)
