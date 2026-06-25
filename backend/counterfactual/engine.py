"""
Counterfactual Engine - Core logic for contract "what-if" simulations.
Combines vector similarity search with LLM reasoning.
"""
import logging
from typing import Dict, List, Optional
try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None
from .qdrant_client import search_similar_outcomes
from .llm_client import get_llm_client
from .models import CounterfactualScenario, HistoricalOutcome
from django.conf import settings

logger = logging.getLogger(__name__)

# Initialize embedding model (lazy loading)
_embedding_model = None


def get_embedding_model():
    """
    Get or create the sentence transformer model for embeddings.

    Returns:
        SentenceTransformer model
    """
    global _embedding_model
    if _embedding_model is None:
        model_name = getattr(settings, 'CONTRACTS_BERT_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
        logger.info(f"Loading embedding model: {model_name}")
        _embedding_model = SentenceTransformer(model_name, device='cpu')
    return _embedding_model


def generate_clause_embedding(clause_text: str) -> List[float]:
    """
    Generate vector embedding for a clause.

    Args:
        clause_text: The clause text to embed

    Returns:
        List of floats representing the embedding vector
    """
    model = get_embedding_model()
    embedding = model.encode(clause_text, convert_to_numpy=True)
    return embedding.tolist()


def simulate_counterfactual(
    contract_id: str,
    contract_text: str,
    original_clause: str,
    modified_clause: str,
    user=None,
    filters: Optional[Dict] = None
) -> Dict:
    """
    Run a counterfactual simulation to predict outcomes of clause changes.

    Args:
        contract_id: Identifier for the contract
        contract_text: Full contract text for context
        original_clause: Original contract clause
        modified_clause: Modified/counterfactual clause to test
        user: Django User object (optional, for saving scenarios)
        filters: Optional filters for similarity search (contract_type, industry)

    Returns:
        Dict containing simulation results, similar outcomes, and confidence metrics
    """
    logger.info(f"Starting counterfactual simulation for contract {contract_id}")

    try:
        # Step 1: Generate embedding for the modified clause context
        combined_text = f"{modified_clause}\n\nContext: {contract_text[:500]}"
        embedding = generate_clause_embedding(combined_text)

        # Step 2: Search for similar historical outcomes
        similar_outcomes = search_similar_outcomes(
            embedding_vector=embedding,
            limit=5,
            filters=filters
        )

        logger.info(f"Found {len(similar_outcomes)} similar historical outcomes")

        # Step 3: Run LLM-based counterfactual reasoning
        llm_client = get_llm_client()
        simulation_result = llm_client.run_counterfactual_simulation(
            contract_text=contract_text,
            original_clause=original_clause,
            modified_clause=modified_clause,
            similar_outcomes=similar_outcomes
        )

        # Step 4: Calculate risk delta
        risk_delta = _calculate_risk_delta(
            original_clause=original_clause,
            modified_clause=modified_clause,
            similar_outcomes=similar_outcomes,
            simulation_result=simulation_result
        )

        # Step 5: Format comprehensive result
        result = {
            "contract_id": contract_id,
            "simulation": simulation_result,
            "similar_outcomes": similar_outcomes,
            "risk_delta": risk_delta,
            "confidence_score": simulation_result.get("confidence_score", 0.75),
            "metadata": {
                "num_similar_contracts": len(similar_outcomes),
                "average_similarity_score": _calculate_average_similarity(similar_outcomes),
                "risk_level": simulation_result.get("risk_level", "MEDIUM")
            }
        }

        # Step 6: Save scenario if user provided
        if user:
            _save_scenario(
                contract_id=contract_id,
                user=user,
                original_clause=original_clause,
                modified_clause=modified_clause,
                result=result
            )

        logger.info(f"Counterfactual simulation completed successfully")
        return result

    except Exception as e:
        logger.error(f"Error in counterfactual simulation: {e}")
        return {
            "error": str(e),
            "contract_id": contract_id,
            "status": "failed"
        }


def _calculate_risk_delta(
    original_clause: str,
    modified_clause: str,
    similar_outcomes: List[Dict],
    simulation_result: Dict
) -> float:
    """
    Calculate the change in risk level from original to modified clause.

    Args:
        original_clause: Original clause text
        modified_clause: Modified clause text
        similar_outcomes: List of similar historical outcomes
        simulation_result: LLM simulation results

    Returns:
        Float between -1.0 (much safer) and 1.0 (much riskier)
    """
    # Extract risk indicators from similar outcomes
    dispute_rate = sum(1 for o in similar_outcomes if o.get('dispute_occurred', False)) / max(len(similar_outcomes), 1)
    litigation_rate = sum(1 for o in similar_outcomes if o.get('litigation_occurred', False)) / max(len(similar_outcomes), 1)

    # Map risk level to numeric score
    risk_map = {'LOW': -0.3, 'MEDIUM': 0.0, 'HIGH': 0.5}
    risk_score = risk_map.get(simulation_result.get('risk_level', 'MEDIUM'), 0.0)

    # Combine factors
    delta = (dispute_rate * 0.4) + (litigation_rate * 0.4) + (risk_score * 0.2)

    # Clamp between -1.0 and 1.0
    return max(-1.0, min(1.0, delta))


def _calculate_average_similarity(similar_outcomes: List[Dict]) -> float:
    """
    Calculate average similarity score from outcomes.

    Args:
        similar_outcomes: List of outcome dicts with 'score' field

    Returns:
        Average similarity score
    """
    if not similar_outcomes:
        return 0.0

    scores = [o.get('score', 0) for o in similar_outcomes]
    return sum(scores) / len(scores)


def _save_scenario(
    contract_id: str,
    user,
    original_clause: str,
    modified_clause: str,
    result: Dict
):
    """
    Save counterfactual scenario to database.

    Args:
        contract_id: Contract identifier
        user: Django User object
        original_clause: Original clause text
        modified_clause: Modified clause text
        result: Simulation result dict
    """
    try:
        scenario = CounterfactualScenario.objects.create(
            contract_id=contract_id,
            user=user,
            original_clause=original_clause,
            modified_clause=modified_clause,
            simulated_outcome=result.get('simulation', {}),
            confidence_score=result.get('confidence_score', 0.75),
            risk_delta=result.get('risk_delta', 0.0),
            business_impact=result.get('simulation', {}).get('business_impact'),
            legal_impact=result.get('simulation', {}).get('legal_impact'),
            operational_impact=result.get('simulation', {}).get('operational_impact'),
        )
        logger.info(f"Saved counterfactual scenario {scenario.id}")
        return scenario
    except Exception as e:
        logger.error(f"Error saving counterfactual scenario: {e}")
        return None


def get_user_scenarios(user, contract_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """
    Get counterfactual scenarios for a user.

    Args:
        user: Django User object
        contract_id: Optional contract ID filter
        limit: Maximum number of scenarios to return

    Returns:
        List of scenario dicts
    """
    try:
        queryset = CounterfactualScenario.objects.filter(user=user).order_by('-created_at')

        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)

        scenarios = queryset[:limit]

        return [
            {
                "id": s.id,
                "contract_id": s.contract_id,
                "original_clause": s.original_clause,
                "modified_clause": s.modified_clause,
                "confidence_score": s.confidence_score,
                "risk_delta": s.risk_delta,
                "risk_level": s.simulated_outcome.get('risk_level'),
                "created_at": s.created_at.isoformat(),
            }
            for s in scenarios
        ]

    except Exception as e:
        logger.error(f"Error retrieving user scenarios: {e}")
        return []


def compare_multiple_scenarios(
    contract_id: str,
    contract_text: str,
    original_clause: str,
    modified_clauses: List[str],
    user=None
) -> Dict:
    """
    Compare multiple counterfactual scenarios side-by-side.

    Args:
        contract_id: Contract identifier
        contract_text: Full contract text
        original_clause: Original clause
        modified_clauses: List of alternative clause versions
        user: Django User object (optional)

    Returns:
        Dict with comparative analysis
    """
    logger.info(f"Comparing {len(modified_clauses)} scenarios for contract {contract_id}")

    results = []

    for i, modified_clause in enumerate(modified_clauses, 1):
        logger.info(f"Simulating scenario {i}/{len(modified_clauses)}")

        result = simulate_counterfactual(
            contract_id=contract_id,
            contract_text=contract_text,
            original_clause=original_clause,
            modified_clause=modified_clause,
            user=user
        )

        results.append({
            "scenario_number": i,
            "modified_clause": modified_clause,
            "result": result
        })

    # Rank scenarios by risk
    ranked = sorted(
        results,
        key=lambda x: x['result'].get('risk_delta', 0)
    )

    return {
        "contract_id": contract_id,
        "num_scenarios": len(modified_clauses),
        "scenarios": results,
        "ranked_by_risk": ranked,
        "recommendation": ranked[0] if ranked else None  # Lowest risk option
    }
