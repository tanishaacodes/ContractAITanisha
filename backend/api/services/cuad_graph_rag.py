"""
CUAD Graph RAG Service
======================
Retrieval-Augmented Generation using the CUAD Neo4j knowledge graph + Qwen 2.5.

Flow:
  1. Query Neo4j subgraph for the target contract(s)
  2. Serialize the graph context (clauses, risks, obligations, parties)
  3. Augment a Qwen 2.5 prompt with the graph context
  4. Return AI-generated analysis with:
     - Risk narrative
     - Negotiation recommendations
     - Clause comparison insights
     - Red-flag summary

Endpoints exposed via cuad_graph_views.py:
  POST /api/cuad-graph/rag-analyze/        — AI analysis of a single contract
  POST /api/cuad-graph/rag-compare/        — AI comparison of two contracts
  POST /api/cuad-graph/rag-negotiate/      — AI negotiation recommendations
"""

import logging
import json
import requests
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

OLLAMA_URL = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
QWEN_MODEL = "qwen2.5:0.5b"

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _call_qwen(prompt: str, max_tokens: int = 600, temperature: float = 0.3) -> str:
    """
    Call Qwen 2.5 via Ollama API.
    Returns the generated text or an error string.
    """
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": QWEN_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "stop": ["</analysis>", "---END---"],
                },
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except Exception as e:
        logger.error(f"[CUAD-RAG] Qwen call failed: {e}")
        return ""


def _get_driver():
    try:
        from contractai.neo4j_config import get_neo4j_driver, check_neo4j_available
        if check_neo4j_available():
            return get_neo4j_driver()
    except Exception:
        pass
    return None


def _build_graph_context_from_mysql(contract_id: str) -> Dict[str, Any]:
    """Fetch contract + clauses from MySQL and format as graph context."""
    from core.models import Contract, Clause
    from api.services.cuad_graph_service import _canonical_type, _text_based_risk, _infer_risk_level

    try:
        contract = Contract.objects.get(id=contract_id)
    except Contract.DoesNotExist:
        return {}

    clauses = list(Clause.objects.filter(contract=contract))

    clause_contexts = []
    for c in clauses:
        ct = _canonical_type(c.clause_type or "", c.clause_name or "")
        rs = _text_based_risk(c)
        text_snippet = (getattr(c, 'extracted_text', '') or '')[:300]
        clause_contexts.append({
            "name": c.clause_name or ct,
            "type": ct,
            "risk_score": round(rs, 3),
            "risk_level": _infer_risk_level(rs),
            "text_snippet": text_snippet,
        })

    # Sort by risk descending
    clause_contexts.sort(key=lambda x: x["risk_score"], reverse=True)

    return {
        "contract_id": contract_id,
        "contract_name": getattr(contract, 'filename', 'Contract') or 'Contract',
        "party_a": getattr(contract, 'partyA', '') or '',
        "party_b": getattr(contract, 'partyB', '') or '',
        "jurisdiction": getattr(contract, 'jurisdiction', '') or '',
        "contract_type": getattr(contract, 'contractType', '') or '',
        "total_clauses": len(clauses),
        "high_risk_count": sum(1 for c in clause_contexts if c["risk_level"] == "HIGH"),
        "medium_risk_count": sum(1 for c in clause_contexts if c["risk_level"] == "MEDIUM"),
        "clauses": clause_contexts,
    }


