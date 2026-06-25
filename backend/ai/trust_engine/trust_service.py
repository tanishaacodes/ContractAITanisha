"""
Trust Engine - Main Trust Service

End-to-end Clause Trust Score (CTS) calculation.
Integrates all trust components into a unified service.
"""
from .enforceability import enforceability_score, litigation_survival_score, enforceability_factors
from .negotiability import negotiability_score, negotiability_factors, negotiation_friction_score
from .ambiguity import ambiguity_score, ambiguity_label, detect_ambiguous_terms
from .scorer import compute_trust_score, trust_breakdown, trust_level, trust_grade, trust_color
from .badges import assign_trust_badge, badge_recommendation, badge_alternatives


def calculate_clause_trust(clause, outcomes=None):
    """
    Calculate complete Clause Trust Score (CTS) for a clause.

    Args:
        clause: Clause object with .clause_text attribute
        outcomes: QuerySet or list of ClauseEvent objects (optional)

    Returns:
        dict: Complete trust analysis
    """
    # Get clause text
    clause_text = getattr(clause, 'clause_text', '') or \
                  getattr(clause, 'text', '') or \
                  str(clause)

    # If no outcomes provided, try to fetch from clause
    if outcomes is None and hasattr(clause, 'events'):
        outcomes = clause.events.all()
    elif outcomes is None:
        outcomes = []

    # Calculate component scores
    enf = enforceability_score(outcomes)
    neg = negotiability_score(outcomes)
    amb = ambiguity_score(clause_text)
    lit = litigation_survival_score(outcomes)

    # Compute composite trust score
    trust = compute_trust_score(enf, neg, amb, lit)

    # Assign trust badge
    badge = assign_trust_badge(trust, amb, neg, enf)

    # Get detailed breakdown
    breakdown = trust_breakdown(enf, neg, amb, lit)

    # Get component factors
    enf_factors = enforceability_factors(outcomes)
    neg_factors = negotiability_factors(outcomes)

    # Detect ambiguous terms
    ambiguous_terms = detect_ambiguous_terms(clause_text)

    return {
        "clause_id": clause.id if hasattr(clause, 'id') else None,
        "trust_score": trust,
        "trust_level": trust_level(trust),
        "trust_grade": trust_grade(trust),
        "color": trust_color(trust),

        # Badge
        "badge": badge["badge"],
        "badge_label": badge["label"],
        "badge_color": badge["color"],
        "badge_icon": badge["icon"],
        "badge_description": badge["description"],
        "recommendation": badge_recommendation(badge),
        "alternatives": badge_alternatives(badge),

        # Component Scores
        "enforceability": enf,
        "negotiability": neg,
        "ambiguity": amb,
        "ambiguity_label": ambiguity_label(amb),
        "litigation_survival": lit,

        # Detailed Factors
        "enforceability_factors": enf_factors,
        "negotiability_factors": neg_factors,
        "ambiguous_terms": ambiguous_terms,

        # Full Breakdown
        "breakdown": breakdown,

        # Metadata
        "outcome_count": len(outcomes) if outcomes else 0,
        "has_history": len(outcomes) > 0 if outcomes else False
    }


def bulk_calculate_trust(clauses, outcomes_map=None):
    """
    Calculate trust scores for multiple clauses efficiently.

    Args:
        clauses: List or QuerySet of Clause objects
        outcomes_map: Optional dict mapping clause_id -> outcomes list

    Returns:
        list: Trust scores for all clauses
    """
    results = []

    for clause in clauses:
        # Get outcomes for this clause
        if outcomes_map and hasattr(clause, 'id'):
            outcomes = outcomes_map.get(clause.id, [])
        else:
            # Get outcomes from clause versions
            outcomes = []
            if hasattr(clause, 'versions') and clause.versions.exists():
                for version in clause.versions.all():
                    if hasattr(version, 'events'):
                        outcomes.extend(list(version.events.all()))

        trust_data = calculate_clause_trust(clause, outcomes)
        results.append(trust_data)

    return results


def update_clause_health_with_trust(clause, health_metrics):
    """
    Update ClauseHealthMetrics model with calculated trust scores.

    Args:
        clause: Clause object
        health_metrics: ClauseHealthMetrics object to update

    Returns:
        ClauseHealthMetrics: Updated health metrics
    """
    # Get outcomes from clause versions
    outcomes = []
    if hasattr(clause, 'versions') and clause.versions.exists():
        for version in clause.versions.all():
            if hasattr(version, 'events'):
                outcomes.extend(list(version.events.all()))

    # Calculate trust
    trust_data = calculate_clause_trust(clause, outcomes)

    # Update health metrics with trust data
    # Note: Assumes ClauseHealthMetrics has been extended with trust fields
    if hasattr(health_metrics, 'trust_score'):
        health_metrics.trust_score = trust_data["trust_score"]
    if hasattr(health_metrics, 'trust_level'):
        health_metrics.trust_level = trust_data["trust_level"]
    if hasattr(health_metrics, 'trust_badge'):
        health_metrics.trust_badge = trust_data["badge"]

    # Update existing fields that map to trust components
    health_metrics.enforceability_score = trust_data["enforceability"]
    health_metrics.negotiation_score = trust_data["negotiability"]

    # Add ambiguity score if field exists
    if hasattr(health_metrics, 'ambiguity_score'):
        health_metrics.ambiguity_score = trust_data["ambiguity"]
    if hasattr(health_metrics, 'litigation_survival_score'):
        health_metrics.litigation_survival_score = trust_data["litigation_survival"]

    health_metrics.save()

    return health_metrics


def get_trust_statistics(clauses):
    """
    Get aggregate trust statistics across multiple clauses.

    Args:
        clauses: List or QuerySet of clauses

    Returns:
        dict: Aggregate statistics
    """
    trust_scores = bulk_calculate_trust(clauses)

    if not trust_scores:
        return {
            "total_clauses": 0,
            "avg_trust": 0.0,
            "median_trust": 0.0,
            "min_trust": 0.0,
            "max_trust": 0.0,
            "badge_distribution": {}
        }

    scores = [t["trust_score"] for t in trust_scores]
    badges = [t["badge"] for t in trust_scores]

    import numpy as np

    # Badge distribution
    badge_dist = {}
    for badge in badges:
        badge_dist[badge] = badge_dist.get(badge, 0) + 1

    return {
        "total_clauses": len(scores),
        "avg_trust": round(float(np.mean(scores)), 3),
        "median_trust": round(float(np.median(scores)), 3),
        "min_trust": round(float(np.min(scores)), 3),
        "max_trust": round(float(np.max(scores)), 3),
        "std_trust": round(float(np.std(scores)), 3),
        "badge_distribution": badge_dist,
        "excellent_count": sum(1 for s in scores if s >= 0.85),
        "poor_count": sum(1 for s in scores if s < 0.50),
        "critical_count": sum(1 for s in scores if s < 0.30)
    }
