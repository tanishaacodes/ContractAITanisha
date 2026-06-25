"""
Production-Grade Multi-Agent Negotiation Engine
================================================
Architecture:
  4 agents (Buyer, Supplier, Legal, CFO) run in parallel per round.
  Each agent outputs a structured proposal: clause + justification + scores.
  After each round the clause is synthesised, scored, and checked for convergence.
  An in-process memory store (TF-IDF cosine, or sentence-transformers if available)
  allows agents to recall past similar negotiations.
  A lightweight RL bandit loop updates agent strategy weights from deal outcomes.
"""

from __future__ import annotations

import json
import math
import re
import uuid
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")

# ── Default scoring weights (sum to 1.0) ─────────────────────────────

DEFAULT_SCORE_WEIGHTS: Dict[str, float] = {
    "risk_weight":       0.30,   # lower risk → higher score
    "financial_weight":  0.35,   # higher margin/deal value → higher score
    "compliance_weight": 0.20,   # legal compliance → higher score
    "balance_weight":    0.15,   # balanced buyer/supplier positions → higher score
}

# ── Agent definitions ─────────────────────────────────────────────────

AGENT_DEFINITIONS: List[Dict] = [
    {
        "name": "Buyer",
        "color": "blue",
        "emoji": "🛒",
        "objectives": [
            "minimize total contract cost and payment obligations",
            "reduce buyer liability exposure to a fixed cap",
            "add broad termination-for-convenience rights",
            "require strong performance guarantees and SLAs from supplier",
            "maximize credit payment terms (net-60 or longer)",
        ],
        "strategy_style": "cost-aggressive",
    },
    {
        "name": "Supplier",
        "color": "green",
        "emoji": "🏭",
        "objectives": [
            "maximize contract revenue and gross margins",
            "limit liability to a reasonable contract-value cap",
            "protect payment terms (net-30 or shorter)",
            "add change-order rights for out-of-scope work",
            "narrow or remove termination-for-convenience provisions",
        ],
        "strategy_style": "revenue-protective",
    },
    {
        "name": "Legal",
        "color": "purple",
        "emoji": "⚖️",
        "objectives": [
            "ensure enforceability under the applicable jurisdiction",
            "eliminate ambiguous or contradictory language",
            "mandate a governing-law clause and dispute-resolution mechanism",
            "limit regulatory non-compliance exposure",
            "clearly define indemnification scope and IP ownership",
        ],
        "strategy_style": "risk-conservative",
    },
    {
        "name": "CFO",
        "color": "orange",
        "emoji": "💰",
        "objectives": [
            "maximise EBITDA margin impact of the clause",
            "reduce working-capital and cash-cycle requirements",
            "minimise FX and currency-conversion exposure",
            "quantify and cap penalty and late-payment risk",
            "align payment timing with internal budget cycles",
        ],
        "strategy_style": "financially-disciplined",
    },
]


# ── Data classes ──────────────────────────────────────────────────────

@dataclass
class AgentResponse:
    agent_name: str
    agent_color: str
    round_num: int
    proposed_clause: str
    justification: str
    risk_impact: float        # 0 = no added risk,      1 = maximum risk
    financial_impact: float   # -1 = bad for the deal,  1 = great for the deal
    compliance_score: float   # 0 = non-compliant,      1 = fully compliant
    raw_message: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class RoundScore:
    round_num: int
    risk_score: float
    financial_score: float
    compliance_score: float
    balance_score: float
    composite_score: float
    score_weights: Dict


@dataclass
class ClauseVersion:
    round_num: int
    clause_text: str
    changed_by: str
    diff_summary: str


@dataclass
class NegotiationResult:
    session_id: str
    original_clause: str
    final_clause: str
    best_clause: str
    best_round: int
    rounds_completed: int
    converged: bool
    convergence_round: Optional[int]
    agent_responses: List[Dict]
    round_scores: List[Dict]
    clause_history: List[Dict]
    final_score: float
    score_trend: str
    reasoning: str
    agent_strategy_weights: Dict


# ── Agent Memory (TF-IDF with optional sentence-transformers) ─────────