def _build_graph_context_from_neo4j(contract_id: str, driver) -> Dict[str, Any]:
    """Fetch contract subgraph from Neo4j and format as graph context."""
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (c:Contract {id: $cid})-[:HAS_CLAUSE]->(cl:Clause)
                OPTIONAL MATCH (cl)-[:CREATES_RISK]->(r:Risk)
                OPTIONAL MATCH (cl)-[:CREATES_OBLIGATION]->(o:Obligation)
                OPTIONAL MATCH (c)-[:HAS_PARTY]->(p:Party)
                OPTIONAL MATCH (c)-[:GOVERNED_BY]->(j:Jurisdiction)
                RETURN c, cl, r, o, collect(DISTINCT p.name) as parties, j.name as jurisdiction
            """, cid=contract_id)

            records = result.data()
            if not records:
                return {}

            first = records[0]
            c = first.get("c", {})

            clause_contexts = []
            for rec in records:
                cl = rec.get("cl", {})
                r = rec.get("r", {})
                if cl:
                    clause_contexts.append({
                        "name": cl.get("clause_name", ""),
                        "type": cl.get("clause_type", ""),
                        "risk_score": cl.get("risk_score", 0),
                        "risk_level": cl.get("risk_level", "LOW"),
                        "risk_category": r.get("category", "") if r else "",
                        "text_snippet": "",
                    })

            clause_contexts.sort(key=lambda x: x["risk_score"], reverse=True)

            return {
                "contract_id": contract_id,
                "contract_name": c.get("name", "Contract"),
                "jurisdiction": first.get("jurisdiction", ""),
                "parties": first.get("parties", []),
                "total_clauses": len(clause_contexts),
                "high_risk_count": sum(1 for c in clause_contexts if c["risk_level"] == "HIGH"),
                "clauses": clause_contexts,
            }
    except Exception as e:
        logger.error(f"[CUAD-RAG] Neo4j context fetch error: {e}")
        return {}


def _get_contract_context(contract_id: str) -> Dict[str, Any]:
    """Get contract graph context from Neo4j if available, else MySQL."""
    driver = _get_driver()
    if driver:
        ctx = _build_graph_context_from_neo4j(contract_id, driver)
        if ctx:
            return ctx
    return _build_graph_context_from_mysql(contract_id)


def _format_clause_list(clauses: List[Dict], max_clauses: int = 8) -> str:
    """Format clause list for prompt injection."""
    lines = []
    for i, c in enumerate(clauses[:max_clauses], 1):
        risk_emoji = "🔴" if c["risk_level"] == "HIGH" else "🟡" if c["risk_level"] == "MEDIUM" else "🟢"
        snippet = c.get("text_snippet", "")
        snippet_part = f' — "{snippet[:150]}..."' if snippet else ""
        lines.append(
            f"{i}. {risk_emoji} [{c['type']}] {c['name']} "
            f"(risk={c['risk_score']:.2f}){snippet_part}"
        )
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

class CUADGraphRAG:
    """
    GraphRAG engine: combines Neo4j knowledge graph with Qwen 2.5 reasoning.
    """

    # ── 1. Single Contract Analysis ──────────────────────────────────────────

    def analyze_contract(self, contract_id: str) -> Dict[str, Any]:
        """
        Graph-RAG analysis of a single contract.
        Returns risk narrative, red flags, and compliance insights.
        """
        ctx = _get_contract_context(contract_id)
        if not ctx:
            return {"error": f"Contract {contract_id} not found"}

        clause_text = _format_clause_list(ctx.get("clauses", []))

        prompt = f"""You are a senior legal AI analyzing a contract for PrimeContractAI.

CONTRACT KNOWLEDGE GRAPH CONTEXT:
- Contract: {ctx['contract_name']}
- Parties: {ctx.get('party_a', 'Party A')} ↔ {ctx.get('party_b', 'Party B')}
- Jurisdiction: {ctx.get('jurisdiction', 'Unknown')}
- Type: {ctx.get('contract_type', 'General')}
- Total Clauses: {ctx['total_clauses']} ({ctx['high_risk_count']} HIGH risk, {ctx['medium_risk_count']} MEDIUM risk)

TOP CLAUSES BY RISK (from graph analysis):
{clause_text}

TASK: Provide a structured legal risk analysis in this exact format:

RISK NARRATIVE:
[2-3 sentences summarizing the overall risk profile based on the graph data]

RED FLAGS:
- [Most critical risk clause and why]
- [Second risk concern]
- [Third risk concern if applicable]

COMPLIANCE INSIGHTS:
[1-2 sentences about jurisdiction-specific compliance concerns]

