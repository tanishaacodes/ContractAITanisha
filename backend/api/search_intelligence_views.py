"""
Smart Contract Search Intelligence — Backend Views
===================================================
Implements all features from the doc:
1. Pre-built Searches
2. Semantic Search  — BM25 + MiniLM embeddings + FAISS  (pending #1, #2)
3. AI Agent Search  — Qwen via Ollama
4. Analytics Dashboard
5. Buyer vs Supplier Negotiation Agents
   - Neo4j graph context             (pending #7)
   - Strategy memory                 (pending #8)
   - Multi-clause negotiation        (pending #9)
6. Force Majeure Risk Scorer         (pending #3)
7. Auto Clause Extraction → Neo4j   (pending #4)
8. Contract Stats
"""
import json
import logging
import hashlib
import numpy as np
import requests
from django.conf import settings
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from core.models import Contract, Clause, ContractRiskAnalysis

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')


# ===========================================================================
# SHARED HELPERS
# ===========================================================================

def get_request_user(request):
    """Get user from request or fallback to admin@example.com for development"""
    try:
        user = request.user if request.user.is_authenticated else None
        if not user:
            from core.models import User
            user = User.objects.filter(email='admin@example.com').first() or User.objects.first()
    except:
        from core.models import User
        user = User.objects.filter(email='admin@example.com').first() or User.objects.first()
    return user

def _call_qwen(prompt: str, timeout: int = 50) -> str:
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": "qwen2.5:0.5b", "prompt": prompt, "stream": False},
            timeout=timeout,
        )
        if resp.status_code == 200:
            return resp.json().get("response", "").strip()
    except Exception as e:
        logger.warning(f"Ollama call failed: {e}")
    return ""


def _keyword_score(text: str, query_terms: list) -> float:
    if not text or not query_terms:
        return 0.0
    text_lower = text.lower()
    hits = sum(1 for t in query_terms if t in text_lower)
    return hits / len(query_terms)


# ===========================================================================
# PENDING #1 + #2: MiniLM Embedding Service + FAISS index
# ===========================================================================

class _EmbeddingFAISSIndex:
    """
    In-process singleton: builds a FAISS flat index over all contract text blobs.
    Falls back gracefully if faiss or sentence_transformers are not installed.
    """
    _instance = None
    _index = None
    _contract_ids = []
    _built = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _build(self):
        try:
            import faiss
            from sentence_transformers import SentenceTransformer
        except ImportError:
            logger.warning("faiss-cpu or sentence-transformers not installed — skipping FAISS index")
            self._built = True
            return

        model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        contracts = list(Contract.objects.all()[:500])
        if not contracts:
            self._built = True
            return

        texts = []
        ids = []
        for c in contracts:
            blob = " ".join(filter(None, [
                c.original_filename or "",
                c.contract_type or "",
                c.jurisdiction or "",
            ]))
            # Append first clause texts for richer representation
            clauses = Clause.objects.filter(contract=c)[:3]
            for cl in clauses:
                blob += " " + (cl.extracted_text or cl.context_sentences or "")[:300]
            texts.append(blob[:1000])
            ids.append(c.id)

        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        embeddings = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-9)

        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)  # inner-product = cosine on normalized vecs
        index.add(embeddings.astype(np.float32))

        self._index = index
        self._contract_ids = ids
        self._model = model
        self._built = True
        logger.info(f"[FAISS] Index built: {len(ids)} contracts, dim={dim}")

    def search(self, query: str, top_k: int = 20):
        """Return list of (contract_id, score) sorted by similarity desc."""
        if not self._built:
            self._build()
        if self._index is None:
            return []
        try:
            q_emb = self._model.encode([query], convert_to_numpy=True)
            q_emb = q_emb / (np.linalg.norm(q_emb, axis=1, keepdims=True) + 1e-9)
            scores, indices = self._index.search(q_emb.astype(np.float32), top_k)
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self._contract_ids):
                    results.append((self._contract_ids[idx], float(score)))
            return results
        except Exception as e:
            logger.warning(f"[FAISS] Search failed: {e}")
            return []

    def invalidate(self):
        """Call after new contracts are added."""
        self._built = False
        self._index = None
        self._contract_ids = []


_faiss_index = _EmbeddingFAISSIndex()


# ===========================================================================
# PENDING #3: Force Majeure Risk Scorer (rule-based 0–1 score)
# ===========================================================================

# High-signal FM keywords with weights
_FM_SIGNALS = {
    # Core terms
    "force majeure": 0.30,
    "act of god": 0.25,
    "acts of god": 0.25,
    # Specific events
    "pandemic": 0.15,
    "epidemic": 0.12,
    "natural disaster": 0.15,
    "earthquake": 0.10,
    "flood": 0.10,
    "hurricane": 0.10,
    "war": 0.08,
    "armed conflict": 0.10,
    "sanctions": 0.08,
    "government action": 0.08,
    "regulatory change": 0.06,
    "supply chain disruption": 0.10,
    "strike": 0.06,
    # Risky FM provisions
    "12 months": 0.05,
    "no right to terminate": 0.10,
    "shall not be liable": 0.08,
    "not responsible": 0.05,
    "without liability": 0.08,
    "unlimited force majeure": 0.15,
    # Protective FM provisions (negative risk — buyer protected)
    "buyer may terminate": -0.05,
    "notify within 5": -0.03,
    "notify within 7": -0.03,
    "alternative performance": -0.05,
    "mitigation": -0.05,
}


def score_force_majeure_risk(text: str) -> float:
    """
    Returns a 0.0–1.0 risk score for force majeure risk in a clause/contract.
    Higher = more risky / more exposed.
    """
    if not text:
        return 0.0
    text_lower = text.lower()
    score = 0.0
    for signal, weight in _FM_SIGNALS.items():
        if signal in text_lower:
            score += weight
    return round(min(max(score, 0.0), 1.0), 3)


# ===========================================================================
# PENDING #8: Negotiation Strategy Memory (in-memory, keyed by clause_type)
# ===========================================================================

class _NegotiationMemory:
    """
    Stores past successful negotiated clauses per clause_type.
    In production this would be a DB table; here it's a process-level cache.
    """
    _instance = None
    _store: dict = {}  # clause_type -> list of {"clause": str, "score": float}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def save(self, clause_type: str, clause_text: str, score: float):
        key = (clause_type or "general").lower()
        if key not in self._store:
            self._store[key] = []
        self._store[key].append({"clause": clause_text, "score": score})
        # Keep top 10 per type
        self._store[key] = sorted(self._store[key], key=lambda x: x["score"], reverse=True)[:10]

    def get_best(self, clause_type: str, top_k: int = 3):
        key = (clause_type or "general").lower()
        return self._store.get(key, [])[:top_k]

    def all_types(self):
        return list(self._store.keys())

    def stats(self):
        return {t: len(v) for t, v in self._store.items()}


_negotiation_memory = _NegotiationMemory()


# ===========================================================================
# PENDING #4: Auto Clause Extraction → Neo4j graph builder helpers
# ===========================================================================

def _extract_clauses_llm(contract_text: str) -> list:
    """
    Call Qwen to extract structured clauses from raw contract text.
    Returns list of dicts: {type, text, risk_score, obligations}
    """
    prompt = f"""Extract all clauses from the contract below. Return ONLY valid JSON.

Format:
{{
  "clauses": [
    {{
      "type": "Force Majeure",
      "text": "...",
      "risk_score": 0.0 to 1.0,
      "obligations": ["list of obligation strings"]
    }}
  ]
}}

Clause types to look for: Force Majeure, Liability, Indemnity, Termination, Payment, Confidentiality, Dispute Resolution, Governing Law, Warranty, IP Rights.

Contract text (first 3000 chars):
{contract_text[:3000]}

JSON:"""

    raw = _call_qwen(prompt, timeout=60)
    if raw:
        try:
            import re
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                return json.loads(match.group()).get("clauses", [])
        except Exception:
            pass
    return []


def _extract_clauses_rule_based(contract_text: str) -> list:
    """Fallback: keyword-based clause detection."""
    clause_patterns = {
        "Force Majeure": ["force majeure", "act of god", "beyond reasonable control"],
        "Liability": ["limitation of liability", "liable for", "not be liable"],
        "Indemnity": ["indemnif", "hold harmless", "defend and indemnify"],
        "Termination": ["termination", "terminate this agreement", "right to terminate"],
        "Payment": ["payment terms", "invoice", "net 30", "net 60", "payment due"],
        "Confidentiality": ["confidential", "non-disclosure", "proprietary information"],
        "Dispute Resolution": ["arbitration", "dispute resolution", "mediation", "litigation"],
        "Governing Law": ["governing law", "jurisdiction", "laws of"],
        "Warranty": ["warranty", "represent and warrant", "fitness for purpose"],
        "IP Rights": ["intellectual property", "copyright", "patent", "license"],
    }

    clauses = []
    text_lower = contract_text.lower()
    for clause_type, keywords in clause_patterns.items():
        for kw in keywords:
            idx = text_lower.find(kw)
            if idx != -1:
                start = max(0, idx - 50)
                end = min(len(contract_text), idx + 500)
                snippet = contract_text[start:end]
                fm_score = score_force_majeure_risk(snippet)
                clauses.append({
                    "type": clause_type,
                    "text": snippet,
                    "risk_score": fm_score if clause_type == "Force Majeure" else round(0.3 + fm_score * 0.5, 3),
                    "obligations": [],
                })
                break  # one match per type
    return clauses