class AgentMemoryStore:
    """In-process memory store for past negotiation sessions."""

    def __init__(self) -> None:
        self._memories: List[Dict] = []
        self._use_st = False
        self._model = None
        self._init_model()

    def _init_model(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            self._model = SentenceTransformer("paraphrase-MiniLM-L3-v2", device='cpu')
            self._use_st = True
            logger.info("AgentMemoryStore: sentence-transformers loaded")
        except Exception:
            logger.info("AgentMemoryStore: falling back to TF-IDF")

    # ── TF-IDF helpers ────────────────────────────────────────────────

    @staticmethod
    def _tfidf(text: str) -> Dict[str, float]:
        words = re.findall(r"\w+", text.lower())
        if not words:
            return {}
        tf: Dict[str, float] = {}
        for w in words:
            tf[w] = tf.get(w, 0) + 1
        n = len(words)
        return {w: c / n for w, c in tf.items()}

    @staticmethod
    def _cosine(v1: Dict, v2: Dict) -> float:
        keys = set(v1) & set(v2)
        if not keys:
            return 0.0
        dot = sum(v1[k] * v2[k] for k in keys)
        m1 = math.sqrt(sum(x * x for x in v1.values()))
        m2 = math.sqrt(sum(x * x for x in v2.values()))
        return dot / (m1 * m2) if m1 and m2 else 0.0

    # ── Public API ────────────────────────────────────────────────────

    def store(self, clause_text: str, outcome: Dict, strategy_used: Dict) -> None:
        entry: Dict = {
            "clause_text": clause_text,
            "outcome": outcome,
            "strategy_used": strategy_used,
            "stored_at": datetime.utcnow().isoformat(),
        }
        if self._use_st and self._model:
            import numpy as np  # type: ignore
            entry["embedding"] = self._model.encode(clause_text[:512]).tolist()
        else:
            entry["tfidf"] = self._tfidf(clause_text)
        self._memories.append(entry)
        if len(self._memories) > 500:
            self._memories = self._memories[-500:]

    def find_similar(self, clause_text: str, top_k: int = 3) -> List[Dict]:
        if not self._memories:
            return []
        if self._use_st and self._model:
            import numpy as np  # type: ignore
            qe = self._model.encode(clause_text[:512])
            scored = []
            for m in self._memories:
                emb = m.get("embedding")
                if not emb:
                    continue
                e = np.array(emb)
                sim = float(np.dot(qe, e) / (np.linalg.norm(qe) * np.linalg.norm(e) + 1e-8))
                scored.append((sim, m))
        else:
            qv = self._tfidf(clause_text)
            scored = [(self._cosine(qv, m.get("tfidf", {})), m) for m in self._memories]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for s, m in scored[:top_k] if s > 0.10]

    def load_from_db(self, db_memories: List[Dict]) -> None:
        """Hydrate from DB-persisted memories on startup."""
        self._memories = db_memories[:500]


_memory_store = AgentMemoryStore()   # module-level singleton


# ── RL Strategy Manager (multi-armed bandit) ──────────────────────────

