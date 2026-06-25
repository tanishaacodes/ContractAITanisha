"""
Advanced Clause Library – Taxonomy Engine & Continuous Pipeline

Responsibilities:
  1. Seed the standard 50+ clause taxonomy once
  2. LDA topic modeling for unsupervised clause discovery
  3. Assign new clause texts to categories via MiniLM cosine similarity
     (FAISS index for scalable ANN search)
  4. Qwen 2.5 auto-naming for new category nodes
  5. Periodic taxonomy cleaning – merge near-duplicate categories
  6. Build tree JSON for the frontend
  7. Neo4j ingestion: Clause-[:BELONGS_TO]->Category, Clause-[:SIMILAR_TO]->Clause
"""

import logging
import os
import json
import hashlib
import numpy as np
from typing import Optional, List, Dict, Tuple

import requests
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer

from core.models import ClauseCategory, Clause, Contract
from django.conf import settings

logger = logging.getLogger(__name__)

# ── Similarity thresholds ────────────────────────────────────────────────────
ASSIGN_THRESHOLD = 0.72
SUBCATEGORY_THRESHOLD = 0.55
MERGE_THRESHOLD = 0.88
SIMILAR_CLAUSE_THRESHOLD = 0.85   # for Neo4j SIMILAR_TO edges

# ── Lazy singletons ──────────────────────────────────────────────────────────
_embed_model: Optional[SentenceTransformer] = None
_faiss_index = None          # faiss.IndexFlatIP
_faiss_ids: List[str] = []   # category ids in FAISS order


def _get_embed_model() -> SentenceTransformer:
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embed_model


def _get_redis():
    try:
        import redis
        r = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_CACHE_DB', 1)),
        )
        r.ping()
        return r
    except Exception:
        return None


# ── Standard legal taxonomy seed ────────────────────────────────────────────
STANDARD_TAXONOMY: Dict[str, List[str]] = {
    "Indemnification": [
        "Third Party Claims", "IP Indemnity", "Employee Claims",
        "Tax Indemnity", "Environmental Indemnity",
    ],
    "Liability": [
        "Limitation of Liability", "Indirect Damages",
        "Consequential Damages", "Liability Cap", "Gross Negligence Carve-out",
    ],
    "Intellectual Property": [
        "Ownership", "Licensing", "Work Product",
        "Patent Rights", "Trademark Usage", "Open Source Compliance",
    ],
    "Confidentiality": [
        "Non-Disclosure", "Data Protection", "Trade Secrets",
        "Confidential Handling", "Return of Materials",
    ],
    "Termination": [
        "Termination for Convenience", "Termination for Cause",
        "Exit Obligations", "Survival Clauses", "Wind-Down Period",
    ],
    "Payment": [
        "Pricing", "Invoicing", "Late Fees",
        "Milestones", "Currency", "Set-Off Rights",
        "Payment Terms",
    ],
    "Dispute Resolution": [
        "Arbitration", "Litigation", "Governing Law",
        "Jurisdiction", "Mediation", "Expert Determination",
    ],
    "Compliance": [
        "Regulatory Compliance", "Anti-Bribery", "Export Control",
        "Ethics", "Sanctions", "Modern Slavery",
    ],
    "Security": [
        "Cybersecurity", "Access Control", "Data Breach",
        "Encryption", "Penetration Testing", "Security Audit",
    ],
    "Service Levels": [
        "SLA", "Penalties", "Uptime", "Response Time",
        "Escalation Procedure", "Measurement Period",
    ],
    "Force Majeure": [
        "Definition", "Notice Requirements", "Mitigation Obligations",
        "Termination Right", "Change in Law",
    ],
    "Assignment": [
        "Assignment Restriction", "Change of Control",
        "Sub-contracting", "Novation",
    ],
    "Warranty": [
        "Product Warranty", "Service Warranty", "Disclaimer",
        "Fitness for Purpose", "Warranty Period",
    ],
    "Insurance": [
        "Coverage Requirements", "Additional Insured", "Evidence of Insurance",
        "Professional Indemnity", "Product Liability",
    ],
    "Audit Rights": [
        "Financial Audit", "Compliance Audit", "Data Audit",
        "Record Retention", "Audit Costs",
    ],
}


# ── FAISS helpers ────────────────────────────────────────────────────────────