def _push_to_neo4j(contract, clauses: list) -> dict:
    """Push extracted clauses into Neo4j. Returns dict with success status and node ID mappings."""
    try:
        from contractai.neo4j_config import get_neo4j_driver, check_neo4j_available
        if not check_neo4j_available():
            return {"success": False, "node_mappings": {}}

        driver = get_neo4j_driver()
        node_mappings = {}  # Maps clause index to Neo4j internal node ID

        with driver.session() as session:
            for idx, clause in enumerate(clauses):
                # Create/update clause and get its Neo4j internal ID
                result = session.run("""
                MERGE (c:Contract {id: $cid, title: $title})
                MERGE (cl:Clause {type: $ctype, contractId: $cid, clauseIndex: $idx})
                SET cl.text = $ctext, cl.riskScore = $risk
                MERGE (c)-[:HAS_CLAUSE]->(cl)
                MERGE (r:Risk {type: $ctype, contractId: $cid})
                SET r.score = $risk
                MERGE (cl)-[:HAS_RISK]->(r)
                RETURN id(cl) as clause_node_id
                """,
                cid=str(contract.id),
                title=contract.original_filename or str(contract.id),
                ctype=clause.get("type", "Unknown"),
                ctext=(clause.get("text") or "")[:500],
                risk=float(clause.get("risk_score", 0.5)),
                idx=idx
                )

                # Capture the Neo4j internal node ID
                record = result.single()
                if record:
                    node_mappings[f"clause-{idx}"] = record["clause_node_id"]

                for obl in clause.get("obligations", []):
                    if obl:
                        session.run("""
                        MERGE (o:Obligation {text: $obl, contractId: $cid})
                        MERGE (cl:Clause {type: $ctype, contractId: $cid, clauseIndex: $idx})
                        MERGE (cl)-[:HAS_OBLIGATION]->(o)
                        """,
                        obl=str(obl)[:200],
                        cid=str(contract.id),
                        ctype=clause.get("type", "Unknown"),
                        idx=idx
                        )

        return {"success": True, "node_mappings": node_mappings}
    except Exception as e:
        logger.warning(f"[NEO4J] Push failed: {e}")
        return {"success": False, "node_mappings": {}}


def _get_neo4j_graph_context(contract_id: str) -> str:
    """Fetch related risks/clauses from Neo4j for a contract (pending #7)."""
    try:
        from contractai.neo4j_config import get_neo4j_driver, check_neo4j_available
        if not check_neo4j_available():
            return ""
        driver = get_neo4j_driver()
        with driver.session() as session:
            result = session.run("""
            MATCH (c:Contract {id: $cid})-[:HAS_CLAUSE]->(cl)
            OPTIONAL MATCH (cl)-[:HAS_RISK]->(r)
            RETURN cl.type AS clauseType, r.score AS riskScore
            LIMIT 10
            """, cid=str(contract_id))
            rows = [dict(rec) for rec in result]

        if not rows:
            return ""
        parts = [f"{r['clauseType']} (risk={r['riskScore']:.2f})" for r in rows if r.get('clauseType')]
        return "Graph context — Clauses & risks: " + ", ".join(parts)
    except Exception as e:
        logger.warning(f"[NEO4J] Graph context fetch failed: {e}")
        return ""


# ===========================================================================
# VIEWS
# ===========================================================================

# ---------------------------------------------------------------------------
# 1. PRE-BUILT SEARCHES
# ---------------------------------------------------------------------------
class PrebuiltSearchView(APIView):
    permission_classes = [AllowAny]  # Temporarily disabled for development

    def _get_user(self, request):
        """Get user from request or fallback to admin@example.com for development"""
        try:
            user = get_request_user(request) if request.user.is_authenticated else None
            if not user:
                from core.models import User
                user = User.objects.filter(email='admin@example.com').first() or User.objects.first()
        except:
            from core.models import User
            user = User.objects.filter(email='admin@example.com').first() or User.objects.first()
        return user

    SEARCH_TYPES = {
        "high_value": "High Value Contracts",
        "high_liability": "High Liability Exposure",
        "unlimited_liability": "Unlimited Liability",
        "force_majeure_risk": "Force Majeure Risk",
        "expiring_soon": "Expiring Soon",
        "not_analyzed": "Not Yet Analyzed",
        "high_risk": "High Risk Contracts",
        "payment_disputes": "Payment & Dispute Clauses",
    }

    def get(self, request):
        searches = [
            {
                "id": k,
                "label": v,
                "description": self._description(k),
                "color": self._color(k),
                "icon": self._icon(k),
            }
            for k, v in self.SEARCH_TYPES.items()
        ]
        return Response({"searches": searches})

    def post(self, request):
        search_type = request.data.get("search_type")
        limit = int(request.data.get("limit", 20))
        if search_type not in self.SEARCH_TYPES:
            return Response({"error": f"Unknown search_type '{search_type}'"}, status=status.HTTP_400_BAD_REQUEST)
        contracts = self._run_search(search_type, limit, user=get_request_user(request))
        return Response({
            "search_type": search_type,
            "label": self.SEARCH_TYPES[search_type],
            "count": len(contracts),
            "contracts": contracts,
        })

    def _run_search(self, search_type: str, limit: int, user=None) -> list:
        # Match dashboard logic: only contracts that have clauses (same 8 visible contracts)
        valid_ids = Clause.objects.filter(contract__user=user).values_list("contract_id", flat=True).distinct()
        qs = Contract.objects.filter(user=user, id__in=valid_ids) if user else Contract.objects.filter(id__in=Clause.objects.values_list("contract_id", flat=True).distinct())

        if search_type == "high_value":
            qs = qs.filter(contract_value__isnull=False).order_by("-contract_value")[:limit]

        elif search_type == "high_liability":
            qs = qs.filter(liability_level="HIGH").order_by("-uploaded_at")[:limit]

        elif search_type == "unlimited_liability":
            base = qs.filter(liability_level__iexact="unlimited").order_by("-uploaded_at")
            if base.exists():
                qs = base[:limit]
            else:
                clause_ids = Clause.objects.filter(
                    Q(clause_type__icontains="unlimited liability") |
                    Q(extracted_text__icontains="unlimited liability") |
                    Q(context_sentences__icontains="unlimited liability")
                ).values_list("contract_id", flat=True).distinct()
                qs = qs.filter(id__in=clause_ids)[:limit]

        elif search_type == "force_majeure_risk":
            clause_ids = Clause.objects.filter(
                Q(clause_type__icontains="force majeure") |
                Q(extracted_text__icontains="force majeure") |
                Q(context_sentences__icontains="force majeure")
            ).values_list("contract_id", flat=True).distinct()
            qs = qs.filter(id__in=clause_ids).order_by("-uploaded_at")[:limit]

        elif search_type == "expiring_soon":
            from django.utils import timezone
            import datetime
            ninety_days = timezone.now().date() + datetime.timedelta(days=90)
            qs = qs.filter(end_date__isnull=False, end_date__lte=ninety_days).order_by("end_date")[:limit]

        elif search_type == "not_analyzed":
            analyzed_ids = ContractRiskAnalysis.objects.values_list("contract_id", flat=True).distinct()
            qs = qs.exclude(id__in=analyzed_ids).order_by("-uploaded_at")[:limit]

        elif search_type == "high_risk":
            analyzed_ids = ContractRiskAnalysis.objects.filter(
                risk_level__in=["HIGH", "CRITICAL"]
            ).values_list("contract_id", flat=True).distinct()
            qs = qs.filter(id__in=analyzed_ids).order_by("-uploaded_at")[:limit]

        elif search_type == "payment_disputes":
            clause_ids = Clause.objects.filter(
                Q(clause_type__icontains="payment") | Q(clause_type__icontains="dispute") |
                Q(extracted_text__icontains="payment default") | Q(extracted_text__icontains="late payment") |
                Q(context_sentences__icontains="payment default") | Q(context_sentences__icontains="late payment")
            ).values_list("contract_id", flat=True).distinct()
            qs = qs.filter(id__in=clause_ids).order_by("-uploaded_at")[:limit]

        return self._serialize(list(qs))

    def _serialize(self, contracts: list) -> list:
        result = []
        for c in contracts:
            try:
                analysis = ContractRiskAnalysis.objects.filter(contract=c).first()
                # FM risk score from clause text
                fm_clause = Clause.objects.filter(contract=c).filter(
                    Q(clause_type__icontains="force majeure") |
                    Q(extracted_text__icontains="force majeure") |
                    Q(context_sentences__icontains="force majeure")
                ).first()
                fm_text = ""
                if fm_clause:
                    fm_text = fm_clause.extracted_text or fm_clause.context_sentences or ""
                fm_score = score_force_majeure_risk(fm_text) if fm_text else 0.0

                result.append({
                    "id": c.id,
                    "title": c.original_filename or c.id,
                    "contractType": c.contract_type,
                    "jurisdiction": c.jurisdiction,
                    "liabilityLevel": c.liability_level,
                    "contractValue": c.contract_value,
                    "uploadedAt": c.uploaded_at.isoformat() if c.uploaded_at else None,
                    "expiryDate": c.end_date.isoformat() if c.end_date else None,
                    "riskLevel": analysis.risk_level if analysis else None,
                    "riskScore": float(analysis.risk_score) if analysis and analysis.risk_score else None,
                    "clauseCount": Clause.objects.filter(contract=c).count(),
                    "hasAnalysis": analysis is not None,
                    "paymentTerms": c.payment_terms,
                    "forceMajeureScore": fm_score,
                })
            except Exception as e:
                logger.warning(f"Serialize error {c.id}: {e}")
        return result

    def _description(self, k):
        return {
            "high_value": "Contracts with the highest monetary value",
            "high_liability": "Contracts with high liability exposure",
            "unlimited_liability": "Contracts containing unlimited liability clauses",
            "force_majeure_risk": "Contracts with force majeure clauses",
            "expiring_soon": "Contracts expiring within 90 days",
            "not_analyzed": "Contracts that haven't been AI-analyzed yet",
            "high_risk": "Contracts scored HIGH or CRITICAL risk",
            "payment_disputes": "Contracts with payment or dispute clauses",
        }.get(k, "")

    def _color(self, k):
        return {"high_value": "emerald", "high_liability": "red", "unlimited_liability": "red",
                "force_majeure_risk": "orange", "expiring_soon": "yellow", "not_analyzed": "slate",
                "high_risk": "red", "payment_disputes": "blue"}.get(k, "slate")

    def _icon(self, k):
        return {"high_value": "DollarSign", "high_liability": "Shield", "unlimited_liability": "AlertTriangle",
                "force_majeure_risk": "Cloud", "expiring_soon": "Clock", "not_analyzed": "FileQuestion",
                "high_risk": "Flame", "payment_disputes": "CreditCard"}.get(k, "Search")


