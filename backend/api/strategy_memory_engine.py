"""
Contract Strategy Memory Engine  –  Feature 3
===============================================

A modular AI memory system that:
  1. Extracts clauses from the DB (or raw text)
  2. Generates MiniLM embeddings via the existing EmbeddingService
  3. Indexes them in a FAISS flat-IP index for sub-millisecond search
  4. Builds a NetworkX knowledge graph (SIMILAR_TO / HIGH_RISK / USED_IN edges)
  5. Mines patterns: frequency stats, variation, risk scores, cluster detection
  6. Emits cross-module integration signals for Redlining, Negotiation, Legal, CFO

Architecture
-----------
  ClauseExtractor      – segment raw contract text into clause dicts
  FAISSIndex           – fast ANN search (falls back to numpy brute-force)
  GraphBuilder         – NetworkX graph + cluster detection
  InsightGenerator     – human-readable insights + risk patterns
  StrategyMemoryEngine – orchestrator; singleton via get_strategy_memory_engine()
"""

from __future__ import annotations

import hashlib
import logging
import random as _rnd
import time
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ── Clause-type colour palette (matches frontend) ────────────────────────────
CLAUSE_TYPE_COLORS: Dict[str, str] = {
    "Payment Terms":          "#4C8EDA",
    "Liability":              "#F16667",
    "Limitation of Liability":"#F16667",
    "Termination":            "#F79767",
    "Indemnification":        "#E8A838",
    "Confidentiality":        "#9063CD",
    "Force Majeure":          "#10b981",
    "Governing Law":          "#06B6D4",
    "Dispute Resolution":     "#8b5cf6",
    "Arbitration":            "#7c3aed",
    "Intellectual Property":  "#ec4899",
    "IP":                     "#ec4899",
    "Warranty":               "#14b8a6",
    "Penalty":                "#ef4444",
    "Insurance":              "#f59e0b",
    "Assignment":             "#64748b",
    "Notice":                 "#0ea5e9",
    "Entire Agreement":       "#6366f1",
    "Amendment":              "#84cc16",
    "General":                "#94a3b8",
}

# Types that require no fallback to "Unknown" — always get classified
_UNCLASSIFIED = {"Unknown", "unknown", "General", "general", "", None}

HIGH_RISK_TYPES = {"Liability", "Limitation of Liability", "Indemnification", "Force Majeure", "Termination", "Penalty"}


# ═══════════════════════════════════════════════════════════════════════════
# 1. Clause Extractor
# ═══════════════════════════════════════════════════════════════════════════

