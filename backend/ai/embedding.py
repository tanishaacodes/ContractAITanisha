"""
Embedding Engine – thin wrapper around EmbeddingService singleton.
Supports whichever model is currently selected (MiniLM or BERT-large).
"""
from api.embedding_service import embedding_service


def embed(text: str):
    """Generate embedding for a given text using the active model."""
    return embedding_service.embed_text(text)


def embed_batch(texts: list):
    """Generate embeddings for multiple texts using the active model."""
    return embedding_service.embed_batch(texts)


def embed_clause_pair(clause_a: str, clause_b: str):
    """
    Generate embedding for a pair of clauses.
    Used for detecting emergent risks from clause interactions.

    Args:
        clause_a: First clause text
        clause_b: Second clause text

    Returns:
        List of floats representing the clause-pair embedding
    """
    combined = f"{clause_a} || {clause_b}"
    return embed(combined)


def embed_clause_pairs(clause_pairs: list):
    """
    Generate embeddings for multiple clause pairs

    Args:
        clause_pairs: List of tuples [(clause_a, clause_b), ...]

    Returns:
        List of embeddings
    """
    combined_texts = [f"{a} || {b}" for a, b in clause_pairs]
    return embed_batch(combined_texts)
