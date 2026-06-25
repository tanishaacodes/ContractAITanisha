"""
Multi-Clause Negotiation Simulator
Simulates round-by-round negotiation outcomes for entire contracts
Models clause interdependencies and trade-off dynamics
"""
from .negotiation_predictor import predict_outcome
import logging

logger = logging.getLogger(__name__)

# Simulation constants
MAX_ROUNDS = 6
STALL_THRESHOLD = 0.75
ACCEPTANCE_THRESHOLD = 0.6

# Clause trade-off matrix
# When clauseA is rejected, these clauses get acceptance boost
TRADEOFF_MATRIX = {
    "IP Ownership": {
        "Limitation of Liability": 0.15,
        "Confidentiality": 0.10,
        "Indemnity": 0.08
    },
    "Termination": {
        "Payment Terms": 0.20,
        "Notice Period": 0.15
    },
    "Limitation of Liability": {
        "Insurance Requirements": 0.12,
        "Warranty": 0.10
    },
    "Price Escalation": {
        "Auto-Renewal": 0.18,
        "Termination": 0.15
    },
    "Exclusivity": {
        "Duration": 0.12,
        "Territory": 0.10
    }
}


def simulate_negotiation(counterparty, clauses):
    """
    Simulate a multi-round negotiation with clause interdependencies

    Args:
        counterparty: Counterparty name
        clauses: List of dicts with {'clause_type': str, 'text': str}

    Returns:
        dict: {
            "status": str ("SIGNED", "STALLED", "PARTIAL"),
            "rounds": int,
            "global_stall_risk": float,
            "clause_states": list of round-by-round states,
            "summary": dict with final stats
        }
    """
    state = []
    global_stall_risk = 0.0
    accepted_clauses = set()
    predictions_cache = {}

    for round_no in range(1, MAX_ROUNDS + 1):
        logger.info(f"Simulating round {round_no}")
        round_states = []
        round_rejections = []

        for clause in clauses:
            clause_type = clause.get('clause_type', '')
            clause_text = clause.get('text', '')

            # Skip if already accepted
            if clause_type in accepted_clauses:
                continue

            # Get prediction (use cache if available)
            cache_key = f"{clause_type}_{round_no}"
            if cache_key not in predictions_cache:
                prediction = predict_outcome(clause_text, clause_type, counterparty)

                # Apply trade-off boosts from previous rejections
                acceptance_prob = prediction['acceptance_probability']
                for rejected_clause in round_rejections:
                    if rejected_clause in TRADEOFF_MATRIX:
                        boost = TRADEOFF_MATRIX[rejected_clause].get(clause_type, 0)
                        acceptance_prob = min(1.0, acceptance_prob + boost)
                        logger.debug(
                            f"Applied {boost} boost to {clause_type} "
                            f"due to {rejected_clause} rejection"
                        )

                prediction['acceptance_probability'] = acceptance_prob
                predictions_cache[cache_key] = prediction
            else:
                prediction = predictions_cache[cache_key]

            # Determine acceptance
            accepted = prediction['acceptance_probability'] > ACCEPTANCE_THRESHOLD

            if accepted:
                accepted_clauses.add(clause_type)

            clause_state = {
                "clause_type": clause_type,
                "round": round_no,
                "accepted": accepted,
                "acceptance_probability": prediction['acceptance_probability'],
                "stall_risk": prediction['stall_risk'],
                "expected_redlines": prediction['expected_redlines']
            }

            round_states.append(clause_state)

            # Track rejections for trade-offs
            if not accepted:
                round_rejections.append(clause_type)

            # Update global stall risk
            global_stall_risk = max(global_stall_risk, prediction['stall_risk'])

        state.extend(round_states)

        # Check stall condition
        if global_stall_risk > STALL_THRESHOLD:
            logger.warning(f"Negotiation stalled at round {round_no}")
            return {
                "status": "STALLED",
                "rounds": round_no,
                "global_stall_risk": round(global_stall_risk, 2),
                "clause_states": state,
                "summary": _generate_summary(clauses, state, accepted_clauses)
            }

        # Check if all clauses accepted
        if len(accepted_clauses) == len(clauses):
            logger.info(f"All clauses accepted at round {round_no}")
            return {
                "status": "SIGNED",
                "rounds": round_no,
                "global_stall_risk": round(global_stall_risk, 2),
                "clause_states": state,
                "summary": _generate_summary(clauses, state, accepted_clauses)
            }

        # If no progress in this round, likely headed for stall
        if not any(cs['accepted'] for cs in round_states):
            logger.warning("No progress in round, increasing stall risk")
            global_stall_risk = min(1.0, global_stall_risk + 0.15)

    # Max rounds reached
    logger.info("Max rounds reached")
    return {
        "status": "PARTIAL",
        "rounds": MAX_ROUNDS,
        "global_stall_risk": round(global_stall_risk, 2),
        "clause_states": state,
        "summary": _generate_summary(clauses, state, accepted_clauses)
    }