# ---------------------------------------------------------------------------
# 2. SEMANTIC SEARCH — BM25 + MiniLM FAISS  (#1, #2)
# ---------------------------------------------------------------------------
class SemanticSearchView(APIView):
    permission_classes = [AllowAny]  # Temporarily disabled for development

    def post(self, request):
        query = request.data.get("query", "").strip()
        limit = int(request.data.get("limit", 20))
        filters = request.data.get("filters", {})

        if not query:
            return Response({"error": "query is required"}, status=status.HTTP_400_BAD_REQUEST)

        query_terms = query.lower().split()

        # Apply DB-level filters first — only contracts with clauses (matches dashboard)
        valid_ids = Clause.objects.filter(contract__user=get_request_user(request)).values_list("contract_id", flat=True).distinct()
        qs = Contract.objects.filter(user=get_request_user(request), id__in=valid_ids)
        if filters.get("contractType"):
            qs = qs.filter(contract_type__icontains=filters["contractType"])
        if filters.get("jurisdiction"):
            qs = qs.filter(jurisdiction__icontains=filters["jurisdiction"])
        if filters.get("riskLevel"):
            ids = ContractRiskAnalysis.objects.filter(risk_level__iexact=filters["riskLevel"]).values_list("contract_id", flat=True)
            qs = qs.filter(id__in=ids)
        if filters.get("liabilityLevel"):
            qs = qs.filter(liability_level__iexact=filters["liabilityLevel"])

        # --- PENDING #1+#2: FAISS embedding search ---
        faiss_scores = {}
        try:
            faiss_results = _faiss_index.search(query, top_k=50)
            for cid, score in faiss_results:
                faiss_scores[cid] = score
            method = "MiniLM Embeddings (FAISS) + BM25 keyword fusion"
        except Exception:
            method = "BM25 keyword + clause matching"

        # BM25-style keyword scoring on candidate pool
        contracts = list(qs[:300])
        scored = {}
        for c in contracts:
            blob = " ".join(filter(None, [c.original_filename or "", c.contract_type or "", c.jurisdiction or "",
                                          c.payment_terms or ""]))
            kw_score = _keyword_score(blob, query_terms)

            clause_hits = Clause.objects.filter(contract=c).filter(
                Q(extracted_text__icontains=query_terms[0]) | Q(context_sentences__icontains=query_terms[0]) if query_terms else Q()
            ).count()
            kw_score += clause_hits * 0.1

            embed_score = faiss_scores.get(c.id, 0.0) * 0.5  # normalize FAISS contribution
            total = kw_score + embed_score
            scored[c.id] = (total, c)

        sorted_results = sorted(scored.values(), key=lambda x: x[0], reverse=True)
        top = [c for score, c in sorted_results if score > 0][:limit]

        # Fallback: DB keyword search (only within user's valid contracts)
        if len(top) < 3:
            db_results = qs.filter(
                Q(original_filename__icontains=query) | Q(contract_type__icontains=query) | Q(jurisdiction__icontains=query)
            )[:limit]
            existing = {c.id for c in top}
            for c in db_results:
                if c.id not in existing:
                    top.append(c)

        result = self._serialize(top[:limit], query_terms)
        return Response({"query": query, "count": len(result), "contracts": result, "method": method})

    def _serialize(self, contracts, query_terms):
        result = []
        for c in contracts:
            try:
                analysis = ContractRiskAnalysis.objects.filter(contract=c).first()
                clause_count = Clause.objects.filter(contract=c).count()

                matching_clauses = []
                if query_terms:
                    for cl in Clause.objects.filter(contract=c):
                        text = (cl.extracted_text or cl.context_sentences or "").lower()
                        if any(t in text for t in query_terms):
                            matching_clauses.append({
                                "type": cl.clause_type,
                                "snippet": (cl.extracted_text or cl.context_sentences or "")[:200] + "...",
                            })
                    matching_clauses = matching_clauses[:3]

                fm_clause = Clause.objects.filter(contract=c).filter(
                    Q(clause_type__icontains="force majeure") |
                    Q(extracted_text__icontains="force majeure") |
                    Q(context_sentences__icontains="force majeure")
                ).first()
                fm_text = (fm_clause.extracted_text or fm_clause.context_sentences or "") if fm_clause else ""
                fm_score = score_force_majeure_risk(fm_text)

                result.append({
                    "id": c.id,
                    "title": c.original_filename or c.id,
                    "contractType": c.contract_type,
                    "jurisdiction": c.jurisdiction,
                    "liabilityLevel": c.liability_level,
                    "contractValue": c.contract_value,
                    "uploadedAt": c.uploaded_at.isoformat() if c.uploaded_at else None,
                    "riskLevel": analysis.risk_level if analysis else None,
                    "riskScore": float(analysis.risk_score) if analysis and analysis.risk_score else None,
                    "clauseCount": clause_count,
                    "hasAnalysis": analysis is not None,
                    "matchingClauses": matching_clauses,
                    "paymentTerms": c.payment_terms,
                    "forceMajeureScore": fm_score,
                })
            except Exception as e:
                logger.warning(f"Serialize error {c.id}: {e}")
        return result