class RLStrategyManager:
    """
    Maintain per-agent strategy weights and update them from deal outcomes.
    Uses a gradient-free bandit update: reward signal shifts weights toward
    what worked, regresses failures toward the default.
    """

    DEFAULT_WEIGHTS: Dict[str, Dict[str, float]] = {
        "Buyer":    {"aggressiveness": 0.50, "risk_tolerance": 0.30, "cost_focus": 0.80},
        "Supplier": {"aggressiveness": 0.50, "margin_protection": 0.70, "flexibility": 0.50},
        "Legal":    {"aggressiveness": 0.30, "compliance_strictness": 0.90, "risk_aversion": 0.80},
        "CFO":      {"aggressiveness": 0.40, "margin_focus": 0.80, "cashflow_priority": 0.70},
    }

    _learned: Dict[str, Dict[str, float]] = {}

    @classmethod
    def get_weights(cls) -> Dict[str, Dict[str, float]]:
        if cls._learned:
            return {k: dict(v) for k, v in cls._learned.items()}
        return {k: dict(v) for k, v in cls.DEFAULT_WEIGHTS.items()}

    @classmethod
    def update_from_outcome(cls, outcome: Dict, current_weights: Dict) -> Dict:
        """
        Compute a reward in [-1, 1] from the deal outcome and apply a
        gradient-free bandit update to all agent strategy weights.
        """
        deal_outcome   = outcome.get("deal_outcome", "PARTIAL")
        profit_margin  = float(outcome.get("profit_margin", 0.0))
        delay_days     = int(outcome.get("delay_days", 0))
        dispute_count  = int(outcome.get("dispute_count", 0))

        reward = 0.0
        if deal_outcome == "SUCCESS":
            reward += 0.50
        elif deal_outcome == "FAILURE":
            reward -= 0.50
        reward += min(0.30,  profit_margin / 100.0)
        reward -= min(0.20,  delay_days    / 365.0)
        reward -= min(0.10,  dispute_count * 0.05)
        reward  = max(-1.0, min(1.0, reward))

        lr = 0.10
        new_weights: Dict = {}
        for agent, weights in current_weights.items():
            new_agent: Dict = {}
            defaults = cls.DEFAULT_WEIGHTS.get(agent, {})
            for key, val in weights.items():
                default_val = defaults.get(key, 0.50)
                if reward >= 0:
                    new_val = val + lr * reward * (1.0 - val)
                else:
                    new_val = val + lr * reward * (val - default_val)
                new_agent[key] = round(max(0.0, min(1.0, new_val)), 4)
            new_weights[agent] = new_agent

        cls._learned = new_weights
        return new_weights


# ── LLM helpers ───────────────────────────────────────────────────────

def _call_ollama(prompt: str, temperature: float = 0.35) -> str:
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": "qwen2.5:0.5b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": 450},
            },
            timeout=60,
        )
        if resp.status_code == 200:
            return resp.json().get("response", "")
    except Exception as exc:
        logger.warning("Ollama call failed: %s", exc)
    return ""


def _parse_agent_json(raw: str, agent_name: str, current_clause: str) -> Dict:
    """Extract structured JSON from an LLM response with multiple fallbacks."""
    for pattern in [
        r'\{[^{}]*"proposed_clause"[^{}]*\}',
        r'\{.*?"proposed_clause".*?\}',
        r'\{.*\}',
    ]:
        try:
            m = re.search(pattern, raw, re.DOTALL)
            if m:
                obj = json.loads(m.group())
                if "proposed_clause" in obj:
                    return obj
        except Exception:
            pass
    # Hard fallback
    return {
        "proposed_clause": current_clause,
        "justification": (raw.strip()[:300] or f"{agent_name} reviewed the clause."),
        "risk_impact":       0.30,
        "financial_impact":  0.00,
        "compliance_score":  0.60,
    }


# ── Text utilities ────────────────────────────────────────────────────

def _jaccard(a: str, b: str) -> float:
    w1 = set(re.findall(r"\w+", a.lower()))
    w2 = set(re.findall(r"\w+", b.lower()))
    if not w1 or not w2:
        return 0.0
    return len(w1 & w2) / len(w1 | w2)


def _diff_summary(old: str, new: str) -> str:
    ow = set(old.lower().split())
    nw = set(new.lower().split())
    added   = len(nw - ow)
    removed = len(ow - nw)
    if added == 0 and removed == 0:
        return "No significant changes"
    parts = []
    if added:
        parts.append(f"+{added} words")
    if removed:
        parts.append(f"-{removed} words")
    return ", ".join(parts)


# ── Scoring ───────────────────────────────────────────────────────────

