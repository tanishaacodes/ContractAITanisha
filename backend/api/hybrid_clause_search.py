"""
Hybrid Clause Search Pipeline
==============================
Multi-stage semantic search combining BM25 + BERT + GraphRAG + LLM re-ranking.

Based on PDF requirements:
- Stage 1: BM25Okapi for keyword search (fast retrieval)
- Stage 2: BERT semantic search (semantic matching)
- Stage 3: Neo4j graph context retrieval (related clauses, risks)
- Stage 4: Qwen LLM re-ranking (final ordering)

Usage:
    searcher = get_hybrid_searcher()
    results = searcher.search("payment within 30 days", limit=10, mode='hybrid')
"""

import logging
from typing import List, Dict, Optional, Literal
from rank_bm25 import BM25Okapi
import numpy as np

from core.models import Clause
from .clause_clustering import get_clusterer
from .qdrant_service import get_qdrant_service

logger = logging.getLogger(__name__)


class HybridClauseSearcher:
    """
    Multi-stage hybrid search combining keyword, semantic, graph, and LLM approaches.
    """

    def __init__(self):
        """Initialize the hybrid searcher."""
        self.bm25_index = None
        self.clause_texts = []
        self.clause_ids = []
        self.tokenized_corpus = []
        self.clusterer = get_clusterer()
        self.qdrant = get_qdrant_service()

        logger.info("HybridClauseSearcher initialized")
        self._build_bm25_index()

    def _build_bm25_index(self):
        """Build BM25 index from all clauses in database."""
        try:
            clauses = Clause.objects.filter(
                extracted_text__isnull=False
            ).exclude(extracted_text='')[:5000]  # Limit for performance

            if not clauses.exists():
                logger.warning("No clauses found for BM25 indexing")
                return

            self.clause_texts = []
            self.clause_ids = []
            self.tokenized_corpus = []

            for clause in clauses:
                text = clause.extracted_text or clause.clause_name or ''
                if text.strip():
                    self.clause_texts.append(text)
                    self.clause_ids.append(str(clause.id))
                    # Simple tokenization (split by whitespace and lowercase)
                    tokens = text.lower().split()
                    self.tokenized_corpus.append(tokens)

            if self.tokenized_corpus:
                self.bm25_index = BM25Okapi(self.tokenized_corpus)
                logger.info(f"Built BM25 index with {len(self.clause_texts)} clauses")
            else:
                logger.warning("No valid texts for BM25 indexing")

        except Exception as e:
            logger.error(f"Failed to build BM25 index: {e}", exc_info=True)

    def search_bm25(self, query: str, limit: int = 10, contract_id: str = None) -> List[Dict]:
        """
        Stage 1: BM25 keyword search, scoped to a single contract if contract_id given.
        """
        if not self.bm25_index or not self.clause_texts:
            logger.warning("BM25 index not available")
            return []

        try:
            # Tokenize query
            query_tokens = query.lower().split()

            # Get BM25 scores
            scores = self.bm25_index.get_scores(query_tokens)

            # Get top N indices — pre-filter by contract_id if provided
            top_indices = np.argsort(scores)[::-1]

            # Fetch metadata for top results in one query
            top_clause_ids = [self.clause_ids[idx] for idx in top_indices if scores[idx] > 0]
            meta_map = {}
            if top_clause_ids:
                qs = Clause.objects.filter(id__in=top_clause_ids).select_related('contract')
                if contract_id:
                    qs = qs.filter(contract_id=contract_id)
                for c in qs:
                    meta_map[str(c.id)] = {
                        'clause_name': c.clause_name or '',
                        'clause_type': c.clause_type or '',
                        'risk_level': c.risk_level or '',
                        'risk_score': float(c.risk_score or 0),
                        'contract_name': c.contract.original_filename if c.contract else '',
                        'contract_id': str(c.contract_id) if c.contract_id else '',
                    }

            results = []
            for idx in top_indices:
                if scores[idx] > 0:
                    cid = self.clause_ids[idx]
                    # Skip if not in this contract
                    if cid not in meta_map:
                        continue
                    meta = meta_map[cid]
                    results.append({
                        'clause_id': cid,
                        'text': self.clause_texts[idx],
                        'bm25_score': float(scores[idx]),
                        'source': 'BM25',
                        **meta,
                    })
                    if len(results) >= limit:
                        break

            logger.debug(f"BM25 search found {len(results)} results for '{query}'")
            return results

        except Exception as e:
            logger.error(f"BM25 search failed: {e}", exc_info=True)
            return []

    def search_bert(self, query: str, limit: int = 10, contract_id: str = None) -> List[Dict]:
        """
        Stage 2: BERT semantic search via Qdrant.

        Args:
            query (str): Search query
            limit (int): Maximum results
            contract_id (str, optional): Filter by contract

        Returns:
            List[Dict]: Search results with semantic scores
        """
        if not self.qdrant or not self.qdrant.client:
            logger.warning("Qdrant not available for BERT search")
            return []

        try:
            # Generate query embedding
            query_embedding = self.clusterer.embed_clauses([query], batch_size=1)[0]

            # Search in Qdrant
            results = self.qdrant.search_similar_clauses(
                query_embedding=query_embedding,
                limit=limit,
                contract_id=contract_id
            )

            # Format results — deduplicate by clause_id, keep highest score
            seen = {}
            for result in results:
                cid = result.get('clause_id')
                if not cid:
                    continue
                score = result.get('score', 0.0)
                if cid not in seen or score > seen[cid]['bert_score']:
                    seen[cid] = {
                        'clause_id': cid,
                        'clause_text': result.get('clause_text', ''),
                        'bert_score': score,
                        'source': 'BERT',
                    }

            # Enrich with DB metadata — filter by contract_id if provided
            if seen:
                qs = Clause.objects.filter(id__in=seen.keys()).select_related('contract')
                if contract_id:
                    qs = qs.filter(contract_id=contract_id)
                    # Remove results not belonging to this contract
                    valid_ids = set(str(c.id) for c in qs)
                    seen = {k: v for k, v in seen.items() if k in valid_ids}
                    qs = Clause.objects.filter(id__in=seen.keys()).select_related('contract')
                for c in qs:
                    cid = str(c.id)
                    if cid in seen:
                        seen[cid]['clause_name'] = c.clause_name or ''
                        seen[cid]['clause_type'] = c.clause_type or ''
                        seen[cid]['risk_level'] = c.risk_level or ''
                        seen[cid]['risk_score'] = float(c.risk_score or 0)
                        seen[cid]['contract_name'] = c.contract.original_filename if c.contract else ''
                        seen[cid]['text'] = c.extracted_text or seen[cid].get('clause_text', '')

            formatted_results = sorted(seen.values(), key=lambda x: x['bert_score'], reverse=True)
            logger.debug(f"BERT search found {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"BERT search failed: {e}", exc_info=True)
            return []

    def search_graph(self, query: str, limit: int = 10, contract_id: str = None) -> List[Dict]:
        """
        Stage 3: GraphRAG context retrieval.
        Tries Neo4j first (MATCH clause→risk graph), falls back to MySQL risk-weighted keyword expansion.
        Scoped to contract_id if provided.
        """
        # --- Try Neo4j first ---
        try:
            from django.conf import settings
            from neo4j import GraphDatabase
            neo4j_uri = getattr(settings, 'NEO4J_URI', None)
            neo4j_user = getattr(settings, 'NEO4J_USER', 'neo4j')
            neo4j_pass = getattr(settings, 'NEO4J_PASSWORD', '')
            if neo4j_uri:
                driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
                cypher = """
                    MATCH (c:Clause)-[:HAS_RISK]->(r:Risk)
                    WHERE toLower(c.text) CONTAINS toLower($query)
                       OR toLower(c.clause_type) CONTAINS toLower($query)
                    RETURN c.clause_id AS clause_id, c.text AS text,
                           c.clause_type AS clause_type, r.score AS risk_score,
                           r.category AS risk_category
                    ORDER BY r.score DESC
                    LIMIT $limit
                """
                with driver.session() as session:
                    rows = session.run(cypher, query=query, limit=limit)
                    neo4j_results = []
                    for row in rows:
                        cid = str(row['clause_id'])
                        # Skip if not in this contract
                        if contract_id:
                            try:
                                clause = Clause.objects.get(id=cid)
                                if str(clause.contract_id) != str(contract_id):
                                    continue
                            except Exception:
                                continue
                        neo4j_results.append({
                            'clause_id': cid,
                            'text': row['text'] or '',
                            'graph_score': float(row['risk_score'] or 0.3),
                            'risk_category': row['risk_category'] or '',
                            'clause_type': row['clause_type'] or '',
                            'source': 'GraphRAG',
                            'contract_id': contract_id or '',
                        })
                driver.close()
                if neo4j_results:
                    logger.debug(f"Neo4j GraphRAG found {len(neo4j_results)} results")
                    return neo4j_results
        except Exception as e:
            logger.debug(f"Neo4j GraphRAG unavailable, falling back to MySQL: {e}")

        # --- Fallback: MySQL risk-weighted keyword expansion ---
        try:
            from django.db.models import Q
            query_lower = query.lower()
            words = [w for w in query_lower.split() if len(w) > 3]
            if not words:
                return []

            q_filter = Q()
            for w in words[:5]:
                q_filter |= Q(clause_type__icontains=w) | Q(clause_name__icontains=w) | Q(extracted_text__icontains=w)

            qs = Clause.objects.filter(q_filter).exclude(extracted_text='').exclude(extracted_text__isnull=True)
            if contract_id:
                qs = qs.filter(contract_id=contract_id)
            graph_clauses = qs.order_by('-risk_score').select_related('contract')[:limit]

            results = []
            for clause in graph_clauses:
                results.append({
                    'clause_id': str(clause.id),
                    'text': clause.extracted_text or '',
                    'clause_name': clause.clause_name or '',
                    'clause_type': clause.clause_type or '',
                    'risk_level': clause.risk_level or '',
                    'risk_score': float(clause.risk_score or 0),
                    'contract_name': clause.contract.original_filename if clause.contract else '',
                    'contract_id': str(clause.contract_id) if clause.contract_id else '',
                    'graph_score': float(clause.risk_score or 0.3),
                    'source': 'GraphRAG',
                })
            logger.debug(f"MySQL GraphRAG fallback found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"GraphRAG search failed: {e}", exc_info=True)
            return []

    def rerank_with_llm(self, query: str, results: List[Dict], top_n: int = 10) -> List[Dict]:
        """
        Stage 4: Advanced LLM re-ranking using Qwen 2.5 via Ollama.
        Single batch prompt — ranks all top candidates at once instead of per-clause calls.
        Falls back to weighted score combination on failure.
        """
        import re, requests
        from django.conf import settings

        if not results:
            return results

        # Pre-score with weighted combination (BM25 + BERT + GraphRAG)
        for r in results:
            bm25_n = min(float(r.get('bm25_score', 0)) / 10.0, 1.0)
            bert_s = float(r.get('bert_score', 0))
            graph_s = float(r.get('graph_score', 0))
            rrf_s = float(r.get('rrf_score', 0)) * 100
            r['combined_score'] = round(0.30 * bm25_n + 0.45 * bert_s + 0.15 * graph_s + 0.10 * rrf_s, 4)

        results.sort(key=lambda x: x['combined_score'], reverse=True)
        candidates = results[:min(top_n, 8)]  # rerank top 8 max
        rest = results[len(candidates):]

        # Build single batch prompt — much faster than per-clause calls
        try:
            numbered = []
            for i, r in enumerate(candidates):
                text_snippet = (r.get('text') or r.get('clause_text') or '')[:200].replace('\n', ' ')
                cname = r.get('clause_name') or r.get('clause_type') or f'Clause {i+1}'
                numbered.append(f"{i+1}. [{cname}] {text_snippet}")

            prompt = (
                f"You are a contract AI. Rank these {len(numbered)} contract clauses by relevance to the query.\n"
                f"Query: \"{query}\"\n\n"
                f"Clauses:\n" + "\n".join(numbered) +
                f"\n\nOutput ONLY a comma-separated list of numbers in order of relevance (most relevant first).\n"
                f"Example: 3,1,2,4\nRanking:"
            )

            resp = requests.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={"model": "qwen2.5:0.5b", "prompt": prompt, "stream": False},
                timeout=20,
            )
            raw = resp.json().get('response', '').strip()

            # Parse ranking: extract numbers from response
            nums = [int(x.strip()) for x in re.findall(r'\d+', raw) if 1 <= int(x.strip()) <= len(candidates)]
            # Deduplicate while preserving order
            seen_n = set()
            ranking = [n for n in nums if not (n in seen_n or seen_n.add(n))]
            # Add any missing indices at end
            for i in range(1, len(candidates) + 1):
                if i not in seen_n:
                    ranking.append(i)

            # Reorder candidates by LLM ranking
            reranked = []
            for rank_pos, idx in enumerate(ranking):
                c = candidates[idx - 1]
                c['llm_rank'] = rank_pos + 1
                c['llm_score'] = round(1.0 - (rank_pos / len(ranking)), 4)
                c['final_score'] = round(0.6 * c['llm_score'] + 0.4 * c['combined_score'], 4)
                reranked.append(c)

            logger.info(f"LLM batch re-ranking completed: {raw[:60]}")
            return (reranked + rest)[:top_n]

        except Exception as e:
            logger.warning(f"LLM rerank failed, using combined score: {e}")
            for r in candidates:
                r['final_score'] = r['combined_score']
                r['llm_score'] = 0.0
            return (candidates + rest)[:top_n]

    def search(
        self,
        query: str,
        limit: int = 10,
        mode: Literal['bm25', 'bert', 'hybrid'] = 'hybrid',
        contract_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Unified search interface with mode selection.

        Args:
            query (str): Search query
            limit (int): Maximum results to return
            mode (str): Search mode - 'bm25', 'bert', or 'hybrid'
            contract_id (Optional[str]): Filter by contract ID

        Returns:
            List[Dict]: Search results with scores and metadata
        """
        if not query or not query.strip():
            return []

        logger.info(f"Hybrid search: query='{query}', mode={mode}, limit={limit}")

        if mode == 'bm25':
            results = self.search_bm25(query, limit=limit, contract_id=contract_id)
            return results

        elif mode == 'bert':
            # BERT only
            results = self.search_bert(query, limit=limit, contract_id=contract_id)
            return results

        elif mode == 'hybrid':
            # Stage 1: BM25 keyword retrieval
            bm25_results = self.search_bm25(query, limit=limit * 2, contract_id=contract_id)

            # Stage 2: BERT semantic search
            try:
                bert_results = self.search_bert(query, limit=limit * 2, contract_id=contract_id)
            except Exception:
                bert_results = []

            # Stage 3: GraphRAG context expansion
            try:
                graph_results = self.search_graph(query, limit=limit, contract_id=contract_id)
            except Exception:
                graph_results = []

            # Merge all 3 sources with Reciprocal Rank Fusion
            merged = {}
            for rank, r in enumerate(bm25_results):
                cid = r['clause_id']
                merged[cid] = r.copy()
                merged[cid]['rrf_score'] = 1.0 / (rank + 60)

            for rank, r in enumerate(bert_results):
                cid = r['clause_id']
                if cid in merged:
                    merged[cid]['rrf_score'] += 1.0 / (rank + 60)
                    merged[cid]['bert_score'] = r.get('bert_score', 0)
                else:
                    merged[cid] = r.copy()
                    merged[cid]['rrf_score'] = 1.0 / (rank + 60)

            for rank, r in enumerate(graph_results):
                cid = r['clause_id']
                if cid in merged:
                    merged[cid]['rrf_score'] += 1.0 / (rank + 60)
                    merged[cid]['graph_score'] = r.get('graph_score', 0)
                    merged[cid]['risk_category'] = r.get('risk_category', '')
                else:
                    merged[cid] = r.copy()
                    merged[cid]['rrf_score'] = 1.0 / (rank + 60)

            # Hard filter: only results from the current contract
            if contract_id:
                merged = {k: v for k, v in merged.items() if v.get('contract_id') == str(contract_id)}

            # Mark source as HYBRID for merged results
            for v in merged.values():
                v['source'] = 'HYBRID'

            combined = sorted(merged.values(), key=lambda x: x.get('rrf_score', 0), reverse=True)

            # Stage 4: Qwen LLM re-ranking of top candidates
            final_results = self.rerank_with_llm(query, combined, top_n=limit)

            logger.info(f"Hybrid search (BM25+BERT+GraphRAG+LLM) returned {len(final_results)} results")
            return final_results

        else:
            logger.error(f"Invalid search mode: {mode}")
            return []

    def rebuild_index(self):
        """Rebuild the BM25 index with latest clauses."""
        logger.info("Rebuilding BM25 index...")
        self._build_bm25_index()


# Singleton instance
_searcher_instance: Optional[HybridClauseSearcher] = None


def get_hybrid_searcher() -> HybridClauseSearcher:
    """
    Get singleton instance of hybrid clause searcher.

    Returns:
        HybridClauseSearcher: The searcher instance
    """
    global _searcher_instance
    if _searcher_instance is None:
        _searcher_instance = HybridClauseSearcher()
    return _searcher_instance


# Convenience function
def search_clauses(
    query: str,
    limit: int = 10,
    mode: Literal['bm25', 'bert', 'hybrid'] = 'hybrid',
    contract_id: Optional[str] = None
) -> List[Dict]:
    """
    Quick search interface.

    Args:
        query (str): Search query
        limit (int): Maximum results
        mode (str): Search mode
        contract_id (Optional[str]): Filter by contract

    Returns:
        List[Dict]: Search results
    """
    searcher = get_hybrid_searcher()
    return searcher.search(query, limit=limit, mode=mode, contract_id=contract_id)