def _build_faiss_index(embeddings: np.ndarray, ids: List[str]):
    """(Re)build a flat inner-product FAISS index over category embeddings."""
    global _faiss_index, _faiss_ids
    try:
        import faiss
        dim = embeddings.shape[1]
        vecs = embeddings.astype('float32')
        faiss.normalize_L2(vecs)
        index = faiss.IndexFlatIP(dim)
        index.add(vecs)
        _faiss_index = index
        _faiss_ids = list(ids)
        logger.info(f"FAISS index built: {index.ntotal} vectors, dim={dim}")
    except Exception as e:
        logger.warning(f"FAISS unavailable: {e}")
        _faiss_index = None
        _faiss_ids = []


def _faiss_search(query_vec: np.ndarray, top_k: int = 1) -> List[Tuple[str, float]]:
    """Return (category_id, score) pairs from FAISS, or [] if unavailable."""
    if _faiss_index is None or not _faiss_ids:
        return []
    try:
        import faiss
        v = query_vec.astype('float32').reshape(1, -1)
        faiss.normalize_L2(v)
        scores, indices = _faiss_index.search(v, min(top_k, len(_faiss_ids)))
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0:
                results.append((_faiss_ids[idx], float(score)))
        return results
    except Exception as e:
        logger.warning(f"FAISS search error: {e}")
        return []


# ── Qwen helpers ─────────────────────────────────────────────────────────────

def _qwen_name_category(clause_text: str) -> str:
    """Ask Qwen 2.5 to summarize a clause into a 2-5 word legal category name."""
    try:
        ollama_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        prompt = (
            "You are a legal expert. Read this contract clause and respond with ONLY "
            "a 2-5 word legal category name (e.g. 'Indemnification – Third Party', "
            "'IP Ownership – Work Product'). No explanation.\n\nClause:\n"
            + clause_text[:500]
        )
        resp = requests.post(
            f"{ollama_url}/api/generate",
            json={"model": "qwen2.5:0.5b", "prompt": prompt, "stream": False},
            timeout=20,
        )
        if resp.status_code == 200:
            name = resp.json().get('response', '').strip().split('\n')[0][:120]
            if name:
                return name
    except Exception as e:
        logger.warning(f"Qwen naming failed: {e}")
    # fallback: first 80 chars
    return clause_text[:80].strip()


def _qwen_rerank(query: str, clauses: List[Dict]) -> List[Dict]:
    """
    Ask Qwen to rerank up to 10 clauses and return structured scores.
    Falls back gracefully if Ollama is down.
    """
    if not clauses:
        return clauses
    try:
        ollama_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        numbered = "\n".join(
            f"{i+1}. {c['text'][:200]}" for i, c in enumerate(clauses[:10])
        )
        prompt = (
            "You are a legal AI assistant. Given the user query and the following numbered "
            "contract clauses, return a JSON array ranking them from most to least relevant.\n"
            'Format: [{"index": 1, "score": 85, "reason": "..."}]\n'
            "Only return valid JSON, no markdown.\n\n"
            f"Query: {query}\n\nClauses:\n{numbered}"
        )
        resp = requests.post(
            f"{ollama_url}/api/generate",
            json={"model": "qwen2.5:0.5b", "prompt": prompt, "stream": False},
            timeout=35,
        )
        if resp.status_code == 200:
            raw = resp.json().get('response', '')
            start, end = raw.find('['), raw.rfind(']')
            if start != -1 and end != -1:
                ranked_meta = json.loads(raw[start:end+1])
                reranked = []
                used = set()
                for item in ranked_meta:
                    idx = int(item.get('index', 0)) - 1
                    if 0 <= idx < len(clauses) and idx not in used:
                        used.add(idx)
                        c = dict(clauses[idx])
                        c['qwen_score'] = item.get('score', 50)
                        c['qwen_reason'] = item.get('reason', '')
                        reranked.append(c)
                # append any clauses Qwen didn't mention
                for i, c in enumerate(clauses):
                    if i not in used:
                        c2 = dict(c)
                        c2['qwen_score'] = 0
                        c2['qwen_reason'] = ''
                        reranked.append(c2)
                return reranked
    except Exception as e:
        logger.warning(f"Qwen rerank failed: {e}")
    # fallback: return as-is with empty qwen fields
    for c in clauses:
        c.setdefault('qwen_score', 50)
        c.setdefault('qwen_reason', '')
    return clauses


# ── LDA topic modeling ────────────────────────────────────────────────────────