RECOMMENDATION:
[1 concrete action the legal team should take before signing]"""

        ai_response = _call_qwen(prompt, max_tokens=500, temperature=0.3)

        # Fallback rule-based response if Qwen fails
        if not ai_response:
            ai_response = self._rule_based_analysis(ctx)

        return {
            "contract_id": contract_id,
            "contract_name": ctx["contract_name"],
            "ai_analysis": ai_response,
            "graph_context": {
                "total_clauses": ctx["total_clauses"],
                "high_risk_count": ctx["high_risk_count"],
                "medium_risk_count": ctx.get("medium_risk_count", 0),
                "top_clauses": ctx.get("clauses", [])[:5],
            },
            "source": "graphrag_qwen25",
        }

    def _rule_based_analysis(self, ctx: Dict) -> str:
        """Fallback when Qwen is unavailable."""
        clauses = ctx.get("clauses", [])
        high_risk = [c for c in clauses if c["risk_level"] == "HIGH"]
        names = [c["name"] for c in high_risk[:3]]

        return f"""RISK NARRATIVE:
This contract contains {ctx['total_clauses']} clauses with {ctx['high_risk_count']} high-risk provisions.
The risk profile is elevated due to {", ".join(names) if names else "multiple liability provisions"}.

RED FLAGS:
- {clauses[0]['name'] if clauses else 'Indemnification'}: High-risk clause requiring immediate legal review
- {clauses[1]['name'] if len(clauses) > 1 else 'Limitation of Liability'}: Potential exposure with uncapped damages
- Consider jurisdiction-specific enforceability in {ctx.get('jurisdiction', 'the applicable jurisdiction')}

COMPLIANCE INSIGHTS:
Ensure all provisions comply with {ctx.get('jurisdiction', 'applicable')} law, particularly around indemnification caps.

RECOMMENDATION:
Engage legal counsel to review all HIGH-risk clauses before execution."""

    # ── 2. Contract Comparison (GraphRAG Diff) ───────────────────────────────

    def compare_contracts(self, c1_id: str, c2_id: str, diff_summary: Optional[Dict] = None) -> Dict[str, Any]:
        """
        AI-powered comparison of two contracts using graph diff context.
        Accepts optional pre-computed diff_summary from compare_contracts_graph().
        """
        ctx1 = _get_contract_context(c1_id)
        ctx2 = _get_contract_context(c2_id)

        if not ctx1 or not ctx2:
            return {"error": "One or both contracts not found"}

        diff_ctx = ""
        if diff_summary:
            diff_ctx = f"""
GRAPH DIFFERENTIAL ANALYSIS:
- Same clauses: {diff_summary.get('same', 0)} (identical risk profile)
- Modified clauses: {diff_summary.get('modified', 0)} (risk differs ≥10%)
- Missing from Contract B: {diff_summary.get('missing', 0)} clauses
- New in Contract B: {diff_summary.get('new', 0)} clauses
- Diff Score: {diff_summary.get('diff_score', 'N/A')}"""

        prompt = f"""You are a senior legal AI performing a graph-based differential contract analysis.

CONTRACT A — {ctx1['contract_name']}:
- Parties: {ctx1.get('party_a', '')} ↔ {ctx1.get('party_b', '')}
- Clauses: {ctx1['total_clauses']} total, {ctx1['high_risk_count']} HIGH risk
- Top risk clauses:
{_format_clause_list(ctx1.get('clauses', []), max_clauses=5)}

CONTRACT B — {ctx2['contract_name']}:
- Parties: {ctx2.get('party_a', '')} ↔ {ctx2.get('party_b', '')}
- Clauses: {ctx2['total_clauses']} total, {ctx2['high_risk_count']} HIGH risk
- Top risk clauses:
{_format_clause_list(ctx2.get('clauses', []), max_clauses=5)}
{diff_ctx}

TASK: Provide a structured comparison in this format:

COMPARATIVE RISK ASSESSMENT:
[Which contract is riskier and why — 2 sentences]

KEY DIFFERENCES:
- [Most significant clause difference]
- [Second difference]
- [Third difference]

MISSING PROTECTIONS:
[What key protections does the weaker contract lack?]

