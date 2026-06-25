"""
Negotiation Outcome Predictor
Predicts clause acceptance probability, expected redlines, and stall risk
Based on historical negotiation data and counterparty behavior
"""
import numpy as np
from .embedding import embed
from .vectorstore import search_similar_negotiations
import logging

logger = logging.getLogger(__name__)


def _analyze_clause_content(clause_text, clause_type):
    """
    Analyze clause content directly for risk indicators when no historical data exists.
    Returns predictions based on text analysis.
    """
    text_lower = clause_text.lower()

    # High-risk keywords that make clauses harder to negotiate
    high_risk_keywords = [
        'indemnify', 'indemnification', 'liability', 'unlimited', 'perpetual',
        'irrevocable', 'non-negotiable', 'sole discretion', 'exclusive',
        'penalty', 'liquidated damages', 'termination for convenience'
    ]

    # Medium-risk keywords
    medium_risk_keywords = [
        'termination', 'breach', 'default', 'warranty', 'representation',
        'confidential', 'proprietary', 'intellectual property', 'ownership',
        'assignment', 'dispute', 'arbitration', 'jurisdiction'
    ]

    # Low-risk keywords (standard business terms)
    low_risk_keywords = [
        'payment', 'invoice', 'delivery', 'notice', 'communication',
        'contact', 'address', 'term', 'renewal', 'amendment'
    ]

    # Count keyword matches
    high_risk_count = sum(1 for kw in high_risk_keywords if kw in text_lower)
    medium_risk_count = sum(1 for kw in medium_risk_keywords if kw in text_lower)
    low_risk_count = sum(1 for kw in low_risk_keywords if kw in text_lower)

    # Clause type specific adjustments
    risky_clause_types = [
        'IP Ownership', 'Limitation of Liability', 'Indemnification',
        'Termination', 'Exclusivity', 'Non-Compete', 'Arbitration'
    ]

    # Calculate base risk from clause type FIRST (stronger differentiation)
    risk_score = 0.0

    if clause_type in risky_clause_types:
        risk_score = 0.45  # Start high for risky types (IP, Indemnity, etc.)
    else:
        risk_score = 0.10  # Start low for standard types

    # Add keyword-based risk (amplified multipliers)
    if high_risk_count > 0:
        risk_score += high_risk_count * 0.22  # Much stronger impact
    if medium_risk_count > 0:
        risk_score += medium_risk_count * 0.12  # Stronger impact
    if low_risk_count > 0:
        risk_score -= low_risk_count * 0.06  # Stronger reduction

    # Clause length factor (longer = more complex = riskier)
    text_length = len(clause_text)
    if text_length > 500:
        risk_score += 0.12
    elif text_length > 300:
        risk_score += 0.06

    # Normalize risk score to 0-1 range
    risk_score = max(0.0, min(1.0, risk_score))

    # Calculate metrics with MUCH WIDER ranges for dramatic variation
    stall_risk = round(0.12 + (risk_score * 0.70), 2)  # Range: 0.12 to 0.82 (HUGE range!)
    acceptance_probability = round(0.92 - (risk_score * 0.55), 2)  # Range: 0.37 to 0.92 (HUGE range!)

    # Expected redlines based on risk (more granular)
    if risk_score > 0.7:
        expected_redlines = 5
    elif risk_score > 0.55:
        expected_redlines = 4
    elif risk_score > 0.38:
        expected_redlines = 3
    elif risk_score > 0.22:
        expected_redlines = 2
    else:
        expected_redlines = 1

    logger.info(
        f"Content analysis for {clause_type}: risk_score={risk_score:.2f}, "
        f"stall={stall_risk}, acceptance={acceptance_probability}, "
        f"redlines={expected_redlines}"
    )

    return {
        "acceptance_probability": acceptance_probability,
        "expected_redlines": expected_redlines,
        "stall_risk": stall_risk,
        "similar_cases": 0  # Indicates content-based analysis
    }


