"""
Node2Vec-style Graph Embeddings for Legal Knowledge Graph
==========================================================
Uses networkx + random walk simulation to generate node embeddings.
Falls back gracefully if Neo4j is unavailable.
"""

import logging
import numpy as np
import networkx as nx
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# RANDOM WALK ENGINE (Node2Vec-style)
# ═══════════════════════════════════════════════════════════════

class Node2VecWalker:
    """
    Biased random walk generator for Node2Vec embeddings.
    p = return parameter (breadth-first tendency)
    q = in-out parameter (depth-first tendency)
    """

    def __init__(self, p: float = 1.0, q: float = 0.5):
        self.p = p
        self.q = q

    def _get_alias_nodes(self, G: nx.Graph) -> Dict:
        """Precompute alias tables for nodes."""
        alias_nodes = {}
        for node in G.nodes():
            unnormalized = np.array([G[node][nbr].get('weight', 1.0) for nbr in G.neighbors(node)])
            if unnormalized.sum() == 0:
                unnormalized = np.ones(len(unnormalized))
            normalized = unnormalized / unnormalized.sum()
            alias_nodes[node] = normalized
        return alias_nodes

    def simulate_walks(self, G: nx.DiGraph, num_walks: int = 10, walk_length: int = 80) -> List[List]:
        """Generate random walks from every node."""
        walks = []
        nodes = list(G.nodes())
        for _ in range(num_walks):
            np.random.shuffle(nodes)
            for node in nodes:
                walk = self._node2vec_walk(G, walk_length, node)
                walks.append(walk)
        return walks

    def _node2vec_walk(self, G: nx.DiGraph, walk_length: int, start_node) -> List:
        walk = [start_node]
        while len(walk) < walk_length:
            cur = walk[-1]
            neighbors = list(G.neighbors(cur))
            if not neighbors:
                break
            if len(walk) == 1:
                walk.append(np.random.choice(neighbors))
            else:
                prev = walk[-2]
                probs = self._transition_probs(G, prev, cur, neighbors)
                walk.append(np.random.choice(neighbors, p=probs))
        return walk

    def _transition_probs(self, G, prev, cur, neighbors) -> np.ndarray:
        probs = []
        for nbr in neighbors:
            w = G[cur][nbr].get('weight', 1.0)
            if nbr == prev:
                probs.append(w / self.p)
            elif G.has_edge(prev, nbr):
                probs.append(w)
            else:
                probs.append(w / self.q)
        probs = np.array(probs)
        return probs / probs.sum()


# ═══════════════════════════════════════════════════════════════
# WORD2VEC-STYLE SKIP-GRAM (simplified)
# ═══════════════════════════════════════════════════════════════

class SkipGramEmbedder:
    """
    Simplified skip-gram word2vec over random walks.
    Uses co-occurrence counting + SVD for embeddings (no gensim needed).
    """

    def __init__(self, embedding_dim: int = 64, window_size: int = 5):
        self.embedding_dim = embedding_dim
        self.window_size = window_size
        self.embeddings: Dict[str, np.ndarray] = {}

    def fit(self, walks: List[List], vocab: List) -> Dict[str, np.ndarray]:
        """Fit embeddings from walks using co-occurrence + SVD."""
        node_to_idx = {n: i for i, n in enumerate(vocab)}
        n = len(vocab)
        cooc = np.zeros((n, n), dtype=np.float32)

        for walk in walks:
            for i, node in enumerate(walk):
                if node not in node_to_idx:
                    continue
                start = max(0, i - self.window_size)
                end = min(len(walk), i + self.window_size + 1)
                for j in range(start, end):
                    if i != j and walk[j] in node_to_idx:
                        cooc[node_to_idx[node], node_to_idx[walk[j]]] += 1

        # Apply PPMI (Positive Pointwise Mutual Information)
        row_sums = cooc.sum(axis=1, keepdims=True) + 1e-9
        col_sums = cooc.sum(axis=0, keepdims=True) + 1e-9
        total = cooc.sum() + 1e-9
        pmi = np.log((cooc * total) / (row_sums * col_sums) + 1e-9)
        ppmi = np.maximum(pmi, 0)

        # SVD for dimensionality reduction
        dim = min(self.embedding_dim, n - 1, ppmi.shape[1] - 1)
        if dim < 1:
            dim = 1
        try:
            U, S, Vt = np.linalg.svd(ppmi, full_matrices=False)
            embs = U[:, :dim] * np.sqrt(S[:dim])
        except Exception:
            embs = np.random.randn(n, dim).astype(np.float32)

        # Normalize
        norms = np.linalg.norm(embs, axis=1, keepdims=True) + 1e-9
        embs = embs / norms

        self.embeddings = {vocab[i]: embs[i] for i in range(n)}
        return self.embeddings