def compute_round_score(
    responses: List[AgentResponse],
    weights: Dict,
    round_num: int,
) -> RoundScore:
    if not responses:
        return RoundScore(round_num, 0.5, 0.5, 0.5, 0.5, 0.5, weights)

    risk_score       = sum(r.risk_impact    for r in responses) / len(responses)
    raw_financial    = sum(r.financial_impact for r in responses) / len(responses)
    financial_score  = (raw_financial + 1.0) / 2.0          # normalise -1..1 → 0..1
    compliance_score = sum(r.compliance_score for r in responses) / len(responses)

    buyer = next((r for r in responses if r.agent_name == "Buyer"), None)
    supp  = next((r for r in responses if r.agent_name == "Supplier"), None)
    if buyer and supp:
        balance_score = max(0.0, 1.0 - abs(buyer.financial_impact - supp.financial_impact))
    else:
        balance_score = 0.50

    rw = weights.get("risk_weight",       0.30)
    fw = weights.get("financial_weight",  0.35)
    cw = weights.get("compliance_weight", 0.20)
    bw = weights.get("balance_weight",    0.15)

    composite = (
        rw * (1.0 - risk_score) +
        fw * financial_score    +
        cw * compliance_score   +
        bw * balance_score
    )
    composite = max(0.0, min(1.0, composite))

    return RoundScore(
        round_num        = round_num,
        risk_score       = round(risk_score, 4),
        financial_score  = round(financial_score, 4),
        compliance_score = round(compliance_score, 4),
        balance_score    = round(balance_score, 4),
        composite_score  = round(composite, 4),
        score_weights    = weights,
    )


# ── Single-agent runner ───────────────────────────────────────────────

def _run_single_agent(
    agent_def: Dict,
    current_clause: str,
    round_num: int,
    total_rounds: int,
    history_context: str,
    strategy_weights: Dict,
    similar_memories: List[Dict],
) -> AgentResponse:
    name         = agent_def["name"]
    objectives   = "\n".join(f"  - {o}" for o in agent_def["objectives"])
    aggressiveness = strategy_weights.get(name, {}).get("aggressiveness", 0.50)

    # Memory hint for agent
    memory_hint = ""
    if similar_memories:
        top = similar_memories[0]
        top_outcome = top.get("outcome", {})
        if float(top_outcome.get("final_score", 0)) > 0.60:
            strat = top.get("strategy_used", {}).get(name, {})
            memory_hint = (
                f"\nPast similar negotiation reference:\n"
                f"  Outcome: {top_outcome.get('deal_outcome','N/A')}, "
                f"Score: {top_outcome.get('final_score','N/A')}\n"
                f"  Strategy that worked: {json.dumps(strat)}\n"
            )

    prompt = f"""You are the {name} agent in an AI-driven multi-party contract negotiation.
Strategy style: {agent_def['strategy_style']} | Aggressiveness: {aggressiveness:.2f}

Your objectives:
{objectives}
{memory_hint}
Current clause under negotiation:
---
{current_clause[:600]}
---
Negotiation history:
{history_context[-1400:] if history_context else "(Round 1 – no prior history)"}

Round {round_num} of {total_rounds}. Respond ONLY with valid JSON, no markdown fences.

Return this exact structure:
{{
  "proposed_clause": "<your negotiated clause text, max 400 words>",
  "justification": "<2–3 sentences from your role's perspective>",
  "risk_impact": <0.0–1.0, risk your proposal adds to the deal>,
  "financial_impact": <-1.0–1.0, financial impact for the deal>,
  "compliance_score": <0.0–1.0, how legally compliant your proposal is>
}}"""

    raw = _call_ollama(prompt, temperature=0.35 + aggressiveness * 0.10)
    if not raw:
        raw = f"As the {name} I recommend reviewing this clause carefully."

    parsed = _parse_agent_json(raw, name, current_clause)

    def _clamp(v: object, lo: float, hi: float) -> float:
        try:
            return max(lo, min(hi, float(v)))
        except (TypeError, ValueError):
            return (lo + hi) / 2

    return AgentResponse(
        agent_name       = name,
        agent_color      = agent_def["color"],
        round_num        = round_num,
        proposed_clause  = str(parsed.get("proposed_clause", current_clause))[:800],
        justification    = str(parsed.get("justification", ""))[:400],
        risk_impact      = _clamp(parsed.get("risk_impact",      0.30), 0.0, 1.0),
        financial_impact = _clamp(parsed.get("financial_impact", 0.00), -1.0, 1.0),
        compliance_score = _clamp(parsed.get("compliance_score", 0.60), 0.0, 1.0),
        raw_message      = raw[:600],
    )


# ── Clause synthesis ──────────────────────────────────────────────────

