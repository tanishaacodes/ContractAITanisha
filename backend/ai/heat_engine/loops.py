"""
Negotiation Loop Detection

Detects repetitive back-and-forth patterns using semantic similarity.
"""
from sentence_transformers import SentenceTransformer
import numpy as np

# Lazy-loaded to avoid startup memory exhaustion on Windows
_model = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2", device='cpu')
    return _model


def detect_loops(redlines, similarity_threshold=0.92):
    """
    Detect negotiation loops via semantic similarity.

    A loop occurs when consecutive redlines are highly similar,
    indicating parties are repeating arguments.

    Args:
        redlines: List of redline texts (chronological order)
        similarity_threshold: Cosine similarity threshold for loop detection

    Returns:
        dict: Loop analysis
    """
    if not redlines or len(redlines) < 2:
        return {
            "loop_count": 0,
            "has_loops": False,
            "loop_positions": [],
            "avg_similarity": 0
        }

    # Embed all redlines
    embeddings = _get_model().encode(redlines)

    # Calculate consecutive similarities
    similarities = []
    loop_positions = []

    for i in range(len(embeddings) - 1):
        sim = cosine_similarity(embeddings[i], embeddings[i + 1])
        similarities.append(sim)

        if sim > similarity_threshold:
            loop_positions.append({
                "round": i + 1,
                "similarity": float(sim)
            })

    loop_count = len(loop_positions)

    return {
        "loop_count": loop_count,
        "has_loops": loop_count > 0,
        "loop_positions": loop_positions,
        "avg_similarity": float(np.mean(similarities)) if similarities else 0,
        "max_similarity": float(np.max(similarities)) if similarities else 0,
        "stalled": loop_count >= 2  # Multiple loops = stalled
    }


def cosine_similarity(vec_a, vec_b):
    """Calculate cosine similarity between two vectors."""
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))


def detect_ping_pong(redlines, window=4):
    """
    Detect ping-pong pattern: A → B → A → B

    Args:
        redlines: List of redline texts
        window: Window size for pattern detection

    Returns:
        dict: Ping-pong analysis
    """
    if len(redlines) < window:
        return {
            "has_ping_pong": False,
            "patterns": []
        }

    embeddings = _get_model().encode(redlines)
    patterns = []

    for i in range(len(embeddings) - window + 1):
        window_embs = embeddings[i:i + window]

        # Check if positions 0 & 2 are similar, and 1 & 3 are similar
        # (but 0 & 1 are different)
        sim_0_2 = cosine_similarity(window_embs[0], window_embs[2])
        sim_1_3 = cosine_similarity(window_embs[1], window_embs[3])
        sim_0_1 = cosine_similarity(window_embs[0], window_embs[1])

        if sim_0_2 > 0.85 and sim_1_3 > 0.85 and sim_0_1 < 0.7:
            patterns.append({
                "start_round": i,
                "end_round": i + window - 1,
                "similarity_a": float(sim_0_2),
                "similarity_b": float(sim_1_3)
            })

    return {
        "has_ping_pong": len(patterns) > 0,
        "pattern_count": len(patterns),
        "patterns": patterns
    }


def loop_severity(loop_count, avg_rounds):
    """
    Calculate loop severity score.

    Args:
        loop_count: Number of detected loops
        avg_rounds: Average negotiation rounds for this clause type

    Returns:
        float: Severity (0-1)
    """
    # Normalize loop count against expected rounds
    expected_loops = max(1, avg_rounds / 3)
    severity = min(1.0, loop_count / expected_loops)

    return severity


def predict_stall_probability(loops, rounds, friction):
    """
    Predict probability that negotiation will stall.

    Args:
        loops: Number of loops detected
        rounds: Total rounds so far
        friction: Emotional friction score

    Returns:
        float: Stall probability (0-1)
    """
    # Factors:
    # 1. High loop count
    # 2. Many rounds without progress
    # 3. High emotional friction

    loop_factor = min(1.0, loops / 3)
    rounds_factor = min(1.0, rounds / 8)
    friction_factor = friction

    # Weighted combination
    stall_prob = (
        0.4 * loop_factor +
        0.3 * rounds_factor +
        0.3 * friction_factor
    )

    return min(1.0, stall_prob)
