"""
Trust Engine - Negotiability Scoring

Measures how easily clauses close deals vs. kill them.
Based on dispute and execution outcomes.
"""


def negotiability_score(outcomes):
    """
    Calculate negotiability score based on dispute rate.

    A clause with high disputes = low negotiability (kills deals).
    A clause with smooth execution = high negotiability.

    Args:
        outcomes: QuerySet or list of ClauseEvent objects

    Returns:
        float: Negotiability score (0-1)
            1.0 = Never disputed, always accepted
            0.5 = Untested or neutral
            0.0 = Always disputed
    """
    if not outcomes or len(outcomes) == 0:
        return 0.5  # Neutral for untested clauses

    total = len(outcomes)
    disputes = [o for o in outcomes if o.event_type == "DISPUTED"]
    executed = [o for o in outcomes if o.event_type == "EXECUTED"]

    # Calculate dispute rate
    dispute_rate = len(disputes) / total if total > 0 else 0

    # Negotiability = inverse of dispute rate
    # If 100% disputed → 0.0 negotiability
    # If 0% disputed → 1.0 negotiability
    base_score = 1.0 - dispute_rate

    # Bonus for successful executions
    if executed:
        avg_execution_score = sum(e.outcome_score for e in executed if e.outcome_score) / len(executed)
        execution_bonus = avg_execution_score * 0.2  # Up to +0.2 bonus
        base_score = min(1.0, base_score + execution_bonus)

    return round(base_score, 3)


def deal_closure_rate(outcomes):
    """
    Calculate how often this clause leads to closed deals.

    Args:
        outcomes: QuerySet or list of ClauseEvent objects

    Returns:
        float: Deal closure rate (0-1)
    """
    if not outcomes or len(outcomes) == 0:
        return 0.5

    executed = [o for o in outcomes if o.event_type == "EXECUTED"]
    disputed = [o for o in outcomes if o.event_type == "DISPUTED"]
    total = len(outcomes)

    # Closure rate = executed / (executed + disputed)
    # Excludes renewals and litigation for now
    relevant = executed + disputed
    if len(relevant) == 0:
        return 0.5

    closure_rate = len(executed) / len(relevant)
    return round(closure_rate, 3)


def negotiation_friction_score(outcomes):
    """
    Measure friction during negotiation.

    High friction = multiple dispute rounds, low outcome scores.

    Args:
        outcomes: QuerySet or list of ClauseEvent objects

    Returns:
        float: Friction score (0-1, where 1 = high friction)
    """
    if not outcomes or len(outcomes) == 0:
        return 0.3  # Low friction assumed for untested

    disputes = [o for o in outcomes if o.event_type == "DISPUTED"]

    if not disputes:
        return 0.1  # Minimal friction

    # Friction factors:
    # 1. Number of disputes relative to total
    # 2. Average outcome score of disputes (low = high friction)

    total = len(outcomes)
    dispute_ratio = len(disputes) / total

    avg_dispute_outcome = sum(d.outcome_score for d in disputes if d.outcome_score) / len(disputes)

    # Friction = dispute ratio + (1 - avg outcome)
    friction = (dispute_ratio * 0.6) + ((1.0 - avg_dispute_outcome) * 0.4)

    return round(min(1.0, friction), 3)


def negotiability_factors(outcomes):
    """
    Break down negotiability into contributing factors.

    Args:
        outcomes: QuerySet or list of ClauseEvent objects

    Returns:
        dict: Factor breakdown
    """
    if not outcomes or len(outcomes) == 0:
        return {
            "total_outcomes": 0,
            "dispute_rate": None,
            "closure_rate": None,
            "friction": None,
            "status": "UNTESTED"
        }

    total = len(outcomes)
    disputes = [o for o in outcomes if o.event_type == "DISPUTED"]
    executed = [o for o in outcomes if o.event_type == "EXECUTED"]

    dispute_rate = len(disputes) / total
    closure = deal_closure_rate(outcomes)
    friction = negotiation_friction_score(outcomes)

    status = "SMOOTH" if dispute_rate < 0.2 else "FRAGILE" if dispute_rate < 0.5 else "HIGH_RISK"

    return {
        "total_outcomes": total,
        "dispute_rate": round(dispute_rate, 3),
        "closure_rate": closure,
        "friction": friction,
        "executed_count": len(executed),
        "disputed_count": len(disputes),
        "status": status
    }
