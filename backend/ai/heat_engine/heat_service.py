"""
Negotiation Heat Service

Main service for calculating negotiation heat scores.
"""
from .emotion import emotion_score, emotional_trend, detect_friction_patterns
from .loops import detect_loops, detect_ping_pong, predict_stall_probability
from .scorer import compute_heat_score, heat_breakdown, explosion_risk, predict_deal_velocity


def analyze_negotiation_heat(redlines, messages=None):
    """
    Complete negotiation heat analysis.

    Args:
        redlines: List of redline texts (chronological)
        messages: Optional list of negotiation messages

    Returns:
        dict: Complete heat analysis
    """
    if not redlines:
        return {
            "heat_score": 0.3,
            "heat_level": "LOW",
            "analysis": "No redline history available"
        }

    # 1. Calculate average rounds
    avg_rounds = len(redlines)

    # 2. Emotional friction analysis
    if messages:
        emotion_analysis = emotional_trend(messages)
        emotion = emotion_analysis["current_friction"]
        friction_trend = emotion_analysis["trend"]
    else:
        # Fallback: analyze redlines for emotion
        redline_emotions = [emotion_score(r) for r in redlines]
        emotion = sum(redline_emotions) / len(redline_emotions)
        friction_trend = "STABLE"
        emotion_analysis = {
            "trend": friction_trend,
            "current_friction": emotion,
            "avg_friction": emotion
        }

    # 3. Loop detection
    loop_analysis = detect_loops(redlines)
    loops = loop_analysis["loop_count"]

    # 4. Ping-pong pattern detection
    pingpong = detect_ping_pong(redlines)

    # 5. Friction patterns
    all_patterns = []
    for redline in redlines[-3:]:  # Last 3 redlines
        patterns = detect_friction_patterns(redline)
        all_patterns.extend(patterns)

    # 6. Compute heat score
    heat = compute_heat_score(avg_rounds, emotion, loops, friction_trend)

    # 7. Heat breakdown
    breakdown = heat_breakdown(avg_rounds, emotion, loops)

    # 8. Stall probability
    stall_prob = predict_stall_probability(loops, avg_rounds, emotion)

    # 9. Explosion risk
    explosion = explosion_risk(heat, stall_prob)

    # 10. Deal velocity prediction
    velocity = predict_deal_velocity(heat)

    return {
        "heat_score": heat,
        "heat_level": breakdown["heat_level"],
        "color": breakdown["color"],

        # Component Analysis
        "emotion_analysis": emotion_analysis,
        "loop_analysis": loop_analysis,
        "pingpong_analysis": pingpong,
        "friction_patterns": all_patterns,

        # Breakdown
        "breakdown": breakdown,

        # Predictions
        "stall_probability": stall_prob,
        "explosion_risk": explosion,
        "deal_velocity": velocity,

        # Metadata
        "total_rounds": avg_rounds,
        "analyzed_redlines": len(redlines),
        "analyzed_messages": len(messages) if messages else 0
    }


def compare_heat(clause_a_redlines, clause_b_redlines):
    """
    Compare heat between two clauses.

    Args:
        clause_a_redlines: Redlines for clause A
        clause_b_redlines: Redlines for clause B

    Returns:
        dict: Comparison result
    """
    heat_a = analyze_negotiation_heat(clause_a_redlines)
    heat_b = analyze_negotiation_heat(clause_b_redlines)

    diff = heat_a["heat_score"] - heat_b["heat_score"]

    if abs(diff) < 0.1:
        verdict = "SIMILAR_HEAT"
    elif diff > 0:
        verdict = "A_HOTTER"
    else:
        verdict = "B_HOTTER"

    return {
        "clause_a_heat": heat_a["heat_score"],
        "clause_b_heat": heat_b["heat_score"],
        "difference": round(diff, 3),
        "verdict": verdict,
        "recommendation": (
            f"Clause A has {abs(diff * 100):.0f}% {'more' if diff > 0 else 'less'} negotiation heat than Clause B"
        )
    }


def recommend_cooling_strategy(heat_analysis):
    """
    Recommend strategies to cool down hot negotiations.

    Args:
        heat_analysis: Heat analysis dict from analyze_negotiation_heat

    Returns:
        list: Cooling strategy recommendations
    """
    recommendations = []

    heat = heat_analysis["heat_score"]
    emotion = heat_analysis["emotion_analysis"]["current_friction"]
    loops = heat_analysis["loop_analysis"]["loop_count"]
    stall_prob = heat_analysis["stall_probability"]

    # High heat strategies
    if heat > 0.7:
        recommendations.append({
            "priority": "CRITICAL",
            "strategy": "Executive Escalation",
            "action": "Involve senior stakeholders to break deadlock"
        })

    # High emotion strategies
    if emotion > 0.7:
        recommendations.append({
            "priority": "HIGH",
            "strategy": "Cooling Period",
            "action": "Propose 24-48 hour pause to reduce emotional tension"
        })

        recommendations.append({
            "priority": "HIGH",
            "strategy": "Language Softening",
            "action": "Remove absolutist terms and use collaborative language"
        })

    # Loop strategies
    if loops >= 2:
        recommendations.append({
            "priority": "HIGH",
            "strategy": "Change Approach",
            "action": "Current strategy is looping. Try alternative clause language or structure."
        })

        recommendations.append({
            "priority": "MEDIUM",
            "strategy": "Offer Trade-offs",
            "action": "Bundle this clause with concessions elsewhere"
        })

    # Stall strategies
    if stall_prob > 0.6:
        recommendations.append({
            "priority": "CRITICAL",
            "strategy": "Walk-Away Assessment",
            "action": "Evaluate if this deal is worth pursuing given stall risk"
        })

        recommendations.append({
            "priority": "HIGH",
            "strategy": "Mediator Introduction",
            "action": "Consider neutral third-party to facilitate agreement"
        })

    # General strategies
    if heat > 0.5:
        recommendations.append({
            "priority": "MEDIUM",
            "strategy": "Focus on Interests",
            "action": "Shift from positions to underlying business interests"
        })

        recommendations.append({
            "priority": "MEDIUM",
            "strategy": "Provide Precedents",
            "action": "Share market-standard language to justify your position"
        })

    # No issues
    if not recommendations:
        recommendations.append({
            "priority": "LOW",
            "strategy": "Continue Current Approach",
            "action": "Negotiation is progressing normally"
        })

    return recommendations


def bulk_heat_analysis(clauses_with_redlines):
    """
    Analyze heat for multiple clauses efficiently.

    Args:
        clauses_with_redlines: List of (clause_id, redlines) tuples

    Returns:
        list: Heat analysis for each clause
    """
    results = []

    for clause_id, redlines in clauses_with_redlines:
        heat_analysis = analyze_negotiation_heat(redlines)
        heat_analysis["clause_id"] = clause_id
        results.append(heat_analysis)

    # Sort by heat (hottest first)
    results.sort(key=lambda x: x["heat_score"], reverse=True)

    return results