def predict_outcome(clause_text, clause_type, counterparty_name):
    """
    Predict negotiation outcome for a specific clause

    Args:
        clause_text: The text of the clause
        clause_type: Type of clause (e.g., "IP Ownership", "Termination")
        counterparty_name: Name of the counterparty

    Returns:
        dict: {
            "acceptance_probability": float (0-1),
            "expected_redlines": int,
            "stall_risk": float (0-1),
            "similar_cases": int
        }
    """
    try:
        # Generate embedding for the clause
        vector = embed(clause_text)

        # Search for similar negotiations
        # Don't filter by clause_type if it's None (many clauses lack this field)
        filter_by_type = clause_type if clause_type and clause_type != "None" else None
        results = search_similar_negotiations(
            vector,
            limit=20,
            clause_type_filter=filter_by_type
        )

        if not results:
            # No historical data, analyze clause text for risk indicators
            logger.info(f"No historical data found for {clause_type}, analyzing clause text")
            return _analyze_clause_content(clause_text, clause_type)

        # Extract metrics from similar cases
        accepted = []
        redlines = []
        stalled = []

        # If we have a valid clause type, try to match it first
        if clause_type and clause_type != "None":
            for result in results:
                payload = result.payload
                # Filter by clause type if available
                if payload.get("clause_type") == clause_type:
                    accepted.append(1 if payload.get("accepted", False) else 0)
                    redlines.append(payload.get("redline_rounds", 2))
                    stalled.append(1 if payload.get("stalled", False) else 0)

        # If no type-specific matches OR clause_type is None, use all results
        if not accepted:
            for result in results:
                payload = result.payload
                accepted.append(1 if payload.get("accepted", False) else 0)
                redlines.append(payload.get("redline_rounds", 2))
                stalled.append(1 if payload.get("stalled", False) else 0)

        # Calculate predictions
        acceptance_prob = np.mean(accepted) if accepted else 0.5
        avg_redlines = int(np.mean(redlines)) if redlines else 2
        stall_risk = np.mean(stalled) if stalled else 0.3

        return {
            "acceptance_probability": round(float(acceptance_prob), 2),
            "expected_redlines": avg_redlines,
            "stall_risk": round(float(stall_risk), 2),
            "similar_cases": len(accepted)
        }

    except Exception as e:
        logger.error(f"Error predicting outcome: {str(e)}")
        # Return safe defaults on error
        return {
            "acceptance_probability": 0.5,
            "expected_redlines": 2,
            "stall_risk": 0.3,
            "similar_cases": 0
        }


def predict_multiple_clauses(clauses, counterparty_name):
    """
    Predict outcomes for multiple clauses

    Args:
        clauses: List of dicts with 'clause_type' and 'text'
        counterparty_name: Name of the counterparty

    Returns:
        List of predictions for each clause
    """
    predictions = []

    for clause in clauses:
        prediction = predict_outcome(
            clause.get('text', ''),
            clause.get('clause_type', ''),
            counterparty_name
        )
        prediction['clause_type'] = clause.get('clause_type', '')
        predictions.append(prediction)

    return predictions


def identify_high_risk_clauses(predictions, stall_threshold=0.6, acceptance_threshold=0.3):
    """
    Identify clauses with high negotiation risk

    Args:
        predictions: List of prediction dicts
        stall_threshold: Stall risk above this is considered high
        acceptance_threshold: Acceptance probability below this is considered high risk

    Returns:
        List of high-risk clause predictions
    """
    high_risk = []

    for pred in predictions:
        if (pred.get('stall_risk', 0) > stall_threshold or
            pred.get('acceptance_probability', 1) < acceptance_threshold):
            high_risk.append(pred)

    # Sort by risk severity
    high_risk.sort(
        key=lambda x: (x.get('stall_risk', 0), -x.get('acceptance_probability', 1)),
        reverse=True
    )

    return high_risk


def calculate_deal_complexity(predictions):
    """
    Calculate overall deal complexity score

    Args:
        predictions: List of prediction dicts

    Returns:
        dict: {
            "complexity_score": float (0-1),
            "expected_rounds": int,
            "deal_risk": str ("LOW", "MEDIUM", "HIGH")
        }
    """
    if not predictions:
        return {
            "complexity_score": 0.5,
            "expected_rounds": 2,
            "deal_risk": "MEDIUM"
        }

    # Calculate weighted complexity
    avg_stall_risk = np.mean([p.get('stall_risk', 0) for p in predictions])
    avg_acceptance = np.mean([p.get('acceptance_probability', 0.5) for p in predictions])
    max_redlines = max([p.get('expected_redlines', 2) for p in predictions])

    complexity_score = (
        avg_stall_risk * 0.4 +
        (1 - avg_acceptance) * 0.4 +
        min(max_redlines / 10, 1) * 0.2
    )

    # Determine risk level
    if complexity_score > 0.7:
        risk_level = "HIGH"
    elif complexity_score > 0.4:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "complexity_score": round(float(complexity_score), 2),
        "expected_rounds": max_redlines,
        "deal_risk": risk_level
    }
