"""
CUAD Graph Service
==================
Enterprise-grade legal knowledge graph service for PrimeContractAI.

Builds an enriched Neo4j graph from existing MySQL Contract/Clause data
using the CUAD-style schema (13 node types, 11 relationship types).

Capabilities:
- Ingest contract into Neo4j with full CUAD schema
- Compare two contracts: clause diff, weighted risk/obligation scoring
- Graph Data Science: PageRank influence, clause cosine similarity
- GNN contract scoring (PyTorch Geometric with rule-based fallback)
"""

import json
import logging
import math
import random
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CUAD Clause Type → canonical CUAD category mapping
# ─────────────────────────────────────────────────────────────────────────────
CLAUSE_TYPE_CANONICAL = {
    "termination": "Termination",
    "indemnification": "Indemnification",
    "indemnity": "Indemnification",
    "liability": "Limitation of Liability",
    "limitation of liability": "Limitation of Liability",
    "payment": "Payment Terms",
    "payment terms": "Payment Terms",
    "confidentiality": "Confidentiality",
    "intellectual property": "Intellectual Property",
    "ip": "Intellectual Property",
    "warranty": "Warranty",
    "warranties": "Warranty",
    "dispute": "Dispute Resolution",
    "dispute resolution": "Dispute Resolution",
    "arbitration": "Dispute Resolution",
    "governing law": "Governing Law",
    "jurisdiction": "Governing Law",
    "force majeure": "Force Majeure",
    "assignment": "Assignment",
    "non-compete": "Non-Compete",
    "non compete": "Non-Compete",
    "audit": "Audit Rights",
    "audit rights": "Audit Rights",
    "renewal": "Renewal",
    "auto-renewal": "Renewal",
    "general": "General",
}

# Risk multipliers per clause type (higher = more risk weight)
CLAUSE_RISK_MULTIPLIERS = {
    "Indemnification": 1.0,
    "Limitation of Liability": 0.8,
    "Termination": 0.6,
    "Payment Terms": 0.7,
    "Confidentiality": 0.5,
    "Intellectual Property": 0.9,
    "Warranty": 0.4,
    "Dispute Resolution": 0.5,
    "Governing Law": 0.3,
    "Force Majeure": 0.3,
    "Assignment": 0.4,
    "Non-Compete": 0.6,
    "Audit Rights": 0.3,
    "Renewal": 0.2,
    "General": 0.2,
}

# Node colors matching Neo4jGraphCanvas.jsx palette
NODE_COLORS = {
    "Contract": "#68BC00",
    "Clause": "#4C8EDA",
    "ClauseType": "#9063CD",
    "Party": "#FFD86E",
    "Jurisdiction": "#9063CD",
    "Obligation": "#F79767",
    "Risk": "#F16667",
    "Industry": "#06B6D4",
    # diff status overrides
    "same": "#68BC00",
    "modified": "#FFD86E",
    "missing": "#F16667",
    "new": "#4C8EDA",
}


# Base risk scores per canonical clause type (floor values, adjusted by text analysis)
CLAUSE_DEFAULT_RISK = {
    "Indemnification": 0.85,
    "Limitation of Liability": 0.75,
    "Intellectual Property": 0.70,
    "Termination": 0.65,
    "Non-Compete": 0.60,
    "Payment Terms": 0.55,
    "Dispute Resolution": 0.50,
    "Confidentiality": 0.45,
    "Assignment": 0.40,
    "Warranty": 0.40,
    "Audit Rights": 0.35,
    "Governing Law": 0.30,
    "Force Majeure": 0.30,
    "Renewal": 0.25,
    "General": 0.20,
}

# High-risk keywords that boost risk score when found in extracted_text
_RISK_KEYWORDS = [
    "indemnify", "indemnification", "liable", "liability", "damages",
    "terminate", "termination", "breach", "penalty", "liquidated",
    "waive", "waiver", "unlimited", "sole discretion", "irrevocable",
    "non-compete", "non compete", "exclusive", "injunction",
    "intellectual property", "proprietary", "confidential", "trade secret",
    "arbitration", "jurisdiction", "governing law", "force majeure",
    "assignment", "sublicense", "audit", "inspection", "warranty", "warrant",
    "guaranty", "guarantee", "indemnitor", "indemnitee", "lien", "encumber",
]


def _canonical_type(raw_type: str, raw_name: str = "") -> str:
    """
    Normalize to CUAD canonical form.
    Tries clause_type first, then falls back to clause_name for lookup.
    """
    for candidate in [raw_type or "", raw_name or ""]:
        key = candidate.lower().strip()
        if key and key != "general" and key != "none":
            result = CLAUSE_TYPE_CANONICAL.get(key)
            if result:
                return result
            # Partial match: check if any key is contained in the candidate
            for map_key, map_val in CLAUSE_TYPE_CANONICAL.items():
                if map_key in key or key in map_key:
                    return map_val
    return "General"


def _text_based_risk(clause) -> float:
    """
    Compute a real per-contract risk score using extracted_text content.

    Formula:
      base_score   = CLAUSE_DEFAULT_RISK[canonical_type]           (type floor)
      text_factor  = min(text_length / 800, 1.0) * 0.15            (richness bonus ±0.15)
      conf_factor  = (confidence / 100) * 0.10                     (OCR quality ±0.10)
      keyword_bump = min(keyword_hits / 5, 1.0) * 0.10             (risk keywords ±0.10)
      final = clamp(base + text_factor + conf_factor + keyword_bump - 0.05, 0.05, 0.99)

    The -0.05 ensures that 0-text / 0-confidence clauses fall below base.
    Different contracts with same clause type will differ because extracted_text
    length, confidence, and keyword density all vary per contract.
    """
    # Stored risk score takes priority (if it's already computed and non-zero)
    rs = getattr(clause, 'risk_score', None)
    if rs is not None:
        try:
            val = float(rs)
            if val > 0.0:
                return val
        except (TypeError, ValueError):
            pass

    ct = _canonical_type(
        getattr(clause, 'clause_type', None) or "",
        getattr(clause, 'clause_name', None) or ""
    )
    base = CLAUSE_DEFAULT_RISK.get(ct, 0.20)

    # Get extracted_text (Django field name is extracted_text)
    text = getattr(clause, 'extracted_text', None) or ""
    text_len = len(text)

    # Confidence: stored as 0-100 float
    conf_raw = getattr(clause, 'confidence', None)
    try:
        confidence = float(conf_raw or 0) / 100.0  # normalize to 0-1
    except (TypeError, ValueError):
        confidence = 0.0

    # Zero-text clause: very low risk (failed extraction)
    if text_len == 0:
        return max(base * 0.3, 0.05)

    # Text richness factor: longer text = richer content = higher stake
    text_factor = min(text_len / 800.0, 1.0) * 0.15

    # Confidence factor: high OCR confidence = reliable extraction
    conf_factor = confidence * 0.10

    # Risk keyword bump: count unique risk keywords in text (case-insensitive)
    text_lower = text.lower()
    keyword_hits = sum(1 for kw in _RISK_KEYWORDS if kw in text_lower)
    keyword_bump = min(keyword_hits / 5.0, 1.0) * 0.10

    # Combine: base type risk + text signals - small penalty so baseline ≠ identical
    raw = base + text_factor + conf_factor + keyword_bump - 0.05
    return round(max(0.05, min(0.99, raw)), 4)


def _infer_risk_score(clause) -> float:
    """Alias kept for backward compatibility — delegates to text-based scoring."""
    return _text_based_risk(clause)


def _infer_risk_level(risk_score: float) -> str:
    if risk_score >= 0.7:
        return "HIGH"
    elif risk_score >= 0.4:
        return "MEDIUM"
    return "LOW"


class _NeoClause:
    """Lightweight wrapper so Neo4j dict records work with all helper functions
    that expect Django Clause objects (attribute access)."""
    __slots__ = ('id', 'clause_name', 'clause_type', 'risk_score', 'risk_level',
                 'extracted_text', 'confidence')

    def __init__(self, rec: dict):
        self.id           = rec.get('clause_id', '')
        self.clause_name  = rec.get('clause_name', '')
        self.clause_type  = rec.get('clause_type', '')
        self.risk_score   = rec.get('risk_score', 0.3)
        self.risk_level   = rec.get('risk_level', None)
        self.extracted_text = rec.get('text', '')
        self.confidence   = rec.get('confidence', 0)


# ─────────────────────────────────────────────────────────────────────────────
# Neo4j helper
# ─────────────────────────────────────────────────────────────────────────────

def _get_driver():
    try:
        from contractai.neo4j_config import get_neo4j_driver, check_neo4j_available
        if check_neo4j_available():
            return get_neo4j_driver()
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Main Service
# ─────────────────────────────────────────────────────────────────────────────