def _generate_summary(clauses, state, accepted_clauses):
    """Generate summary statistics for simulation"""
    total_clauses = len(clauses)
    accepted_count = len(accepted_clauses)
    pending_clauses = [
        c['clause_type'] for c in clauses
        if c['clause_type'] not in accepted_clauses
    ]

    # Find most problematic clauses
    clause_max_stall = {}
    for state_item in state:
        clause_type = state_item['clause_type']
        stall_risk = state_item['stall_risk']
        if clause_type not in clause_max_stall:
            clause_max_stall[clause_type] = stall_risk
        else:
            clause_max_stall[clause_type] = max(clause_max_stall[clause_type], stall_risk)

    problematic = sorted(
        clause_max_stall.items(),
        key=lambda x: x[1],
        reverse=True
    )[:3]

    return {
        "total_clauses": total_clauses,
        "accepted_clauses": accepted_count,
        "pending_clauses": len(pending_clauses),
        "acceptance_rate": round(accepted_count / total_clauses, 2) if total_clauses > 0 else 0,
        "pending_clause_types": pending_clauses,
        "most_problematic": [{"clause_type": ct, "stall_risk": sr} for ct, sr in problematic]
    }


def generate_negotiation_strategy(simulation_result):
    """
    Generate strategic recommendations based on simulation

    Args:
        simulation_result: Output from simulate_negotiation

    Returns:
        dict: {
            "strategy": str,
            "recommendations": list of strings,
            "trade_off_opportunities": list
        }
    """
    status = simulation_result.get('status', '')
    summary = simulation_result.get('summary', {})
    stall_risk = simulation_result.get('global_stall_risk', 0)

    recommendations = []
    trade_offs = []

    if status == "STALLED":
        recommendations.append("Negotiation likely to stall. Consider executive escalation.")
        recommendations.append("Review most problematic clauses for potential concessions.")

        # Identify trade-off opportunities
        problematic = summary.get('most_problematic', [])
        for item in problematic:
            clause_type = item.get('clause_type', '')
            if clause_type in TRADEOFF_MATRIX:
                alternative_clauses = list(TRADEOFF_MATRIX[clause_type].keys())
                trade_offs.append({
                    "give_up": clause_type,
                    "strengthen": alternative_clauses
                })

    elif status == "PARTIAL":
        recommendations.append("Some clauses remain unresolved after maximum rounds.")
        recommendations.append("Focus on pending high-value clauses.")

        pending = summary.get('pending_clause_types', [])
        if pending:
            recommendations.append(f"Priority pending clauses: {', '.join(pending[:3])}")

    elif stall_risk > 0.6:
        recommendations.append("High stall risk despite acceptance. Proceed with caution.")
        recommendations.append("Prepare fallback positions for key clauses.")

    else:
        recommendations.append("Negotiation likely to conclude successfully.")
        recommendations.append(f"Expected rounds: {simulation_result.get('rounds', 'N/A')}")

    strategy_description = _get_strategy_description(status, stall_risk, summary)

    return {
        "strategy": strategy_description,
        "recommendations": recommendations,
        "trade_off_opportunities": trade_offs
    }


def _get_strategy_description(status, stall_risk, summary):
    """Generate overall strategy description"""
    if status == "STALLED":
        return "Defensive strategy required. High risk of deal failure without major concessions."
    elif status == "PARTIAL":
        return "Balanced strategy. Some clauses will require intensive negotiation."
    elif stall_risk > 0.6:
        return "Cautious approach. Deal is achievable but expect resistance on key terms."
    elif summary.get('acceptance_rate', 0) > 0.7:
        return "Aggressive strategy. Counterparty is likely receptive to most terms."
    else:
        return "Standard negotiation strategy. Expect typical redline process."