class ClauseExtractor:
    """
    Segment raw contract text into structured clause dicts.

    Strategy
    --------
    1. Split on numbered section / article headers (regex).
    2. Heuristic keyword matching to detect clause type.
       Keywords are ordered by specificity — first match wins.
    """

    # Priority-ordered: more-specific entries first so they match before generic ones.
    _TYPE_KEYWORDS: Dict[str, List[str]] = {
        "Force Majeure": [
            "force majeure", "act of god", "acts of god",
            "pandemic", "epidemic", "unforeseeable event", "unforeseeable circumstances",
            "natural disaster", "civil unrest", "war", "strike", "lockout",
            "beyond the control", "beyond reasonable control",
            "extraordinary event", "circumstances beyond",
            "neither party shall be liable for any failure or delay",
            "failure or delay in the performance of its obligations",
            "article 9", "clause 9",  # common section numbers for FM
        ],
        "Indemnification": [
            "indemni", "hold harmless", "defend and indemnify",
            "indemnify and hold", "indemnification obligations",
            "indemnifying party", "indemnified party",
        ],
        "Liability": [
            "limitation of liability", "limit of liability", "limits of liability",
            "cap on liability", "aggregate liability",
            "liable", "liability", "consequential damages", "indirect damages",
            "punitive damages", "loss of profits",
            "in no event shall", "shall not be liable",
        ],
        "Termination": [
            "terminat", "termination for cause", "termination for convenience",
            "right to terminate", "terminate this agreement",
            "notice of termination", "cancellation", "cancel this agreement",
            "expiry", "expiration", "end of contract", "dissolution",
        ],
        "Confidentiality": [
            "confidential", "confidentiality", "non-disclosure",
            "nda", "proprietary information", "trade secret",
            "shall not disclose", "keep confidential",
            "protect the confidentiality", "confidential information",
        ],
        "Dispute Resolution": [
            "dispute resolution", "dispute settlement",
            "arbitrat", "arbitration clause", "mediat", "mediation",
            "litigation", "courts of", "submission to jurisdiction",
            "governing dispute", "refer to arbitration",
            "amicable settlement", "expert determination",
        ],
        "Governing Law": [
            "governing law", "choice of law", "applicable law",
            "this agreement shall be governed", "construed in accordance with the laws",
            "laws of", "jurisdiction of the courts", "legal system",
            "subject to the laws", "under the laws of",
        ],
        "Intellectual Property": [
            "intellectual property", "ip rights", "copyright",
            "patent", "trademark", "trade mark", "proprietary rights",
            "software license", "open source", "source code",
            "moral rights", "work made for hire",
        ],
        "Payment Terms": [
            "payment terms", "terms of payment",
            "invoice", "invoicing", "remittance", "billing",
            "due and payable", "payment schedule",
            "milestone payment", "advance payment", "down payment",
            "late payment", "interest on overdue",
            "price", "fee", "compensation", "consideration",
            "shall pay", "payment within",
        ],
        "Warranty": [
            "warrant", "warranty", "warranties",
            "guarantee", "guarantees",
            "fitness for purpose", "merchantability",
            "as-is", "no warranty", "without warranty",
            "representations and warranties",
        ],
        "Arbitration": [
            "icc arbitration", "lcia", "siac", "aaa arbitration",
            "arbitral tribunal", "arbitral award", "seat of arbitration",
            "rules of arbitration", "number of arbitrators",
        ],
        "Penalty": [
            "penalty", "penalties", "liquidated damages",
            "delay penalty", "performance penalty",
            "penalty clause", "breach penalty",
        ],
        "Insurance": [
            "insurance", "insur", "indemnity insurance",
            "policy of insurance", "insurance coverage",
            "worker's compensation", "general liability insurance",
            "professional indemnity",
        ],
        "Limitation of Liability": [
            "limitation of liability", "maximum liability",
            "not exceed", "shall not exceed the contract value",
            "liability cap",
        ],
        "Assignment": [
            "assign", "assignment", "assignee", "assignor",
            "transfer of rights", "novation",
            "shall not assign", "may not assign",
        ],
        "Notice": [
            "notice", "notices", "notification",
            "written notice", "give notice", "receipt of notice",
            "notice period", "days' notice",
        ],
        "Entire Agreement": [
            "entire agreement", "entire contract",
            "supersede", "supersedes all prior",
            "integration clause", "merger clause",
        ],
        "Amendment": [
            "amendment", "modification", "vary", "variation",
            "shall not be amended", "written amendment",
            "change order",
        ],
    }

    def extract_from_text(self, text: str) -> List[Dict[str, str]]:
        """Split contract text into clauses using regex + heuristics."""
        import re

        pattern = r"(?:^|\n)(?:(?:Article|Section|Clause)\s+\d+|\d+\.\d*|\d+\.)\s+[A-Z]"
        parts = re.split(pattern, text, flags=re.IGNORECASE | re.MULTILINE)

        clauses: List[Dict[str, str]] = []
        for idx, part in enumerate(parts):
            part = part.strip()
            if len(part) < 30:
                continue
            clauses.append(
                {
                    "text":        part[:1_000],
                    "clause_type": self._classify(part),
                    "source":      "extracted",
                    "index":       str(idx),
                }
            )
        return clauses

    def classify(self, text: str, hint: str = "") -> str:
        """
        Score-based classification: count keyword hits per type.
        Uses `hint` (e.g. clause_label from DB) as a tie-breaker.
        Returns the type with the highest match score, or 'General'.
        """
        text_lower = text.lower()
        hint_lower = hint.lower() if hint else ""

        scores: Dict[str, int] = {}
        for clause_type, keywords in self._TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            # Bonus: keyword in section header / hint
            if hint_lower and any(kw in hint_lower for kw in keywords):
                score += 3
            if score > 0:
                scores[clause_type] = score

        if not scores:
            return "General"
        return max(scores, key=lambda t: scores[t])

    # Keep old name as alias for backward compat
    def _classify(self, text: str) -> str:
        return self.classify(text)


# ═══════════════════════════════════════════════════════════════════════════
# 2. FAISS Index  (cosine via normalised inner-product)
# ═══════════════════════════════════════════════════════════════════════════