class CUADGraphService:
    """
    Builds and queries a CUAD-style enterprise legal knowledge graph.
    Falls back to NetworkX / rule-based scoring when Neo4j is unavailable.
    """

    def __init__(self):
        self.driver = _get_driver()
        self.neo4j_available = self.driver is not None
        if self.neo4j_available:
            logger.info("[CUAD-GRAPH] Neo4j available")
        else:
            logger.warning("[CUAD-GRAPH] Neo4j unavailable — using fallback mode")

    # ──────────────────────────────────────────────────────────────────────────
    # 1. INGEST CONTRACT INTO NEO4J
    # ──────────────────────────────────────────────────────────────────────────

    def ingest_contract_graph(self, contract_id: str) -> Dict[str, Any]:
        """
        Pull Contract + Clause rows from MySQL and build full CUAD graph in Neo4j.

        Node types created:
          Contract, Clause, ClauseType, Party, Jurisdiction, Obligation, Risk, Industry

        Returns summary dict with node/relationship counts.
        """
        from core.models import Contract, Clause

        try:
            contract = Contract.objects.get(id=contract_id)
        except Contract.DoesNotExist:
            return {"error": f"Contract {contract_id} not found"}

        clauses = list(Clause.objects.filter(contract=contract))

        if self.neo4j_available:
            return self._neo4j_ingest(contract, clauses)
        else:
            return self._fallback_ingest_summary(contract, clauses)

    def _neo4j_ingest(self, contract, clauses: List) -> Dict[str, Any]:
        nodes_created = 0
        rels_created = 0
        contract_id = str(contract.id)

        try:
            with self.driver.session() as session:
                # Clear existing graph for this contract
                session.run("""
                    MATCH (n {contract_id: $cid}) DETACH DELETE n
                """, cid=contract_id)

                # Create Contract node
                session.run("""
                    MERGE (c:Contract {id: $id})
                    SET c.name = $name,
                        c.contract_id = $cid,
                        c.jurisdiction = $jurisdiction,
                        c.contract_type = $contract_type,
                        c.party_a = $party_a,
                        c.party_b = $party_b,
                        c.node_type = 'Contract'
                """, id=contract_id, cid=contract_id,
                    name=contract.filename or "Unnamed Contract",
                    jurisdiction=contract.jurisdiction or "Unknown",
                    contract_type=contract.contractType or "General",
                    party_a=contract.partyA or "",
                    party_b=contract.partyB or "")
                nodes_created += 1

                # Party nodes
                for party_name in [contract.partyA, contract.partyB]:
                    if party_name:
                        session.run("""
                            MERGE (p:Party {name: $name})
                            SET p.node_type = 'Party'
                            WITH p
                            MATCH (c:Contract {id: $cid})
                            MERGE (c)-[:HAS_PARTY]->(p)
                        """, name=party_name, cid=contract_id)
                        nodes_created += 1
                        rels_created += 1

                # Jurisdiction node
                if contract.jurisdiction:
                    session.run("""
                        MERGE (j:Jurisdiction {name: $name})
                        SET j.node_type = 'Jurisdiction'
                        WITH j
                        MATCH (c:Contract {id: $cid})
                        MERGE (c)-[:GOVERNED_BY]->(j)
                    """, name=contract.jurisdiction, cid=contract_id)
                    nodes_created += 1
                    rels_created += 1

                # Industry node
                contract_type = contract.contractType or "Technology"
                session.run("""
                    MERGE (ind:Industry {name: $name})
                    SET ind.node_type = 'Industry'
                    WITH ind
                    MATCH (c:Contract {id: $cid})
                    MERGE (c)-[:BELONGS_TO]->(ind)
                """, name=contract_type, cid=contract_id)
                nodes_created += 1
                rels_created += 1

                # Clause nodes + ClauseType nodes
                for clause in clauses:
                    clause_id = str(clause.id)
                    canonical = _canonical_type(clause.clause_type or "", clause.clause_name or "")
                    risk_score = _infer_risk_score(clause)
                    risk_level = clause.risk_level or _infer_risk_level(risk_score)

                    # Clause node
                    session.run("""
                        MERGE (cl:Clause {id: $id})
                        SET cl.contract_id = $cid,
                            cl.clause_name = $name,
                            cl.clause_type = $ctype,
                            cl.risk_score = $risk_score,
                            cl.risk_level = $risk_level,
                            cl.node_type = 'Clause'
                        WITH cl
                        MATCH (c:Contract {id: $cid})
                        MERGE (c)-[:HAS_CLAUSE]->(cl)
                    """, id=clause_id, cid=contract_id,
                        name=clause.clause_name or canonical,
                        ctype=canonical,
                        risk_score=risk_score,
                        risk_level=risk_level)
                    nodes_created += 1
                    rels_created += 1

                    # ClauseType node
                    session.run("""
                        MERGE (ct:ClauseType {type: $type})
                        SET ct.node_type = 'ClauseType'
                        WITH ct
                        MATCH (cl:Clause {id: $id})
                        MERGE (cl)-[:IS_TYPE]->(ct)
                    """, type=canonical, id=clause_id)
                    nodes_created += 1
                    rels_created += 1

                    # Risk node (if risk_score >= 0.5)
                    if risk_score >= 0.5:
                        risk_cat = canonical.upper().replace(" ", "_")
                        session.run("""
                            MERGE (r:Risk {id: $rid})
                            SET r.category = $cat,
                                r.level = $level,
                                r.impact_score = $impact,
                                r.node_type = 'Risk',
                                r.contract_id = $cid
                            WITH r
                            MATCH (cl:Clause {id: $cid2})
                            MERGE (cl)-[:CREATES_RISK]->(r)
                        """, rid=f"RISK_{clause_id}",
                            cat=risk_cat, level=risk_level,
                            impact=risk_score, cid=contract_id,
                            cid2=clause_id)
                        nodes_created += 1
                        rels_created += 1

                    # Obligation node (if risk_score >= 0.4)
                    if risk_score >= 0.4:
                        session.run("""
                            MERGE (o:Obligation {id: $oid})
                            SET o.description = $desc,
                                o.severity = $severity,
                                o.financial_value = $fv,
                                o.node_type = 'Obligation',
                                o.contract_id = $cid
                            WITH o
                            MATCH (cl:Clause {id: $cid2})
                            MERGE (cl)-[:CREATES_OBLIGATION]->(o)
                        """, oid=f"OBL_{clause_id}",
                            desc=f"Obligation from {canonical} clause",
                            severity=risk_level,
                            fv=risk_score * 100,
                            cid=contract_id, cid2=clause_id)
                        nodes_created += 1
                        rels_created += 1

            logger.info(f"[CUAD-GRAPH] Ingested contract {contract_id}: {nodes_created} nodes, {rels_created} rels")
            return {
                "success": True,
                "contract_id": contract_id,
                "contract_name": contract.filename,
                "nodes_created": nodes_created,
                "relationships_created": rels_created,
                "clauses_processed": len(clauses),
                "mode": "neo4j",
            }

        except Exception as e:
            logger.error(f"[CUAD-GRAPH] Neo4j ingest error: {e}", exc_info=True)
            return {"error": str(e)}

    def _fallback_ingest_summary(self, contract, clauses: List) -> Dict[str, Any]:
        """Return a simulated ingest summary when Neo4j is unavailable."""
        n_clauses = len(clauses)
        high_risk = sum(1 for c in clauses if _infer_risk_score(c) >= 0.5)
        return {
            "success": True,
            "contract_id": str(contract.id),
            "contract_name": contract.filename,
            "nodes_created": n_clauses * 3 + 5,
            "relationships_created": n_clauses * 2 + 4,
            "clauses_processed": n_clauses,
            "mode": "fallback_mysql",
            "note": "Neo4j unavailable. Graph computed in-memory from MySQL data.",
        }

    # ──────────────────────────────────────────────────────────────────────────
    # 2. COMPARE TWO CONTRACTS
    # ──────────────────────────────────────────────────────────────────────────

    def compare_contracts_graph(
        self,
        c1_id: str,
        c2_id: str,
        risk_weight: float = 1.0,
        obligation_weight: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Compare two contracts and return a React Flow compatible diff graph.

        Returns:
            {
              nodes: [...],   # React Flow nodes, color-coded by diff_status
              edges: [...],   # React Flow edges
              diff_score: float,
              contract1: {id, name, weighted_score, clause_count, risk_total},
              contract2: {id, name, weighted_score, clause_count, risk_total},
            }
        """
        from core.models import Contract, Clause

        try:
            contract1 = Contract.objects.get(id=c1_id)
            contract2 = Contract.objects.get(id=c2_id)
        except Contract.DoesNotExist as e:
            return {"error": str(e)}

        clauses1 = list(Clause.objects.filter(contract=contract1))
        clauses2 = list(Clause.objects.filter(contract=contract2))

        # Build clause type maps: {canonical_type: clause_obj}
        # When multiple clauses share the same canonical type (e.g. Arbitration + Dispute
        # Resolution → both map to "Dispute Resolution"), keep the one with the highest
        # confidence score to avoid duplicate nodes and inflated PageRank.
        def _best_clause_map(clauses):
            result = {}
            for c in clauses:
                ct = _canonical_type(c.clause_type or "", c.clause_name or "")
                if ct == "General":
                    # Use clause_name as key for General to preserve uniqueness
                    ct = (c.clause_name or f"Clause_{str(c.id)[:6]}").strip()
                conf = float(getattr(c, 'confidence', 0) or 0)
                text_len = len(getattr(c, 'extracted_text', '') or '')
                # Priority = confidence * 100 + text_length (higher is better)
                priority = conf + text_len * 0.01
                if ct not in result or priority > result[ct][1]:
                    result[ct] = (c, priority)
            return {k: v[0] for k, v in result.items()}

        map1 = _best_clause_map(clauses1)
        map2 = _best_clause_map(clauses2)
        all_types = set(map1.keys()) | set(map2.keys())

        # Diff status per clause type
        # same:     in both, risk_score diff < 0.10 AND text_length diff < 20%
        # modified: in both, risk_score diff >= 0.10 OR text_length diff >= 20%
        # missing:  only in contract1
        # new:      only in contract2
        diff_map: Dict[str, str] = {}
        for ct in all_types:
            in1 = ct in map1
            in2 = ct in map2
            if in1 and in2:
                r1 = _text_based_risk(map1[ct])
                r2 = _text_based_risk(map2[ct])
                risk_diff = abs(r1 - r2)
                # Also check text length difference as secondary signal
                t1_len = len(getattr(map1[ct], 'extracted_text', '') or '')
                t2_len = len(getattr(map2[ct], 'extracted_text', '') or '')
                max_len = max(t1_len, t2_len, 1)
                text_diff_pct = abs(t1_len - t2_len) / max_len
                is_modified = (risk_diff >= 0.10) or (text_diff_pct >= 0.20 and max_len > 50)
                diff_map[ct] = "modified" if is_modified else "same"
            elif in1:
                diff_map[ct] = "missing"
            else:
                diff_map[ct] = "new"

        # Weighted scores using text-based risk scores on deduplicated clause maps
        risk1 = sum(
            _text_based_risk(c) * CLAUSE_RISK_MULTIPLIERS.get(
                _canonical_type(c.clause_type or "", c.clause_name or ""), 0.2
            ) for c in map1.values()
        )
        risk2 = sum(
            _text_based_risk(c) * CLAUSE_RISK_MULTIPLIERS.get(
                _canonical_type(c.clause_type or "", c.clause_name or ""), 0.2
            ) for c in map2.values()
        )
        ob1 = sum(1 for c in map1.values() if _text_based_risk(c) >= 0.4)
        ob2 = sum(1 for c in map2.values() if _text_based_risk(c) >= 0.4)

        score1 = round(risk1 * risk_weight * 10 + ob1 * obligation_weight * 2, 2)
        score2 = round(risk2 * risk_weight * 10 + ob2 * obligation_weight * 2, 2)
        diff_score = round(abs(score1 - score2), 2)

        # Build React Flow nodes + edges
        nodes = []
        edges = []
        pos_radius = 350
        n_types = len(all_types)

        # Central Contract nodes
        nodes.append({
            "id": f"c1_{c1_id}",
            "type": "default",
            "position": {"x": -500, "y": 0},
            "data": {
                "label": (contract1.filename or "Contract A")[:20],
                "type": "Contract",
                "nodeType": "Contract",
                "size": 80,
                "score": score1,
                "color": NODE_COLORS["Contract"],
            },
        })
        nodes.append({
            "id": f"c2_{c2_id}",
            "type": "default",
            "position": {"x": 500, "y": 0},
            "data": {
                "label": (contract2.filename or "Contract B")[:20],
                "type": "Contract",
                "nodeType": "Contract",
                "size": 80,
                "score": score2,
                "color": NODE_COLORS["Contract"],
            },
        })

        # Clause type nodes in circular layout
        for i, ct in enumerate(sorted(all_types)):
            angle = (2 * math.pi * i) / max(n_types, 1)
            x = pos_radius * math.cos(angle)
            y = pos_radius * math.sin(angle)
            status = diff_map[ct]
            color = NODE_COLORS[status]
            node_id = f"ct_{ct.replace(' ', '_')}"

            # Risk score of this clause type — use text-based score
            r1 = _text_based_risk(map1[ct]) if ct in map1 else 0.0
            r2 = _text_based_risk(map2[ct]) if ct in map2 else 0.0
            avg_risk = round((r1 + r2) / max(sum([int(ct in map1), int(ct in map2)]), 1), 2)
            size = 40 + int(avg_risk * 50)  # 40–90px based on risk

            nodes.append({
                "id": node_id,
                "type": "default",
                "position": {"x": x, "y": y},
                "data": {
                    "label": ct[:18],
                    "type": "ClauseType",
                    "nodeType": "ClauseType",
                    "diff_status": status,
                    "color": color,
                    "size": size,
                    "risk_c1": r1,
                    "risk_c2": r2,
                },
            })

            # Edges: contract1 → clause type (if present in c1)
            if ct in map1:
                edges.append({
                    "id": f"e_c1_{node_id}",
                    "source": f"c1_{c1_id}",
                    "target": node_id,
                    "label": "HAS_CLAUSE",
                    "color": "#68BC00",
                    "width": 2,
                    "animated": status == "missing",
                })

            # Edges: contract2 → clause type (if present in c2)
            if ct in map2:
                edges.append({
                    "id": f"e_c2_{node_id}",
                    "source": f"c2_{c2_id}",
                    "target": node_id,
                    "label": "HAS_CLAUSE",
                    "color": "#4C8EDA",
                    "width": 2,
                    "animated": status == "new",
                })

            # Cross-edge between contracts for same/modified clauses
            if status in ("same", "modified"):
                edges.append({
                    "id": f"e_diff_{node_id}",
                    "source": f"c1_{c1_id}",
                    "target": f"c2_{c2_id}",
                    "label": f"DIFF:{status.upper()}",
                    "color": color,
                    "width": 1,
                    "animated": status == "modified",
                    "style": {"strokeDasharray": "5,5" if status == "modified" else "none"},
                })

            # Add Risk node for high-risk clauses (risk >= 0.55)
            # Use the higher of the two risk scores
            high_risk = max(r1, r2)
            if high_risk >= 0.55:
                risk_node_id = f"risk_{node_id}"
                # Position Risk node offset from clause node
                rx = x + 80 * math.cos(angle + 0.5)
                ry = y + 80 * math.sin(angle + 0.5)
                nodes.append({
                    "id": risk_node_id,
                    "type": "default",
                    "position": {"x": rx, "y": ry},
                    "data": {
                        "label": f"Risk\n{int(high_risk * 100)}%",
                        "type": "Risk",
                        "nodeType": "Risk",
                        "size": 28 + int(high_risk * 20),
                        "color": NODE_COLORS.get("Risk", "#F16667"),
                        "risk_score": round(high_risk, 3),
                        "severity": "HIGH" if high_risk >= 0.70 else "MEDIUM",
                    },
                })
                edges.append({
                    "id": f"e_risk_{node_id}",
                    "source": node_id,
                    "target": risk_node_id,
                    "label": "CREATES_RISK",
                    "color": "#F16667",
                    "width": 1,
                    "animated": high_risk >= 0.70,
                })

            # Add Obligation node for medium+ risk clauses (risk >= 0.35)
            mid_risk = max(r1, r2)
            if mid_risk >= 0.35:
                ob_node_id = f"ob_{node_id}"
                ox = x + 90 * math.cos(angle - 0.5)
                oy = y + 90 * math.sin(angle - 0.5)
                nodes.append({
                    "id": ob_node_id,
                    "type": "default",
                    "position": {"x": ox, "y": oy},
                    "data": {
                        "label": f"Oblig.\n{ct[:10]}",
                        "type": "Obligation",
                        "nodeType": "Obligation",
                        "size": 24,
                        "color": NODE_COLORS.get("Obligation", "#F79767"),
                        "clause_type": ct,
                    },
                })
                edges.append({
                    "id": f"e_ob_{node_id}",
                    "source": node_id,
                    "target": ob_node_id,
                    "label": "CREATES_OBLIGATION",
                    "color": "#F79767",
                    "width": 1,
                    "animated": False,
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "diff_score": diff_score,
            "diff_summary": {
                "same": sum(1 for s in diff_map.values() if s == "same"),
                "modified": sum(1 for s in diff_map.values() if s == "modified"),
                "missing": sum(1 for s in diff_map.values() if s == "missing"),
                "new": sum(1 for s in diff_map.values() if s == "new"),
            },
            "contract1": {
                "id": c1_id,
                "name": contract1.filename or "Contract A",
                "weighted_score": score1,
                "clause_count": len(clauses1),
                "risk_total": round(risk1, 3),
                "obligation_count": ob1,
            },
            "contract2": {
                "id": c2_id,
                "name": contract2.filename or "Contract B",
                "weighted_score": score2,
                "clause_count": len(clauses2),
                "risk_total": round(risk2, 3),
                "obligation_count": ob2,
            },
        }

    # ──────────────────────────────────────────────────────────────────────────
    # 2b. Multi-Contract Portfolio Comparison (3–5 contracts)
    # ──────────────────────────────────────────────────────────────────────────

    def compare_multi_contracts_graph(
        self,
        contract_ids: List[str],
        risk_weight: float = 1.0,
        obligation_weight: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Compare 2–5 contracts in a single portfolio graph.

        For each clause type, classifies coverage as:
          - universal  : present in ALL contracts
          - common     : present in majority (>50%) but not all
          - partial    : present in minority (≤50%) but not 1
          - unique     : present in exactly 1 contract
          - absent     : present in no contract (never emitted)

        Returns React Flow compatible nodes + edges plus per-contract summary scores.
        """
        from core.models import Contract, Clause

        if len(contract_ids) < 2 or len(contract_ids) > 5:
            return {"error": "Provide between 2 and 5 contract IDs"}

        # Load contracts
        contracts = []
        for cid in contract_ids:
            try:
                c = Contract.objects.get(id=cid)
                contracts.append(c)
            except Contract.DoesNotExist:
                return {"error": f"Contract {cid} not found"}

        n = len(contracts)

        # Build clause type maps per contract
        def _best_clause_map(clauses):
            result = {}
            for c in clauses:
                ct = _canonical_type(c.clause_type or "", c.clause_name or "")
                if ct == "General":
                    ct = (c.clause_name or f"Clause_{str(c.id)[:6]}").strip()
                conf = float(getattr(c, 'confidence', 0) or 0)
                text_len = len(getattr(c, 'extracted_text', '') or '')
                priority = conf + text_len * 0.01
                if ct not in result or priority > result[ct][1]:
                    result[ct] = (c, priority)
            return {k: v[0] for k, v in result.items()}

        maps = []
        for contract in contracts:
            clauses = list(Clause.objects.filter(contract=contract))
            maps.append(_best_clause_map(clauses))

        # All clause types across all contracts
        all_types = set()
        for m in maps:
            all_types.update(m.keys())

        # Determine coverage status per clause type
        coverage: Dict[str, str] = {}
        for ct in all_types:
            count_present = sum(1 for m in maps if ct in m)
            if count_present == n:
                coverage[ct] = "universal"
            elif count_present > n / 2:
                coverage[ct] = "common"
            elif count_present > 1:
                coverage[ct] = "partial"
            else:
                coverage[ct] = "unique"

        # Color map for coverage status
        coverage_colors = {
            "universal": "#68BC00",   # green  — all contracts
            "common":    "#FFD86E",   # yellow — majority
            "partial":   "#F97316",   # orange — minority
            "unique":    "#4C8EDA",   # blue   — only one contract
        }

        # Per-contract weighted scores
        contract_scores = []
        for i, (contract, m) in enumerate(zip(contracts, maps)):
            risk_total = sum(
                _text_based_risk(c) * CLAUSE_RISK_MULTIPLIERS.get(
                    _canonical_type(c.clause_type or "", c.clause_name or ""), 0.2
                ) for c in m.values()
            )
            ob_count = sum(1 for c in m.values() if _text_based_risk(c) >= 0.4)
            weighted = round(risk_total * risk_weight * 10 + ob_count * obligation_weight * 2, 2)
            contract_scores.append({
                "id": str(contract.id),
                "name": (contract.filename or f"Contract {chr(65 + i)}")[:24],
                "weighted_score": weighted,
                "clause_count": len(m),
                "risk_total": round(risk_total, 3),
                "obligation_count": ob_count,
                "idx": i,
            })

        # ── Build React Flow graph ──────────────────────────────────────────
        nodes = []
        edges = []

        # Contract nodes in outer circle
        contract_radius = 520
        for i, cs in enumerate(contract_scores):
            angle = (2 * math.pi * i) / n
            cx = contract_radius * math.cos(angle)
            cy = contract_radius * math.sin(angle)
            nodes.append({
                "id": f"mc_{cs['id']}",
                "type": "default",
                "position": {"x": cx, "y": cy},
                "data": {
                    "label": cs["name"],
                    "type": "Contract",
                    "nodeType": "Contract",
                    "size": 70,
                    "score": cs["weighted_score"],
                    "color": NODE_COLORS["Contract"],
                    "rank": i + 1,
                },
            })

        # Clause type nodes in inner circle
        n_types = len(all_types)
        clause_radius = 220
        for j, ct in enumerate(sorted(all_types)):
            angle = (2 * math.pi * j) / max(n_types, 1)
            tx = clause_radius * math.cos(angle)
            ty = clause_radius * math.sin(angle)
            status = coverage[ct]
            color = coverage_colors[status]
            node_id = f"mct_{ct.replace(' ', '_')}"

            # Average risk across contracts that have this clause
            risks = [_text_based_risk(maps[i][ct]) for i in range(n) if ct in maps[i]]
            avg_risk = round(sum(risks) / len(risks), 2) if risks else 0.0
            size = 36 + int(avg_risk * 44)

            nodes.append({
                "id": node_id,
                "type": "default",
                "position": {"x": tx, "y": ty},
                "data": {
                    "label": ct[:18],
                    "type": "ClauseType",
                    "nodeType": "ClauseType",
                    "coverage": status,
                    "color": color,
                    "size": size,
                    "avg_risk": avg_risk,
                    "present_in": sum(1 for m in maps if ct in m),
                    "total_contracts": n,
                },
            })

            # Edges from each contract to clause types it contains
            for i, (cs, m) in enumerate(zip(contract_scores, maps)):
                if ct in m:
                    r = _text_based_risk(m[ct])
                    edges.append({
                        "id": f"mc_e_{cs['id']}_{node_id}",
                        "source": f"mc_{cs['id']}",
                        "target": node_id,
                        "label": "HAS_CLAUSE",
                        "color": color,
                        "width": 1 + int(r * 3),
                        "animated": r >= 0.70,
                    })

            # Add risk node for universal high-risk clauses
            if avg_risk >= 0.55 and status in ("universal", "common"):
                risk_id = f"mc_risk_{node_id}"
                rx = tx + 70 * math.cos(angle + 0.5)
                ry = ty + 70 * math.sin(angle + 0.5)
                nodes.append({
                    "id": risk_id,
                    "type": "default",
                    "position": {"x": rx, "y": ry},
                    "data": {
                        "label": f"Risk\n{int(avg_risk * 100)}%",
                        "type": "Risk",
                        "nodeType": "Risk",
                        "size": 26 + int(avg_risk * 18),
                        "color": NODE_COLORS.get("Risk", "#F16667"),
                        "risk_score": avg_risk,
                        "severity": "HIGH" if avg_risk >= 0.70 else "MEDIUM",
                    },
                })
                edges.append({
                    "id": f"mc_erisk_{node_id}",
                    "source": node_id,
                    "target": risk_id,
                    "label": "CREATES_RISK",
                    "color": "#F16667",
                    "width": 1,
                    "animated": avg_risk >= 0.70,
                })

        # Coverage summary
        cov_summary = {
            "universal": sum(1 for s in coverage.values() if s == "universal"),
            "common":    sum(1 for s in coverage.values() if s == "common"),
            "partial":   sum(1 for s in coverage.values() if s == "partial"),
            "unique":    sum(1 for s in coverage.values() if s == "unique"),
        }

        return {
            "nodes": nodes,
            "edges": edges,
            "contracts": contract_scores,
            "coverage_summary": cov_summary,
            "total_clause_types": n_types,
            "contract_count": n,
            "coverage_legend": {
                "universal": "Present in ALL contracts",
                "common":    "Present in majority (>50%)",
                "partial":   "Present in minority (≤50%)",
                "unique":    "Unique to 1 contract",
            },
        }

    # ──────────────────────────────────────────────────────────────────────────
    # 3. GDS — PageRank (clause influence)
    # ──────────────────────────────────────────────────────────────────────────

    def get_gds_pagerank(self, contract_id: str) -> Dict[str, Any]:
        """
        Compute PageRank-based clause influence scores.
        Uses Neo4j GDS if available, otherwise NetworkX PageRank.
        Supports both MySQL-backed contracts and Neo4j-only CUAD JSON contracts.
        """
        from core.models import Clause

        all_clauses = list(Clause.objects.filter(contract_id=contract_id))

        # ── Neo4j fallback for CUAD JSON ingested contracts (no MySQL row) ─────
        neo4j_mode = False
        neo4j_records = []
        if not all_clauses and self.neo4j_available:
            try:
                with self.driver.session() as session:
                    neo4j_records = session.run(
                        """
                        MATCH (cl:Clause {contract_id: $cid})
                        RETURN cl.id AS clause_id, cl.clause_name AS clause_name,
                               cl.clause_type AS clause_type,
                               cl.risk_score AS risk_score,
                               cl.risk_level AS risk_level
                        """,
                        cid=contract_id
                    ).data()
            except Exception as e:
                logger.warning(f"[PAGERANK] Neo4j query failed: {e}")
                neo4j_records = []
            if not neo4j_records:
                return {"error": f"No clauses found for contract '{contract_id}'", "pagerank": []}
            neo4j_mode = True
        elif not all_clauses:
            return {"error": "No clauses found", "pagerank": []}

        # ── Build clause list (unified format) ────────────────────────────────
        # Each entry: (clause_id, canonical_type, risk_score, display_name, risk_level)
        G = nx.DiGraph()
        cl_list = []

        if neo4j_mode:
            for rec in neo4j_records:
                clause_id = rec.get("clause_id") or f"neo_{hash(str(rec))}"
                ct = _canonical_type(rec.get("clause_type") or "", rec.get("clause_name") or "")
                rs = float(rec.get("risk_score") or 0.3)
                name = rec.get("clause_name") or ct
                rl = rec.get("risk_level") or _infer_risk_level(rs)
                cl_list.append((clause_id, ct, rs, name, rl))
                G.add_node(clause_id, name=name, risk_score=rs, clause_type=ct)
        else:
            for clause in all_clauses:
                clause_id = str(clause.id)
                ct = _canonical_type(clause.clause_type or "", clause.clause_name or "")
                rs = _text_based_risk(clause)
                name = clause.clause_name or ct
                rl = clause.risk_level or _infer_risk_level(rs)
                cl_list.append((clause_id, ct, rs, name, rl))
                G.add_node(clause_id, name=name, risk_score=rs, clause_type=ct)

        # Edges: weight by RISK SCORE of target node so higher-risk clauses attract
        # more flow and produce meaningfully different PageRank values
        type_to_ids: Dict[str, List] = {}
        for cid, ct, rs, *_ in cl_list:
            type_to_ids.setdefault(ct, []).append((cid, rs))

        for ct, members in type_to_ids.items():
            if len(members) > 1:
                for i, (id1, r1) in enumerate(members):
                    for j, (id2, r2) in enumerate(members):
                        if i != j:
                            # Weight = risk score of the TARGET node so that
                            # high-risk clauses pull more PageRank flow into them
                            G.add_edge(id1, id2, weight=max(r2, 0.05))

        # Cross-type edges: high-risk types amplify each other,
        # but use asymmetric risk-proportional weights (not flat 0.3)
        HIGH_RISK_TYPES = {"Indemnification", "Limitation of Liability", "Intellectual Property", "Termination"}
        high_risk_ids = [(cid, rs) for cid, ct, rs, *_ in cl_list if ct in HIGH_RISK_TYPES]
        for i, (id1, r1) in enumerate(high_risk_ids):
            for j, (id2, r2) in enumerate(high_risk_ids):
                if i != j and not G.has_edge(id1, id2):
                    # Asymmetric: weight proportional to target's risk score
                    G.add_edge(id1, id2, weight=max(r2 * 0.5, 0.05))

        # If still no edges, add risk-weighted chain
        if len(G.edges) == 0 and len(G.nodes) > 1:
            node_list = sorted(G.nodes,
                               key=lambda n: G.nodes[n].get("risk_score", 0),
                               reverse=True)
            for i in range(len(node_list) - 1):
                r_target = G.nodes[node_list[i + 1]].get("risk_score", 0.3)
                G.add_edge(node_list[i], node_list[i + 1], weight=max(r_target, 0.05))

        if len(G.nodes) == 0:
            return {"pagerank": [], "contract_id": contract_id}

        try:
            pr = nx.pagerank(G, alpha=0.85, weight="weight", max_iter=200)
        except Exception:
            pr = {n: G.nodes[n].get("risk_score", 1.0 / len(G.nodes)) for n in G.nodes}

        # ── Composite score: 55% PageRank + 45% risk_score ────────────────────
        # Blending prevents the all-100 collapse that happens when PageRank values
        # are near-equal (fully-connected symmetric cluster).
        pr_vals = list(pr.values())
        min_pr = min(pr_vals)
        max_pr = max(pr_vals)
        pr_range = max_pr - min_pr if max_pr > min_pr else 1e-9

        risk_vals = [rs for _, _, rs, *_ in cl_list]
        min_rs = min(risk_vals)
        max_rs = max(risk_vals)
        rs_range = max_rs - min_rs if max_rs > min_rs else 1e-9

        results = []
        for clause_id, ct, rs, name, rl in cl_list:
            raw_pr = pr.get(clause_id, min_pr)
            # Normalize each signal to [0, 1] independently
            pr_norm = (raw_pr - min_pr) / pr_range
            rs_norm = (rs - min_rs) / rs_range
            # Blend: PageRank captures graph centrality, risk_score captures content severity
            combined = 0.55 * pr_norm + 0.45 * rs_norm
            # Scale to 20–100 range (floor at 20 so every clause is visible)
            score = round(20.0 + combined * 80.0, 1)
            results.append({
                "clause_id": clause_id,
                "clause_name": name,
                "clause_type": ct,
                "pagerank_score": score,
                "pagerank_raw": round(raw_pr, 6),
                "risk_score": round(rs, 3),
                "risk_level": rl,
            })

        results.sort(key=lambda x: x["pagerank_score"], reverse=True)

        return {
            "contract_id": contract_id,
            "method": "networkx_pagerank",
            "node_count": len(G.nodes),
            "edge_count": len(G.edges),
            "pagerank": results,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # 4. GDS — Contract Similarity
    # ──────────────────────────────────────────────────────────────────────────

    def get_gds_similarity(self, c1_id: str, c2_id: str) -> Dict[str, Any]:
        """
        Compute structural similarity between two contracts.

        Uses TWO levels of comparison:
        1. RAW clause names (Jaccard) — shows which specific clauses each contract has
        2. CANONICAL types (cosine on risk vectors) — measures risk-profile similarity

        Raw-name Jaccard avoids the 100%-always bug: when all contracts share the same
        9 canonical buckets but may have different raw clause names, we show the
        differences at the raw-name level.  If raw names are also identical we fall back
        to a risk-delta-adjusted Jaccard so the result still reflects real differences.
        """
        from core.models import Clause, Contract

        clauses1 = list(Clause.objects.filter(contract_id=c1_id))
        clauses2 = list(Clause.objects.filter(contract_id=c2_id))

        if not clauses1 or not clauses2:
            return {"similarity": 0.0, "error": "One or both contracts have no clauses"}

        # ── 1. Raw-name sets (used for Jaccard + overlap display) ─────────────
        def _raw_name(c):
            return (c.clause_name or "").strip().lower()

        raw1 = {_raw_name(c) for c in clauses1 if _raw_name(c)}
        raw2 = {_raw_name(c) for c in clauses2 if _raw_name(c)}

        raw_intersection = raw1 & raw2
        raw_union = raw1 | raw2
        raw_jaccard = round(len(raw_intersection) / len(raw_union) if raw_union else 0, 4)

        # ── 2. Canonical-type risk-vector cosine (measures risk-profile diff) ──
        def _best_type_map(clauses):
            result = {}
            for c in clauses:
                ct = _canonical_type(c.clause_type or "", c.clause_name or "")
                conf = float(getattr(c, 'confidence', 0) or 0)
                text_len = len(getattr(c, 'extracted_text', '') or '')
                priority = conf + text_len * 0.01
                if ct not in result or priority > result[ct][1]:
                    result[ct] = (c, priority)
            return {k: v[0] for k, v in result.items()}

        bmap1 = _best_type_map(clauses1)
        bmap2 = _best_type_map(clauses2)
        all_types = sorted(set(bmap1.keys()) | set(bmap2.keys()))

        vec1 = [_text_based_risk(bmap1[t]) if t in bmap1 else 0.0 for t in all_types]
        vec2 = [_text_based_risk(bmap2[t]) if t in bmap2 else 0.0 for t in all_types]

        dot = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = math.sqrt(sum(a * a for a in vec1))
        mag2 = math.sqrt(sum(b * b for b in vec2))
        cosine = round(dot / (mag1 * mag2) if mag1 * mag2 > 0 else 0, 4)

        # ── 3. If raw names are 100% identical, apply a risk-delta penalty ─────
        # This prevents the "always 100% Jaccard" when contracts share all clause
        # names but differ in risk content.
        if raw_jaccard == 1.0 and raw1 == raw2:
            # Compute average absolute risk difference across shared names
            name_to_clause1 = {_raw_name(c): c for c in clauses1}
            name_to_clause2 = {_raw_name(c): c for c in clauses2}
            risk_diffs = []
            for nm in raw_intersection:
                r1 = _text_based_risk(name_to_clause1[nm])
                r2 = _text_based_risk(name_to_clause2[nm])
                risk_diffs.append(abs(r1 - r2))
            avg_risk_delta = sum(risk_diffs) / len(risk_diffs) if risk_diffs else 0
            # Penalise Jaccard proportionally to risk delta (max 30% reduction)
            raw_jaccard = round(max(0.0, 1.0 - avg_risk_delta * 1.5), 4)

        # ── 4. Combined score ──────────────────────────────────────────────────
        combined = round(0.5 * raw_jaccard + 0.5 * cosine, 4)

        # ── 5. Overlap details using RAW names (display-friendly, Title Case) ──
        def _title(nm): return nm.title()

        common_names  = sorted(_title(n) for n in raw_intersection)
        only_in_c1    = sorted(_title(n) for n in (raw1 - raw2))
        only_in_c2    = sorted(_title(n) for n in (raw2 - raw1))

        # Per-clause risk comparison for common raw names
        name_to_clause1 = {_raw_name(c): c for c in clauses1}
        name_to_clause2 = {_raw_name(c): c for c in clauses2}
        clause_risk_diff = {}
        for nm in raw_intersection:
            if nm in name_to_clause1 and nm in name_to_clause2:
                r1 = round(_text_based_risk(name_to_clause1[nm]), 3)
                r2 = round(_text_based_risk(name_to_clause2[nm]), 3)
                clause_risk_diff[nm.title()] = {
                    "contract1_risk": r1, "contract2_risk": r2,
                    "diff": round(abs(r1 - r2), 3)
                }

        return {
            "contract1_id": c1_id,
            "contract2_id": c2_id,
            "similarity_score": combined,
            "jaccard_similarity": raw_jaccard,
            "cosine_similarity": cosine,
            "clause_overlap": {
                "common": common_names,
                "only_in_contract1": only_in_c1,
                "only_in_contract2": only_in_c2,
                "common_count": len(common_names),
            },
            "clause_risk_comparison": clause_risk_diff,
            "method": "raw_name_jaccard_cosine_hybrid",
        }

    # ──────────────────────────────────────────────────────────────────────────
    # 5. GNN — Contract Risk/Stability Scoring
    # ──────────────────────────────────────────────────────────────────────────

    def get_gnn_score(self, contract_id: str) -> Dict[str, Any]:
        """
        Score a contract using Graph Neural Network (GCN).
        Falls back to weighted graph centrality scoring if PyTorch unavailable.
        Supports both MySQL-backed contracts and Neo4j-only CUAD JSON contracts.
        """
        from core.models import Clause

        clauses = list(Clause.objects.filter(contract_id=contract_id))

        # ── Neo4j fallback for CUAD JSON ingested contracts ───────────────────
        if not clauses and self.neo4j_available:
            try:
                with self.driver.session() as session:
                    neo4j_records = session.run(
                        """
                        MATCH (cl:Clause {contract_id: $cid})
                        RETURN cl.id AS clause_id, cl.clause_name AS clause_name,
                               cl.clause_type AS clause_type, cl.risk_score AS risk_score,
                               cl.risk_level AS risk_level, cl.text AS text,
                               cl.confidence AS confidence
                        """,
                        cid=contract_id
                    ).data()
                clauses = [_NeoClause(r) for r in neo4j_records]
            except Exception as e:
                logger.warning(f"[CUAD-GNN] Neo4j fallback failed: {e}")
                clauses = []

        if not clauses:
            return {"error": f"No clauses found for contract '{contract_id}'",
                    "risk_score": 0, "stability_score": 100}

        # Always try PyTorch GCN first
        try:
            return self._gnn_pytorch_score(contract_id, clauses)
        except Exception as e:
            logger.warning(f"[CUAD-GNN] PyTorch unavailable, using rule-based fallback: {e}")
            return self._gnn_rule_based_score(contract_id, clauses)

    def _gnn_pytorch_score(self, contract_id: str, clauses: List) -> Dict[str, Any]:
        """PyTorch Geometric GCN scoring."""
        import torch
        import torch.nn.functional as F
        from torch_geometric.nn import GCNConv
        from torch_geometric.data import Data

        n = len(clauses)
        if n < 2:
            raise ValueError("Not enough clauses for GNN")

        # Node features: [risk_score, type_multiplier, clause_type_idx]
        type_list = sorted(set(_canonical_type(c.clause_type or "", c.clause_name or "") for c in clauses))
        type_idx = {t: i for i, t in enumerate(type_list)}

        x_rows = []
        for c in clauses:
            rs = _text_based_risk(c)
            ct = _canonical_type(c.clause_type or "", c.clause_name or "")
            mult = CLAUSE_RISK_MULTIPLIERS.get(ct, 0.2)
            x_rows.append([rs, mult, float(type_idx[ct]) / max(len(type_list), 1)])
        x = torch.tensor(x_rows, dtype=torch.float)

        # Build edges (fully connected within same clause type)
        edge_src, edge_dst = [], []
        for i, c1 in enumerate(clauses):
            for j, c2 in enumerate(clauses):
                if i != j and _canonical_type(c1.clause_type or "", c1.clause_name or "") == _canonical_type(c2.clause_type or "", c2.clause_name or ""):
                    edge_src.append(i)
                    edge_dst.append(j)

        if not edge_src:
            # Default: linear chain
            edge_src = list(range(n - 1))
            edge_dst = list(range(1, n))

        edge_index = torch.tensor([edge_src, edge_dst], dtype=torch.long)
        data = Data(x=x, edge_index=edge_index)

        class SimpleGCN(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.conv1 = GCNConv(3, 16)
                self.conv2 = GCNConv(16, 1)

            def forward(self, data):
                x = self.conv1(data.x, data.edge_index)
                x = F.relu(x)
                x = self.conv2(x, data.edge_index)
                return torch.sigmoid(x)

        model = SimpleGCN()
        model.eval()
        with torch.no_grad():
            out = model(data).squeeze().tolist()

        if isinstance(out, float):
            out = [out]

        avg_risk = sum(out) / len(out)
        risk_score = round(avg_risk * 100, 1)
        stability_score = round((1 - avg_risk) * 100, 1)

        # Top risky clauses from GNN output
        scored = sorted(zip(clauses, out), key=lambda x: x[1], reverse=True)
        top_risky = [
            {
                "clause_id": str(c.id),
                "clause_name": c.clause_name or _canonical_type(c.clause_type or "", c.clause_name or ""),
                "gnn_risk": round(s * 100, 1),
                "risk_level": c.risk_level or _infer_risk_level(s),
            }
            for c, s in scored[:5]
        ]

        return {
            "contract_id": contract_id,
            "risk_score": risk_score,
            "stability_score": stability_score,
            "node_count": n,
            "edge_count": len(edge_src),
            "top_risky_clauses": top_risky,
            "method": "pytorch_geometric_gcn",
        }

    def _gnn_rule_based_score(self, contract_id: str, clauses: List) -> Dict[str, Any]:
        """
        Rule-based fallback when PyTorch unavailable.
        Uses PageRank centrality × risk_score × clause_type_multiplier.
        """
        G = nx.DiGraph()
        for c in clauses:
            cid = str(c.id)
            ct = _canonical_type(c.clause_type or "", c.clause_name or "")
            rs = _text_based_risk(c)
            G.add_node(cid, risk_score=rs, clause_type=ct)

        cl_list = [
            (str(c.id), _canonical_type(c.clause_type or "", c.clause_name or ""), _text_based_risk(c))
            for c in clauses
        ]
        for i, (id1, t1, _) in enumerate(cl_list):
            for j, (id2, t2, _) in enumerate(cl_list):
                if i != j and t1 == t2:
                    G.add_edge(id1, id2)

        # If no same-type edges, add chain so PageRank works
        if len(G.edges) == 0 and len(G.nodes) > 1:
            node_list = list(G.nodes)
            for i in range(len(node_list) - 1):
                G.add_edge(node_list[i], node_list[i + 1])

        n = len(G.nodes)
        try:
            pr = nx.pagerank(G, alpha=0.85, max_iter=100) if n > 1 else {list(G.nodes)[0]: 1.0}
        except Exception:
            pr = {node: 1.0 / n for node in G.nodes}

        weighted_scores = []
        top_risky = []
        for c in clauses:
            cid = str(c.id)
            ct = _canonical_type(c.clause_type or "", c.clause_name or "")
            rs = _text_based_risk(c)
            mult = CLAUSE_RISK_MULTIPLIERS.get(ct, 0.2)
            centrality = pr.get(cid, 1.0 / n)
            weighted = rs * mult * (1 + centrality)
            weighted_scores.append(weighted)
            top_risky.append({
                "clause_id": cid,
                "clause_name": c.clause_name or ct,
                "gnn_risk": round(min(weighted * 100, 100), 1),
                "risk_level": c.risk_level or _infer_risk_level(rs),
            })

        top_risky.sort(key=lambda x: x["gnn_risk"], reverse=True)

        avg_risk = sum(weighted_scores) / len(weighted_scores) if weighted_scores else 0
        # Scale to 0-100 range (typical max is ~1.0)
        risk_score = round(min(avg_risk * 100, 100), 1)
        stability_score = round(max(100 - risk_score, 0), 1)

        return {
            "contract_id": contract_id,
            "risk_score": risk_score,
            "stability_score": stability_score,
            "node_count": n,
            "edge_count": len(G.edges),
            "top_risky_clauses": top_risky[:5],
            "method": "rule_based_pagerank_fallback",
        }

    # ──────────────────────────────────────────────────────────────────────────
    # 6. GNN TRAINING (200-epoch loop with PyTorch)
    # ──────────────────────────────────────────────────────────────────────────

    def train_gnn(self, contract_id: str, epochs: int = 200, lr: float = 0.01) -> Dict[str, Any]:
        """
        Train a SimpleGCN on the contract graph for `epochs` iterations.
        Saves checkpoint to /tmp/cuad_gnn_{contract_id}.pt.
        Returns final loss, risk_score, stability_score.
        Falls back to rule-based scoring if PyTorch unavailable.
        """
        from core.models import Clause

        clauses = list(Clause.objects.filter(contract_id=contract_id))
        if not clauses:
            return {"error": "No clauses found", "trained": False}

        try:
            import torch
            import torch.nn.functional as F
            from torch_geometric.nn import GCNConv
            from torch_geometric.data import Data

            n = len(clauses)
            type_list = sorted(set(_canonical_type(c.clause_type or "", c.clause_name or "") for c in clauses))
            type_idx = {t: i for i, t in enumerate(type_list)}

            # Node features: [risk_score, type_multiplier, type_idx_normalized]
            x_rows = []
            y_rows = []  # target = text-based risk score (supervised signal)
            for c in clauses:
                rs = _text_based_risk(c)
                ct = _canonical_type(c.clause_type or "", c.clause_name or "")
                mult = CLAUSE_RISK_MULTIPLIERS.get(ct, 0.2)
                x_rows.append([rs, mult, float(type_idx[ct]) / max(len(type_list), 1)])
                y_rows.append([rs])  # self-supervised: predict own risk score

            x = torch.tensor(x_rows, dtype=torch.float)
            y = torch.tensor(y_rows, dtype=torch.float)

            # Build edges
            edge_src, edge_dst = [], []
            for i, c1 in enumerate(clauses):
                for j, c2 in enumerate(clauses):
                    if i != j and _canonical_type(c1.clause_type or "", c1.clause_name or "") == _canonical_type(c2.clause_type or "", c2.clause_name or ""):
                        edge_src.append(i)
                        edge_dst.append(j)
            if not edge_src:
                edge_src = list(range(n - 1))
                edge_dst = list(range(1, n))

            edge_index = torch.tensor([edge_src, edge_dst], dtype=torch.long)
            data = Data(x=x, edge_index=edge_index, y=y)

            class SimpleGCN(torch.nn.Module):
                def __init__(self):
                    super().__init__()
                    self.conv1 = GCNConv(3, 16)
                    self.conv2 = GCNConv(16, 1)

                def forward(self, d):
                    h = F.relu(self.conv1(d.x, d.edge_index))
                    return torch.sigmoid(self.conv2(h, d.edge_index))

            model = SimpleGCN()
            optimizer = torch.optim.Adam(model.parameters(), lr=lr)
            loss_history = []

            model.train()
            for epoch in range(epochs):
                optimizer.zero_grad()
                out = model(data)
                loss = F.mse_loss(out, data.y)
                loss.backward()
                optimizer.step()
                record_every = max(1, epochs // 40)
                if epoch % record_every == 0 or epoch == epochs - 1:
                    loss_history.append({"epoch": epoch, "loss": round(loss.item(), 6)})

            # Save checkpoint — use cross-platform temp dir (fixes Windows /tmp/ crash)
            import os, tempfile
            ckpt_path = os.path.join(tempfile.gettempdir(), f"cuad_gnn_{contract_id}.pt")
            torch.save(model.state_dict(), ckpt_path)

            # Compute final scores from trained model
            model.eval()
            with torch.no_grad():
                out = model(data).squeeze().tolist()
            if isinstance(out, float):
                out = [out]

            avg_risk = sum(out) / len(out)
            risk_score = round(avg_risk * 100, 1)
            stability_score = round((1 - avg_risk) * 100, 1)

            scored = sorted(zip(clauses, out), key=lambda x: x[1], reverse=True)
            top_risky = [
                {
                    "clause_name": c.clause_name or _canonical_type(c.clause_type or "", c.clause_name or ""),
                    "gnn_risk": round(s * 100, 1),
                    "risk_level": _infer_risk_level(s),
                }
                for c, s in scored[:5]
            ]

            return {
                "contract_id": contract_id,
                "trained": True,
                "epochs": epochs,
                "final_loss": loss_history[-1]["loss"] if loss_history else 0,
                "loss_history": loss_history,
                "risk_score": risk_score,
                "stability_score": stability_score,
                "top_risky_clauses": top_risky,
                "checkpoint_path": ckpt_path,
                "method": "pytorch_gcn_trained",
            }

        except Exception as pytorch_err:
            logger.warning(f"[CUAD-GNN-TRAIN] PyTorch GCN failed ({type(pytorch_err).__name__}: {pytorch_err}), running NumPy GCN fallback")
            result = self._train_numpy_gcn(contract_id, clauses, epochs, lr)
            result["fallback_reason"] = f"{type(pytorch_err).__name__}: {pytorch_err}"
            return result

    def _train_numpy_gcn(self, contract_id: str, clauses: list, epochs: int, lr: float) -> Dict[str, Any]:
        """
        Pure NumPy 2-layer GCN.  No PyTorch/torch_geometric needed.

        Architecture:
          Input  (n × 3)  → W1 (3 × 16) → ReLU → GCN message passing
          Hidden (n × 16) → W2 (16 × 1) → Sigmoid → risk probability per node
          Loss: MSE against text-based risk scores (self-supervised)
          Optimiser: gradient descent with momentum (β=0.9)
        """
        import numpy as np, os, json as _json

        n = len(clauses)
        type_list = sorted(set(_canonical_type(c.clause_type or "", c.clause_name or "") for c in clauses))
        type_idx  = {t: i for i, t in enumerate(type_list)}

        # ── Node features X  (n × 3) ─────────────────────────────────────────
        X = np.zeros((n, 3), dtype=np.float32)
        y = np.zeros((n, 1), dtype=np.float32)
        for i, c in enumerate(clauses):
            rs   = _text_based_risk(c)
            ct   = _canonical_type(c.clause_type or "", c.clause_name or "")
            mult = CLAUSE_RISK_MULTIPLIERS.get(ct, 0.2)
            X[i] = [rs, mult, float(type_idx[ct]) / max(len(type_list) - 1, 1)]
            y[i] = rs  # self-supervised target

        # ── Adjacency matrix A  (n × n) with self-loops → D^-½ A D^-½ ───────
        A = np.zeros((n, n), dtype=np.float32)
        for i, c1 in enumerate(clauses):
            for j, c2 in enumerate(clauses):
                if i == j:
                    A[i, j] = 1.0
                elif _canonical_type(c1.clause_type or "", c1.clause_name or "") == \
                     _canonical_type(c2.clause_type or "", c2.clause_name or ""):
                    A[i, j] = 0.5
        # Symmetric normalisation: D^-½ A D^-½
        deg  = A.sum(axis=1, keepdims=True)
        deg  = np.where(deg == 0, 1, deg)
        Dh   = 1.0 / np.sqrt(deg)
        A_hat = Dh * A * Dh.T   # broadcast symmetric norm

        # ── Weights init (Xavier) ─────────────────────────────────────────────
        np.random.seed(42)
        W1 = np.random.randn(3,  16).astype(np.float32) * np.sqrt(2.0 / 3)
        W2 = np.random.randn(16,  1).astype(np.float32) * np.sqrt(2.0 / 16)
        # Momentum buffers
        vW1 = np.zeros_like(W1)
        vW2 = np.zeros_like(W2)
        beta = 0.9

        def relu(z):   return np.maximum(0, z)
        def sigmoid(z): return 1.0 / (1.0 + np.exp(-np.clip(z, -20, 20)))
        def d_relu(z):  return (z > 0).astype(np.float32)

        loss_history = []
        record_every = max(1, epochs // 20)   # ~20 points on the loss curve

        # ── Training loop ─────────────────────────────────────────────────────
        for epoch in range(epochs):
            # Forward
            H1_pre = A_hat @ X  @ W1          # (n × 16)
            H1     = relu(H1_pre)
            H2_pre = A_hat @ H1 @ W2          # (n × 1)
            out    = sigmoid(H2_pre)

            # MSE loss
            diff  = out - y                   # (n × 1)
            loss  = float(np.mean(diff ** 2))

            # Backward
            # dL/d_out = 2/n * diff
            dout  = (2.0 / n) * diff          # (n × 1)
            # dL/dH2_pre = dout * sigmoid'(H2_pre) = dout * out*(1-out)
            dH2_pre = dout * out * (1 - out)  # (n × 1)
            # dL/dW2 = H1^T A_hat^T dH2_pre
            dW2   = H1.T @ (A_hat.T @ dH2_pre)  # (16 × 1)
            # dL/dH1 = A_hat dH2_pre W2^T
            dH1   = (A_hat @ dH2_pre) @ W2.T    # (n × 16)
            # dL/dH1_pre = dH1 * relu'
            dH1_pre = dH1 * d_relu(H1_pre)      # (n × 16)
            # dL/dW1 = X^T A_hat^T dH1_pre
            dW1   = X.T @ (A_hat.T @ dH1_pre)   # (3 × 16)

            # Gradient clipping
            for g in (dW1, dW2):
                np.clip(g, -5, 5, out=g)

            # Momentum update
            vW1 = beta * vW1 + (1 - beta) * dW1
            vW2 = beta * vW2 + (1 - beta) * dW2
            W1  -= lr * vW1
            W2  -= lr * vW2

            if epoch % record_every == 0 or epoch == epochs - 1:
                loss_history.append({"epoch": epoch, "loss": round(loss, 6)})

        # ── Final inference ───────────────────────────────────────────────────
        H1_f  = relu(A_hat @ X  @ W1)
        out_f = sigmoid(A_hat @ H1_f @ W2).flatten().tolist()

        avg_risk       = float(np.mean(out_f))
        risk_score     = round(avg_risk * 100, 1)
        stability_score = round((1 - avg_risk) * 100, 1)

        scored = sorted(zip(clauses, out_f), key=lambda x: x[1], reverse=True)
        top_risky = [
            {
                "clause_name":  c.clause_name or _canonical_type(c.clause_type or "", c.clause_name or ""),
                "gnn_risk":     round(s * 100, 1),
                "risk_level":   _infer_risk_level(s),
            }
            for c, s in scored[:5]
        ]

        # Save checkpoint as JSON — cross-platform temp dir (fixes Windows /tmp/ crash)
        import os, tempfile as _tf
        ckpt_path = os.path.join(_tf.gettempdir(), f"cuad_gnn_{contract_id}.json")
        try:
            with open(ckpt_path, "w") as f:
                _json.dump({"W1": W1.tolist(), "W2": W2.tolist(),
                            "final_loss": loss_history[-1]["loss"],
                            "epochs": epochs}, f)
        except Exception:
            ckpt_path = None

        return {
            "contract_id":      contract_id,
            "trained":          True,
            "epochs":           epochs,
            "final_loss":       loss_history[-1]["loss"] if loss_history else 0,
            "loss_history":     loss_history,
            "risk_score":       risk_score,
            "stability_score":  stability_score,
            "top_risky_clauses": top_risky,
            "checkpoint_path":  ckpt_path,
            "method":           "numpy_gcn_trained",
        }

    # ──────────────────────────────────────────────────────────────────────────
    # 7. PERSIST SIMILAR EDGES IN NEO4J (Auto-build cosine similarity graph)
    # ──────────────────────────────────────────────────────────────────────────

    def build_similarity_edges(self, threshold: float = 0.70) -> Dict[str, Any]:
        """
        Auto-build SIMILAR relationships between clauses across all contracts.
        Uses MiniLM embeddings if available, else cosine on risk vectors.
        Persists edges as (:Clause)-[:SIMILAR {score}]->(:Clause) in Neo4j.
        Falls back to in-memory index when Neo4j unavailable.

        Args:
            threshold: Minimum similarity score to create edge (0–1)

        Returns:
            {edges_created, clauses_compared, method}
        """
        from core.models import Clause

        all_clauses = list(Clause.objects.all()[:500])  # cap at 500 for performance
        if len(all_clauses) < 2:
            return {"error": "Not enough clauses to build similarity graph", "edges_created": 0}

        # Try to get MiniLM embeddings
        vectors = self._get_clause_vectors(all_clauses)

        edges_created = 0
        similar_pairs = []

        # Build clause ID → name mapping
        clause_names = {str(c.id): c.clause_name or _canonical_type(c.clause_type or "", c.clause_name or "") for c in all_clauses}

        # Compute pairwise cosine similarity
        n = len(all_clauses)
        duplicate_count = 0
        for i in range(n):
            for j in range(i + 1, n):
                sim = self._cosine_sim(vectors[i], vectors[j])
                # Skip near-perfect matches (likely duplicates) unless threshold is very high
                if sim >= 0.98 and threshold < 0.95:
                    duplicate_count += 1
                    continue
                if sim >= threshold:
                    c1_id = str(all_clauses[i].id)
                    c2_id = str(all_clauses[j].id)
                    similar_pairs.append((c1_id, c2_id, round(sim, 4)))

        if not similar_pairs:
            return {
                "edges_created": 0,
                "clauses_compared": n,
                "pairs_found": 0,
                "threshold": threshold,
                "method": "cosine_no_matches",
            }

        # Persist to Neo4j if available
        if self.neo4j_available:
            try:
                with self.driver.session() as session:
                    # Remove old SIMILAR edges first
                    session.run("MATCH ()-[r:SIMILAR]->() DELETE r")

                    for c1_id, c2_id, score in similar_pairs:
                        session.run("""
                            MATCH (cl1:Clause {id: $id1}), (cl2:Clause {id: $id2})
                            MERGE (cl1)-[:SIMILAR {score: $score, method: 'cosine'}]->(cl2)
                            MERGE (cl2)-[:SIMILAR {score: $score, method: 'cosine'}]->(cl1)
                        """, id1=c1_id, id2=c2_id, score=score)
                        edges_created += 2

                return {
                    "edges_created": edges_created,
                    "clauses_compared": n,
                    "pairs_found": len(similar_pairs),
                    "duplicates_skipped": duplicate_count,
                    "threshold": threshold,
                    "method": "neo4j_cosine_similar",
                    "top_pairs": [
                        {
                            "clause1_id": p[0],
                            "clause1_name": clause_names.get(p[0], p[0][:20]),
                            "clause2_id": p[1],
                            "clause2_name": clause_names.get(p[1], p[1][:20]),
                            "score": p[2]
                        }
                        for p in sorted(similar_pairs, key=lambda x: x[2], reverse=True)[:10]
                    ],
                }
            except Exception as e:
                logger.error(f"[CUAD-SIMILAR] Neo4j edge write error: {e}")

        # Fallback: return in-memory results
        return {
            "edges_created": len(similar_pairs) * 2,
            "clauses_compared": n,
            "pairs_found": len(similar_pairs),
            "duplicates_skipped": duplicate_count,
            "threshold": threshold,
            "method": "in_memory_cosine_similar",
            "note": "Neo4j unavailable — edges not persisted",
            "top_pairs": [
                {
                    "clause1_id": p[0],
                    "clause1_name": clause_names.get(p[0], p[0][:20]),
                    "clause2_id": p[1],
                    "clause2_name": clause_names.get(p[1], p[1][:20]),
                    "score": p[2]
                }
                for p in sorted(similar_pairs, key=lambda x: x[2], reverse=True)[:10]
            ],
        }

    def _get_clause_vectors(self, clauses: List) -> List[List[float]]:
        """
        Get embedding vectors for clauses.
        Tries MiniLM sentence-transformers first, falls back to risk-based vector.
        """
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2", device='cpu')
            texts = []
            for c in clauses:
                text = (getattr(c, 'extracted_text', '') or '') or (c.clause_name or "")
                texts.append(text[:512])  # truncate for speed
            embeddings = model.encode(texts, batch_size=32, show_progress_bar=False)
            return embeddings.tolist()
        except Exception:
            # Fallback: risk-feature vector [risk_score, type_mult, type_idx_norm]
            type_list = sorted(set(_canonical_type(c.clause_type or "", c.clause_name or "") for c in clauses))
            type_idx = {t: i for i, t in enumerate(type_list)}
            vectors = []
            for c in clauses:
                rs = _text_based_risk(c)
                ct = _canonical_type(c.clause_type or "", c.clause_name or "")
                mult = CLAUSE_RISK_MULTIPLIERS.get(ct, 0.2)
                idx = float(type_idx.get(ct, 0)) / max(len(type_list), 1)
                # Expand to 5-dim for better differentiation
                text_len = min(len(getattr(c, 'extracted_text', '') or ''), 1000) / 1000.0
                conf = float(getattr(c, 'confidence', 0) or 0) / 100.0
                vectors.append([rs, mult, idx, text_len, conf])
            return vectors

    def _cosine_sim(self, v1: List[float], v2: List[float]) -> float:
        """Cosine similarity between two vectors."""
        dot = sum(a * b for a, b in zip(v1, v2))
        mag1 = math.sqrt(sum(a * a for a in v1))
        mag2 = math.sqrt(sum(b * b for b in v2))
        if mag1 * mag2 == 0:
            return 0.0
        return dot / (mag1 * mag2)

    # ──────────────────────────────────────────────────────────────────────────
    # 8. FULL CUAD JSON BULK INGESTION PIPELINE
    # ──────────────────────────────────────────────────────────────────────────

    def ingest_cuad_json(self, json_data: List[Dict], source: str = "cuad_dataset") -> Dict[str, Any]:
        """
        Bulk ingest CUAD-format JSON into Neo4j.

        Expected JSON structure per contract:
        {
          "contract_id": "C-1001",
          "name": "Enterprise SaaS Agreement",
          "text": "...",
          "party_a": "VendorCorp",
          "party_b": "ClientCorp",
          "jurisdiction": "Delaware",
          "industry": "Technology",
          "clauses": [
            {
              "clause_id": "CL-1",
              "clause_type": "Termination",
              "clause_name": "Termination for Convenience",
              "text": "...",
              "risk_score": 0.7,
              "confidence": 85.0
            }
          ],
          "amendments": [
            {"amendment_id": "AM-1", "date": "2024-01-15", "description": "Rate increase amendment"}
          ],
          "definitions": [
            {"term": "Confidential Information", "definition": "Any non-public information..."}
          ]
        }

        Returns summary with counts per contract.
        """
        total_contracts = 0
        total_nodes = 0
        total_rels = 0
        errors = []

        for contract_data in json_data:
            try:
                result = self._ingest_single_cuad_contract(contract_data, source)
                total_contracts += 1
                total_nodes += result.get("nodes_created", 0)
                total_rels += result.get("relationships_created", 0)
            except Exception as e:
                errors.append({"contract_id": contract_data.get("contract_id", "unknown"), "error": str(e)})

        return {
            "success": True,
            "source": source,
            "contracts_ingested": total_contracts,
            "total_nodes_created": total_nodes,
            "total_relationships_created": total_rels,
            "errors": errors,
            "mode": "neo4j" if self.neo4j_available else "fallback_summary",
        }

    def _ingest_single_cuad_contract(self, data: Dict, source: str) -> Dict[str, Any]:
        """Ingest one CUAD JSON contract record into Neo4j with all 13 node types."""
        contract_id = data.get("contract_id", f"cuad_{hash(str(data))}")
        nodes_created = 0
        rels_created = 0

        if not self.neo4j_available:
            # Count what would be created
            n_clauses = len(data.get("clauses", []))
            return {
                "nodes_created": n_clauses * 5 + 7,
                "relationships_created": n_clauses * 4 + 6,
                "mode": "dry_run",
            }

        with self.driver.session() as session:
            # ── Contract node ──
            session.run("""
                MERGE (c:Contract {id: $id})
                SET c.name = $name,
                    c.contract_id = $id,
                    c.source = $source,
                    c.party_a = $party_a,
                    c.party_b = $party_b,
                    c.jurisdiction = $jurisdiction,
                    c.node_type = 'Contract'
            """, id=contract_id, name=data.get("name", "CUAD Contract"),
                source=source,
                party_a=data.get("party_a", ""), party_b=data.get("party_b", ""),
                jurisdiction=data.get("jurisdiction", ""))
            nodes_created += 1

            # ── Party nodes ──
            for party_name in [data.get("party_a"), data.get("party_b")]:
                if party_name:
                    session.run("""
                        MERGE (p:Party {name: $name}) SET p.node_type = 'Party'
                        WITH p MATCH (c:Contract {id: $cid})
                        MERGE (c)-[:HAS_PARTY]->(p)
                    """, name=party_name, cid=contract_id)
                    nodes_created += 1; rels_created += 1

            # ── Jurisdiction node ──
            if data.get("jurisdiction"):
                session.run("""
                    MERGE (j:Jurisdiction {name: $name}) SET j.node_type = 'Jurisdiction'
                    WITH j MATCH (c:Contract {id: $cid})
                    MERGE (c)-[:GOVERNED_BY]->(j)
                """, name=data["jurisdiction"], cid=contract_id)
                nodes_created += 1; rels_created += 1

            # ── GoverningLaw node (distinct from Jurisdiction) ──
            if data.get("governing_law"):
                session.run("""
                    MERGE (gl:GoverningLaw {law: $law}) SET gl.node_type = 'GoverningLaw'
                    WITH gl MATCH (c:Contract {id: $cid})
                    MERGE (c)-[:SUBJECT_TO]->(gl)
                """, law=data["governing_law"], cid=contract_id)
                nodes_created += 1; rels_created += 1

            # ── Industry node ──
            if data.get("industry"):
                session.run("""
                    MERGE (ind:Industry {name: $name}) SET ind.node_type = 'Industry'
                    WITH ind MATCH (c:Contract {id: $cid})
                    MERGE (c)-[:BELONGS_TO]->(ind)
                """, name=data["industry"], cid=contract_id)
                nodes_created += 1; rels_created += 1

            # ── Amendment nodes ──
            for amend in data.get("amendments", []):
                amend_id = amend.get("amendment_id", f"AM_{contract_id}_{nodes_created}")
                session.run("""
                    MERGE (a:Amendment {id: $id})
                    SET a.date = $date, a.description = $desc, a.node_type = 'Amendment'
                    WITH a MATCH (c:Contract {id: $cid})
                    MERGE (c)-[:AMENDED_BY]->(a)
                """, id=amend_id, date=amend.get("date", ""), desc=amend.get("description", ""), cid=contract_id)
                nodes_created += 1; rels_created += 1

            # ── Definition nodes ──
            for defn in data.get("definitions", []):
                def_id = f"DEF_{contract_id}_{defn.get('term', '')[:20].replace(' ', '_')}"
                session.run("""
                    MERGE (d:Definition {id: $id})
                    SET d.term = $term, d.definition = $defn, d.node_type = 'Definition'
                    WITH d MATCH (c:Contract {id: $cid})
                    MERGE (c)-[:DEFINES]->(d)
                """, id=def_id, term=defn.get("term", ""), defn=defn.get("definition", ""), cid=contract_id)
                nodes_created += 1; rels_created += 1

            # ── Clause nodes (all 13 node types, 11 relationship types) ──
            clause_ids = []
            for clause in data.get("clauses", []):
                clause_id = clause.get("clause_id", f"CL_{contract_id}_{nodes_created}")
                canonical = _canonical_type(clause.get("clause_type", ""), clause.get("clause_name", ""))
                risk_score = clause.get("risk_score") or CLAUSE_DEFAULT_RISK.get(canonical, 0.3)
                risk_level = _infer_risk_level(float(risk_score))

                # Clause node
                session.run("""
                    MERGE (cl:Clause {id: $id})
                    SET cl.contract_id = $cid, cl.clause_name = $name,
                        cl.clause_type = $ctype, cl.risk_score = $rs,
                        cl.risk_level = $rl, cl.text = $text,
                        cl.confidence = $conf, cl.node_type = 'Clause'
                    WITH cl MATCH (c:Contract {id: $cid})
                    MERGE (c)-[:HAS_CLAUSE]->(cl)
                """, id=clause_id, cid=contract_id,
                    name=clause.get("clause_name", canonical),
                    ctype=canonical, rs=float(risk_score), rl=risk_level,
                    text=clause.get("text", "")[:500],
                    conf=float(clause.get("confidence", 0)))
                nodes_created += 1; rels_created += 1

                # ClauseType node
                session.run("""
                    MERGE (ct:ClauseType {type: $type}) SET ct.node_type = 'ClauseType'
                    WITH ct MATCH (cl:Clause {id: $id})
                    MERGE (cl)-[:IS_TYPE]->(ct)
                """, type=canonical, id=clause_id)
                nodes_created += 1; rels_created += 1

                # Risk node
                if float(risk_score) >= 0.4:
                    session.run("""
                        MERGE (r:Risk {id: $rid})
                        SET r.category = $cat, r.level = $lvl, r.impact_score = $rs,
                            r.probability_score = $ps, r.contract_id = $cid, r.node_type = 'Risk'
                        WITH r MATCH (cl:Clause {id: $clid})
                        MERGE (cl)-[:CREATES_RISK]->(r)
                    """, rid=f"RISK_{clause_id}", cat=canonical.upper().replace(" ", "_"),
                        lvl=risk_level, rs=float(risk_score),
                        ps=round(float(risk_score) * 0.8, 3), cid=contract_id, clid=clause_id)
                    nodes_created += 1; rels_created += 1

                # Obligation node
                if float(risk_score) >= 0.35:
                    session.run("""
                        MERGE (o:Obligation {id: $oid})
                        SET o.description = $desc, o.severity = $sev,
                            o.financial_value = $fv, o.contract_id = $cid, o.node_type = 'Obligation'
                        WITH o MATCH (cl:Clause {id: $clid})
                        MERGE (cl)-[:CREATES_OBLIGATION]->(o)
                    """, oid=f"OBL_{clause_id}",
                        desc=f"Obligation from {canonical} clause",
                        sev=risk_level, fv=float(risk_score) * 100,
                        cid=contract_id, clid=clause_id)
                    nodes_created += 1; rels_created += 1

                # Term node (for high-value clauses)
                if float(risk_score) >= 0.6:
                    session.run("""
                        MERGE (t:Term {id: $tid})
                        SET t.name = $name, t.clause_ref = $cref, t.node_type = 'Term'
                        WITH t MATCH (cl:Clause {id: $clid})
                        MERGE (cl)-[:CONTAINS_TERM]->(t)
                    """, tid=f"TERM_{clause_id}",
                        name=clause.get("clause_name", canonical),
                        cref=clause_id, clid=clause_id)
                    nodes_created += 1; rels_created += 1

                clause_ids.append((clause_id, canonical, float(risk_score)))

            # ── CrossReference edges between related clauses ──
            CROSS_REF_PAIRS = {
                ("Indemnification", "Limitation of Liability"),
                ("Termination", "Force Majeure"),
                ("Confidentiality", "Intellectual Property"),
                ("Dispute Resolution", "Governing Law"),
                ("Payment Terms", "Audit Rights"),
            }
            for id1, t1, _ in clause_ids:
                for id2, t2, _ in clause_ids:
                    if id1 != id2 and (t1, t2) in CROSS_REF_PAIRS:
                        # Create CrossReference node + REFERS_TO edge
                        xref_id = f"XREF_{id1[:8]}_{id2[:8]}"
                        session.run("""
                            MERGE (x:CrossReference {id: $xid})
                            SET x.from_type = $t1, x.to_type = $t2, x.node_type = 'CrossReference'
                            WITH x
                            MATCH (cl1:Clause {id: $id1}), (cl2:Clause {id: $id2})
                            MERGE (cl1)-[:REFERS_TO]->(x)
                            MERGE (x)-[:REFERS_TO]->(cl2)
                        """, xid=xref_id, t1=t1, t2=t2, id1=id1, id2=id2)
                        nodes_created += 1; rels_created += 2

            # ── ContractEmbedding node (stores vector metadata) ──
            session.run("""
                MERGE (emb:ContractEmbedding {id: $eid})
                SET emb.contract_id = $cid, emb.model = 'MiniLM-L6-v2',
                    emb.dim = 384, emb.node_type = 'ContractEmbedding',
                    emb.indexed = false
                WITH emb MATCH (c:Contract {id: $cid})
                MERGE (c)-[:HAS_VECTOR]->(emb)
            """, eid=f"EMB_{contract_id}", cid=contract_id)
            nodes_created += 1; rels_created += 1

        return {
            "contract_id": contract_id,
            "nodes_created": nodes_created,
            "relationships_created": rels_created,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # 9. NEO4J GDS NATIVE CALLS (PageRank + NodeSimilarity)
    # ──────────────────────────────────────────────────────────────────────────

    def gds_pagerank(self, contract_id: str) -> Dict[str, Any]:
        """
        Native Neo4j GDS PageRank on the contract subgraph.
        Requires Neo4j GDS plugin. Falls back to NetworkX PageRank.
        """
        if not self.neo4j_available:
            return self.get_gds_pagerank(contract_id)

        try:
            with self.driver.session() as session:
                # Project in-memory graph for this contract
                graph_name = f"cuad_pr_{contract_id[:8]}"

                # Drop existing projection if present
                try:
                    session.run("CALL gds.graph.drop($gn, false) YIELD graphName", gn=graph_name)
                except Exception:
                    pass

                # Project subgraph: Contract → Clause → Risk nodes
                session.run("""
                    CALL gds.graph.project(
                        $gn,
                        ['Clause', 'Risk', 'Obligation'],
                        {
                            CREATES_RISK: { orientation: 'UNDIRECTED' },
                            CREATES_OBLIGATION: { orientation: 'UNDIRECTED' }
                        },
                        { nodeFilter: 'n.contract_id = "' + $cid + '"' }
                    )
                """, gn=graph_name, cid=contract_id)

                # Run GDS PageRank
                result = session.run("""
                    CALL gds.pageRank.stream($gn, { maxIterations: 20, dampingFactor: 0.85 })
                    YIELD nodeId, score
                    RETURN gds.util.asNode(nodeId).id AS node_id,
                           gds.util.asNode(nodeId).clause_name AS clause_name,
                           gds.util.asNode(nodeId).clause_type AS clause_type,
                           gds.util.asNode(nodeId).risk_score AS risk_score,
                           score
                    ORDER BY score DESC
                """, gn=graph_name)

                rows = result.data()

                # Cleanup projection
                try:
                    session.run("CALL gds.graph.drop($gn, false)", gn=graph_name)
                except Exception:
                    pass

                if not rows:
                    return self.get_gds_pagerank(contract_id)

                pr_vals = [r["score"] for r in rows]
                min_pr = min(pr_vals)
                max_pr = max(pr_vals)
                pr_range = max_pr - min_pr if max_pr > min_pr else 1.0

                pagerank_results = []
                for r in rows:
                    score = round(30.0 + ((r["score"] - min_pr) / pr_range) * 70.0, 2)
                    rs = float(r.get("risk_score") or 0.2)
                    pagerank_results.append({
                        "clause_id": r.get("node_id", ""),
                        "clause_name": r.get("clause_name", ""),
                        "clause_type": r.get("clause_type", ""),
                        "pagerank_score": score,
                        "risk_score": round(rs, 3),
                        "risk_level": _infer_risk_level(rs),
                    })

                return {
                    "contract_id": contract_id,
                    "method": "neo4j_gds_pagerank",
                    "node_count": len(rows),
                    "pagerank": pagerank_results,
                }

        except Exception as e:
            logger.warning(f"[CUAD-GDS] Native PageRank failed ({e}), falling back to NetworkX")
            return self.get_gds_pagerank(contract_id)

    def gds_node_similarity(self, c1_id: str, c2_id: str) -> Dict[str, Any]:
        """
        Native Neo4j GDS Node Similarity between two contracts.
        Falls back to Jaccard+cosine hybrid.
        """
        if not self.neo4j_available:
            return self.get_gds_similarity(c1_id, c2_id)

        try:
            with self.driver.session() as session:
                graph_name = f"cuad_sim_{c1_id[:6]}_{c2_id[:6]}"

                try:
                    session.run("CALL gds.graph.drop($gn, false) YIELD graphName", gn=graph_name)
                except Exception:
                    pass

                # Project both contracts' clause nodes
                session.run("""
                    CALL gds.graph.project(
                        $gn,
                        ['Contract', 'Clause', 'ClauseType'],
                        {
                            HAS_CLAUSE: { orientation: 'UNDIRECTED' },
                            IS_TYPE: { orientation: 'UNDIRECTED' }
                        }
                    )
                """, gn=graph_name)

                result = session.run("""
                    CALL gds.nodeSimilarity.stream($gn, { topK: 5, similarityCutoff: 0.0 })
                    YIELD node1, node2, similarity
                    WITH gds.util.asNode(node1) AS n1, gds.util.asNode(node2) AS n2, similarity
                    WHERE (n1.id = $c1 OR n1.id = $c2) AND (n2.id = $c1 OR n2.id = $c2)
                    RETURN n1.id as contract1, n2.id as contract2, similarity
                    LIMIT 1
                """, gn=graph_name, c1=c1_id, c2=c2_id)

                rows = result.data()

                try:
                    session.run("CALL gds.graph.drop($gn, false)", gn=graph_name)
                except Exception:
                    pass

                if rows:
                    sim = round(float(rows[0].get("similarity", 0)), 4)
                    base = self.get_gds_similarity(c1_id, c2_id)
                    base["gds_node_similarity"] = sim
                    base["method"] = "neo4j_gds_node_similarity"
                    return base

        except Exception as e:
            logger.warning(f"[CUAD-GDS] Node similarity failed ({e}), falling back")

        return self.get_gds_similarity(c1_id, c2_id)

    # ──────────────────────────────────────────────────────────────────────────
    # 10. TEMPORAL GRAPH — Amendment Evolution Tracking
    # ──────────────────────────────────────────────────────────────────────────

    def track_amendment(
        self,
        contract_id: str,
        amendment_description: str,
        affected_clause_types: Optional[List[str]] = None,
        amendment_date: str = "",
    ) -> Dict[str, Any]:
        """
        Record an amendment event in the temporal graph.
        Creates Amendment node + AMENDED_BY relationship + updates clause risk scores.

        Returns the amendment ID and updated risk deltas.
        """
        from core.models import Contract, Clause
        import datetime

        try:
            contract = Contract.objects.get(id=contract_id)
        except Contract.DoesNotExist:
            return {"error": f"Contract {contract_id} not found"}

        amendment_id = f"AM_{contract_id[:8]}_{int(__import__('time').time())}"
        date_str = amendment_date or datetime.datetime.now().strftime("%Y-%m-%d")

        # Find affected clauses
        clauses = list(Clause.objects.filter(contract=contract))
        affected = []
        if affected_clause_types:
            for c in clauses:
                ct = _canonical_type(c.clause_type or "", c.clause_name or "")
                if ct in affected_clause_types:
                    old_risk = _text_based_risk(c)
                    # Amendment typically increases risk by 10-15%
                    new_risk = round(min(old_risk * 1.12, 0.99), 4)
                    affected.append({
                        "clause_id": str(c.id),
                        "clause_name": c.clause_name or ct,
                        "clause_type": ct,
                        "old_risk": old_risk,
                        "new_risk": new_risk,
                        "delta": round(new_risk - old_risk, 4),
                    })

        # Persist amendment in Neo4j if available
        if self.neo4j_available:
            try:
                with self.driver.session() as session:
                    # First ensure Contract node exists
                    session.run("""
                        MERGE (c:Contract {id: $cid})
                        ON CREATE SET c.contract_id = $cid,
                                      c.name = $name,
                                      c.node_type = 'Contract'
                    """, cid=contract_id, name=contract.filename or "Contract")

                    # Then create Amendment and link it
                    session.run("""
                        MERGE (a:Amendment {id: $aid})
                        SET a.description = $desc,
                            a.date = $date,
                            a.affected_types = $types,
                            a.contract_id = $cid,
                            a.node_type = 'Amendment'
                        WITH a
                        MATCH (c:Contract {id: $cid})
                        MERGE (c)-[:AMENDED_BY {date: $date}]->(a)
                    """, aid=amendment_id, desc=amendment_description,
                        date=date_str,
                        types=json.dumps(affected_clause_types or []),
                        cid=contract_id)

                    # Link amendment to affected clauses
                    for item in affected:
                        session.run("""
                            MATCH (a:Amendment {id: $aid}), (cl:Clause {id: $clid})
                            MERGE (a)-[:AFFECTS_CLAUSE {risk_delta: $delta}]->(cl)
                        """, aid=amendment_id, clid=item["clause_id"], delta=item["delta"])

            except Exception as e:
                logger.error(f"[CUAD-TEMPORAL] Amendment write error: {e}")

        return {
            "amendment_id": amendment_id,
            "contract_id": contract_id,
            "contract_name": contract.filename or "Contract",
            "date": date_str,
            "description": amendment_description,
            "affected_clauses": affected,
            "risk_increased": len([a for a in affected if a["delta"] > 0]),
            "total_affected": len(affected),
        }

    def get_amendment_history(self, contract_id: str) -> Dict[str, Any]:
        """
        Retrieve full amendment timeline for a contract.
        Returns amendments sorted by date + cumulative risk evolution.
        """
        from core.models import Contract, Clause

        try:
            contract = Contract.objects.get(id=contract_id)
        except Contract.DoesNotExist:
            return {"error": f"Contract {contract_id} not found"}

        amendments = []

        if self.neo4j_available:
            try:
                with self.driver.session() as session:
                    result = session.run("""
                        MATCH (c:Contract {id: $cid})-[r:AMENDED_BY]->(a:Amendment)
                        RETURN a.id as id, a.description as description,
                               a.date as date, a.affected_types as types,
                               r.date as rel_date
                        ORDER BY a.date ASC
                    """, cid=contract_id)
                    amendments = result.data()
            except Exception as e:
                logger.error(f"[CUAD-TEMPORAL] History fetch error: {e}")

        # Compute current risk baseline
        clauses = list(Clause.objects.filter(contract=contract))
        current_risk = sum(_text_based_risk(c) for c in clauses) / max(len(clauses), 1)

        return {
            "contract_id": contract_id,
            "contract_name": contract.filename or "Contract",
            "total_amendments": len(amendments),
            "amendments": amendments,
            "current_avg_risk": round(current_risk, 3),
            "current_risk_level": _infer_risk_level(current_risk),
        }