# ═══════════════════════════════════════════════════════════════
# LEGAL GRAPH EMBEDDINGS SERVICE
# ═══════════════════════════════════════════════════════════════

class LegalGraphEmbeddings:
    """
    Builds a networkx graph from Neo4j data, runs Node2Vec walks,
    generates embeddings for Clause/Risk/CaseLaw nodes.
    """

    def __init__(self, embedding_dim: int = 64):
        self.embedding_dim = embedding_dim
        self.G: Optional[nx.DiGraph] = None
        self.embeddings: Dict[str, np.ndarray] = {}
        self.node_types: Dict[str, str] = {}
        self._built = False

    def build_from_neo4j(self, contract_id: str = "") -> bool:
        """Load graph from Neo4j and build networkx DiGraph."""
        try:
            from contractai.neo4j_config import get_neo4j_driver
            driver = get_neo4j_driver()
            if not driver:
                return False

            G = nx.DiGraph()
            with driver.session() as session:
                # Load all nodes for the contract
                if contract_id:
                    # Clauses
                    r = session.run("""
                        MATCH (c:LegalContract {id: $cid})-[:HAS_CLAUSE]->(cl:LegalClause)
                        RETURN cl.id as id, cl.clause_type as ctype, cl.risk_level as rl
                    """, cid=contract_id)
                    for rec in r:
                        nid = rec['id']
                        G.add_node(nid, type='Clause', clause_type=rec.get('ctype', ''), risk=rec.get('rl', 'LOW'))
                        self.node_types[nid] = 'Clause'

                    # Risks
                    r2 = session.run("""
                        MATCH (c:LegalContract {id: $cid})-[:HAS_RISK]->(r:Risk)
                        RETURN r.id as id, r.category as cat, r.severity as sev
                    """, cid=contract_id)
                    for rec in r2:
                        nid = rec['id']
                        G.add_node(nid, type='Risk', category=rec.get('cat', ''), severity=rec.get('sev', 'LOW'))
                        self.node_types[nid] = 'Risk'

                    # CaseLaw reachable from contract
                    r3 = session.run("""
                        MATCH (c:LegalContract {id: $cid})-[:HAS_CLAUSE]->(cl:LegalClause)
                              -[:SUPPORTED_BY]->(cs:CaseLaw)
                        RETURN cs.id as id
                    """, cid=contract_id)
                    for rec in r3:
                        nid = rec['id']
                        G.add_node(nid, type='CaseLaw')
                        self.node_types[nid] = 'CaseLaw'

                    # Courts
                    r4 = session.run("""
                        MATCH (c:LegalContract {id: $cid})-[:HAS_CLAUSE]->(cl:LegalClause)
                              -[:SUPPORTED_BY]->(cs:CaseLaw)-[:DECIDED_BY]->(ct:Court)
                        RETURN ct.name as id
                    """, cid=contract_id)
                    for rec in r4:
                        nid = f"court_{rec['id']}"
                        G.add_node(nid, type='Court')
                        self.node_types[nid] = 'Court'

                    # Relationships → weighted edges
                    _EDGE_WEIGHTS = {
                        'HAS_CLAUSE': 1.0,
                        'INTRODUCES_RISK': 2.0,  # higher weight = more important
                        'SUPPORTED_BY': 1.5,
                        'CITED_IN': 1.0,
                        'DECIDED_BY': 0.8,
                        'SIMILAR_TO': 1.2,
                        'HAS_RISK': 1.8,
                    }
                    r5 = session.run("""
                        MATCH (c:LegalContract {id: $cid})-[:HAS_CLAUSE]->(cl:LegalClause)
                        OPTIONAL MATCH (cl)-[r1:SUPPORTED_BY]->(cs:CaseLaw)
                        OPTIONAL MATCH (cl)-[r2:INTRODUCES_RISK]->(rk:Risk)
                        OPTIONAL MATCH (cs)-[r3:DECIDED_BY]->(ct:Court)
                        OPTIONAL MATCH (cl)-[r4:SIMILAR_TO]->(cl2:LegalClause)
                        RETURN cl.id as src,
                               cs.id as case_tgt,
                               rk.id as risk_tgt,
                               'court_' + ct.name as court_tgt,
                               cl2.id as similar_tgt
                    """, cid=contract_id)
                    for rec in r5:
                        src = rec['src']
                        if rec['case_tgt'] and G.has_node(rec['case_tgt']):
                            G.add_edge(src, rec['case_tgt'], weight=_EDGE_WEIGHTS['SUPPORTED_BY'], rel='SUPPORTED_BY')
                        if rec['risk_tgt'] and G.has_node(rec['risk_tgt']):
                            G.add_edge(src, rec['risk_tgt'], weight=_EDGE_WEIGHTS['INTRODUCES_RISK'], rel='INTRODUCES_RISK')
                        if rec['court_tgt'] and G.has_node(rec['court_tgt']):
                            if rec['case_tgt']:
                                G.add_edge(rec['case_tgt'], rec['court_tgt'], weight=_EDGE_WEIGHTS['DECIDED_BY'], rel='DECIDED_BY')
                        if rec['similar_tgt'] and G.has_node(rec['similar_tgt']):
                            G.add_edge(src, rec['similar_tgt'], weight=_EDGE_WEIGHTS['SIMILAR_TO'], rel='SIMILAR_TO')

            self.G = G
            logger.info(f"[GraphEmb] Built networkx graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
            return True
        except Exception as e:
            logger.warning(f"[GraphEmb] Failed to build from Neo4j: {e}")
            return False

    def compute_embeddings(self) -> Dict[str, np.ndarray]:
        """Run Node2Vec walks + skip-gram SVD to get node embeddings."""
        if not self.G or self.G.number_of_nodes() < 2:
            logger.warning("[GraphEmb] Graph too small for embeddings")
            return {}
        try:
            walker = Node2VecWalker(p=1.0, q=0.5)
            walks = walker.simulate_walks(self.G, num_walks=10, walk_length=40)
            vocab = list(self.G.nodes())
            embedder = SkipGramEmbedder(embedding_dim=self.embedding_dim, window_size=5)
            self.embeddings = embedder.fit(walks, vocab)
            self._built = True
            logger.info(f"[GraphEmb] Computed embeddings for {len(self.embeddings)} nodes")
            return self.embeddings
        except Exception as e:
            logger.warning(f"[GraphEmb] Embedding computation failed: {e}")
            return {}

    def get_similar_nodes(self, node_id: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Find most similar nodes by cosine similarity in embedding space."""
        if node_id not in self.embeddings or not self.embeddings:
            return []
        query_emb = self.embeddings[node_id]
        scores = []
        for nid, emb in self.embeddings.items():
            if nid == node_id:
                continue
            score = float(np.dot(query_emb, emb) / (np.linalg.norm(query_emb) * np.linalg.norm(emb) + 1e-9))
            scores.append((nid, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def get_high_risk_subgraph(self, contract_id: str) -> Dict:
        """Return nodes with highest centrality (PageRank) as risk hubs."""
        if not self.G or self.G.number_of_nodes() < 2:
            return {"nodes": [], "pagerank": {}}
        try:
            pr = nx.pagerank(self.G, weight='weight')
            top_nodes = sorted(pr.items(), key=lambda x: x[1], reverse=True)[:10]
            return {
                "nodes": [{"id": n, "pagerank": round(s, 4), "type": self.node_types.get(n, 'unknown')} for n, s in top_nodes],
                "pagerank": {n: round(s, 4) for n, s in pr.items()},
            }
        except Exception as e:
            logger.warning(f"[GraphEmb] PageRank failed: {e}")
            return {"nodes": [], "pagerank": {}}

    def get_embeddings_summary(self) -> Dict:
        """Return summary of graph structure + embedding stats."""
        if not self.G:
            return {"built": False}
        return {
            "built": self._built,
            "nodes": self.G.number_of_nodes(),
            "edges": self.G.number_of_edges(),
            "node_types": dict(defaultdict(int, {v: 0 for v in set(self.node_types.values())})),
            "embeddings_count": len(self.embeddings),
            "embedding_dim": self.embedding_dim,
        }


# ═══════════════════════════════════════════════════════════════
# SINGLETON CACHE (per-contract)
# ═══════════════════════════════════════════════════════════════

_graph_emb_cache: Dict[str, LegalGraphEmbeddings] = {}


def get_graph_embeddings(contract_id: str) -> LegalGraphEmbeddings:
    """Get or build graph embeddings for a contract (cached)."""
    if contract_id not in _graph_emb_cache:
        emb = LegalGraphEmbeddings(embedding_dim=64)
        built = emb.build_from_neo4j(contract_id)
        if built:
            emb.compute_embeddings()
        _graph_emb_cache[contract_id] = emb
    return _graph_emb_cache[contract_id]


def invalidate_cache(contract_id: str):
    """Invalidate cached embeddings after graph update."""
    _graph_emb_cache.pop(contract_id, None)