class FAISSIndex:
    """
    Thin wrapper over faiss.IndexFlatIP for cosine similarity.
    Falls back to numpy dot-product when FAISS is not installed.
    """

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension
        self._ids:         List[str]            = []
        self._matrix:      Optional[np.ndarray] = None   # numpy fallback
        self._faiss_index  = None
        self._use_faiss    = False

        try:
            import faiss                                       # type: ignore
            self._faiss_index = faiss.IndexFlatIP(dimension)
            self._use_faiss   = True
            logger.info("FAISSIndex initialised  dim=%d", dimension)
        except ImportError:
            logger.info("FAISS unavailable – using numpy brute-force search")

    # ── batch build ──────────────────────────────────────────────────────────
    def build_batch(
        self, clause_ids: List[str], embeddings: List[List[float]]
    ) -> None:
        if not embeddings:
            return
        self._ids  = list(clause_ids)
        matrix     = np.array(embeddings, dtype=np.float32)
        matrix     = self._l2_normalise(matrix)

        if self._use_faiss:
            self._faiss_index.reset()
            self._faiss_index.add(matrix)
        else:
            self._matrix = matrix

    # ── search ───────────────────────────────────────────────────────────────
    def search(
        self,
        query_emb: List[float],
        top_k:     int   = 10,
        threshold: float = 0.65,
    ) -> List[Tuple[str, float]]:
        if not self._ids:
            return []

        q   = np.array(query_emb, dtype=np.float32)
        nrm = np.linalg.norm(q)
        q   = q / nrm if nrm > 0 else q
        k   = min(top_k + 1, len(self._ids))

        if self._use_faiss and self._faiss_index is not None:
            scores, indices = self._faiss_index.search(q.reshape(1, -1), k)
            results = [
                (self._ids[int(i)], float(s))
                for s, i in zip(scores[0], indices[0])
                if int(i) >= 0 and float(s) >= threshold
            ]
        else:
            if self._matrix is None:
                return []
            raw   = (self._matrix @ q).flatten()
            order = np.argsort(raw)[::-1][:k]
            results = [
                (self._ids[i], float(raw[i]))
                for i in order
                if float(raw[i]) >= threshold
            ]

        return results[:top_k]

    # ── helpers ──────────────────────────────────────────────────────────────
    @staticmethod
    def _l2_normalise(matrix: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        return matrix / norms


# ═══════════════════════════════════════════════════════════════════════════
# 3. Graph Builder  (NetworkX)
# ═══════════════════════════════════════════════════════════════════════════

class GraphBuilder:
    """
    Build a NetworkX knowledge graph from clause nodes + a FAISS index.

    Edge types
    ----------
    SIMILAR_TO  – cosine similarity ≥ threshold
    HIGH_RISK   – source node risk_score > 0.6
    USED_IN     – clause appears in more than one contract
    """

    def __init__(self, similarity_threshold: float = 0.75) -> None:
        self.threshold = similarity_threshold

    # ── main entry ───────────────────────────────────────────────────────────
    def build(
        self,
        nodes:       List[Dict],
        embeddings:  List[List[float]],
        faiss_index: FAISSIndex,
    ) -> Tuple[Any, List[Dict]]:
        """Returns (nx.Graph | None, edges_list)."""
        try:
            import networkx as nx                              # type: ignore
        except ImportError:
            return None, self._brute_force_edges(nodes, embeddings)

        G   = nx.Graph()
        id2emb = {n["id"]: embeddings[i] for i, n in enumerate(nodes)}

        for node in nodes:
            G.add_node(node["id"], **{k: v for k, v in node.items() if k != "id"})

        edges      = []
        seen_pairs: set = set()

        for node in nodes:
            raw = faiss_index.search(
                id2emb[node["id"]], top_k=25, threshold=self.threshold
            )
            for cand_id, sim in raw:
                if cand_id == node["id"]:
                    continue
                pair = tuple(sorted([node["id"], cand_id]))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)

                # Determine edge type
                edge_type = "SIMILAR_TO"
                if node.get("risk_score", 0) > 0.6:
                    edge_type = "HIGH_RISK"
                elif node.get("contract_id") != next(
                    (n["contract_id"] for n in nodes if n["id"] == cand_id), None
                ):
                    edge_type = "USED_IN"

                edge = {
                    "id":         f"e-{node['id'][:8]}-{cand_id[:8]}",
                    "source":     node["id"],
                    "target":     cand_id,
                    "similarity": round(float(sim), 3),
                    "label":      f"{round(float(sim) * 100)}% similar",
                    "edge_type":  edge_type,
                }
                edges.append(edge)
                G.add_edge(node["id"], cand_id, weight=sim, edge_type=edge_type)

        return G, edges

    # ── cluster detection ─────────────────────────────────────────────────────
    def detect_clusters(
        self, graph: Any, nodes: List[Dict]
    ) -> List[Dict]:
        if graph is None:
            return []
        try:
            import networkx as nx                              # type: ignore

            node_map = {n["id"]: n for n in nodes}
            clusters = []
            for idx, component in enumerate(nx.connected_components(graph)):
                members = list(component)
                if len(members) < 2:
                    continue
                types   = [node_map[nid]["clause_type"] for nid in members if nid in node_map]
                dominant = Counter(types).most_common(1)[0][0] if types else "Mixed"
                avg_risk = float(
                    np.mean([node_map[nid].get("risk_score", 0) for nid in members if nid in node_map])
                )
                clusters.append(
                    {
                        "cluster_id":         idx,
                        "size":               len(members),
                        "dominant_type":      dominant,
                        "avg_risk_score":     round(avg_risk, 3),
                        "type_distribution":  dict(Counter(types)),
                        "node_ids":           members[:20],
                    }
                )
            return sorted(clusters, key=lambda c: c["size"], reverse=True)[:10]
        except Exception as exc:
            logger.warning("Cluster detection failed: %s", exc)
            return []

    # ── brute-force fallback (no networkx) ────────────────────────────────────
    def _brute_force_edges(
        self, nodes: List[Dict], embeddings: List[List[float]]
    ) -> List[Dict]:
        edges      = []
        seen_pairs: set = set()
        matrix    = np.array(embeddings, dtype=np.float32)
        norms     = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms     = np.where(norms == 0, 1.0, norms)
        normed    = matrix / norms

        for i in range(len(nodes)):
            sims = (normed @ normed[i]).tolist()
            for j in range(len(nodes)):
                if j == i:
                    continue
                sim = float(sims[j])
                if sim < self.threshold:
                    continue
                pair = tuple(sorted([nodes[i]["id"], nodes[j]["id"]]))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                edges.append(
                    {
                        "id":         f"e-{nodes[i]['id'][:8]}-{nodes[j]['id'][:8]}",
                        "source":     nodes[i]["id"],
                        "target":     nodes[j]["id"],
                        "similarity": round(sim, 3),
                        "label":      f"{round(sim * 100)}% similar",
                        "edge_type":  "SIMILAR_TO",
                    }
                )
        return edges


