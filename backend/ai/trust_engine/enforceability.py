"""
Trust Engine - Enforceability Scoring

Calculates court enforceability based on litigation outcomes.
Outcome-driven, not opinion-based.
"""


def enforceability_score(outcomes):
    """
    Calculate enforceability score based on litigation outcomes.

    Args:
        outcomes: QuerySet or list of ClauseEvent objects with event_type='LITIGATED'

    Returns:
        float: Enforceability score (0-1)
            1.0 = Always enforced in court
            0.5 = Untested (strong presumption)
            0.0 = Never enforced
    """
    if not outcomes:
        return 0.8  # Strong but untested (default trust)

    # Filter to litigation events only
    litigated = [o for o in outcomes if o.event_type == "LITIGATED"]

    if not litigated:
        return 0.8  # No litigation history = presumed enforceable

    # Count wins vs losses
    # outcome_score: 1.0 = success, 0.0 = failure
    wins = sum(1 for o in litigated if o.outcome_score and o.outcome_score >= 0.6)
    total = len(litigated)

    if total == 0:
        return 0.8

    # Calculate win rate
    win_rate = wins / total

    # Apply confidence penalty for small sample size
    confidence = min(1.0, total / 5.0)  # Full confidence at 5+ cases
    adjusted_score = (win_rate * confidence) + (0.8 * (1 - confidence))

    return round(adjusted_score, 3)


def litigation_survival_score(outcomes):
    """
    Calculate how well clause survives litigation based on financial impact.

    Args:
        outcomes: QuerySet or list of ClauseEvent objects

    Returns:
        float: Survival score (0-1)
            1.0 = No adverse financial impact
            0.0 = Catastrophic losses
    """
    if not outcomes:
        return 0.9  # No history = presumed safe

    litigated = [o for o in outcomes if o.event_type == "LITIGATED"]

    if not litigated:
        return 0.9

    # Calculate total settlement/penalty amounts
    # Assuming ClauseEvent will be extended with settlement_amount field
    total_penalties = 0
    for outcome in litigated:
        # For now, use outcome_score as proxy
        # outcome_score of 0.0 = max penalty, 1.0 = no penalty
        if hasattr(outcome, 'settlement_amount') and outcome.settlement_amount:
            total_penalties += outcome.settlement_amount
        else:
            # Estimate: low outcome_score = high implied penalty
            implied_penalty = (1.0 - outcome.outcome_score) * 100000
            total_penalties += implied_penalty

    # Normalize to 0-1 scale (assuming $1M = catastrophic)
    max_penalty = 1_000_000
    survival = max(0.1, 1.0 - (total_penalties / max_penalty))

    return round(survival, 3)


def enforceability_factors(outcomes):
    """
    Break down enforceability into contributing factors.

    Args:
        outcomes: QuerySet or list of ClauseEvent objects

    Returns:
        dict: Factor breakdown
    """
    litigated = [o for o in outcomes if o.event_type == "LITIGATED"]

    if not litigated:
        return {
            "sample_size": 0,
            "win_rate": None,
            "avg_outcome": None,
            "status": "UNTESTED"
        }

    wins = sum(1 for o in litigated if o.outcome_score and o.outcome_score >= 0.6)
    avg_outcome = sum(o.outcome_score for o in litigated if o.outcome_score) / len(litigated)

    return {
        "sample_size": len(litigated),
        "win_rate": wins / len(litigated),
        "avg_outcome": round(avg_outcome, 3),
        "status": "PROVEN" if wins / len(litigated) > 0.7 else "RISKY"
    }