def run_lda_discovery(texts: List[str], n_topics: int = 10) -> List[str]:
    """
    Run LDA on a list of clause texts and return top keywords per topic
    as candidate new category names (for surfacing to taxonomy engine).
    """
    if len(texts) < n_topics:
        return []
    try:
        vectorizer = CountVectorizer(
            max_df=0.9, min_df=2, max_features=500,
            stop_words='english', ngram_range=(1, 2),
        )
        dtm = vectorizer.fit_transform(texts)
        lda = LatentDirichletAllocation(
            n_components=n_topics, random_state=42,
            max_iter=10, learning_method='online',
        )
        lda.fit(dtm)
        vocab = vectorizer.get_feature_names_out()
        topic_labels = []
        for topic in lda.components_:
            top_words = [vocab[i] for i in topic.argsort()[:-6:-1]]
            label = ' '.join(top_words[:3]).title()
            topic_labels.append(label)
        return topic_labels
    except Exception as e:
        logger.warning(f"LDA failed: {e}")
        return []


# ── Neo4j helpers ─────────────────────────────────────────────────────────────

def _get_neo4j_driver():
    try:
        from neo4j import GraphDatabase
        uri = getattr(settings, 'NEO4J_URI', 'bolt://localhost:7687')
        user = getattr(settings, 'NEO4J_USER', 'neo4j')
        password = getattr(settings, 'NEO4J_PASSWORD', 'password')
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        return driver
    except Exception as e:
        logger.warning(f"Neo4j unavailable: {e}")
        return None


def neo4j_ingest_clause(clause_id: str, clause_text: str, category_name: str):
    """Upsert Clause and Category nodes; create BELONGS_TO edge."""
    driver = _get_neo4j_driver()
    if not driver:
        return
    try:
        with driver.session() as s:
            s.run(
                """
                MERGE (cat:ClauseCategory {name: $cat})
                MERGE (c:LibraryClause {id: $cid})
                  ON CREATE SET c.text = $text, c.category = $cat
                MERGE (c)-[:BELONGS_TO]->(cat)
                """,
                cat=category_name, cid=clause_id, text=clause_text[:500],
            )
    except Exception as e:
        logger.warning(f"Neo4j ingest failed: {e}")
    finally:
        driver.close()


def neo4j_ingest_similar(clause_id_a: str, clause_id_b: str, score: float):
    """Create SIMILAR_TO edge between two LibraryClause nodes."""
    driver = _get_neo4j_driver()
    if not driver:
        return
    try:
        with driver.session() as s:
            s.run(
                """
                MATCH (a:LibraryClause {id: $aid}), (b:LibraryClause {id: $bid})
                MERGE (a)-[r:SIMILAR_TO]->(b)
                  ON CREATE SET r.score = $score
                  ON MATCH  SET r.score = $score
                """,
                aid=clause_id_a, bid=clause_id_b, score=round(score, 4),
            )
    except Exception as e:
        logger.warning(f"Neo4j SIMILAR_TO failed: {e}")
    finally:
        driver.close()


def neo4j_get_graph(limit: int = 150) -> Dict:
    """Return nodes + edges for the frontend knowledge graph."""
    driver = _get_neo4j_driver()
    if not driver:
        return {'nodes': [], 'edges': []}
    try:
        with driver.session() as s:
            result = s.run(
                """
                MATCH (c:LibraryClause)-[:BELONGS_TO]->(cat:ClauseCategory)
                RETURN c.id AS cid, c.text AS text, cat.name AS category
                LIMIT $limit
                """,
                limit=limit,
            )
            nodes, edges = [], []
            node_ids = {}

            for rec in result:
                cat = rec['category']
                cid = rec['cid']
                text = (rec['text'] or '')[:80]

                if cat not in node_ids:
                    node_ids[cat] = f"cat_{len(node_ids)}"
                    nodes.append({'id': node_ids[cat], 'label': cat, 'type': 'category'})

                if cid not in node_ids:
                    node_ids[cid] = f"cl_{len(node_ids)}"
                    nodes.append({'id': node_ids[cid], 'label': text, 'type': 'clause'})

                edges.append({'source': node_ids[cid], 'target': node_ids[cat], 'label': 'BELONGS_TO'})

            # SIMILAR_TO edges
            sim_result = s.run(
                """
                MATCH (a:LibraryClause)-[r:SIMILAR_TO]->(b:LibraryClause)
                RETURN a.id AS aid, b.id AS bid, r.score AS score
                LIMIT 100
                """
            )
            for rec in sim_result:
                aid = node_ids.get(rec['aid'])
                bid = node_ids.get(rec['bid'])
                if aid and bid:
                    edges.append({'source': aid, 'target': bid, 'label': 'SIMILAR_TO', 'score': rec['score']})

        return {'nodes': nodes, 'edges': edges}
    except Exception as e:
        logger.warning(f"Neo4j graph fetch failed: {e}")
        return {'nodes': [], 'edges': []}
    finally:
        driver.close()