# ═══════════════════════════════════════════════════════════════════════════
# 4. Insight Generator
# ═══════════════════════════════════════════════════════════════════════════

class InsightGenerator:
    """
    Mine pattern-level insights from the graph data:
    - Clause frequency across contracts
    - Variation score (low internal similarity → high variation)
    - Risk pattern detection
    - Cross-module integration signals
    """

    def generate(
        self,
        nodes:           List[Dict],
        edges:           List[Dict],
        clusters:        List[Dict],
        total_contracts: int,
    ) -> Dict[str, Any]:
        type_stats    = self._compute_type_stats(nodes, edges, total_contracts)
        insights      = self._build_insight_strings(type_stats, total_contracts)
        risk_patterns = self._detect_risk_patterns(type_stats)
        integration   = self._build_integration_data(type_stats, risk_patterns)

        return {
            "insights":      insights,
            "risk_patterns": risk_patterns,
            "type_stats":    type_stats,
            "integration":   integration,
        }

    # ── per-type statistics ───────────────────────────────────────────────────
    def _compute_type_stats(
        self,
        nodes:           List[Dict],
        edges:           List[Dict],
        total_contracts: int,
    ) -> Dict[str, Dict]:
        by_type: Dict[str, List[Dict]] = defaultdict(list)
        for n in nodes:
            by_type[n["clause_type"]].append(n)

        degree_map: Dict[str, int] = defaultdict(int)
        for e in edges:
            degree_map[e["source"]] += 1
            degree_map[e["target"]] += 1

        type_stats: Dict[str, Dict] = {}
        for clause_type, type_nodes in by_type.items():
            ids            = {n["id"] for n in type_nodes}
            contract_ids   = {n.get("contract_id") for n in type_nodes if n.get("contract_id")}
            coverage_pct   = round(len(contract_ids) / max(total_contracts, 1) * 100, 1)

            risk_scores    = [float(n.get("risk_score", 0)) for n in type_nodes]
            avg_risk       = round(float(np.mean(risk_scores)) if risk_scores else 0.0, 3)
            max_risk       = round(float(np.max(risk_scores))  if risk_scores else 0.0, 3)

            degrees        = [degree_map[nid] for nid in ids]
            avg_degree     = round(float(np.mean(degrees)) if degrees else 0.0, 1)

            internal_sims  = [
                e["similarity"] for e in edges
                if e["source"] in ids and e["target"] in ids
            ]
            avg_int_sim    = round(float(np.mean(internal_sims)) if internal_sims else 0.0, 3)
            variation      = round(1.0 - avg_int_sim, 3)

            type_stats[clause_type] = {
                "clause_type":          clause_type,
                "count":                len(type_nodes),
                "contract_coverage_pct": coverage_pct,
                "contracts_present":    len(contract_ids),
                "avg_risk_score":       avg_risk,
                "max_risk_score":       max_risk,
                "avg_degree":           avg_degree,
                "variation_score":      variation,
                "is_high_risk":         clause_type in HIGH_RISK_TYPES,
                "color":                CLAUSE_TYPE_COLORS.get(clause_type, "#68BC00"),
            }
        return type_stats

    # ── human-readable insight strings ────────────────────────────────────────
    def _build_insight_strings(
        self, type_stats: Dict[str, Dict], total_contracts: int
    ) -> List[Dict]:
        insights: List[Dict] = []

        for clause_type, stats in sorted(
            type_stats.items(), key=lambda x: x[1]["contract_coverage_pct"], reverse=True
        ):
            pct = stats["contract_coverage_pct"]

            if pct >= 75:
                insights.append(
                    {
                        "type":        "frequency",
                        "severity":    "info",
                        "icon":        "📊",
                        "message":     f"{clause_type} appears in {pct}% of contracts — considered standard.",
                        "clause_type": clause_type,
                        "value":       pct,
                    }
                )
            elif pct <= 20 and stats["count"] > 0:
                insights.append(
                    {
                        "type":        "frequency",
                        "severity":    "warning",
                        "icon":        "⚠️",
                        "message":     f"{clause_type} is rare — found in only {pct}% of contracts.",
                        "clause_type": clause_type,
                        "value":       pct,
                    }
                )

            if stats["variation_score"] > 0.35:
                insights.append(
                    {
                        "type":        "variation",
                        "severity":    "warning",
                        "icon":        "📈",
                        "message":     f"{clause_type} has high variation ({stats['variation_score']:.0%}) — no standard version exists.",
                        "clause_type": clause_type,
                        "value":       stats["variation_score"],
                    }
                )

            if stats["avg_risk_score"] > 0.6:
                insights.append(
                    {
                        "type":        "risk",
                        "severity":    "critical",
                        "icon":        "🚨",
                        "message":     f"High-risk {clause_type} detected — avg risk score {stats['avg_risk_score']:.0%}.",
                        "clause_type": clause_type,
                        "value":       stats["avg_risk_score"],
                    }
                )

            if stats["avg_degree"] >= 3:
                insights.append(
                    {
                        "type":        "standardization",
                        "severity":    "success",
                        "icon":        "✅",
                        "message":     f"{clause_type} is highly standardized — avg {stats['avg_degree']} similar matches.",
                        "clause_type": clause_type,
                        "value":       stats["avg_degree"],
                    }
                )

        return insights[:15]

    # ── risk pattern detection ────────────────────────────────────────────────
    def _detect_risk_patterns(
        self, type_stats: Dict[str, Dict]
    ) -> List[Dict]:
        patterns: List[Dict] = []

        for clause_type, stats in type_stats.items():
            if stats["is_high_risk"] and stats["avg_risk_score"] > 0.5:
                patterns.append(
                    {
                        "pattern_type":       "HIGH_RISK_CLAUSE",
                        "clause_type":        clause_type,
                        "severity":           "critical" if stats["avg_risk_score"] > 0.7 else "high",
                        "description":        f"High-risk {clause_type} clauses — avg risk {stats['avg_risk_score']:.0%}",
                        "recommendation":     f"Review all {clause_type} clauses before signing",
                        "affected_contracts": stats["contracts_present"],
                        "risk_score":         stats["avg_risk_score"],
                        "icon":               "🚨",
                    }
                )

            if stats["variation_score"] > 0.40 and stats["count"] > 2:
                patterns.append(
                    {
                        "pattern_type":       "HIGH_VARIATION",
                        "clause_type":        clause_type,
                        "severity":           "medium",
                        "description":        f"{clause_type} has {stats['variation_score']:.0%} variation — no standard wording",
                        "recommendation":     f"Standardize {clause_type} across supplier contracts",
                        "affected_contracts": stats["contracts_present"],
                        "risk_score":         stats["variation_score"],
                        "icon":               "📈",
                    }
                )

        return sorted(patterns, key=lambda p: p["risk_score"], reverse=True)[:8]

    # ── cross-module integration signals ──────────────────────────────────────
    def _build_integration_data(
        self, type_stats: Dict[str, Dict], risk_patterns: List[Dict]
    ) -> Dict[str, Any]:
        high_risk_types = [
            p["clause_type"] for p in risk_patterns
            if p["pattern_type"] == "HIGH_RISK_CLAUSE"
        ]
        variable_types = [
            p["clause_type"] for p in risk_patterns
            if p["pattern_type"] == "HIGH_VARIATION"
        ]
        financial_types = [
            t for t in high_risk_types
            if t in ("Liability", "Payment Terms", "Indemnification")
        ]

        return {
            "redlining": {
                "flag_clause_types": high_risk_types,
                "message": (
                    f"Auto-flag {len(high_risk_types)} high-risk clause types during redlining"
                    if high_risk_types else "No high-risk clauses to flag"
                ),
            },
            "negotiation": {
                "strategy_clause_types": variable_types,
                "message": (
                    f"Apply custom negotiation strategies for {len(variable_types)} variable clause types"
                    if variable_types else "All clauses are standardized"
                ),
            },
            "legal": {
                "review_required": high_risk_types,
                "message": (
                    f"{len(high_risk_types)} clause types require mandatory legal review"
                    if high_risk_types else "No mandatory legal review flagged"
                ),
            },
            "cfo": {
                "financial_risk_types": financial_types,
                "message": (
                    f"Financial exposure detected in {len(financial_types)} clause types"
                    if financial_types else "No critical financial exposure flagged"
                ),
            },
        }