def _synthesise_clause(
    current_clause: str,
    responses: List[AgentResponse],
) -> Tuple[str, str]:
    """
    Select the best agent proposal for this round.
    Scoring: 40% risk-reduction + 30% financial + 30% compliance.
    Falls back to Legal's proposal when no substantive change is detected.
    """
    if not responses:
        return current_clause, "None"

    best_score, best_resp = -1.0, responses[0]
    for r in responses:
        s = (
            0.40 * (1.0 - r.risk_impact) +
            0.30 * (r.financial_impact + 1.0) / 2.0 +
            0.30 * r.compliance_score
        )
        if s > best_score:
            best_score, best_resp = s, r

    # If proposed clause is almost identical to current, prefer Legal
    if _jaccard(current_clause, best_resp.proposed_clause) > 0.95:
        legal = next((r for r in responses if r.agent_name == "Legal"), None)
        if legal and legal.proposed_clause:
            return legal.proposed_clause, "Legal"

    return best_resp.proposed_clause, best_resp.agent_name


# ── Convergence detection ─────────────────────────────────────────────

def _check_convergence(
    clause_history: List[ClauseVersion],
    round_scores: List[RoundScore],
    sim_threshold: float = 0.85,
    delta_threshold: float = 0.02,
) -> Tuple[bool, Optional[int]]:
    if len(clause_history) < 2:
        return False, None

    sim = _jaccard(clause_history[-1].clause_text, clause_history[-2].clause_text)
    if sim >= sim_threshold:
        return True, clause_history[-1].round_num

    if len(round_scores) >= 2:
        delta = abs(round_scores[-1].composite_score - round_scores[-2].composite_score)
        if delta < delta_threshold and round_scores[-1].composite_score > 0.50:
            return True, round_scores[-1].round_num

    return False, None


# ── Best-round selector ───────────────────────────────────────────────

def _select_best(
    round_scores: List[RoundScore],
    clause_history: List[ClauseVersion],
) -> Tuple[int, str]:
    if not round_scores:
        return 1, (clause_history[0].clause_text if clause_history else "")
    best = max(round_scores, key=lambda s: s.composite_score)
    clause = next(
        (cv.clause_text for cv in clause_history if cv.round_num == best.round_num),
        clause_history[-1].clause_text if clause_history else "",
    )
    return best.round_num, clause


def _score_trend(scores: List[RoundScore]) -> str:
    if len(scores) < 2:
        return "stable"
    delta = scores[-1].composite_score - scores[0].composite_score
    if delta > 0.05:
        return "improving"
    if delta < -0.05:
        return "degrading"
    return "stable"


# ── Main engine ───────────────────────────────────────────────────────