# ── TaxonomyEngine ───────────────────────────────────────────────────────────

class TaxonomyEngine:
    def __init__(self):
        self._categories: List[ClauseCategory] = []
        self._embeddings: Optional[np.ndarray] = None

    def load(self):
        """Reload categories + rebuild FAISS index from DB."""
        self._categories = list(ClauseCategory.objects.all())
        if not self._categories:
            self._embeddings = None
            return
        model = _get_embed_model()
        stored = [c.embedding_vector for c in self._categories]
        if all(stored):
            self._embeddings = np.array(stored, dtype='float32')
        else:
            texts = [c.name for c in self._categories]
            self._embeddings = model.encode(texts, show_progress_bar=False)
            for cat, vec in zip(self._categories, self._embeddings):
                cat.embedding_vector = vec.tolist()
            ClauseCategory.objects.bulk_update(self._categories, ['embedding_vector'])

        _build_faiss_index(self._embeddings, [c.id for c in self._categories])

    def seed_standard_taxonomy(self) -> int:
        created = 0
        model = _get_embed_model()
        for parent_name, children in STANDARD_TAXONOMY.items():
            parent_emb = model.encode([parent_name])[0].tolist()
            parent, is_new = ClauseCategory.objects.get_or_create(
                name=parent_name,
                defaults={'is_standard': True, 'embedding_vector': parent_emb},
            )
            if is_new:
                created += 1
            for child_name in children:
                child_emb = model.encode([child_name])[0].tolist()
                _, child_new = ClauseCategory.objects.get_or_create(
                    name=child_name,
                    defaults={
                        'is_standard': True,
                        'parent_id': parent.id,
                        'embedding_vector': child_emb,
                    },
                )
                if child_new:
                    created += 1
        return created

    def _best_match_faiss(self, text: str) -> Tuple[Optional[ClauseCategory], float]:
        """Use FAISS for fast ANN; fall back to brute-force cosine."""
        model = _get_embed_model()
        emb = model.encode([text])[0]

        faiss_results = _faiss_search(emb, top_k=1)
        if faiss_results:
            cat_id, score = faiss_results[0]
            cat = next((c for c in self._categories if c.id == cat_id), None)
            if cat:
                return cat, score

        # brute-force fallback
        if self._embeddings is not None and len(self._categories):
            sims = cosine_similarity([emb], self._embeddings)[0]
            idx = int(np.argmax(sims))
            return self._categories[idx], float(sims[idx])

        return None, 0.0

    def assign_category(self, clause_text: str, use_qwen_naming: bool = True) -> ClauseCategory:
        best, score = self._best_match_faiss(clause_text)

        if best and score >= ASSIGN_THRESHOLD:
            best.clause_count += 1
            best.save(update_fields=['clause_count', 'updated_at'])
            return best

        model = _get_embed_model()
        emb = model.encode([clause_text])[0].tolist()

        # Qwen names new nodes; raw text fallback if Qwen is down
        name = _qwen_name_category(clause_text) if use_qwen_naming else clause_text[:80].strip()

        if best and score >= SUBCATEGORY_THRESHOLD:
            cat, created = ClauseCategory.objects.get_or_create(
                name=name,
                defaults={'parent_id': best.id, 'clause_count': 1, 'embedding_vector': emb},
            )
        else:
            cat, created = ClauseCategory.objects.get_or_create(
                name=name,
                defaults={'clause_count': 1, 'embedding_vector': emb},
            )

        if not created:
            cat.clause_count += 1
            cat.save(update_fields=['clause_count', 'updated_at'])

        if cat not in self._categories:
            self._categories.append(cat)
            new_vec = np.array([emb], dtype='float32')
            self._embeddings = (
                np.vstack([self._embeddings, new_vec])
                if self._embeddings is not None else new_vec
            )
            _build_faiss_index(self._embeddings, [c.id for c in self._categories])

        return cat

    def clean_taxonomy(self) -> int:
        self.load()
        if len(self._categories) < 2:
            return 0

        merged = 0
        to_delete: set = set()

        for i in range(len(self._categories)):
            if self._categories[i].id in to_delete:
                continue
            for j in range(i + 1, len(self._categories)):
                if self._categories[j].id in to_delete:
                    continue
                sim = cosine_similarity(
                    [self._embeddings[i]], [self._embeddings[j]]
                )[0][0]
                if sim >= MERGE_THRESHOLD:
                    self._merge(self._categories[i], self._categories[j])
                    to_delete.add(self._categories[j].id)
                    merged += 1
        return merged

    def _merge(self, keep: ClauseCategory, absorb: ClauseCategory):
        Clause.objects.filter(clause_type=absorb.name).update(clause_type=keep.name)
        keep.clause_count += absorb.clause_count
        keep.save(update_fields=['clause_count', 'updated_at'])
        absorb.delete()

    def sync_counts(self):
        """
        Recompute clause_count for every category using only clauses
        that belong to an existing (non-deleted) contract.
        Called automatically by build_tree / analytics so counts are always fresh.
        """
        from django.db.models import Count
        # Only count clauses whose contract still exists in the DB
        live_contract_ids = set(
            Contract.objects.values_list('id', flat=True)
        )
        counts = (
            Clause.objects
            .filter(contract_id__in=live_contract_ids)
            .exclude(clause_type__isnull=True)
            .exclude(clause_type='')
            .values('clause_type')
            .annotate(n=Count('id'))
        )
        count_map = {row['clause_type']: row['n'] for row in counts}

        to_update = []
        for cat in ClauseCategory.objects.all():
            new_count = count_map.get(cat.name, 0)
            if cat.clause_count != new_count:
                cat.clause_count = new_count
                to_update.append(cat)
        if to_update:
            ClauseCategory.objects.bulk_update(to_update, ['clause_count'])

    def build_tree(self) -> List[Dict]:
        self.sync_counts()
        cats = list(ClauseCategory.objects.all())
        count_map = {c.id: c.clause_count for c in cats}

        def node_dict(c):
            children = [node_dict(ch) for ch in cats if ch.parent_id == c.id]
            # roll up child counts into parent so tree totals are meaningful
            total = c.clause_count + sum(ch['count'] for ch in children)
            return {
                'id': c.id,
                'name': c.name,
                'count': total,
                'ownCount': c.clause_count,
                'isStandard': c.is_standard,
                'children': children,
            }
        return [node_dict(c) for c in cats if not c.parent_id]

    def analytics(self) -> Dict:
        self.sync_counts()
        cats = list(ClauseCategory.objects.all())
        total = len(cats)
        return {
            'total_categories': total,
            'total_clauses_indexed': sum(c.clause_count for c in cats),
            'standard_categories': sum(1 for c in cats if c.is_standard),
            'auto_discovered': sum(1 for c in cats if not c.is_standard),
            'top_categories': [
                {'name': c.name, 'count': c.clause_count, 'isStandard': c.is_standard}
                for c in sorted(cats, key=lambda x: x.clause_count, reverse=True)[:10]
            ],
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
_engine: Optional[TaxonomyEngine] = None


def get_taxonomy_engine() -> TaxonomyEngine:
    global _engine
    if _engine is None:
        _engine = TaxonomyEngine()
        _engine.load()
    return _engine


# ── Hybrid search (BM25 + FAISS embeddings + Qwen rerank + Redis cache) ──────

def hybrid_search_with_rerank(query: str, top_k: int = 20, use_qwen: bool = True) -> List[Dict]:
    """
    Full pipeline:
      1. Redis cache check
      2. BM25 keyword recall
      3. FAISS embedding recall
      4. Merge + deduplicate
      5. Qwen reranking
      6. Cache result
    """
    cache_key = f"acl:search:{hashlib.md5(f'{query}:{top_k}'.encode()).hexdigest()}"
    redis = _get_redis()
    if redis:
        try:
            cached = redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

    # Scope to active (non-deleted) contracts only
    live_contract_ids = list(Contract.objects.values_list('id', flat=True))
    clauses = list(
        Clause.objects.filter(contract_id__in=live_contract_ids)
                      .exclude(extracted_text__isnull=True)
                      .exclude(extracted_text='')
                      .values('id', 'extracted_text', 'clause_type', 'risk_level', 'risk_score', 'contract_id')[:8000]
    )
    if not clauses:
        return []

    texts = [c['extracted_text'] for c in clauses]

    # ── BM25 ──
    from rank_bm25 import BM25Okapi
    tokenized = [t.lower().split() for t in texts]
    bm25 = BM25Okapi(tokenized)
    bm25_scores = bm25.get_scores(query.lower().split())
    max_bm25 = max(bm25_scores) or 1.0
    norm_bm25 = bm25_scores / max_bm25

    # ── FAISS embedding recall (graceful fallback if model unavailable) ──
    norm_emb = np.zeros(len(clauses))
    try:
        model = _get_embed_model()
        q_emb = model.encode([query])[0].astype('float32')
        doc_embs = model.encode(texts[:3000], show_progress_bar=False, batch_size=64)
        from sklearn.metrics.pairwise import cosine_similarity as cos_sim
        emb_scores = np.zeros(len(clauses))
        if len(doc_embs):
            sims = cos_sim([q_emb], doc_embs)[0]
            emb_scores[:len(sims)] = sims
        max_emb = max(emb_scores) or 1.0
        norm_emb = emb_scores / max_emb
    except Exception as e:
        logger.warning(f'[ACL] Embedding model unavailable, using BM25-only search: {e}')

    # ── Merge ──
    combined = 0.55 * norm_bm25 + 0.45 * norm_emb
    ranked_idx = np.argsort(combined)[::-1][:top_k]

    results = []
    for i in ranked_idx:
        c = clauses[i]
        results.append({
            'id': c['id'],
            'text': c['extracted_text'][:400],
            'category': c['clause_type'] or 'Uncategorised',
            'risk_level': c['risk_level'] or 'UNKNOWN',
            'risk_score': round(float(c['risk_score'] or 0), 3),
            'score': round(float(combined[i]), 4),
            'qwen_score': 50,
            'qwen_reason': '',
        })

    # ── Qwen rerank ──
    if use_qwen and results:
        results = _qwen_rerank(query, results)

    # ── Cache ──
    if redis:
        try:
            redis.set(cache_key, json.dumps(results), ex=3600)
        except Exception:
            pass

    return results


# ── Continuous pipeline entry point ──────────────────────────────────────────

def process_contract_for_library(contract, use_qwen_naming: bool = True) -> Dict:
    """
    Called after clause extraction; assigns every clause to the taxonomy,
    ingests into Neo4j, and links SIMILAR_TO edges within the contract.
    """
    engine = get_taxonomy_engine()
    engine.load()

    clauses = list(
        Clause.objects.filter(contract=contract).exclude(extracted_text='')
    )
    total = len(clauses)
    processed = 0
    texts = []
    valid_clauses = []

    for clause in clauses:
        text = clause.extracted_text or clause.context_sentences or clause.clause_name
        if not text or len(text.strip()) < 15:
            continue
        texts.append(text)
        valid_clauses.append(clause)

    # ── LDA topic discovery (surface new candidate names) ──
    lda_topics = run_lda_discovery(texts)
    if lda_topics:
        logger.info(f"LDA discovered {len(lda_topics)} topic candidates: {lda_topics}")
        model = _get_embed_model()
        for topic_label in lda_topics:
            emb = model.encode([topic_label])[0].tolist()
            ClauseCategory.objects.get_or_create(
                name=topic_label,
                defaults={'is_standard': False, 'embedding_vector': emb},
            )
        engine.load()  # reload with LDA-discovered nodes

    # ── Assign each clause → category + Neo4j ingest ──
    model = _get_embed_model()
    clause_embs = model.encode(texts, show_progress_bar=False, batch_size=32) if texts else []

    for i, (clause, text) in enumerate(zip(valid_clauses, texts)):
        cat = engine.assign_category(text, use_qwen_naming=use_qwen_naming)

        if not clause.clause_type:
            clause.clause_type = cat.name
            clause.save(update_fields=['clause_type', 'updated_at'])

        neo4j_ingest_clause(str(clause.id), text, cat.name)
        processed += 1

    # ── SIMILAR_TO edges within this contract ──
    if len(clause_embs) > 1:
        from sklearn.metrics.pairwise import cosine_similarity as cos_sim
        sims = cos_sim(clause_embs)
        n = len(valid_clauses)
        for a in range(n):
            for b in range(a + 1, n):
                if sims[a][b] >= SIMILAR_CLAUSE_THRESHOLD:
                    neo4j_ingest_similar(
                        str(valid_clauses[a].id),
                        str(valid_clauses[b].id),
                        float(sims[a][b]),
                    )

    return {'total': total, 'processed': processed, 'lda_topics': lda_topics}