# ═══════════════════════════════════════════════════════════════════════════
# 5. Strategy Memory Engine  (orchestrator)
# ═══════════════════════════════════════════════════════════════════════════

class StrategyMemoryEngine:
    """
    Orchestrator for Contract Strategy Memory.

    Usage
    -----
    engine = get_strategy_memory_engine()

    result = engine.build()                              # full graph + insights
    result = engine.search("payment clause liability")   # semantic search
    result = engine.get_insights("clause-uuid")          # per-clause analysis
    """

    SIMILARITY_THRESHOLD = 0.75
    MAX_CLAUSES          = 200

    def __init__(self) -> None:
        self.clause_extractor  = ClauseExtractor()
        self.graph_builder     = GraphBuilder(self.SIMILARITY_THRESHOLD)
        self.insight_generator = InsightGenerator()

        # Runtime state (populated after build())
        self._faiss_index: Optional[FAISSIndex]    = None
        self._nodes:        List[Dict]              = []
        self._embeddings:   List[List[float]]       = []
        self._last_result:  Optional[Dict[str, Any]] = None

    # ── helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _get_embedding_service():
        try:
            from api.embedding_service import embedding_service  # type: ignore
            return embedding_service
        except Exception:
            return None

    def _embed(self, text: str, emb_svc) -> List[float]:
        """Embed text with a deterministic hash-based fallback."""
        if emb_svc:
            try:
                return emb_svc.embed_text(text[:512])
            except Exception:
                pass
        # Deterministic pseudo-embedding (reproducible, no ML required)
        h   = int(hashlib.md5(text[:50].encode()).hexdigest(), 16)
        rng = _rnd.Random(h)
        return [rng.gauss(0, 1) for _ in range(384)]

    # ── build ─────────────────────────────────────────────────────────────────
    def build(self, user=None) -> Dict[str, Any]:
        """
        Full pipeline:
          Fetch clauses → embed → FAISS index → NetworkX graph → insights.

        Returns a dict ready to be JSON-serialised in a DRF Response.
        """
        from core.models import Clause, Contract               # type: ignore

        t0 = time.time()

        # ── 1. Fetch clauses ─────────────────────────────────────────────────
        clauses_qs = (
            Clause.objects
            .exclude(extracted_text__isnull=True)
            .exclude(extracted_text__exact="")
            .select_related("contract")
            .order_by("-contract__uploaded_at")[: self.MAX_CLAUSES]
        )
        clauses = list(clauses_qs)

        if not clauses:
            return {
                "error": "No clauses with text found. Upload and analyse contracts first.",
                "nodes": [], "edges": [], "insights": [], "risk_patterns": [],
                "clusters": [], "type_stats": [], "stats": {},
            }

        total_contracts = Contract.objects.count()
        emb_svc         = self._get_embedding_service()

        # ── 2. Embed & build node list ────────────────────────────────────────
        nodes:       List[Dict]          = []
        embeddings:  List[List[float]]   = []
        clause_ids:  List[str]           = []

        for clause in clauses:
            text = clause.extracted_text or ""
            if len(text.strip()) < 20:
                continue

            emb = self._embed(text, emb_svc)

            # ── Resolve clause type ──────────────────────────────────────────
            # Priority: DB clause_type → DB clause_label → NLP auto-classify
            db_type  = (clause.clause_type or "").strip()
            db_label = (getattr(clause, "clause_label", "") or "").strip()

            if db_type and db_type not in _UNCLASSIFIED:
                clause_type = db_type
            elif db_label and db_label not in _UNCLASSIFIED:
                # Use label as hint for the classifier
                clause_type = self.clause_extractor.classify(text, hint=db_label)
            else:
                # Fully unknown — auto-classify from clause text
                clause_type = self.clause_extractor.classify(text)

            contract_name = ""
            try:
                contract_name = clause.contract.original_filename if clause.contract else ""
            except Exception:
                pass

            nodes.append(
                {
                    "id":            clause.id,
                    "clause_id":     clause.id,
                    "contract_id":   clause.contract_id,
                    "contract_name": contract_name,
                    "text_snippet":  text[:150],
                    "clause_type":   clause_type,
                    "color":         CLAUSE_TYPE_COLORS.get(clause_type, "#94a3b8"),
                    "risk_score":    float(getattr(clause, "risk_score", 0) or 0),
                }
            )
            embeddings.append(emb)
            clause_ids.append(clause.id)

        if not nodes:
            return {
                "error": "No valid clauses after filtering.",
                "nodes": [], "edges": [], "insights": [], "risk_patterns": [],
                "clusters": [], "type_stats": [], "stats": {},
            }

        # ── 3. FAISS index ────────────────────────────────────────────────────
        dim         = len(embeddings[0])
        faiss_index = FAISSIndex(dimension=dim)
        faiss_index.build_batch(clause_ids, embeddings)
        self._faiss_index = faiss_index
        self._nodes       = nodes
        self._embeddings  = embeddings

        # ── 4. Build knowledge graph ──────────────────────────────────────────
        graph, edges = self.graph_builder.build(nodes, embeddings, faiss_index)
        clusters     = self.graph_builder.detect_clusters(graph, nodes)

        # ── 5. Generate insights ──────────────────────────────────────────────
        insight_data = self.insight_generator.generate(
            nodes, edges, clusters, total_contracts
        )

        # ── Assemble response ─────────────────────────────────────────────────
        avg_sim   = (
            round(sum(e["similarity"] for e in edges) / len(edges), 3)
            if edges else 0.0
        )
        elapsed   = round(time.time() - t0, 2)

        result = {
            "nodes":        nodes,
            "edges":        edges,
            "stats": {
                "total_nodes":         len(nodes),
                "total_connections":   len(edges),
                "avg_similarity":      avg_sim,
                "clauses_analyzed":    len(clauses),
                "total_contracts":     total_contracts,
                "clusters_found":      len(clusters),
                "build_time_seconds":  elapsed,
            },
            "insights":      insight_data["insights"],
            "risk_patterns": insight_data["risk_patterns"],
            "type_stats":    list(insight_data["type_stats"].values()),
            "clusters":      clusters,
            "integration":   insight_data["integration"],
            "built_at":      datetime.utcnow().isoformat(),
        }
        self._last_result = result
        return result

    # ── semantic search ───────────────────────────────────────────────────────
    def search(self, query_text: str, limit: int = 10) -> Dict[str, Any]:
        """Semantic search over the in-memory clause index."""
        if not self._faiss_index or not self._nodes:
            return {
                "error": "Memory not built. Call POST /api/contract-suite/memory/build/ first.",
                "results": [],
            }

        emb_svc   = self._get_embedding_service()
        query_emb = self._embed(query_text, emb_svc)
        raw       = self._faiss_index.search(query_emb, top_k=limit, threshold=0.50)
        node_map  = {n["id"]: n for n in self._nodes}

        return {
            "query":   query_text,
            "results": [
                {**node_map[cid], "similarity": round(sim, 3)}
                for cid, sim in raw
                if cid in node_map
            ],
        }

    # ── per-clause insights ───────────────────────────────────────────────────
    def get_insights(self, clause_id: str) -> Dict[str, Any]:
        """Detailed insights for a single clause: similar clauses, frequency, risk."""
        from core.models import Clause, Contract               # type: ignore

        try:
            target = Clause.objects.select_related("contract").get(id=clause_id)
        except Clause.DoesNotExist:
            return {"error": "Clause not found"}

        text = target.extracted_text or ""
        if not text.strip():
            return {"error": "Clause has no text"}

        emb_svc    = self._get_embedding_service()
        target_emb = self._embed(text, emb_svc)

        # Ensure index is populated
        if not self._faiss_index or not self._nodes:
            self.build()

        similar_raw = (
            self._faiss_index.search(target_emb, top_k=15, threshold=0.60)
            if self._faiss_index else []
        )
        node_map     = {n["id"]: n for n in self._nodes}
        similar_nodes = [
            {**node_map[cid], "similarity": round(sim, 3)}
            for cid, sim in similar_raw
            if cid in node_map and cid != clause_id
        ]

        # Frequency stats
        total_contracts = Contract.objects.count()
        db_type  = (target.clause_type or "").strip()
        db_label = (getattr(target, "clause_label", "") or "").strip()
        if db_type and db_type not in _UNCLASSIFIED:
            clause_type = db_type
        elif db_label and db_label not in _UNCLASSIFIED:
            clause_type = self.clause_extractor.classify(text, hint=db_label)
        else:
            clause_type = self.clause_extractor.classify(text)

        contracts_with_type = (
            Clause.objects.filter(clause_type=clause_type)
            .values("contract_id")
            .distinct()
            .count()
        )
        frequency_pct = round(contracts_with_type / max(total_contracts, 1) * 100, 1)

        avg_risk        = float(np.mean([n.get("risk_score", 0) for n in similar_nodes])) if similar_nodes else 0.0
        high_risk_count = sum(1 for n in similar_nodes if n.get("risk_score", 0) > 0.6)

        return {
            "clause_id":      clause_id,
            "clause_type":    clause_type,
            "text_snippet":   text[:200],
            "similar_clauses": similar_nodes[:10],
            "stats": {
                "similar_count":       len(similar_nodes),
                "frequency_pct":       frequency_pct,
                "contracts_with_type": contracts_with_type,
                "total_contracts":     total_contracts,
                "avg_similar_risk":    round(avg_risk, 3),
                "high_risk_similar":   high_risk_count,
            },
            "insights": [
                {
                    "icon":    "📊",
                    "message": f"{clause_type} appears in {frequency_pct}% of contracts",
                },
                {
                    "icon":    "🔗",
                    "message": f"{len(similar_nodes)} semantically similar clauses found across your portfolio",
                },
                {
                    "icon":    "⚖️",
                    "message": f"Average risk in similar clauses: {avg_risk:.0%}",
                },
                {
                    "icon":    "🚨" if high_risk_count > 0 else "✅",
                    "message": (
                        f"{high_risk_count} high-risk variants detected"
                        if high_risk_count > 0
                        else "No high-risk variants detected"
                    ),
                },
            ],
        }


# ═══════════════════════════════════════════════════════════════════════════
# Module-level singleton
# ═══════════════════════════════════════════════════════════════════════════

_engine_instance: Optional[StrategyMemoryEngine] = None


def get_strategy_memory_engine() -> StrategyMemoryEngine:
    """Return the module-level singleton StrategyMemoryEngine."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = StrategyMemoryEngine()
    return _engine_instance