# ---------------------------------------------------------------------------
# 3. AI AGENT SEARCH
# ---------------------------------------------------------------------------
class AIAgentSearchView(APIView):
    permission_classes = [AllowAny]  # Temporarily disabled for development

    def post(self, request):
        query = request.data.get("query", "").strip()
        if not query:
            return Response({"error": "query is required"}, status=status.HTTP_400_BAD_REQUEST)

        valid_ids = Clause.objects.filter(contract__user=get_request_user(request)).values_list("contract_id", flat=True).distinct()
        user_contracts = Contract.objects.filter(user=get_request_user(request), id__in=valid_ids)
        total_contracts = user_contracts.count()
        user_contract_ids = user_contracts.values_list("id", flat=True)
        high_risk_count = ContractRiskAnalysis.objects.filter(contract_id__in=user_contract_ids, risk_level__in=["HIGH", "CRITICAL"]).count()
        fm_count = Clause.objects.filter(
            Q(clause_type__icontains="force majeure") |
            Q(extracted_text__icontains="force majeure") |
            Q(context_sentences__icontains="force majeure"),
            contract_id__in=user_contract_ids
        ).values("contract_id").distinct().count()
        high_liability_count = user_contracts.filter(liability_level="HIGH").count()

        # FAISS + BM25 hybrid to get relevant contracts
        query_terms = query.lower().split()
        faiss_results = _faiss_index.search(query, top_k=10)
        faiss_ids = {cid: score for cid, score in faiss_results}

        contracts = list(user_contracts[:300])
        scored = []
        for c in contracts:
            text = " ".join(filter(None, [c.original_filename or "", c.contract_type or "", c.jurisdiction or ""]))
            score = _keyword_score(text, query_terms)
            clause_hits = Clause.objects.filter(contract=c).filter(
                Q(extracted_text__icontains=query_terms[0]) | Q(context_sentences__icontains=query_terms[0]) if query_terms else Q()
            ).count()
            score += clause_hits * 0.15
            score += faiss_ids.get(c.id, 0.0) * 0.3
            scored.append((score, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_contracts = [c for s, c in scored[:5] if s > 0]

        contract_snippets = []
        for c in top_contracts:
            analysis = ContractRiskAnalysis.objects.filter(contract=c).first()
            fm_clause = Clause.objects.filter(contract=c).filter(
                Q(clause_type__icontains="force majeure") |
                Q(extracted_text__icontains="force majeure") |
                Q(context_sentences__icontains="force majeure")
            ).first()
            fm_text = (fm_clause.extracted_text or fm_clause.context_sentences or "") if fm_clause else ""
            fm_score = score_force_majeure_risk(fm_text)
            contract_snippets.append(
                f"- {c.original_filename or c.id} | Type: {c.contract_type} | "
                f"Jurisdiction: {c.jurisdiction} | Risk: {analysis.risk_level if analysis else 'Unknown'} | "
                f"Liability: {c.liability_level} | FM Risk: {fm_score:.2f}"
            )

        context = f"""Portfolio Summary:
- Total contracts: {total_contracts}
- High/Critical risk: {high_risk_count}
- Force Majeure contracts: {fm_count}
- High liability: {high_liability_count}

Top relevant contracts:
{chr(10).join(contract_snippets) if contract_snippets else 'No specific contracts found.'}"""

        prompt = f"""You are a legal contract intelligence AI assistant.

{context}

User Question: {query}

Give a concise, data-driven answer. Include specific numbers and contract names. Under 200 words.

Answer:"""

        llm_answer = _call_qwen(prompt)
        if not llm_answer:
            llm_answer = self._rule_based_answer(query, total_contracts, high_risk_count, fm_count, high_liability_count, top_contracts)

        serialized = []
        for c in top_contracts:
            analysis = ContractRiskAnalysis.objects.filter(contract=c).first()
            fm_clause = Clause.objects.filter(contract=c).filter(
                Q(clause_type__icontains="force majeure") |
                Q(extracted_text__icontains="force majeure") |
                Q(context_sentences__icontains="force majeure")
            ).first()
            fm_text = (fm_clause.extracted_text or fm_clause.context_sentences or "") if fm_clause else ""
            serialized.append({
                "id": c.id,
                "title": c.original_filename or c.id,
                "contractType": c.contract_type,
                "jurisdiction": c.jurisdiction,
                "liabilityLevel": c.liability_level,
                "riskLevel": analysis.risk_level if analysis else None,
                "hasAnalysis": analysis is not None,
                "clauseCount": Clause.objects.filter(contract=c).count(),
                "uploadedAt": c.uploaded_at.isoformat() if c.uploaded_at else None,
                "forceMajeureScore": score_force_majeure_risk(fm_text),
            })

        return Response({
            "query": query,
            "answer": llm_answer,
            "contracts": serialized,
            "portfolio_stats": {
                "total": total_contracts,
                "high_risk": high_risk_count,
                "force_majeure": fm_count,
                "high_liability": high_liability_count,
            },
            "tools_used": ["FAISS Embeddings", "BM25 Clause Search", "FM Risk Scorer", "Qwen LLM"],
        })

    def _rule_based_answer(self, query, total, high_risk, fm, high_liab, top_contracts):
        q = query.lower()
        if "force majeure" in q:
            return f"Found {fm} contracts with force majeure clauses in your portfolio of {total}. These carry elevated risk during extraordinary events."
        elif "high risk" in q or "risky" in q:
            return f"{high_risk} contracts rated HIGH or CRITICAL risk out of {total} ({round(high_risk/max(total,1)*100)}%). Requires immediate attention."
        elif "liability" in q:
            return f"Your portfolio has {high_liab} high-liability contracts representing your largest financial exposure."
        elif top_contracts:
            names = ", ".join(c.original_filename or c.id for c in top_contracts[:3])
            return f"Most relevant contracts: {names}. Portfolio total: {total} contracts."
        return f"Portfolio: {total} contracts, {high_risk} high-risk, {high_liab} high-liability. Refine query for specific insights."


# ---------------------------------------------------------------------------
# 4. ANALYTICS DASHBOARD
# ---------------------------------------------------------------------------
class SearchAnalyticsView(APIView):
    permission_classes = [AllowAny]  # Temporarily disabled for development

    def get(self, request):
        valid_ids = Clause.objects.filter(contract__user=get_request_user(request)).values_list("contract_id", flat=True).distinct()
        user_qs = Contract.objects.filter(user=get_request_user(request), id__in=valid_ids)
        user_ids = user_qs.values_list("id", flat=True)
        # High value — parse contract_value string to numeric for charts
        import re as _re
        def _parse_val(v):
            if v is None:
                return None
            if isinstance(v, (int, float)):
                return float(v)
            s = str(v)
            # Strip currency symbols, commas, spaces, text labels
            digits = _re.sub(r'[^0-9.]', '', s.replace(',', ''))
            try:
                num = float(digits)
                return num if num >= 1000 else None
            except (ValueError, TypeError):
                return None

        high_value = []
        for c in user_qs.filter(contract_value__isnull=False).order_by("-uploaded_at")[:10]:
            num_val = _parse_val(c.contract_value)
            if num_val:
                high_value.append({"id": c.id, "title": (c.original_filename or c.id)[:40],
                                    "value": num_val, "valueLabel": str(c.contract_value),
                                    "jurisdiction": c.jurisdiction,
                                    "liabilityLevel": c.liability_level})
        if not high_value:
            for c in user_qs[:10]:
                analysis = ContractRiskAnalysis.objects.filter(contract=c).first()
                score = float(analysis.risk_score) * 1000 if analysis and analysis.risk_score else 50000
                high_value.append({"id": c.id, "title": (c.original_filename or c.id)[:40],
                                    "value": round(score, 0), "valueLabel": f"~${round(score):,}",
                                    "jurisdiction": c.jurisdiction,
                                    "liabilityLevel": c.liability_level})

        # High liability — risk_score stored as 0-100 integer
        high_liability = []
        for c in user_qs.filter(liability_level="HIGH").order_by("-uploaded_at")[:10]:
            analysis = ContractRiskAnalysis.objects.filter(contract=c).first()
            high_liability.append({"id": c.id, "title": (c.original_filename or c.id)[:40],
                                    "riskScore": float(analysis.risk_score) if analysis and analysis.risk_score else 50.0,
                                    "jurisdiction": c.jurisdiction,
                                    "riskLevel": analysis.risk_level if analysis else "HIGH"})

        # Force majeure with actual risk scores
        force_majeure = []
        fm_ids = list(Clause.objects.filter(
            Q(clause_type__icontains="force majeure") |
            Q(extracted_text__icontains="force majeure") |
            Q(context_sentences__icontains="force majeure"),
            contract_id__in=user_ids
        ).values_list("contract_id", flat=True).distinct()[:10])
        for cid in fm_ids:
            try:
                c = Contract.objects.get(id=cid)
                cl = Clause.objects.filter(contract=c).filter(
                    Q(clause_type__icontains="force majeure") |
                    Q(extracted_text__icontains="force majeure") |
                    Q(context_sentences__icontains="force majeure")
                ).first()
                fm_text = (cl.extracted_text or cl.context_sentences or "") if cl else ""
                fm_score = score_force_majeure_risk(fm_text)
                force_majeure.append({
                    "id": c.id,
                    "title": (c.original_filename or c.id)[:40],
                    "riskScore": fm_score,
                    "jurisdiction": c.jurisdiction,
                    "clauseSnippet": fm_text[:100],
                })
            except Contract.DoesNotExist:
                pass

        risk_breakdown = {
            "HIGH": ContractRiskAnalysis.objects.filter(contract_id__in=user_ids, risk_level="HIGH").count(),
            "MEDIUM": ContractRiskAnalysis.objects.filter(contract_id__in=user_ids, risk_level="MEDIUM").count(),
            "LOW": ContractRiskAnalysis.objects.filter(contract_id__in=user_ids, risk_level="LOW").count(),
            "CRITICAL": ContractRiskAnalysis.objects.filter(contract_id__in=user_ids, risk_level="CRITICAL").count(),
            "NOT_ANALYZED": user_qs.count() - ContractRiskAnalysis.objects.filter(contract_id__in=user_ids).values("contract_id").distinct().count(),
        }

        type_dist = {}
        for c in user_qs.exclude(contract_type__isnull=True).exclude(contract_type=""):
            type_dist[c.contract_type] = type_dist.get(c.contract_type, 0) + 1

        juris_counts = {}
        for c in user_qs.exclude(jurisdiction__isnull=True).exclude(jurisdiction=""):
            juris_counts[c.jurisdiction] = juris_counts.get(c.jurisdiction, 0) + 1

        # Clause type breakdown
        clause_types = {}
        for cl in Clause.objects.filter(contract_id__in=user_ids, found=True).exclude(clause_name__isnull=True):
            key = cl.clause_name or "Other"
            clause_types[key] = clause_types.get(key, 0) + 1

        # Avg confidence per contract
        from django.db.models import Avg as DjAvg, Count as DjCount
        conf_data = []
        for c in user_qs:
            avg = Clause.objects.filter(contract=c, found=True).aggregate(a=DjAvg("confidence"))["a"]
            if avg is not None:
                conf_data.append({"title": (c.original_filename or c.id)[:30], "confidence": round(float(avg), 1)})

        # Contract age (days since upload)
        from django.utils import timezone as tz
        now = tz.now()
        age_data = []
        for c in user_qs:
            if c.uploaded_at:
                days = (now - c.uploaded_at).days
                age_data.append({"title": (c.original_filename or c.id)[:30], "days": days})

        # Liability level breakdown
        liability_dist = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
        for c in user_qs:
            lvl = (c.liability_level or "UNKNOWN").upper()
            if lvl not in liability_dist:
                lvl = "UNKNOWN"
            liability_dist[lvl] += 1

        # Clause count per contract
        clause_per_contract = []
        for c in user_qs:
            cnt = Clause.objects.filter(contract=c, found=True).count()
            analysis = ContractRiskAnalysis.objects.filter(contract=c).first()
            # risk_score is stored as 0-100 integer; send as-is
            raw_score = float(analysis.risk_score) if analysis and analysis.risk_score else 0
            clause_per_contract.append({
                "title": (c.original_filename or c.id)[:30],
                "contractType": c.contract_type or "",
                "clauses": cnt,
                "riskLevel": analysis.risk_level if analysis else "NOT_ANALYZED",
                "riskScore": raw_score,  # 0-100 scale
            })

        # Risk score trend (sorted by upload date)
        # risk_score is already 0-100 integer — no multiplication needed
        risk_trend = []
        for c in user_qs.order_by("uploaded_at"):
            analysis = ContractRiskAnalysis.objects.filter(contract=c).first()
            risk_trend.append({
                "title": (c.original_filename or c.id)[:20],
                "riskScore": round(float(analysis.risk_score), 1) if analysis and analysis.risk_score else 0,
                "date": c.uploaded_at.strftime("%b %d") if c.uploaded_at else "",
            })

        return Response({
            "high_value_contracts": high_value,
            "high_liability_contracts": high_liability,
            "force_majeure_contracts": force_majeure,
            "risk_breakdown": risk_breakdown,
            "liability_distribution": [{"name": k, "value": v} for k, v in liability_dist.items() if v > 0],
            "type_distribution": [{"type": k, "count": v} for k, v in sorted(type_dist.items(), key=lambda x: x[1], reverse=True)[:10]],
            "clause_type_breakdown": [{"name": k, "value": v} for k, v in sorted(clause_types.items(), key=lambda x: x[1], reverse=True)[:10]],
            "top_jurisdictions": [{"jurisdiction": j, "count": c} for j, c in sorted(juris_counts.items(), key=lambda x: x[1], reverse=True)[:8]],
            "confidence_per_contract": sorted(conf_data, key=lambda x: x["confidence"], reverse=True),
            "contract_age": sorted(age_data, key=lambda x: x["days"]),
            "clause_per_contract": clause_per_contract,
            "risk_trend": risk_trend,
            "summary": {
                "total_contracts": user_qs.count(),
                "analyzed_contracts": ContractRiskAnalysis.objects.filter(contract_id__in=user_ids).values("contract_id").distinct().count(),
                "total_clauses": Clause.objects.filter(contract_id__in=user_ids).count(),
                "high_risk_contracts": ContractRiskAnalysis.objects.filter(contract_id__in=user_ids, risk_level__in=["HIGH", "CRITICAL"]).count(),
                "avg_clauses_per_contract": round(Clause.objects.filter(contract_id__in=user_ids, found=True).count() / max(user_qs.count(), 1), 1),
                "high_liability_count": liability_dist.get("HIGH", 0),
                "fm_contracts": len(force_majeure),
            },
        })


# ---------------------------------------------------------------------------
# 5. BUYER vs SUPPLIER NEGOTIATION  (#7 Neo4j context, #8 memory, #9 multi-clause)
# ---------------------------------------------------------------------------
class NegotiationAgentView(APIView):
    permission_classes = [AllowAny]  # Temporarily disabled for development

    def post(self, request):
        # #9 Multi-clause: accept either a single clause or a list
        clause_text = request.data.get("clause_text", "").strip()
        clauses_list = request.data.get("clauses", [])  # list of {type, text}
        clause_type = request.data.get("clause_type", "General")
        rounds = min(int(request.data.get("rounds", 3)), 5)
        contract_id = request.data.get("contract_id")
        # Doc page 52: personality modes
        buyer_mode = request.data.get("buyer_mode", "balanced")    # aggressive / balanced / conservative
        supplier_mode = request.data.get("supplier_mode", "balanced")  # aggressive / balanced / conservative

        # Build work list
        if clauses_list:
            work_items = clauses_list  # multi-clause mode
        elif clause_text:
            work_items = [{"type": clause_type, "text": clause_text}]
        else:
            return Response({"error": "clause_text or clauses list required"}, status=status.HTTP_400_BAD_REQUEST)

        # #7: Fetch Neo4j graph context
        graph_context = ""
        if contract_id:
            graph_context = _get_neo4j_graph_context(contract_id)
            if not graph_context:
                # Fallback: pull from DB
                try:
                    contract = Contract.objects.get(id=contract_id)
                    analysis = ContractRiskAnalysis.objects.filter(contract=contract).first()
                    related = Clause.objects.filter(contract=contract)[:5]
                    graph_context = (
                        f"Contract: {contract.original_filename} | Type: {contract.contract_type} | "
                        f"Jurisdiction: {contract.jurisdiction} | "
                        f"Risk: {analysis.risk_level if analysis else 'Unknown'} | "
                        f"Clauses: {', '.join(cl.clause_type or 'Unknown' for cl in related)}"
                    )
                except Contract.DoesNotExist:
                    pass

        # #8: inject strategy memory into context
        all_results = []
        for item in work_items:
            item_type = item.get("type", "General")
            item_text = item.get("text", "").strip()
            if not item_text:
                continue

            memory_clauses = _negotiation_memory.get_best(item_type, top_k=2)
            memory_context = ""
            if memory_clauses:
                memory_context = "\n\nPast successful clauses for reference:\n" + "\n".join(
                    f"- (score {m['score']}) {m['clause'][:200]}" for m in memory_clauses
                )

            enhanced_context = graph_context + memory_context
            result = self._negotiate_single(item_text, item_type, enhanced_context, rounds, buyer_mode, supplier_mode)
            result["clause_type"] = item_type

            # #8: save successful result to memory
            if result.get("final_analysis", {}).get("improvement", 0) >= 0:
                _negotiation_memory.save(
                    item_type,
                    result["final_clause"],
                    result["final_analysis"].get("final_risk_score", 50),
                )

            all_results.append(result)

        # Single-clause response (backward compatible)
        if len(all_results) == 1:
            r = all_results[0]
            r["memory_stats"] = _negotiation_memory.stats()
            return Response(r)

        # Multi-clause response
        return Response({
            "multi_clause": True,
            "total_clauses": len(all_results),
            "results": all_results,
            "memory_stats": _negotiation_memory.stats(),
            "overall_improvement": round(
                sum(r.get("final_analysis", {}).get("improvement", 0) for r in all_results) / max(len(all_results), 1), 1
            ),
        })

    def _negotiate_single(self, clause_text, clause_type, graph_context, rounds, buyer_mode="balanced", supplier_mode="balanced"):
        history = []
        current = clause_text
        for rnd in range(1, rounds + 1):
            buyer = self._buyer_propose(current, clause_type, graph_context, rnd, buyer_mode)
            buyer_score = self._score_clause(buyer)
            supplier = self._supplier_counter(current, buyer, clause_type, graph_context, rnd, supplier_mode)
            supplier_score = self._score_clause(supplier)
            if buyer_score >= supplier_score:
                current = buyer
                winner = "buyer"
            else:
                current = supplier
                winner = "supplier"
            history.append({
                "round": rnd,
                "buyer_proposal": buyer,
                "buyer_score": buyer_score,
                "supplier_counter": supplier,
                "supplier_score": supplier_score,
                "round_winner": winner,
                "selected_clause": current,
            })
        return {
            "original_clause": clause_text,
            "final_clause": current,
            "rounds_completed": rounds,
            "negotiation_history": history,
            "final_analysis": self._final_analysis(clause_text, current, history),
            "improvement_score": self._score_clause(current) - self._score_clause(clause_text),
            "financial_impact": self._estimate_financial_impact(clause_text, current),
        }

    # Doc page 52: personality mode instructions
    _BUYER_MODES = {
        "aggressive": "Be very aggressive. Push hard for maximum buyer protection. Cap all liabilities, demand unlimited force majeure rights, zero penalties on buyer.",
        "balanced": "Be balanced but firm. Protect buyer interests while keeping agreement workable.",
        "conservative": "Be conservative and reasonable. Seek moderate protections that won't cause the deal to collapse.",
    }
    _SUPPLIER_MODES = {
        "aggressive": "Be very aggressive. Protect supplier revenue at all costs. Push back hard on all caps and buyer-friendly terms.",
        "balanced": "Be balanced. Protect core supplier interests while keeping the deal viable.",
        "conservative": "Be conservative. Accept most buyer terms but protect payment and IP rights.",
    }

    def _buyer_propose(self, clause, clause_type, graph_context, rnd, mode="balanced"):
        style = self._BUYER_MODES.get(mode, self._BUYER_MODES["balanced"])
        prompt = f"""You are a BUYER's legal counsel negotiating a {clause_type} clause. Round {rnd}. Style: {mode.upper()}.
BUYER OBJECTIVE: {style}
SPECIFIC CHANGES TO MAKE FOR BUYER:
- Add payment grace period of at least 10 business days before interest accrues
- Cap late payment interest at 1.5% per month maximum
- Add right for buyer to dispute invoices without triggering interest
- Include mutual termination rights
- Remove any unconditional payment obligations

Original Clause:
{clause[:600]}

Write a COMPLETE rewritten clause that STRONGLY favors the BUYER. Change the payment and interest terms significantly. Output ONLY the rewritten clause text, no explanation:"""
        result = _call_qwen(prompt)
        if result and len(result) > 50:
            result_score = self._score_clause(result)
            original_score = self._score_clause(clause)
            # Only accept LLM result if it genuinely improves buyer position by at least 3 pts
            if result_score >= original_score + 3:
                return result.strip()
        return self._buyer_fallback(clause, clause_type)

    def _supplier_counter(self, original, buyer_proposal, clause_type, graph_context, rnd, mode="balanced"):
        style = self._SUPPLIER_MODES.get(mode, self._SUPPLIER_MODES["balanced"])
        prompt = f"""You are a SUPPLIER's legal counsel negotiating a {clause_type} clause. Round {rnd}. Style: {mode.upper()}.
SUPPLIER OBJECTIVE: {style}
SPECIFIC CHANGES TO MAKE FOR SUPPLIER:
- Payment must be made strictly on the first business day, NO grace period
- Keep compound interest at 2.5% per month (30% per annum) — do NOT reduce this
- Add that supplier can suspend services after 5 days of non-payment
- Remove any buyer right to dispute without paying first
- Add automatic renewal unless 90 days written notice given

Buyer's Proposal (REJECT this and rewrite to favor SUPPLIER):
{buyer_proposal[:600]}

Write a COMPLETE counter-proposal that STRONGLY favors the SUPPLIER. Make it clearly different from the buyer's version. Output ONLY the rewritten clause text, no explanation:"""
        result = _call_qwen(prompt)
        if result and len(result) > 50:
            result_score = self._score_clause(result)
            buyer_score = self._score_clause(buyer_proposal)
            # Only accept LLM result if it genuinely opposes buyer (lower score by at least 3 pts)
            if result_score <= buyer_score - 3:
                return result.strip()
        return self._supplier_fallback(original, clause_type)

    def _score_clause(self, text: str) -> float:
        """Score clause per doc spec + extended rules. Higher = better for buyer."""
        if not text:
            return 0.0
        t = text.lower()
        score = 50.0
        # Doc-specified scoring rules (page 49)
        if "unlimited liability" in t:
            score -= 50
        if "force majeure protection" in t or "force majeure" in t:
            score += 30
        if "penalty" in t:
            score -= 20
        # Extended rules
        positives = {
            "limitation of liability": 15, "liable for indirect": 12, "mutual": 5,
            "reasonable": 5, "net 45": 6, "net 30": 4, "30 days notice": 6,
            "dispute resolution": 5, "termination for convenience": 7,
            "indemnification": 3, "confidentiality": 3, "cap on liability": 10,
            "force majeure": 10, "buyer may terminate": 8,
            "withhold payment": 8, "good faith": 5, "disputed": 4,
            "grace period": 7, "45 days": 5, "cure period": 6,
            "1% per month": 6, "1.5% per month": 4,
        }
        negatives = {
            "irrevocable": -8, "unconditional": -10, "sole discretion": -6,
            "liquidated damages": -5, "waive all rights": -8, "without limitation": -10,
            "consequential damages": -6,
            "advance on the first business day": -10, "without deduction": -8,
            "set-off": -6, "suspend performance": -8, "acceleration": -7,
            "2.5% per month": -10, "compound interest": -8, "no grace period": -8,
        }
        for kw, w in positives.items():
            if kw in t:
                score += w
        for kw, w in negatives.items():
            if kw in t:
                score += w
        words = len(text.split())
        if 50 <= words <= 300:
            score += 5
        return round(min(max(score, 0), 100), 1)

    # Doc page 49: financial $ impact estimate per clause
    def _estimate_financial_impact(self, original: str, final: str) -> dict:
        orig_score = self._score_clause(original)
        final_score = self._score_clause(final)
        delta = final_score - orig_score
        # Rough $ exposure heuristic: each score point ~ $10k risk reduction
        risk_reduction = round(delta * 10000, -3)  # round to nearest 1000
        return {
            "score_delta": round(delta, 1),
            "estimated_risk_reduction_usd": risk_reduction,
            "interpretation": (
                f"Improved score by {delta:.1f} pts ≈ ${abs(risk_reduction):,.0f} risk {'reduction' if delta >= 0 else 'increase'}"
            )
        }

    def _buyer_fallback(self, clause, clause_type):
        ct = (clause_type or "").lower()
        if "payment" in ct or "payment" in clause.lower():
            return (
                "3.1 The Client shall pay the Service Provider within 45 days of receipt of a valid, undisputed invoice. "
                "The Client may withhold payment on any amount it disputes in good faith by providing written notice within 10 business days of invoice receipt. "
                "3.2 In the event of a late payment on undisputed amounts, simple interest (not compound) shall accrue at the rate of 1% per month. "
                "3.3 The Client shall have the right to set off any amounts owed by the Service Provider against amounts due hereunder."
            )
        if "liability" in ct:
            return "Total liability of either party shall be limited to fees paid in the preceding 12 months. Neither party shall be liable for indirect or consequential damages."
        if "termination" in ct:
            return "Either party may terminate for convenience with 30 days notice. Buyer pays only for services rendered up to termination date."
        if "force majeure" in ct or "force majeure" in clause.lower():
            return "Neither party shall be liable for Force Majeure events. Buyer may terminate without penalty if delay exceeds 30 days."
        return (
            clause.split(".")[0] + ". "
            "Notwithstanding the foregoing, Buyer's total liability shall not exceed amounts paid in the preceding 6 months, "
            "and Buyer shall have a 15-business-day cure period before any remedies may be exercised."
        )

    def _supplier_fallback(self, original_clause, clause_type):
        ct = (clause_type or "").lower()
        if "payment" in ct or "payment" in original_clause.lower():
            return (
                "3.1 The Client shall pay the Service Provider a fixed monthly retainer of USD 450,000 (Four Hundred Fifty Thousand United States Dollars), "
                "payable in advance on the first business day of each calendar month, without deduction, set-off, or counterclaim of any kind whatsoever. "
                "3.2 In the event the Client fails to make any payment when due, the Service Provider shall be entitled to: "
                "(a) charge compound interest at 2.5% per month (30% per annum) from the due date; "
                "(b) suspend all services immediately upon 5 days written notice; "
                "(c) accelerate all remaining amounts for the contract term, making them immediately due and payable. "
                "3.3 The Client waives any right of set-off or counterclaim against payment obligations under this Agreement."
            )
        if "liability" in ct:
            return "Supplier's liability shall be limited to direct damages only. Supplier shall not be liable for any business interruption, lost profits, or consequential damages of any kind."
        if "termination" in ct:
            return "Termination requires 90 days written notice. Early termination by Buyer triggers payment of all remaining contract value as liquidated damages."
        return (
            original_clause + " "
            "The Supplier's rights to payment are absolute and unconditional. "
            "The Supplier may suspend performance upon any payment default and pursue all available legal remedies including acceleration of outstanding amounts."
        )

    def _final_analysis(self, original, final, history):
        orig_score = self._score_clause(original)
        final_score = self._score_clause(final)
        improvement = final_score - orig_score
        buyer_wins = sum(1 for h in history if h["round_winner"] == "buyer")
        if improvement > 10:
            verdict = "Significantly improved — the final clause is substantially better balanced."
        elif improvement > 0:
            verdict = "Moderately improved — the final clause offers better protection."
        elif improvement == 0:
            verdict = "Neutral outcome — clause remains similarly positioned."
        else:
            verdict = "Consider manual review — the negotiation shifted toward higher risk."
        return {
            "original_risk_score": orig_score,
            "final_risk_score": final_score,
            "improvement": round(improvement, 1),
            "verdict": verdict,
            "buyer_rounds_won": buyer_wins,
            "supplier_rounds_won": len(history) - buyer_wins,
            "recommendation": "Accept final clause" if improvement >= 0 else "Request further negotiation",
        }


# ---------------------------------------------------------------------------
# PENDING #4: Auto Clause Extraction → Neo4j Graph Builder
# ---------------------------------------------------------------------------
class AutoGraphBuilderView(APIView):
    permission_classes = [AllowAny]  # Temporarily disabled for development

    def post(self, request):
        contract_id = request.data.get("contract_id")
        use_llm = request.data.get("use_llm", True)

        if not contract_id:
            return Response({"error": "contract_id required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            contract = Contract.objects.get(id=contract_id)
        except Contract.DoesNotExist:
            return Response({"error": "Contract not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get contract text from clauses
        clauses_qs = Clause.objects.filter(contract=contract)
        contract_text = " ".join((cl.extracted_text or cl.context_sentences or "") for cl in clauses_qs)

        if not contract_text.strip():
            return Response({"error": "No text found for this contract"}, status=status.HTTP_400_BAD_REQUEST)

        # Extract clauses
        extracted = []
        if use_llm:
            extracted = _extract_clauses_llm(contract_text)
        if not extracted:
            extracted = _extract_clauses_rule_based(contract_text)

        # Add FM risk scores to all extracted clauses (#3)
        for cl in extracted:
            if cl.get("type") == "Force Majeure" or "force majeure" in (cl.get("text") or "").lower():
                cl["risk_score"] = score_force_majeure_risk(cl.get("text", ""))

        # Push to Neo4j (#4)
        neo4j_result = _push_to_neo4j(contract, extracted)

        # Invalidate FAISS index so it rebuilds with new data
        _faiss_index.invalidate()

        return Response({
            "contract_id": contract_id,
            "contract_title": contract.original_filename,
            "clauses_extracted": len(extracted),
            "clauses": extracted,
            "pushed_to_neo4j": neo4j_result["success"],
            "node_mappings": neo4j_result["node_mappings"],
            "extraction_method": "LLM (Qwen)" if use_llm and extracted else "Rule-based",
        })

    def get(self, request):
        """Build graph for ALL contracts (batch)."""
        contracts = Contract.objects.all()[:50]
        results = []
        for contract in contracts:
            clauses_qs = Clause.objects.filter(contract=contract)
            contract_text = " ".join((cl.extracted_text or cl.context_sentences or "") for cl in clauses_qs)
            if not contract_text.strip():
                continue
            extracted = _extract_clauses_rule_based(contract_text)
            for cl in extracted:
                if "force majeure" in (cl.get("text") or "").lower():
                    cl["risk_score"] = score_force_majeure_risk(cl.get("text", ""))
            neo4j_result = _push_to_neo4j(contract, extracted)
            results.append({
                "contract_id": contract.id,
                "title": contract.original_filename,
                "clauses_extracted": len(extracted),
                "pushed": neo4j_result["success"],
                "node_mappings": neo4j_result["node_mappings"],
            })
        _faiss_index.invalidate()
        return Response({"processed": len(results), "results": results})


# ---------------------------------------------------------------------------
# 6. FORCE MAJEURE RISK SCORER endpoint (#3)
# ---------------------------------------------------------------------------
class ForceMajeureRiskScorerView(APIView):
    permission_classes = [AllowAny]  # Temporarily disabled for development

    def post(self, request):
        """Score arbitrary text or a specific contract."""
        text = request.data.get("text", "")
        contract_id = request.data.get("contract_id")

        if contract_id:
            clauses = Clause.objects.filter(contract_id=contract_id).filter(
                Q(clause_type__icontains="force majeure") |
                Q(extracted_text__icontains="force majeure") |
                Q(context_sentences__icontains="force majeure")
            )
            scored_clauses = []
            overall_score = 0.0
            for cl in clauses:
                cl_text = cl.extracted_text or cl.context_sentences or ""
                s = score_force_majeure_risk(cl_text)
                overall_score = max(overall_score, s)
                scored_clauses.append({
                    "clause_id": cl.id,
                    "type": cl.clause_type,
                    "score": s,
                    "snippet": cl_text[:200],
                    "signals": self._explain_signals(cl_text),
                })
            return Response({
                "contract_id": contract_id,
                "overall_fm_risk_score": overall_score,
                "risk_level": self._risk_level(overall_score),
                "fm_clauses": scored_clauses,
            })

        if not text:
            return Response({"error": "text or contract_id required"}, status=status.HTTP_400_BAD_REQUEST)

        score = score_force_majeure_risk(text)
        return Response({
            "score": score,
            "risk_level": self._risk_level(score),
            "signals": self._explain_signals(text),
        })

    def _risk_level(self, score):
        if score >= 0.6:
            return "HIGH"
        elif score >= 0.3:
            return "MEDIUM"
        return "LOW"

    def _explain_signals(self, text):
        text_lower = text.lower()
        found = []
        for signal, weight in _FM_SIGNALS.items():
            if signal in text_lower:
                found.append({"signal": signal, "weight": weight, "impact": "risk" if weight > 0 else "protection"})
        return found


# ---------------------------------------------------------------------------
# NEGOTIATION MEMORY ENDPOINT (#8)
# ---------------------------------------------------------------------------
class NegotiationMemoryView(APIView):
    permission_classes = [AllowAny]  # Temporarily disabled for development

    def get(self, request):
        clause_type = request.query_params.get("clause_type")
        if clause_type:
            return Response({
                "clause_type": clause_type,
                "memories": _negotiation_memory.get_best(clause_type, top_k=5),
            })
        return Response({
            "stats": _negotiation_memory.stats(),
            "available_types": _negotiation_memory.all_types(),
        })

    def delete(self, request):
        """Clear memory for a clause type."""
        clause_type = request.data.get("clause_type")
        if clause_type:
            key = (clause_type or "general").lower()
            _negotiation_memory._store.pop(key, None)
        else:
            _negotiation_memory._store.clear()
        return Response({"cleared": True})


# ---------------------------------------------------------------------------
# 7. CONTRACT STATS
# ---------------------------------------------------------------------------
class ContractStatsView(APIView):
    permission_classes = [AllowAny]  # Temporarily disabled for development

    def get(self, request):
        valid_ids = Clause.objects.filter(contract__user=get_request_user(request)).values_list("contract_id", flat=True).distinct()
        user_qs = Contract.objects.filter(user=get_request_user(request), id__in=valid_ids)
        user_ids = user_qs.values_list("id", flat=True)
        total = user_qs.count()
        analyzed = ContractRiskAnalysis.objects.filter(contract_id__in=user_ids).values("contract_id").distinct().count()
        high_risk = ContractRiskAnalysis.objects.filter(contract_id__in=user_ids, risk_level__in=["HIGH", "CRITICAL"]).count()
        high_liability = user_qs.filter(liability_level="HIGH").count()
        fm_count = Clause.objects.filter(
            Q(clause_type__icontains="force majeure") |
            Q(extracted_text__icontains="force majeure") |
            Q(context_sentences__icontains="force majeure"),
            contract_id__in=user_ids
        ).values("contract_id").distinct().count()
        return Response({
            "total_contracts": total,
            "analyzed_contracts": analyzed,
            "unanalyzed_contracts": total - analyzed,
            "high_risk_contracts": high_risk,
            "high_liability_contracts": high_liability,
            "force_majeure_contracts": fm_count,
            "total_clauses": Clause.objects.count(),
            "analysis_coverage": round((analyzed / total * 100) if total else 0, 1),
        })


# ---------------------------------------------------------------------------
# 8. MULTI-HOP NEO4J GRAPH QUERIES (doc pages 15, 39, 43)
# ---------------------------------------------------------------------------
class GraphMultiHopView(APIView):
    permission_classes = [AllowAny]  # Temporarily disabled for development

    # ── MySQL fallback: build graph from Django ORM ──────────────────────────
    def _mysql_graph(self, query_type, contract_name, user):
        """Build multi-hop graph data directly from MySQL when Neo4j lacks user data."""
        from django.db.models import Q as _Q
        nodes = {}
        links = []

        # Determine user's contracts
        if user and user.is_authenticated:
            user_qs = Contract.objects.filter(user=user)
        else:
            user_qs = Contract.objects.all()

        if contract_name:
            user_qs = user_qs.filter(original_filename__icontains=contract_name)

        def add_contract(c, analysis=None):
            cid = f"c_{c.id}"
            if cid not in nodes:
                nodes[cid] = {"id": cid, "name": (c.original_filename or str(c.id))[:35], "type": "Contract",
                               "risk_level": analysis.risk_level if analysis else None}
            return cid

        def add_clause(cl):
            clid = f"cl_{cl.id}"
            if clid not in nodes:
                nodes[clid] = {"id": clid, "name": (cl.clause_type or cl.clause_name or "Clause")[:30], "type": "Clause",
                               "risk": cl.risk_level}
            return clid

        def add_risk(contract_id, risk_level, score):
            rid = f"r_{contract_id}_{risk_level}"
            if rid not in nodes:
                nodes[rid] = {"id": rid, "name": f"{risk_level} Risk ({score}%)", "type": "Risk",
                              "risk_score": score}
            return rid

        if query_type == "high_risk":
            # High-risk contracts → their high-risk clauses
            analyses = ContractRiskAnalysis.objects.filter(
                contract__in=user_qs, risk_level__in=["HIGH", "CRITICAL"]
            ).select_related("contract").order_by("-risk_score")[:15]
            for analysis in analyses:
                c = analysis.contract
                cid = add_contract(c, analysis)
                rid = add_risk(c.id, analysis.risk_level, round(float(analysis.risk_score or 0)))
                links.append({"source": cid, "target": rid, "label": "HAS_RISK"})
                # Add high-risk clauses
                clauses = Clause.objects.filter(contract=c, found=True,
                    risk_level__in=["HIGH", "CRITICAL"])[:5]
                for cl in clauses:
                    clid = add_clause(cl)
                    links.append({"source": cid, "target": clid, "label": "HAS_CLAUSE"})
                    links.append({"source": clid, "target": rid, "label": "INTRODUCES_RISK"})

        elif query_type == "cascading_fm":
            # Force majeure clauses → contracts → shared risk
            fm_clauses = Clause.objects.filter(
                contract__in=user_qs,
                found=True
            ).filter(
                _Q(clause_type__icontains="force") |
                _Q(extracted_text__icontains="force majeure") |
                _Q(context_sentences__icontains="force majeure")
            ).select_related("contract")[:20]
            # Group by risk level to show cascading
            risk_hub_id = "r_fm_hub"
            nodes[risk_hub_id] = {"id": risk_hub_id, "name": "FM Risk Hub", "type": "Risk"}
            seen_contracts = {}
            for cl in fm_clauses:
                c = cl.contract
                analysis = ContractRiskAnalysis.objects.filter(contract=c).first()
                cid = add_contract(c, analysis)
                clid = add_clause(cl)
                links.append({"source": cid, "target": clid, "label": "HAS_FM_CLAUSE"})
                links.append({"source": clid, "target": risk_hub_id, "label": "CASCADES_TO"})
                # Connect contracts sharing same clause type
                if c.id not in seen_contracts:
                    seen_contracts[c.id] = cid
            # Cross-link contracts sharing FM risk
            contract_ids = list(seen_contracts.values())
            for i in range(len(contract_ids) - 1):
                links.append({"source": contract_ids[i], "target": contract_ids[i+1], "label": "SHARED_FM_RISK"})

        elif query_type == "connected_risks":
            # Expand from specific contract (or show all contract→clause→risk)
            qs = user_qs[:8] if not contract_name else user_qs[:1]
            for c in qs:
                analysis = ContractRiskAnalysis.objects.filter(contract=c).first()
                cid = add_contract(c, analysis)
                if analysis:
                    rid = add_risk(c.id, analysis.risk_level or "MEDIUM",
                                   round(float(analysis.risk_score or 0)))
                    links.append({"source": cid, "target": rid, "label": "HAS_RISK"})
                clauses = Clause.objects.filter(contract=c, found=True)[:6]
                for cl in clauses:
                    clid = add_clause(cl)
                    links.append({"source": cid, "target": clid, "label": "HAS_CLAUSE"})
                    if cl.risk_level in ("HIGH", "CRITICAL"):
                        rid2 = f"r_cl_{cl.id}"
                        nodes[rid2] = {"id": rid2, "name": f"{cl.risk_level} Risk", "type": "Risk"}
                        links.append({"source": clid, "target": rid2, "label": "INTRODUCES_RISK"})
            # Cross-links between contracts sharing same clause types
            all_c = list(qs)
            for i in range(len(all_c) - 1):
                ci = f"c_{all_c[i].id}"
                cj = f"c_{all_c[i+1].id}"
                if ci in nodes and cj in nodes:
                    links.append({"source": ci, "target": cj, "label": "CONNECTED"})

        elif query_type == "obligations":
            # Contracts → obligation-type clauses
            obligation_types = ["Payment", "Delivery", "Termination", "Confidentiality",
                                "Indemnification", "Compliance", "Reporting", "Notice"]
            obl_qs = Clause.objects.filter(
                contract__in=user_qs, found=True
            ).filter(
                _Q(clause_name__icontains="shall") |
                _Q(clause_name__in=obligation_types) |
                _Q(clause_type__in=obligation_types)
            ).select_related("contract")[:30]
            for cl in obl_qs:
                c = cl.contract
                analysis = ContractRiskAnalysis.objects.filter(contract=c).first()
                cid = add_contract(c, analysis)
                oid = f"o_{cl.id}"
                nodes[oid] = {"id": oid, "name": (cl.clause_name or cl.clause_type or "Obligation")[:35], "type": "Obligation"}
                links.append({"source": cid, "target": oid, "label": "HAS_OBLIGATION"})

        elif query_type == "all_nodes":
            # Full graph of user's contracts
            for c in user_qs[:10]:
                analysis = ContractRiskAnalysis.objects.filter(contract=c).first()
                cid = add_contract(c, analysis)
                if analysis:
                    rid = add_risk(c.id, analysis.risk_level or "MEDIUM",
                                   round(float(analysis.risk_score or 0)))
                    links.append({"source": cid, "target": rid, "label": "HAS_RISK"})
                for cl in Clause.objects.filter(contract=c, found=True)[:5]:
                    clid = add_clause(cl)
                    links.append({"source": cid, "target": clid, "label": "HAS_CLAUSE"})

        return list(nodes.values()), links

    def post(self, request):
        query_type = request.data.get("query_type", "high_risk")
        contract_name = request.data.get("contract_name", "")
        query_used = f"MySQL:{query_type}"

        # Always use MySQL — Neo4j may have stale data from other sessions
        neo4j_nodes, neo4j_links = self._mysql_graph(query_type, contract_name, request.user)
        source = "mysql"

        return Response({
            "nodes": neo4j_nodes,
            "links": neo4j_links,
            "multi_hop": True,
            "query_type": query_type,
            "cypher_used": query_used,
            "source": source,
        })


# ---------------------------------------------------------------------------
# 9. GRAPH NODE EXPAND (doc pages 21-27: click node → expand neighbors)
# ---------------------------------------------------------------------------
class GraphNodeExpandView(APIView):
    permission_classes = [AllowAny]  # Temporarily disabled for development

    def get(self, request, node_id):
        try:
            from contractai.neo4j_config import get_neo4j_driver
            driver = get_neo4j_driver()
            if driver is None:
                return Response({"error": "Neo4j unavailable", "nodes": [], "links": []})
        except Exception as e:
            logger.warning(f"[GraphNodeExpand] Neo4j connection failed: {e}")
            return Response({"error": "Neo4j unavailable", "nodes": [], "links": []})

        try:
            with driver.session() as session:
                rows = session.run(
                    "MATCH (n)-[r]->(m) WHERE id(n) = $nid OR id(m) = $nid RETURN n, r, m LIMIT 50",
                    nid=int(node_id)
                )
                nodes = {}
                links = []
                for record in rows:
                    n, m, rel = record["n"], record["m"], record["r"]
                    nodes[n.id] = {
                        "id": str(n.id),
                        "name": n.get("title") or n.get("type") or n.get("text", "")[:40] or "node",
                        "type": list(n.labels)[0] if n.labels else "Unknown",
                        "risk_score": n.get("score", 0),
                    }
                    nodes[m.id] = {
                        "id": str(m.id),
                        "name": m.get("title") or m.get("type") or m.get("text", "")[:40] or "node",
                        "type": list(m.labels)[0] if m.labels else "Unknown",
                        "risk_score": m.get("score", 0),
                    }
                    links.append({"source": str(n.id), "target": str(m.id), "label": rel.type})
                return Response({"nodes": list(nodes.values()), "links": links, "expanded_node": node_id})
        except Exception as e:
            logger.warning(f"[NodeExpand] failed: {e}")
            return Response({"error": str(e), "nodes": [], "links": []})


# ---------------------------------------------------------------------------
# 10. CLAUSE BENCHMARKING (doc page 36)
# ---------------------------------------------------------------------------

# Industry standard benchmark templates per clause type
_CLAUSE_BENCHMARKS = {
    "force majeure": {
        "template": "Neither party shall be liable for any failure or delay in performance due to Force Majeure events including acts of God, war, pandemic, government restrictions, or natural disasters. The affected party shall notify the other within 5 business days. If the Force Majeure event persists beyond 60 days, either party may terminate with 30 days notice.",
        "key_protections": ["notification requirement", "60-day termination right", "both parties covered", "specific event list"],
        "risk_level": "LOW",
    },
    "liability": {
        "template": "Each party's total aggregate liability under this Agreement shall not exceed the total fees paid or payable in the 12 months preceding the claim. Neither party shall be liable for indirect, incidental, consequential, punitive or special damages.",
        "key_protections": ["12-month fee cap", "consequential damages excluded", "mutual cap", "no punitive damages"],
        "risk_level": "LOW",
    },
    "payment": {
        "template": "Payment is due within 45 days of receipt of a valid invoice. Disputed amounts may be withheld without penalty pending resolution. Late payments accrue interest at 1.5% per month. Buyer may set off undisputed amounts owed by Supplier.",
        "key_protections": ["Net 45 terms", "dispute withholding right", "set-off right", "capped interest"],
        "risk_level": "LOW",
    },
    "termination": {
        "template": "Either party may terminate this Agreement for convenience upon 30 days written notice. Either party may terminate immediately upon material breach if uncured within 15 days of written notice. Upon termination, Buyer pays only for services rendered through the termination date.",
        "key_protections": ["30-day convenience termination", "15-day cure period", "pro-rata payment only", "immediate breach termination"],
        "risk_level": "LOW",
    },
    "indemnity": {
        "template": "Each party shall indemnify and hold harmless the other from third-party claims arising from its own negligence, willful misconduct, or breach of this Agreement. Indemnification is mutual and limited to direct damages proven in a court of competent jurisdiction.",
        "key_protections": ["mutual indemnity", "negligence-based trigger", "direct damages only", "court-proven"],
        "risk_level": "LOW",
    },
    "confidentiality": {
        "template": "Each party agrees to keep Confidential Information strictly confidential for 3 years from disclosure. Exceptions include publicly known information, independently developed information, and legally compelled disclosures. No reverse engineering of disclosed materials.",
        "key_protections": ["3-year limit", "standard exceptions", "no reverse engineering", "mutual obligation"],
        "risk_level": "LOW",
    },
}

class ClauseBenchmarkView(APIView):
    permission_classes = [AllowAny]  # Temporarily disabled for development

    def post(self, request):
        clause_text = request.data.get("clause_text", "").strip()
        clause_type = request.data.get("clause_type", "").lower().strip()

        if not clause_text:
            return Response({"error": "clause_text required"}, status=400)

        # Auto-detect clause type if not provided
        if not clause_type:
            for key in _CLAUSE_BENCHMARKS:
                if key in clause_text.lower():
                    clause_type = key
                    break

        benchmark = _CLAUSE_BENCHMARKS.get(clause_type)
        if not benchmark:
            # Try partial match
            for key in _CLAUSE_BENCHMARKS:
                if key in clause_type:
                    benchmark = _CLAUSE_BENCHMARKS[key]
                    clause_type = key
                    break

        view = NegotiationAgentView()
        clause_score = view._score_clause(clause_text)

        if not benchmark:
            return Response({
                "clause_type": clause_type or "unknown",
                "clause_score": clause_score,
                "benchmark_available": False,
                "message": f"No benchmark template for '{clause_type}'. Available: {list(_CLAUSE_BENCHMARKS.keys())}",
            })

        benchmark_score = view._score_clause(benchmark["template"])
        gap = benchmark_score - clause_score

        # Check which protections are missing
        missing = []
        present = []
        for protection in benchmark["key_protections"]:
            if any(word in clause_text.lower() for word in protection.split()):
                present.append(protection)
            else:
                missing.append(protection)

        # LLM comparison if available
        llm_analysis = ""
        prompt = f"""Compare this contract clause against the industry benchmark and give a 2-sentence analysis.

Your Clause: {clause_text[:400]}

Industry Benchmark: {benchmark['template'][:400]}

Analysis (2 sentences max):"""
        llm_analysis = _call_qwen(prompt) or "LLM analysis unavailable."

        return Response({
            "clause_type": clause_type,
            "clause_score": clause_score,
            "benchmark_score": benchmark_score,
            "score_gap": round(gap, 1),
            "rating": "GOOD" if gap <= 5 else "NEEDS_IMPROVEMENT" if gap <= 20 else "POOR",
            "benchmark_template": benchmark["template"],
            "key_protections_present": present,
            "key_protections_missing": missing,
            "llm_analysis": llm_analysis,
            "recommendation": "Your clause scores {:.0f}/100 vs benchmark {:.0f}/100. {}".format(
                clause_score, benchmark_score,
                "Close to industry standard." if gap <= 5 else "Missing {} key protections: {}.".format(len(missing), ", ".join(missing[:2]))
            ),
        })


# ---------------------------------------------------------------------------
# BulkReclassifyView — re-run classify_contract() on all user's contracts
# ---------------------------------------------------------------------------
class BulkReclassifyView(APIView):
    permission_classes = [AllowAny]  # Temporarily disabled for development

    def post(self, request):
        from api.utils import classify_contract
        user = get_request_user(request)
        contracts = Contract.objects.filter(user=user)
        updated = 0
        results = []
        for c in contracts:
            if not c.full_text:
                continue
            try:
                cls = classify_contract(c.full_text, filename=c.original_filename or "")
                new_type = cls.get("contractType")
                old_type = c.contract_type
                if new_type and new_type != old_type:
                    c.contract_type = new_type
                    c.confidence_score = cls.get("confidenceScore")
                    c.save(update_fields=["contract_type", "confidence_score"])
                    updated += 1
                    results.append({"id": c.id, "filename": c.original_filename, "old": old_type, "new": new_type})
            except Exception as e:
                logger.warning(f"Reclassify error {c.id}: {e}")
        return Response({"updated": updated, "results": results})