class NegotiationEngine:
    """Orchestrates a full multi-agent contract-clause negotiation session."""

    def __init__(
        self,
        score_weights: Optional[Dict] = None,
        strategy_weights: Optional[Dict] = None,
    ) -> None:
        self.score_weights    = score_weights    or dict(DEFAULT_SCORE_WEIGHTS)
        self.strategy_weights = strategy_weights or RLStrategyManager.get_weights()

    def run_session(
        self,
        clause_text: str,
        rounds: int,
        session_id: Optional[str] = None,
        contract_id: Optional[str] = None,
    ) -> NegotiationResult:
        session_id = session_id or str(uuid.uuid4())
        rounds     = max(1, min(rounds, 5))

        current_clause = clause_text.strip()
        all_responses: List[AgentResponse] = []
        round_scores:  List[RoundScore]    = []
        clause_history: List[ClauseVersion] = [
            ClauseVersion(0, current_clause, "Original", "Initial clause")
        ]

        history_ctx = f"Original Clause:\n{current_clause[:500]}\n\n"
        converged        = False
        convergence_round: Optional[int] = None

        similar_mems = _memory_store.find_similar(current_clause, top_k=3)

        for round_num in range(1, rounds + 1):
            snapshot_ctx    = history_ctx        # frozen context for this round
            round_responses: List[AgentResponse] = []

            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(
                        _run_single_agent,
                        agent_def, current_clause, round_num, rounds,
                        snapshot_ctx, self.strategy_weights, similar_mems,
                    ): agent_def
                    for agent_def in AGENT_DEFINITIONS
                }
                for future in as_completed(futures):
                    try:
                        round_responses.append(future.result())
                    except Exception as exc:
                        logger.error("Agent execution error round %d: %s", round_num, exc)

            # Deterministic order: Buyer, Supplier, Legal, CFO
            order = {a["name"]: i for i, a in enumerate(AGENT_DEFINITIONS)}
            round_responses.sort(key=lambda r: order.get(r.agent_name, 99))
            all_responses.extend(round_responses)

            # Score this round
            rs = compute_round_score(round_responses, self.score_weights, round_num)
            round_scores.append(rs)

            # Evolve the clause
            new_clause, driver = _synthesise_clause(current_clause, round_responses)
            clause_history.append(ClauseVersion(
                round_num   = round_num,
                clause_text = new_clause,
                changed_by  = driver,
                diff_summary = _diff_summary(current_clause, new_clause),
            ))
            current_clause = new_clause

            # Append to running context (trimmed to avoid mega-prompts)
            for r in round_responses:
                history_ctx += (
                    f"[R{round_num} {r.agent_name}]: {r.justification}\n"
                    f"  → {r.proposed_clause[:180]}…\n\n"
                )

            converged, convergence_round = _check_convergence(clause_history, round_scores)
            if converged:
                break

        best_round, best_clause = _select_best(round_scores, clause_history)
        final_score  = round_scores[-1].composite_score if round_scores else 0.5
        trend        = _score_trend(round_scores)

        trend_desc = {
            "improving": "Negotiation improved over rounds — strong convergence signal.",
            "stable":    "Negotiation reached a stable plateau.",
            "degrading": "Score declined — manual review recommended.",
        }.get(trend, "")

        best_rs = next((s for s in round_scores if s.round_num == best_round), None)
        score_str = f"{best_rs.composite_score:.1%}" if best_rs else "N/A"
        reasoning = (
            f"Session ran {len(round_scores)} round(s). "
            + (f"Agents converged at round {convergence_round}. " if converged else "Full rounds completed. ")
            + f"Best outcome at round {best_round} (score {score_str}). "
            + trend_desc
        )

        # Store to memory for future recall
        _memory_store.store(
            clause_text  = clause_text,
            outcome      = {
                "deal_outcome": "COMPLETED",
                "final_score":  round(final_score, 4),
                "converged":    converged,
                "rounds":       len(round_scores),
            },
            strategy_used = self.strategy_weights,
        )

        return NegotiationResult(
            session_id        = session_id,
            original_clause   = clause_text[:800],
            final_clause      = current_clause[:800],
            best_clause       = best_clause[:800],
            best_round        = best_round,
            rounds_completed  = len(round_scores),
            converged         = converged,
            convergence_round = convergence_round,
            agent_responses   = [
                {
                    "id":               r.message_id,
                    "agent_name":       r.agent_name,
                    "agent_color":      r.agent_color,
                    "round":            r.round_num,
                    "proposed_clause":  r.proposed_clause,
                    "justification":    r.justification,
                    "risk_impact":      r.risk_impact,
                    "financial_impact": r.financial_impact,
                    "compliance_score": r.compliance_score,
                    "message":          r.justification,   # backward-compat
                    "timestamp":        r.timestamp,
                }
                for r in all_responses
            ],
            round_scores      = [
                {
                    "round":            s.round_num,
                    "risk_score":       s.risk_score,
                    "financial_score":  s.financial_score,
                    "compliance_score": s.compliance_score,
                    "balance_score":    s.balance_score,
                    "composite_score":  s.composite_score,
                }
                for s in round_scores
            ],
            clause_history    = [
                {
                    "round":        cv.round_num,
                    "clause_text":  cv.clause_text[:600],
                    "changed_by":   cv.changed_by,
                    "diff_summary": cv.diff_summary,
                }
                for cv in clause_history
            ],
            final_score             = round(final_score, 4),
            score_trend             = trend,
            reasoning               = reasoning,
            agent_strategy_weights  = self.strategy_weights,
        )