RECOMMENDATION FOR NEGOTIATION:
[Specific clause changes the team should negotiate]"""

        ai_response = _call_qwen(prompt, max_tokens=550, temperature=0.3)

        if not ai_response:
            ai_response = self._rule_based_comparison(ctx1, ctx2)

        return {
            "contract1_id": c1_id,
            "contract2_id": c2_id,
            "contract1_name": ctx1["contract_name"],
            "contract2_name": ctx2["contract_name"],
            "ai_comparison": ai_response,
            "graph_context": {
                "contract1_clauses": ctx1["total_clauses"],
                "contract2_clauses": ctx2["total_clauses"],
                "contract1_high_risk": ctx1["high_risk_count"],
                "contract2_high_risk": ctx2["high_risk_count"],
            },
            "source": "graphrag_qwen25_compare",
        }

    def _rule_based_comparison(self, ctx1: Dict, ctx2: Dict) -> str:
        riskier = ctx1["contract_name"] if ctx1["high_risk_count"] >= ctx2["high_risk_count"] else ctx2["contract_name"]
        return f"""COMPARATIVE RISK ASSESSMENT:
{riskier} presents higher overall risk with more high-risk clauses.
Both contracts require careful review before execution.

KEY DIFFERENCES:
- Risk profile differs significantly between the two agreements
- Liability exposure varies across termination and indemnification clauses
- Obligation density may affect financial exposure differently

MISSING PROTECTIONS:
The lower-risk contract may lack adequate protections around IP ownership and liability caps.

