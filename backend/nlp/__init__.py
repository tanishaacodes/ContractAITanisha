"""
NLP Module for Contract AI
===========================
Natural Language Processing utilities for contract analysis.
"""

from .clause_extractor import (
    split_into_clauses,
    extract_clause_with_metadata,
    identify_clause_type_by_keywords,
    merge_short_clauses
)

from .embedding import (
    ClauseEmbedder,
    get_embedder,
    embed_clauses
)

from .clustering import (
    ClauseClusterer,
    cluster_clauses,
    group_clauses_by_cluster,
    find_optimal_k,
    get_cluster_statistics
)

__all__ = [
    'split_into_clauses',
    'extract_clause_with_metadata',
    'identify_clause_type_by_keywords',
    'merge_short_clauses',
    'ClauseEmbedder',
    'get_embedder',
    'embed_clauses',
    'ClauseClusterer',
    'cluster_clauses',
    'group_clauses_by_cluster',
    'find_optimal_k',
    'get_cluster_statistics'
]
