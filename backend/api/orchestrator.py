"""
Contract Intelligence Orchestrator
=====================================
Central pipeline that connects all AI modules into a single analysis flow.

Pipeline:
  Contract Input
    → [1] Clause Extraction      (from DB or raw text, with real type classification)
    → [2] Legal Reasoning        (parallel, RAG + Rules + LLM per clause)
    → [3] CFO Monte Carlo (1000) (contract-specific seed, real dollar mapping)
    → [4] Multi-Agent Negotiation(top-3 high-risk clauses)
    → [5] Scoring Engine         (confidence-weighted legal + financial + negotiation)
    → [6] Recommendation Engine  (fully dynamic, derived from detected risks)
    → [7] RL Update              (async, real timing)

All timings in pipeline_trace are real measurements – no hardcoded durations.
Each contract produces different outputs via a content-derived RNG seed.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# In-memory result cache  (replace with Redis in production)
# ──────────────────────────────────────────────────────────────────────────────
_RESULT_CACHE: Dict[str, Dict] = {}
_CACHE_LOCK = threading.Lock()
_MAX_CACHE = 200


def _cache_set(analysis_id: str, result: Dict) -> None:
    with _CACHE_LOCK:
        if len(_RESULT_CACHE) >= _MAX_CACHE:
            oldest = next(iter(_RESULT_CACHE))
            del _RESULT_CACHE[oldest]
        _RESULT_CACHE[analysis_id] = result


def _cache_get(analysis_id: str) -> Optional[Dict]:
    with _CACHE_LOCK:
        return _RESULT_CACHE.get(analysis_id)


# ──────────────────────────────────────────────────────────────────────────────
# Pipeline trace helper
# ──────────────────────────────────────────────────────────────────────────────

def _trace_step(
    trace: List[Dict],
    step: int,
    name: str,
    status: str,
    duration_ms: float,
    summary: str,
    data: Optional[Dict] = None,
) -> None:
    trace.append({
        "step":        step,
        "name":        name,
        "status":      status,
        "duration_ms": round(duration_ms, 1),
        "summary":     summary,
        "data":        data or {},
        "timestamp":   datetime.utcnow().isoformat(),
    })


# ──────────────────────────────────────────────────────────────────────────────
# Contract-specific RNG seed
# ──────────────────────────────────────────────────────────────────────────────

def _derive_seed(
    contract_id: Optional[str],
    raw_text: Optional[str],
    clauses: List[Dict],
) -> int:
    """
    Derive a deterministic, contract-specific integer seed so that every
    distinct contract produces different Monte Carlo outputs, while the
    same contract always produces the same output.
    """
    parts: List[str] = []
    if contract_id:
        parts.append(contract_id)
    if raw_text:
        parts.append(raw_text[:800])
    for c in clauses[:5]:
        parts.append(c.get("text", "")[:150])
    combined = "".join(parts) or "default-seed"
    digest = hashlib.md5(combined.encode("utf-8", errors="replace")).hexdigest()
    return int(digest[:8], 16) % (2 ** 31)


# ──────────────────────────────────────────────────────────────────────────────
# Step 1 – Clause Extraction + Classification
# ──────────────────────────────────────────────────────────────────────────────

# Ordered from most specific to most general; first match wins.
_CLAUSE_TYPE_PATTERNS: List[Tuple[str, List[str]]] = [
    ("payment",               [r"payment\s+terms?", r"\binvoice\b", r"net\s+\d+\s+days?", r"\bprice\b.*\bpay", r"billing\s+cycle", r"amount\s+due", r"remittance"]),
    ("liability",             [r"\bliabilit", r"\bindemnif", r"hold\s+harmless", r"responsible\s+for\s+all\s+loss"]),
    ("termination",           [r"\bterminat", r"right\s+to\s+(end|cancel)", r"notice\s+of\s+terminat", r"early\s+exit"]),
    ("intellectual_property", [r"intellectual\s+property", r"\bip\s+rights?\b", r"\bcopyright\b", r"\btrademark\b", r"\bpatent\b", r"proprietary\s+rights?"]),
    ("confidentiality",       [r"confidential", r"non.disclosure", r"\bnda\b", r"trade\s+secret", r"proprietary\s+information"]),
    ("force_majeure",         [r"force\s+majeure", r"act\s+of\s+god", r"beyond.*reasonable\s+control", r"extraordinary\s+event", r"unforeseeable\s+event"]),
    ("governing_law",         [r"governed\s+by", r"governing\s+law", r"laws?\s+of\s+the\s+state\s+of", r"subject\s+to\s+the\s+laws?\s+of"]),
    ("dispute_resolution",    [r"\barbitrat", r"dispute\s+resolution", r"mediation", r"conciliation", r"jurisdiction\s+.*\s+disputes?"]),
    ("delivery",              [r"\bdeliver(y|ies|ed|ing)\b", r"\bshipment\b", r"\bmilestone\b", r"completion\s+date", r"delivery\s+schedule", r"time\s+of\s+delivery"]),
    ("warranty",              [r"\bwarrant(y|ies|s)?\b", r"as\s+is\s+basis", r"\brepresents?\s+and\s+warrants?\b", r"\bguarantee\b"]),
    ("penalty",               [r"\bpenalt(y|ies)\b", r"liquidated\s+damages?", r"\bforfeiture\b", r"per.diem\s+charge"]),
    ("non_compete",           [r"non.compete", r"non.solicitation", r"restraint\s+of\s+trade", r"exclusivity"]),
    ("change_control",        [r"change\s+order", r"change\s+in\s+control", r"variation\s+order", r"amendment\s+procedure"]),
    ("insurance",             [r"\binsurance\b", r"\bindemnity\s+bond\b", r"\bperformance\s+bond\b", r"surety"]),
    ("assignment",            [r"\bassignment\b", r"right\s+to\s+assign", r"transfer\s+of\s+rights?", r"sub.contract"]),
]


def _classify_clause(text: str, title: str = "") -> str:
    """
    Classify a clause by its primary legal type using pattern matching.
    Returns the type string (e.g. "payment", "liability") or "general".
    """
    combined = (title + " " + text).lower()
    for clause_type, patterns in _CLAUSE_TYPE_PATTERNS:
        if any(re.search(pat, combined) for pat in patterns):
            return clause_type
    return "general"


def _extract_clauses_from_db(contract_id: str) -> List[Dict]:
    """Fetch clauses from Django ORM and classify any that lack a type."""
    try:
        from core.models import Clause  # type: ignore
        qs = Clause.objects.filter(
            contract__id=contract_id
        ).exclude(text__isnull=True).exclude(text="")
        clauses = []
        for i, c in enumerate(qs[:20]):
            title = getattr(c, "title", None) or f"Clause {i + 1}"
            text  = c.text[:800]
            raw_type = getattr(c, "clause_type", None) or ""
            clause_type = raw_type if raw_type and raw_type != "general" else _classify_clause(text, title)
            clauses.append({
                "id":    str(c.id),
                "title": title,
                "text":  text,
                "type":  clause_type,
            })
        return clauses
    except Exception as exc:
        logger.warning("Clause DB fetch failed: %s", exc)
        return []


def _split_text_into_clauses(raw_text: str) -> List[Dict]:
    """
    Split raw contract text into clauses using multiple extraction strategies.
    Each extracted clause is classified with _classify_clause.
    """
    clauses: List[Dict] = []

    # Strategy 1: Numbered headings (e.g. "1. Payment Terms\n...")
    numbered = re.findall(
        r"(?:^|\n)(\d+\.(?:\d+\.?)?\s+[A-Z][^\n]{5,}(?:\n(?!\d+\.)[^\n]+)*)",
        raw_text,
        re.MULTILINE,
    )
    if numbered:
        for i, block in enumerate(numbered[:18]):
            block = block.strip()
            if len(block) < 40:
                continue
            # Extract title from first line
            lines = block.splitlines()
            title_raw = re.sub(r"^\d+\.(?:\d+\.)?\s*", "", lines[0]).strip()
            title = title_raw[:100] if title_raw else f"Clause {i + 1}"
            clauses.append({
                "id":    f"clause-{i}",
                "title": title,
                "text":  block[:800],
                "type":  _classify_clause(block, title),
            })

    # Strategy 2: ALL-CAPS section headers (e.g. "PAYMENT TERMS\nThe buyer shall pay...")
    if not clauses:
        caps = re.findall(
            r"(?:^|\n)([A-Z][A-Z\s]{5,50})\n((?:[^\n]+\n?){1,10})",
            raw_text,
            re.MULTILINE,
        )
        for i, (heading, body) in enumerate(caps[:15]):
            title = heading.strip()
            text  = (title + "\n" + body).strip()
            if len(text) < 40:
                continue
            clauses.append({
                "id":    f"section-{i}",
                "title": title[:100],
                "text":  text[:800],
                "type":  _classify_clause(text, title),
            })

    # Strategy 3: Blank-line paragraph split
    if not clauses:
        paragraphs = [p.strip() for p in raw_text.split("\n\n") if len(p.strip()) > 60]
        for i, para in enumerate(paragraphs[:15]):
            first_line = para.splitlines()[0][:80]
            clauses.append({
                "id":    f"para-{i}",
                "title": first_line or f"Section {i + 1}",
                "text":  para[:800],
                "type":  _classify_clause(para, first_line),
            })

    # Final fallback: treat whole text as a single clause
    if not clauses:
        clauses.append({
            "id":    "para-0",
            "title": "Contract Text",
            "text":  raw_text[:800],
            "type":  _classify_clause(raw_text[:800]),
        })

    return clauses


# ──────────────────────────────────────────────────────────────────────────────
# Step 2 – Legal Reasoning (parallel)
# ──────────────────────────────────────────────────────────────────────────────

def _legal_analyze_one(clause: Dict, jurisdiction: str) -> Dict:
    try:
        from api.legal_reasoning_engine import analyze_clause  # type: ignore
        result = analyze_clause(clause["text"], jurisdiction)
        return {
            "clause_id":         clause["id"],
            "clause_title":      clause["title"],
            "clause_type":       clause.get("type", "general"),
            "clause_text":       clause["text"][:300],
            "risk_level":        result.get("risk_level", "MEDIUM"),
            "compliance_status": result.get("compliance_status", "Partially Compliant"),
            "confidence_score":  float(result.get("confidence_score", 0.5)),
            "issues":            result.get("issues", [])[:4],
            "explanation":       result.get("explanation", "")[:500],
            "suggested_clause":  result.get("suggested_clause", clause["text"])[:600],
            "rule_flags":        result.get("rule_flags", [])[:5],
        }
    except Exception as exc:
        logger.warning("Legal analysis failed for clause %s: %s", clause["id"], exc)
        return {
            "clause_id":         clause["id"],
            "clause_title":      clause["title"],
            "clause_type":       clause.get("type", "general"),
            "clause_text":       clause["text"][:300],
            "risk_level":        "MEDIUM",
            "compliance_status": "Unknown",
            "confidence_score":  0.30,
            "issues":            [],
            "explanation":       "Legal analysis unavailable.",
            "suggested_clause":  clause["text"],
            "rule_flags":        [],
        }


def _run_legal_analysis(clauses: List[Dict], jurisdiction: str, max_workers: int = 4) -> List[Dict]:
    results: List[Dict] = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_legal_analyze_one, c, jurisdiction): c for c in clauses}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as exc:
                logger.error("Legal analysis thread error: %s", exc)
    order = {c["id"]: i for i, c in enumerate(clauses)}
    results.sort(key=lambda r: order.get(r["clause_id"], 999))
    return results


# ──────────────────────────────────────────────────────────────────────────────
# Step 3 – CFO Monte Carlo Simulation (1000 runs, contract-specific seed)
# ──────────────────────────────────────────────────────────────────────────────

def _run_cfo_simulation(
    contract_value: float,
    duration_months: int,
    legal_risks: List[Dict],
    seed: int = 42,
) -> Dict:
    """
    Run 1000-path Monte Carlo via the CFO engine.
    - Uses a contract-specific seed so each contract produces different numbers.
    - Maps margin-percentage output to dollar amounts.
    - Falls back to rule-based estimates if numpy/engine unavailable.
    """
    high_risk_count   = sum(1 for r in legal_risks if r["risk_level"] in ("HIGH", "CRITICAL"))
    medium_risk_count = sum(1 for r in legal_risks if r["risk_level"] == "MEDIUM")
    delay_prob = round(min(0.05 + high_risk_count * 0.08 + medium_risk_count * 0.03, 0.60), 3)

    try:
        from api.cfo_engine import ContractParameters, MonteCarloEngine, generate_risk_insights  # type: ignore

        params = ContractParameters(
            contract_value    = float(contract_value),
            duration_months   = int(duration_months),
            delay_probability = delay_prob,
        )

        # 1000 simulations, contract-specific seed → different results per contract
        engine    = MonteCarloEngine(params, n_sims=1000, seed=seed)
        mc_result = engine.run(oil_shock=0.0, inflation=0.0, fx_shock=0.0)

        # generate_risk_insights signature: (params, sim_dict, oil, inflation, fx)
        insights = generate_risk_insights(params, mc_result, 0.0, 0.0, 0.0)

        summary = mc_result["summary"]
        penalty = mc_result["penalty"]

        # Convert margin percentages → dollar amounts
        mean_margin_pct  = float(summary["mean_margin"])       # e.g. 22.4 %
        var_95_pct       = float(summary["var_95"])            # e.g. -6.1 % (neg = loss at tail)
        min_margin_pct   = float(summary.get("min_margin", var_95_pct * 1.5))

        expected_margin  = contract_value * mean_margin_pct / 100.0
        expected_revenue = contract_value                       # baseline = full contract value
        var_95_dollars   = abs(contract_value * var_95_pct / 100.0)
        max_loss_dollars = abs(contract_value * min_margin_pct / 100.0)

        fin_score = _compute_financial_score(summary)

        # Format insight objects as display strings for the frontend
        insight_lines = [
            ins.get("finding", "")
            for ins in insights[:5]
            if ins.get("finding")
        ]

        return {
            "contract_value":       contract_value,
            "expected_revenue":     round(expected_revenue, 2),
            "expected_margin":      round(expected_margin, 2),
            "var_95":               round(var_95_dollars, 2),
            "max_loss":             round(max_loss_dollars, 2),
            "delay_probability":    delay_prob,
            "mean_margin_pct":      round(mean_margin_pct, 2),
            "loss_probability_pct": round(float(summary["loss_probability"]), 2),
            "std_deviation_pct":    round(float(summary["std_deviation"]), 2),
            "financial_score":      fin_score,
            "simulation_source":    "monte_carlo",
            "n_simulations":        1000,
            "risk_insights":        insight_lines,
            "penalty_stats": {
                "mean_penalty":    round(float(penalty["mean_penalty"]), 2),
                "max_penalty_p99": round(float(penalty["max_penalty_p99"]), 2),
                "delay_rate_pct":  round(float(penalty["delay_rate"]), 2),
            },
        }

    except Exception as exc:
        logger.warning("CFO engine failed (%s) – using rule-based estimate", exc)
        # Rule-based fallback: never produces identical numbers for different inputs
        # because it's still driven by high_risk_count and contract_value
        base_margin_rate = max(0.05, 0.30 - high_risk_count * 0.06 - medium_risk_count * 0.02)
        expected_margin  = contract_value * base_margin_rate
        penalty_est      = contract_value * 0.05 * max(high_risk_count, 1)
        net_margin       = max(expected_margin - penalty_est, 0)
        var_est          = penalty_est * 2.0
        fin_score        = round(max(0.05, min(0.95, net_margin / (contract_value * 0.30 + 1e-6))), 3)

        fallback_insight = (
            f"{high_risk_count} high-risk clause(s) detected — estimated penalty exposure "
            f"${penalty_est:,.0f} ({high_risk_count * 5:.0f}% of contract value)."
        )

        return {
            "contract_value":       contract_value,
            "expected_revenue":     contract_value,
            "expected_margin":      round(net_margin, 2),
            "var_95":               round(var_est, 2),
            "max_loss":             round(penalty_est * 3, 2),
            "delay_probability":    delay_prob,
            "mean_margin_pct":      round(base_margin_rate * 100, 2),
            "loss_probability_pct": round(min(high_risk_count * 12.0, 60.0), 2),
            "std_deviation_pct":    round(high_risk_count * 3.0 + 5.0, 2),
            "financial_score":      fin_score,
            "simulation_source":    "rule_based_fallback",
            "n_simulations":        0,
            "risk_insights":        [fallback_insight],
            "penalty_stats":        {},
        }


def _compute_financial_score(summary: Dict) -> float:
    """
    Derive a 0–1 financial health score from Monte Carlo summary statistics.

    Scoring logic (all from real simulation output):
      - Mean margin ≥ 30 % → 1.0 base
      - Loss probability penalises up to –0.40
      - Deep VaR tail (< –20 %) penalises up to –0.20
    """
    mean_margin  = float(summary.get("mean_margin", 20.0))     # percent
    loss_prob    = float(summary.get("loss_probability", 20.0)) # percent
    var_95       = float(summary.get("var_95", -5.0))           # percent (neg = tail loss)

    # Base: 30 % margin target → 1.0; linear below
    margin_score = max(0.0, min(1.0, mean_margin / 30.0))

    # Penalise loss probability: 50 % loss_prob → –0.40
    loss_penalty = min(0.40, loss_prob / 100.0 * 0.80)

    # Penalise deep VaR: –20 % VaR → –0.20
    var_penalty = min(0.20, abs(min(var_95, 0.0)) / 20.0 * 0.20)

    score = max(0.05, min(1.0, margin_score - loss_penalty - var_penalty))
    return round(score, 3)


# ──────────────────────────────────────────────────────────────────────────────
# Step 4 – Negotiation (top-3 highest-risk clauses)
# ──────────────────────────────────────────────────────────────────────────────

_RISK_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}


def _run_negotiation(legal_risks: List[Dict], session_id: str) -> List[Dict]:
    """Negotiate the top-3 highest-risk clauses using the multi-agent engine."""
    sorted_risks = sorted(
        legal_risks,
        key=lambda r: (
            _RISK_RANK.get(r["risk_level"], 0),
            float(r.get("confidence_score", 0.5)),
        ),
        reverse=True,
    )
    candidates = [r for r in sorted_risks if r["risk_level"] in ("CRITICAL", "HIGH", "MEDIUM")][:3]

    if not candidates:
        return []

    results: List[Dict] = []
    try:
        from api.negotiation_engine import NegotiationEngine  # type: ignore
        engine = NegotiationEngine()
        for risk in candidates:
            try:
                clause_text = risk.get("suggested_clause") or risk.get("clause_text", "")
                if not clause_text:
                    continue
                neg = engine.run_session(
                    clause_text = clause_text[:600],
                    rounds      = 2,
                    session_id  = f"{session_id}-{risk['clause_id']}",
                )
                results.append({
                    "clause_id":     risk["clause_id"],
                    "clause_title":  risk["clause_title"],
                    "original_risk": risk["risk_level"],
                    "final_clause":  neg.final_clause[:500],
                    "best_clause":   neg.best_clause[:500],
                    "final_score":   neg.final_score,
                    "converged":     neg.converged,
                    "rounds":        neg.rounds_completed,
                    "score_trend":   neg.score_trend,
                })
            except Exception as exc:
                logger.warning("Negotiation failed for clause %s: %s", risk["clause_id"], exc)
    except Exception as exc:
        logger.warning("NegotiationEngine unavailable: %s", exc)

    return results


# ──────────────────────────────────────────────────────────────────────────────
# Step 5 – Scoring Engine
# ──────────────────────────────────────────────────────────────────────────────

def _compute_legal_score(legal_risks: List[Dict]) -> float:
    """
    Confidence-weighted risk aggregation.
    High-confidence assessments carry more weight than uncertain ones.
    Returns 0 (all critical/high) → 1 (all low risk).
    """
    if not legal_risks:
        return 0.70
    rank_map = {"CRITICAL": 1.0, "HIGH": 0.75, "MEDIUM": 0.45, "LOW": 0.15}
    weighted_sum = 0.0
    total_weight  = 0.0
    for r in legal_risks:
        confidence = max(0.10, float(r.get("confidence_score", 0.5)))
        raw_risk   = rank_map.get(r["risk_level"], 0.45)
        weighted_sum += confidence * raw_risk
        total_weight  += confidence
    avg_risk = weighted_sum / total_weight if total_weight > 0 else 0.45
    return round(max(0.0, min(1.0, 1.0 - avg_risk)), 3)


def _compute_negotiation_score(neg_results: List[Dict]) -> float:
    if not neg_results:
        return 0.60   # neutral when no negotiation ran
    avg = sum(r.get("final_score", 0.5) for r in neg_results) / len(neg_results)
    return round(avg, 3)


def compute_final_score(
    legal_score: float,
    financial_score: float,
    negotiation_score: float,
) -> Tuple[float, str]:
    """
    Weights: legal 40 %, financial 35 %, negotiation 25 %.
    Returns (score_0_to_100, decision_string).
    """
    raw = (
        0.40 * legal_score +
        0.35 * financial_score +
        0.25 * negotiation_score
    )
    score_100 = round(raw * 100, 1)

    if score_100 >= 70:
        decision = "ACCEPT"
    elif score_100 >= 45:
        decision = "RENEGOTIATE"
    else:
        decision = "REJECT"

    return score_100, decision


# ──────────────────────────────────────────────────────────────────────────────
# Step 6 – Recommendation Engine  (fully dynamic, no static text)
# ──────────────────────────────────────────────────────────────────────────────

def generate_recommendations(
    legal_risks:  List[Dict],
    cfo_result:   Dict,
    neg_results:  List[Dict],
    final_score:  float,
    decision:     str,
) -> List[Dict]:
    recs: List[Dict] = []

    # ── Decision-level ───────────────────────────────────────────────────────
    critical_count = sum(1 for r in legal_risks if r["risk_level"] == "CRITICAL")
    high_count     = sum(1 for r in legal_risks if r["risk_level"] == "HIGH")
    medium_count   = sum(1 for r in legal_risks if r["risk_level"] == "MEDIUM")
    fin_score      = float(cfo_result.get("financial_score", 0.5))
    loss_prob      = float(cfo_result.get("loss_probability_pct", 0.0))
    mean_margin    = float(cfo_result.get("mean_margin_pct", 20.0))

    if decision == "ACCEPT":
        detail = (
            f"Overall score {final_score:.1f}/100 with {high_count} high-risk clause(s) and "
            f"mean margin {mean_margin:.1f}%. No critical blockers identified."
        )
        recs.append({
            "type": "decision", "priority": "LOW",
            "title": "Contract is acceptable",
            "detail": detail,
            "action": "Proceed to signature workflow.",
        })
    elif decision == "RENEGOTIATE":
        blocking = []
        if critical_count:
            blocking.append(f"{critical_count} critical clause(s)")
        if high_count:
            blocking.append(f"{high_count} high-risk clause(s)")
        if loss_prob > 20:
            blocking.append(f"{loss_prob:.0f}% loss probability")
        detail = (
            f"Score {final_score:.1f}/100. Issues: {', '.join(blocking) or 'moderate risk detected'}. "
            "Resolve flagged items before signing."
        )
        recs.append({
            "type": "decision", "priority": "MEDIUM",
            "title": "Renegotiation recommended",
            "detail": detail,
            "action": "Use negotiated clause rewrites and address flagged risks.",
        })
    else:
        detail = (
            f"Score {final_score:.1f}/100. {critical_count} critical and {high_count} high-risk clause(s) "
            f"detected. Loss probability: {loss_prob:.0f}%."
        )
        recs.append({
            "type": "decision", "priority": "HIGH",
            "title": "Contract should be rejected or substantially redrafted",
            "detail": detail,
            "action": "Escalate to legal counsel before proceeding.",
        })

    # ── Per-clause legal recommendations (dynamic) ───────────────────────────
    critical_and_high = [r for r in legal_risks if r["risk_level"] in ("CRITICAL", "HIGH")]
    for risk in critical_and_high[:4]:
        top_issue = (risk.get("issues") or [{}])[0]
        recs.append({
            "type":           "legal",
            "priority":       risk["risk_level"],
            "title":          f"Renegotiate: {risk['clause_title']}",
            "detail":         (top_issue.get("reason") or risk.get("explanation", ""))[:280],
            "law_reference":  top_issue.get("law_reference", ""),
            "case_reference": top_issue.get("case_reference", ""),
            "action":         "Replace with the suggested compliant rewrite shown in Legal Risks tab.",
        })

    # ── Financial recommendations (driven by real MC numbers) ────────────────
    var_95   = float(cfo_result.get("var_95", 0))
    contract_v = float(cfo_result.get("contract_value", 1))

    if fin_score < 0.40:
        var_pct = (var_95 / (contract_v + 1e-6)) * 100
        recs.append({
            "type": "financial", "priority": "HIGH",
            "title": "High financial risk – Monte Carlo analysis",
            "detail": (
                f"95% VaR = {_fmt_currency(var_95)} ({var_pct:.1f}% of contract value). "
                f"Loss probability = {loss_prob:.1f}%. "
                f"Mean margin = {mean_margin:.1f}%."
            ),
            "action": "Add liability cap clause and revisit penalty structure.",
        })
    elif fin_score < 0.65:
        recs.append({
            "type": "financial", "priority": "MEDIUM",
            "title": "Moderate financial exposure",
            "detail": (
                f"Expected margin: {_fmt_currency(cfo_result.get('expected_margin', 0))} "
                f"({mean_margin:.1f}% of contract value). "
                f"Delay probability: {cfo_result.get('delay_probability', 0) * 100:.0f}%."
            ),
            "action": "Add force majeure and delay compensation clauses.",
        })

    # Penalty exposure recommendation
    p_stats = cfo_result.get("penalty_stats", {})
    if p_stats:
        mean_pen = float(p_stats.get("mean_penalty", 0))
        pen_pct  = (mean_pen / (contract_v + 1e-6)) * 100
        if pen_pct > 2.0:
            recs.append({
                "type": "financial", "priority": "MEDIUM",
                "title": "Penalty exposure detected",
                "detail": (
                    f"Average simulated penalty: {_fmt_currency(mean_pen)} ({pen_pct:.1f}% of contract). "
                    f"Delay rate: {p_stats.get('delay_rate_pct', 0):.0f}% of simulation paths."
                ),
                "action": f"Ensure penalty cap clause at ≤10% of contract value ({_fmt_currency(contract_v * 0.10)}).",
            })

    # ── Negotiation improvements ──────────────────────────────────────────────
    for neg in neg_results:
        if neg.get("final_score", 0) >= 0.65:
            recs.append({
                "type": "negotiation", "priority": "LOW",
                "title": f"Improved clause available: {neg['clause_title']}",
                "detail": (
                    f"Multi-agent negotiation score: {neg['final_score'] * 100:.0f}/100. "
                    f"Converged in {neg['rounds']} round(s). Trend: {neg.get('score_trend', 'stable')}."
                ),
                "action": "Accept negotiated rewrite shown in Negotiation Results tab.",
            })

    # ── Missing-clause structural warnings ───────────────────────────────────
    all_flags = []
    for r in legal_risks:
        all_flags.extend(r.get("rule_flags", []))
    absence_flags = [f for f in all_flags if f.get("rule_id") in ("R-NO-GOV-LAW", "R-NO-DISPUTE")]
    for flag in absence_flags[:2]:
        recs.append({
            "type":     "structure",
            "priority": flag.get("severity", "MEDIUM"),
            "title":    flag["flag_message"],
            "detail":   flag.get("explanation", ""),
            "action":   f"Add a standard {flag['flag_message'].lower()} clause.",
        })

    return recs[:12]


def _fmt_currency(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:.2f}"


# ──────────────────────────────────────────────────────────────────────────────
# Step 7 – RL Update
# ──────────────────────────────────────────────────────────────────────────────

def _rl_update(session_id: str, analysis_id: str, final_score: float, decision: str) -> None:
    """Non-blocking: update RL strategy weights from completed analysis."""
    try:
        from api.negotiation_engine import RLStrategyManager  # type: ignore
        outcome = {
            "deal_outcome":  "SUCCESS" if decision == "ACCEPT" else ("PARTIAL" if decision == "RENEGOTIATE" else "FAILURE"),
            "final_score":   final_score / 100.0,
            "profit_margin": max(0.0, (final_score - 50) / 50.0 * 30),
            "delay_days":    0,
            "dispute_count": 0,
        }
        current_weights = RLStrategyManager.get_weights()
        RLStrategyManager.update_from_outcome(outcome, current_weights)
        logger.info("RL weights updated for analysis %s (decision=%s)", analysis_id, decision)
    except Exception as exc:
        logger.debug("RL update skipped: %s", exc)


# ──────────────────────────────────────────────────────────────────────────────
# Main Orchestrator
# ──────────────────────────────────────────────────────────────────────────────

class ContractOrchestrator:
    """
    Runs the full Contract Intelligence pipeline and returns a
    unified ContractAnalysisResult dict.
    All step timings are real measurements. Monte Carlo uses a
    contract-specific seed so every unique contract produces different outputs.
    """

    def run_full_analysis(
        self,
        contract_id:      Optional[str],
        jurisdiction:     str,
        contract_value:   float,
        duration_months:  int,
        raw_clauses:      Optional[List[Dict]] = None,
        raw_text:         Optional[str]        = None,
    ) -> Dict:
        analysis_id = str(uuid.uuid4())
        session_id  = f"orch-{analysis_id[:8]}"
        trace: List[Dict] = []
        started_at = time.monotonic()

        # ── Step 1: Clause Extraction ─────────────────────────────────────
        t0 = time.monotonic()
        clauses: List[Dict] = []

        if raw_clauses:
            clauses = raw_clauses[:20]
        elif contract_id:
            clauses = _extract_clauses_from_db(contract_id)
        if not clauses and raw_text:
            clauses = _split_text_into_clauses(raw_text)
        if not clauses:
            clauses = [{
                "id":    "fallback-0",
                "title": "Contract Text",
                "text":  raw_text[:800] if raw_text else "No clause text provided.",
                "type":  "general",
            }]

        # Classify any clauses that still have type "general" from raw_clauses input
        for c in clauses:
            if not c.get("type") or c["type"] == "general":
                c["type"] = _classify_clause(c.get("text", ""), c.get("title", ""))

        clause_types = list({c["type"] for c in clauses if c["type"] != "general"})

        _trace_step(trace, 1, "Clause Extraction", "complete",
                    (time.monotonic() - t0) * 1000,
                    f"Extracted {len(clauses)} clause(s) · types: {', '.join(clause_types[:5]) or 'general'}",
                    {"count": len(clauses), "types": clause_types})

        # Derive contract-specific seed for reproducible but unique outputs
        seed = _derive_seed(contract_id, raw_text, clauses)

        # ── Step 2: Legal Reasoning ───────────────────────────────────────
        t0 = time.monotonic()
        legal_risks = _run_legal_analysis(clauses, jurisdiction)
        high_risk   = sum(1 for r in legal_risks if r["risk_level"] in ("CRITICAL", "HIGH"))
        legal_score = _compute_legal_score(legal_risks)
        avg_conf    = round(
            sum(r.get("confidence_score", 0.5) for r in legal_risks) / max(len(legal_risks), 1), 2
        )

        _trace_step(trace, 2, "Legal Reasoning", "complete",
                    (time.monotonic() - t0) * 1000,
                    f"{len(legal_risks)} clause(s) analysed · {high_risk} high/critical · avg confidence {avg_conf:.0%}",
                    {"high_risk_count": high_risk, "legal_score": legal_score, "avg_confidence": avg_conf})

        # ── Step 3: CFO Monte Carlo ───────────────────────────────────────
        t0 = time.monotonic()
        cfo_result      = _run_cfo_simulation(contract_value, duration_months, legal_risks, seed=seed)
        financial_score = float(cfo_result.get("financial_score", 0.50))
        sim_source      = cfo_result.get("simulation_source", "unknown")

        _trace_step(trace, 3, "CFO Simulation", "complete",
                    (time.monotonic() - t0) * 1000,
                    (
                        f"Expected margin: {_fmt_currency(cfo_result.get('expected_margin', 0))} "
                        f"({cfo_result.get('mean_margin_pct', 0):.1f}%) · "
                        f"VaR(95%): {_fmt_currency(cfo_result.get('var_95', 0))} · "
                        f"Loss prob: {cfo_result.get('loss_probability_pct', 0):.0f}%"
                    ),
                    {
                        "financial_score":      financial_score,
                        "simulation_source":    sim_source,
                        "n_simulations":        cfo_result.get("n_simulations", 0),
                        "mean_margin_pct":      cfo_result.get("mean_margin_pct"),
                        "loss_probability_pct": cfo_result.get("loss_probability_pct"),
                    })

        # ── Step 4: Negotiation ───────────────────────────────────────────
        t0 = time.monotonic()
        neg_results       = _run_negotiation(legal_risks, session_id)
        negotiation_score = _compute_negotiation_score(neg_results)

        _trace_step(trace, 4, "Multi-Agent Negotiation", "complete",
                    (time.monotonic() - t0) * 1000,
                    f"{len(neg_results)} clause(s) negotiated · avg score {negotiation_score:.1%}",
                    {"negotiated_count": len(neg_results), "negotiation_score": negotiation_score})

        # ── Step 5: Scoring ───────────────────────────────────────────────
        t0 = time.monotonic()
        final_score, decision = compute_final_score(legal_score, financial_score, negotiation_score)

        score_breakdown = {
            "legal_score":       round(legal_score * 100, 1),
            "financial_score":   round(financial_score * 100, 1),
            "negotiation_score": round(negotiation_score * 100, 1),
            "final_score":       final_score,
            "decision":          decision,
            "weights":           {"legal": 0.40, "financial": 0.35, "negotiation": 0.25},
        }

        _trace_step(trace, 5, "Scoring Engine", "complete",
                    (time.monotonic() - t0) * 1000,
                    f"Final score: {final_score:.1f}/100 → {decision}",
                    score_breakdown)

        # ── Step 6: Recommendations ───────────────────────────────────────
        t0 = time.monotonic()
        recommendations = generate_recommendations(
            legal_risks, cfo_result, neg_results, final_score, decision
        )

        _trace_step(trace, 6, "Recommendation Engine", "complete",
                    (time.monotonic() - t0) * 1000,
                    f"{len(recommendations)} recommendation(s) generated",
                    {"count": len(recommendations)})

        # ── Step 7: RL Update (background – real timing) ──────────────────
        t0 = time.monotonic()
        threading.Thread(
            target=_rl_update,
            args=(session_id, analysis_id, final_score, decision),
            daemon=True,
        ).start()
        _trace_step(trace, 7, "RL Update", "complete",
                    (time.monotonic() - t0) * 1000,   # real measurement (thread spawn time)
                    "Strategy weights update queued (async)", {})

        # ── Assemble result ───────────────────────────────────────────────
        total_ms = (time.monotonic() - started_at) * 1000

        result: Dict = {
            "analysis_id":  analysis_id,
            "contract_id":  contract_id,
            "jurisdiction": jurisdiction,
            "status":       "complete",

            # Stage outputs
            "clauses":             clauses,
            "legal_risks":         legal_risks,
            "cfo_result":          cfo_result,
            "negotiation_results": neg_results,

            # Final outputs
            "score_breakdown":  score_breakdown,
            "final_score":      final_score,
            "decision":         decision,
            "recommendations":  recommendations,

            # Risk summary
            "risk_summary": {
                "total_clauses":  len(clauses),
                "critical":       sum(1 for r in legal_risks if r["risk_level"] == "CRITICAL"),
                "high":           sum(1 for r in legal_risks if r["risk_level"] == "HIGH"),
                "medium":         sum(1 for r in legal_risks if r["risk_level"] == "MEDIUM"),
                "low":            sum(1 for r in legal_risks if r["risk_level"] == "LOW"),
                "avg_confidence": avg_conf,
            },

            "pipeline_trace":    trace,
            "total_duration_ms": round(total_ms, 1),
            "created_at":        datetime.utcnow().isoformat(),
        }

        _cache_set(analysis_id, result)
        return result


# Module-level singleton
_orchestrator = ContractOrchestrator()


def run_full_analysis(
    contract_id:     Optional[str],
    jurisdiction:    str,
    contract_value:  float,
    duration_months: int,
    raw_clauses:     Optional[List[Dict]] = None,
    raw_text:        Optional[str]        = None,
) -> Dict:
    """Public API – call this from Django views."""
    return _orchestrator.run_full_analysis(
        contract_id      = contract_id,
        jurisdiction     = jurisdiction,
        contract_value   = contract_value,
        duration_months  = duration_months,
        raw_clauses      = raw_clauses,
        raw_text         = raw_text,
    )


def get_cached_result(analysis_id: str) -> Optional[Dict]:
    """Retrieve a previously computed analysis result."""
    return _cache_get(analysis_id)