RECOMMENDATION FOR NEGOTIATION:
Align indemnification caps and termination notice periods across both agreements."""

    # ── 3. Negotiation Recommendations ───────────────────────────────────────

    def get_negotiation_recommendations(
        self,
        contract_id: str,
        negotiation_goals: str = "",
        diff_context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Generate AI negotiation recommendations based on graph analysis.

        Args:
            contract_id: Target contract to negotiate
            negotiation_goals: Free-text goals (e.g. "reduce liability exposure, shorten notice periods")
            diff_context: Optional graph diff result if comparing with another contract
        """
        ctx = _get_contract_context(contract_id)
        if not ctx:
            return {"error": f"Contract {contract_id} not found"}

        high_risk_clauses = [c for c in ctx.get("clauses", []) if c["risk_level"] == "HIGH"]
        medium_risk_clauses = [c for c in ctx.get("clauses", []) if c["risk_level"] == "MEDIUM"]

        goals_section = f"\nNEGOTIATION GOALS: {negotiation_goals}" if negotiation_goals else ""

        modified_clauses = ""
        if diff_context:
            modified = diff_context.get("diff_summary", {}).get("modified", 0)
            missing = diff_context.get("diff_summary", {}).get("missing", 0)
            modified_clauses = f"\nDIFF CONTEXT: {modified} modified clauses, {missing} missing protections identified"

        prompt = f"""You are an expert legal negotiation advisor for PrimeContractAI.

CONTRACT GRAPH ANALYSIS — {ctx['contract_name']}:
- Parties: {ctx.get('party_a', 'Party A')} ↔ {ctx.get('party_b', 'Party B')}
- Jurisdiction: {ctx.get('jurisdiction', 'Unknown')}
- High-Risk Clauses ({len(high_risk_clauses)}):
{_format_clause_list(high_risk_clauses, max_clauses=5)}
- Medium-Risk Clauses ({len(medium_risk_clauses)}):
{_format_clause_list(medium_risk_clauses, max_clauses=3)}
{goals_section}{modified_clauses}

TASK: Provide targeted negotiation strategy in this format:

PRIORITY CLAUSES TO NEGOTIATE:
1. [Highest priority clause + specific redline suggestion]
2. [Second priority clause + counter-proposal language]
3. [Third priority clause + negotiation tactic]

ACCEPTABLE FALLBACK POSITIONS:
- [What you can concede on clause 1]
- [What you can concede on clause 2]

WALK-AWAY CONDITIONS:
[Specific clause conditions that should be deal-breakers]

NEGOTIATION TACTICS:
[2 concrete tactics for this specific contract type and jurisdiction]"""

        ai_response = _call_qwen(prompt, max_tokens=600, temperature=0.35)

        if not ai_response:
            ai_response = self._rule_based_negotiation(ctx, high_risk_clauses)

        # Build structured tips separately
        tips = self._extract_negotiation_tips(high_risk_clauses, ctx)

        return {
            "contract_id": contract_id,
            "contract_name": ctx["contract_name"],
            "ai_recommendations": ai_response,
            "quick_tips": tips,
            "high_risk_count": len(high_risk_clauses),
            "source": "graphrag_qwen25_negotiate",
        }

    def _rule_based_negotiation(self, ctx: Dict, high_risk_clauses: List[Dict]) -> str:
        names = [c["name"] for c in high_risk_clauses[:3]]
        return f"""PRIORITY CLAUSES TO NEGOTIATE:
1. {names[0] if names else 'Indemnification'}: Cap mutual indemnification at contract value; add carve-outs for gross negligence
2. {names[1] if len(names) > 1 else 'Limitation of Liability'}: Insert bilateral liability cap at 12 months of fees
3. {names[2] if len(names) > 2 else 'Termination'}: Negotiate 30→60 day notice period with cure rights

ACCEPTABLE FALLBACK POSITIONS:
- Accept uncapped IP indemnification for 3rd-party IP infringement only
- Allow unilateral termination with 30 days notice in lieu of 60

WALK-AWAY CONDITIONS:
Unlimited liability exposure or unilateral termination without cause and without notice period

NEGOTIATION TACTICS:
1. Lead with jurisdiction-specific enforceability arguments for {ctx.get('jurisdiction', 'applicable')} law
2. Present industry-benchmark comparison data for liability caps"""

    def _extract_negotiation_tips(self, high_risk_clauses: List[Dict], ctx: Dict) -> List[Dict]:
        """Generate quick-action negotiation tips per clause."""
        CLAUSE_TIPS = {
            "Indemnification": {
                "action": "Cap & Carve-out",
                "tip": "Cap mutual indemnification at total contract value. Exclude indirect/consequential damages.",
                "urgency": "HIGH",
            },
            "Limitation of Liability": {
                "action": "Bilateral Cap",
                "tip": "Insert bilateral 12-month fee cap. Remove 'unlimited liability' language.",
                "urgency": "HIGH",
            },
            "Intellectual Property": {
                "action": "Ownership Clarity",
                "tip": "Ensure work-for-hire IP ownership is explicitly defined. Add license-back provisions.",
                "urgency": "HIGH",
            },
            "Termination": {
                "action": "Notice & Cure",
                "tip": "Negotiate 30-day cure period before termination. Add material breach definition.",
                "urgency": "MEDIUM",
            },
            "Confidentiality": {
                "action": "Scope Limit",
                "tip": "Define confidential information narrowly. Set 2-year post-termination limit.",
                "urgency": "MEDIUM",
            },
            "Non-Compete": {
                "action": "Geographic/Time Limit",
                "tip": "Limit scope to direct competitors only, 12-month max, within specific geography.",
                "urgency": "MEDIUM",
            },
            "Payment Terms": {
                "action": "Dispute Mechanism",
                "tip": "Add invoice dispute process. Include late payment interest at prime+2%.",
                "urgency": "LOW",
            },
            "Force Majeure": {
                "action": "Define & Time-box",
                "tip": "Specify qualifying events explicitly. Add 90-day termination right if FM persists.",
                "urgency": "LOW",
            },
        }

        tips = []
        for c in high_risk_clauses[:5]:
            ct = c.get("type", "")
            if ct in CLAUSE_TIPS:
                tips.append({
                    "clause": c["name"],
                    "type": ct,
                    "action": CLAUSE_TIPS[ct]["action"],
                    "tip": CLAUSE_TIPS[ct]["tip"],
                    "urgency": CLAUSE_TIPS[ct]["urgency"],
                    "risk_score": c["risk_score"],
                })

        return tips
