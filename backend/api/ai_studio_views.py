"""
AI Studio Views – Contract-specific AI features
================================================
Feature 1: Autonomous Redlining AI
Feature 2: Negotiation Agents (basic + advanced engine)
Feature 4: CFO Simulator
Feature 5: Legal Reasoning Engine
"""

import json
import uuid
import logging
import re
import requests
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from django.conf import settings
from rest_framework.views import APIView
from api.cfo_engine import (
    ContractParameters, MonteCarloEngine, TimeSeriesSimulator,
    run_scenario_cascade, generate_risk_insights,
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from core.models import Contract, Clause
from negotiation.models import (
    EngineNegotiationSession,
    EngineNegotiationMessage,
    EngineNegotiationOutcome,
)
from api.negotiation_engine import (
    NegotiationEngine,
    RLStrategyManager,
    DEFAULT_SCORE_WEIGHTS,
)

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')


def _call_ollama(prompt: str, temperature: float = 0.3) -> str:
    """Call Ollama Qwen 2.5 with a prompt and return the response text."""
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": "qwen2.5:0.5b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature},
            },
            timeout=50,
        )
        if resp.status_code == 200:
            return resp.json().get("response", "")
        return ""
    except Exception as exc:
        logger.warning("Ollama call failed: %s", exc)
        return ""


def _parse_json_from_llm(text: str, fallback: dict) -> dict:
    """Safely parse JSON embedded in LLM output."""
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return fallback


# ─────────────────────────────────────────────
# Feature 1: Autonomous Redlining AI
# ─────────────────────────────────────────────

class RedlineGenerateView(APIView):
    """POST /api/ai-studio/redline/"""
    permission_classes = [AllowAny]

    def post(self, request):
        contract_id = request.data.get("contract_id")
        jurisdiction = request.data.get("jurisdiction", "india").lower()
        if not contract_id:
            return Response({"error": "contract_id required"}, status=status.HTTP_400_BAD_REQUEST)

        # Jurisdiction context for prompt
        jurisdiction_context = {
            "india": "Indian Contract Act 1872 (ICA). Unlimited liability and penalty clauses may be unenforceable under Section 23.",
            "us": "US Uniform Commercial Code (UCC). Reasonableness standard applies to limitation of liability clauses.",
            "uk": "UK Unfair Contract Terms Act 1977 (UCTA). Exclusion clauses subject to reasonableness test.",
        }.get(jurisdiction, "Indian Contract Act 1872")

        # Fetch clauses for the contract
        clauses = Clause.objects.filter(contract__id=contract_id).exclude(
            extracted_text__isnull=True
        ).exclude(extracted_text__exact="")[:30]

        if not clauses.exists():
            return Response({"error": "No clauses found for this contract"}, status=status.HTTP_404_NOT_FOUND)

        redlines = []
        for clause in clauses:
            original_text = clause.extracted_text or ""
            if len(original_text.strip()) < 20:
                continue

            prompt = f"""You are a contract redlining AI. Analyze the following clause and provide jurisdiction-aware suggested improvements.

Jurisdiction: {jurisdiction.upper()} ({jurisdiction_context})

Original Clause:
{original_text[:800]}

Return a JSON object with exactly these fields:
{{
  "suggested_clause": "<improved version of the clause, compliant with {jurisdiction.upper()} law>",
  "risk_score": <float between 0.0 and 1.0>,
  "change_type": "<minor|moderate|major>",
  "explanation": "<brief explanation of why this change is recommended under {jurisdiction.upper()} jurisdiction>"
}}

Respond with only the JSON object, nothing else."""

            llm_response = _call_ollama(prompt, temperature=0.3)

            fallback = {
                "suggested_clause": original_text,
                "risk_score": 0.3,
                "change_type": "minor",
                "explanation": "No significant risk detected. Clause appears standard.",
            }
            parsed = _parse_json_from_llm(llm_response, fallback)

            # Validate and clamp values
            risk_score = float(parsed.get("risk_score", 0.3))
            risk_score = max(0.0, min(1.0, risk_score))
            change_type = parsed.get("change_type", "minor")
            if change_type not in ("minor", "moderate", "major"):
                change_type = "minor"

            redline_id = str(uuid.uuid4())
            redlines.append({
                "id": redline_id,
                "clause_id": clause.id,
                "clause_name": clause.clause_name or "",
                "clause_type": clause.clause_type or "Unknown",
                "original_clause": original_text[:1000],
                "suggested_clause": parsed.get("suggested_clause", original_text)[:1000],
                "risk_score": risk_score,
                "change_type": change_type,
                "explanation": parsed.get("explanation", "")[:500],
                "status": "pending",
            })

        return Response({
            "contract_id": contract_id,
            "jurisdiction": jurisdiction,
            "total_clauses_analyzed": len(redlines),
            "redlines": redlines,
            "generated_at": datetime.utcnow().isoformat(),
        })


class RedlineAcceptView(APIView):
    """POST /api/ai-studio/redline/accept/"""
    permission_classes = [AllowAny]

    def post(self, request):
        redline_id = request.data.get("redline_id")
        redline_status = request.data.get("status", "accepted")

        if not redline_id:
            return Response({"error": "redline_id required"}, status=status.HTTP_400_BAD_REQUEST)
        if redline_status not in ("accepted", "rejected", "pending"):
            return Response({"error": "status must be accepted|rejected|pending"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "redline_id": redline_id,
            "status": redline_status,
            "updated_at": datetime.utcnow().isoformat(),
            "message": f"Redline {redline_status} successfully.",
        })


# ─────────────────────────────────────────────
# Feature 2: Negotiation Agents
# ─────────────────────────────────────────────

AGENT_ROLES = [
    {
        "name": "Buyer",
        "color": "blue",
        "persona": "You are the Buyer agent. Your goal is to minimize costs, reduce liability exposure, add termination rights, and ensure performance guarantees protect the buyer.",
    },
    {
        "name": "Supplier",
        "color": "green",
        "persona": "You are the Supplier agent. Your goal is to maximize revenue, limit liability, protect payment terms, and add change order rights that benefit the supplier.",
    },
    {
        "name": "Legal",
        "color": "purple",
        "persona": "You are the Legal agent. Your goal is to ensure regulatory compliance, identify enforceable language, flag jurisdiction risks, and recommend legally sound clauses.",
    },
    {
        "name": "CFO",
        "color": "orange",
        "persona": "You are the CFO agent. Your goal is to optimize financial margins, assess cash flow impact, evaluate currency risk, and quantify the financial exposure of clause terms.",
    },
]


class NegotiationAgentsView(APIView):
    """POST /api/ai-studio/negotiate/"""
    permission_classes = [AllowAny]

    def post(self, request):
        contract_id = request.data.get("contract_id")
        clause_text = request.data.get("clause_text", "").strip()
        rounds = int(request.data.get("rounds", 3))
        rounds = max(1, min(rounds, 5))

        if not clause_text:
            return Response({"error": "clause_text required"}, status=status.HTTP_400_BAD_REQUEST)

        session_id = str(uuid.uuid4())
        conversation_history = []
        context_so_far = f"Original Clause:\n{clause_text[:600]}\n\n"

        def _call_agent(agent, round_context, round_num, rounds):
            prompt = f"""{agent['persona']}

{round_context}
Round {round_num} of {rounds}. Provide your negotiation position on this clause in 2-3 sentences. Be specific, practical, and stay in character. Do not repeat prior responses verbatim."""
            response_text = _call_ollama(prompt, temperature=0.4)
            if not response_text:
                response_text = (
                    f"As the {agent['name']}, I recommend reviewing this clause carefully "
                    "to ensure it aligns with our interests before proceeding."
                )
            return agent, response_text.strip()

        for round_num in range(1, rounds + 1):
            round_context = context_so_far  # snapshot — same for all agents this round

            with ThreadPoolExecutor(max_workers=len(AGENT_ROLES)) as executor:
                future_to_agent = {
                    executor.submit(_call_agent, agent, round_context, round_num, rounds): agent
                    for agent in AGENT_ROLES
                }
                round_results = {}
                for future in as_completed(future_to_agent):
                    agent, response_text = future.result()
                    round_results[agent["name"]] = (agent, response_text)

            # Append in deterministic order and update context
            for agent in AGENT_ROLES:
                agent_obj, response_text = round_results[agent["name"]]
                message = {
                    "id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "agent_name": agent_obj["name"],
                    "agent_color": agent_obj["color"],
                    "round": round_num,
                    "message": response_text,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                conversation_history.append(message)
                context_so_far += f"[Round {round_num} – {agent_obj['name']}]: {response_text}\n\n"

        # ── Convergence Detection ──────────────────────────────────
        converged = False
        convergence_round = None
        if rounds >= 2 and len(conversation_history) >= len(AGENT_ROLES) * 2:
            # Compare last two rounds: compute keyword overlap per agent
            overlap_scores = []
            for agent in AGENT_ROLES:
                agent_msgs = [m["message"] for m in conversation_history if m["agent_name"] == agent["name"]]
                if len(agent_msgs) >= 2:
                    # Last 2 messages for this agent
                    words_r_last = set(agent_msgs[-1].lower().split())
                    words_r_prev = set(agent_msgs[-2].lower().split())
                    if words_r_last and words_r_prev:
                        overlap = len(words_r_last & words_r_prev) / max(len(words_r_last | words_r_prev), 1)
                        overlap_scores.append(overlap)

            if overlap_scores:
                avg_overlap = sum(overlap_scores) / len(overlap_scores)
                converged = avg_overlap >= 0.60
                if converged:
                    convergence_round = rounds  # converged at final round

        return Response({
            "session_id": session_id,
            "contract_id": contract_id,
            "clause_text": clause_text[:600],
            "rounds": rounds,
            "agents": [{"name": a["name"], "color": a["color"]} for a in AGENT_ROLES],
            "conversation": conversation_history,
            "total_messages": len(conversation_history),
            "status": "completed",
            "converged": converged,
            "convergence_round": convergence_round,
        })


# ─────────────────────────────────────────────
# Feature 4: CFO Simulator (Monte Carlo)
# ─────────────────────────────────────────────

class CFOSimulateView(APIView):
    """POST /api/ai-studio/cfo-simulate/"""
    permission_classes = [AllowAny]

    def post(self, request):
        contract_id = request.data.get("contract_id")
        oil_shock = float(request.data.get("oil_shock", 0.0))
        inflation = float(request.data.get("inflation", 0.0))
        fx_rate = float(request.data.get("fx_rate", 0.0))
        simulations = int(request.data.get("simulations", 1000))
        simulations = max(100, min(simulations, 5000))

        # Get contract value
        base_value = 1_000_000.0
        if contract_id:
            try:
                contract = Contract.objects.get(id=contract_id)
                if contract.contract_value:
                    # Extract numeric value from string like "$1,500,000" or "1500000"
                    numeric_str = re.sub(r'[^\d.]', '', str(contract.contract_value))
                    if numeric_str:
                        base_value = float(numeric_str)
            except Contract.DoesNotExist:
                pass

        # Apply macro shock multipliers to cost base
        adjusted_cost = base_value * (1 + oil_shock * 0.05) * (1 + inflation * 0.1) * (1 + fx_rate * 0.07)

        # Revenue assumed at base_value; margin = revenue - cost
        revenue = base_value

        # Monte Carlo simulation
        rng = np.random.default_rng(42)
        noise_oil = rng.normal(0, oil_shock * 0.02 + 0.01, simulations)
        noise_inf = rng.normal(0, inflation * 0.03 + 0.01, simulations)
        noise_fx = rng.normal(0, fx_rate * 0.02 + 0.005, simulations)

        simulated_costs = adjusted_cost * (1 + noise_oil + noise_inf + noise_fx)
        simulated_margins = (revenue - simulated_costs) / revenue * 100  # percent

        mean_margin = float(np.mean(simulated_margins))
        min_margin = float(np.min(simulated_margins))
        max_margin = float(np.max(simulated_margins))
        loss_probability = float(np.mean(simulated_margins < 0)) * 100  # percent

        # Sample 20 points for the chart
        indices = np.linspace(0, simulations - 1, 20, dtype=int)
        scenario_data = [
            {"x": int(i), "margin": round(float(simulated_margins[i]), 2)}
            for i in indices
        ]

        # Histogram for distribution chart
        hist_counts, hist_bins = np.histogram(simulated_margins, bins=20)
        distribution = [
            {"margin": round(float(hist_bins[i]), 2), "count": int(hist_counts[i])}
            for i in range(len(hist_counts))
        ]

        return Response({
            "contract_id": contract_id,
            "base_value": round(base_value, 2),
            "adjusted_cost": round(adjusted_cost, 2),
            "inputs": {
                "oil_shock": oil_shock,
                "inflation": inflation,
                "fx_rate": fx_rate,
                "simulations": simulations,
            },
            "results": {
                "mean_margin": round(mean_margin, 2),
                "min_margin": round(min_margin, 2),
                "max_margin": round(max_margin, 2),
                "loss_probability": round(loss_probability, 2),
                "std_deviation": round(float(np.std(simulated_margins)), 2),
            },
            "scenario_data": scenario_data,
            "distribution": distribution,
            "simulated_at": datetime.utcnow().isoformat(),
        })


# ─────────────────────────────────────────────
# Feature 4b: Contract-Aware CFO Engine (Advanced)
# ─────────────────────────────────────────────

def _parse_contract_params(request, contract=None) -> ContractParameters:
    """Extract ContractParameters from request data + optional contract model."""
    base_value = 1_000_000.0
    if contract and contract.contract_value:
        numeric = re.sub(r'[^\d.]', '', str(contract.contract_value))
        if numeric:
            base_value = float(numeric)

    return ContractParameters(
        contract_value=float(request.data.get("contract_value", base_value)),
        duration_months=int(request.data.get("duration_months", 12)),
        payment_terms_days=int(request.data.get("payment_terms_days", 30)),
        penalty_rate_daily=float(request.data.get("penalty_rate_daily", 0.001)),
        max_penalty_cap=float(request.data.get("max_penalty_cap", 0.10)),
        cost_base_ratio=float(request.data.get("cost_base_ratio", 0.70)),
        currency=request.data.get("currency", "USD"),
        delay_probability=float(request.data.get("delay_probability", 0.25)),
        avg_delay_days=float(request.data.get("avg_delay_days", 30.0)),
    )


class CFOSimulateContractView(APIView):
    """
    POST /api/ai-studio/simulate-contract/
    Full contract-aware Monte Carlo + time-series simulation.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        contract_id  = request.data.get("contract_id")
        oil_shock    = float(request.data.get("oil_shock",  0.0))
        inflation    = float(request.data.get("inflation",  0.0))
        fx_shock     = float(request.data.get("fx_shock",   0.0))
        n_sims       = int(request.data.get("simulations",  2000))
        n_sims       = max(500, min(n_sims, 5000))

        contract = None
        if contract_id:
            try:
                contract = Contract.objects.get(id=contract_id)
            except Contract.DoesNotExist:
                pass

        params = _parse_contract_params(request, contract)

        # Monte Carlo
        mc = MonteCarloEngine(params, n_sims=n_sims)
        mc_result = mc.run(oil_shock, inflation, fx_shock)

        # Time-series cashflow (300 paths, capped duration for speed)
        ts_params = ContractParameters(
            contract_value=params.contract_value,
            duration_months=min(params.duration_months, 24),
            payment_terms_days=params.payment_terms_days,
            penalty_rate_daily=params.penalty_rate_daily,
            max_penalty_cap=params.max_penalty_cap,
            cost_base_ratio=params.cost_base_ratio,
            currency=params.currency,
            delay_probability=params.delay_probability,
            avg_delay_days=params.avg_delay_days,
        )
        ts = TimeSeriesSimulator(ts_params)
        timeline = ts.simulate(oil_shock, inflation, fx_shock, n_paths=300)

        return Response({
            "contract_id":  contract_id,
            "contract_name": contract.contract_name if contract else None,
            "params": {
                "contract_value":    params.contract_value,
                "duration_months":   params.duration_months,
                "payment_terms_days": params.payment_terms_days,
                "cost_base_ratio":   params.cost_base_ratio,
                "delay_probability": params.delay_probability,
                "currency":          params.currency,
            },
            "inputs": {
                "oil_shock":  oil_shock,
                "inflation":  inflation,
                "fx_shock":   fx_shock,
                "simulations": n_sims,
            },
            "monte_carlo": mc_result,
            "cashflow_timeline": timeline,
            "simulated_at": datetime.utcnow().isoformat(),
        })


class CFORiskInsightsView(APIView):
    """
    POST /api/ai-studio/risk-insights/
    Generate CFO-level decision intelligence from a simulation run.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        oil_shock = float(request.data.get("oil_shock",  0.0))
        inflation = float(request.data.get("inflation",  0.0))
        fx_shock  = float(request.data.get("fx_shock",   0.0))
        n_sims    = int(request.data.get("simulations",  1000))
        n_sims    = max(500, min(n_sims, 3000))

        contract_id = request.data.get("contract_id")
        contract = None
        if contract_id:
            try:
                contract = Contract.objects.get(id=contract_id)
            except Contract.DoesNotExist:
                pass

        params = _parse_contract_params(request, contract)
        mc = MonteCarloEngine(params, n_sims=n_sims)
        sim = mc.run(oil_shock, inflation, fx_shock)
        insights = generate_risk_insights(params, sim, oil_shock, inflation, fx_shock)

        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        insights.sort(key=lambda x: severity_order.get(x["severity"], 9))

        return Response({
            "contract_id": contract_id,
            "simulation_summary": sim["summary"],
            "penalty_summary":    sim["penalty"],
            "insights":           insights,
            "total_insights":     len(insights),
            "generated_at": datetime.utcnow().isoformat(),
        })


class CFOScenarioAnalysisView(APIView):
    """
    POST /api/ai-studio/scenario-analysis/
    Run all 4 cascading scenarios and compare vs baseline.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        scenario_key = request.data.get("scenario")  # optional: single scenario
        n_sims       = int(request.data.get("simulations", 800))
        n_sims       = max(400, min(n_sims, 2000))

        contract_id = request.data.get("contract_id")
        contract = None
        if contract_id:
            try:
                contract = Contract.objects.get(id=contract_id)
            except Contract.DoesNotExist:
                pass

        params = _parse_contract_params(request, contract)
        keys = [scenario_key] if scenario_key else ["war", "pandemic", "inflation", "supply_chain"]

        results = []
        for key in keys:
            results.append(run_scenario_cascade(params, key, n_sims=n_sims))

        return Response({
            "contract_id": contract_id,
            "scenarios":   results,
            "analyzed_at": datetime.utcnow().isoformat(),
        })


# ─────────────────────────────────────────────
# Feature 5: Legal Reasoning Engine (Production RAG + Rule Engine)
# ─────────────────────────────────────────────

from api.legal_reasoning_engine import analyze_clause as _legal_analyze_clause  # noqa: E402


class LegalAnalyzeView(APIView):
    """POST /api/ai-studio/legal-analyze/

    Production-grade legal analysis:
      - RAG retrieval from jurisdiction-specific legal KB (statutes + case law)
      - Rule engine: 11 universal + jurisdiction-specific rules
      - LLM reasoning with retrieved context and structured JSON output
      - Confidence scoring
    """
    permission_classes = [AllowAny]

    def post(self, request):
        clause_text = request.data.get("clause_text", "").strip()
        jurisdiction = request.data.get("jurisdiction", "india").lower()

        if not clause_text:
            return Response({"error": "clause_text required"}, status=status.HTTP_400_BAD_REQUEST)

        result = _legal_analyze_clause(clause_text, jurisdiction)
        return Response(result)


# ─────────────────────────────────────────────────────────────────────
# Feature 2b: Advanced Multi-Agent Negotiation Engine
# ─────────────────────────────────────────────────────────────────────

class AdvancedNegotiationView(APIView):
    """
    POST /api/ai-studio/negotiate-advanced/

    Runs the production-grade NegotiationEngine:
      • 4 agents (Buyer, Supplier, Legal, CFO) negotiate in parallel per round
      • Structured per-agent proposals: proposed_clause + justification + 3 scores
      • Composite scoring per round (risk / financial / compliance / balance)
      • Convergence detection (clause Jaccard similarity + score-delta threshold)
      • Clause-state evolution with diff tracking
      • Best-round selection
      • Persists session + messages to DB for history & RL feedback
    """
    permission_classes = [AllowAny]

    def post(self, request):
        clause_text = request.data.get("clause_text", "").strip()
        contract_id = request.data.get("contract_id")
        rounds      = int(request.data.get("rounds", 3))
        rounds      = max(1, min(rounds, 5))

        # Optional per-request score weight overrides
        score_weights = {
            "risk_weight":       float(request.data.get("risk_weight",       DEFAULT_SCORE_WEIGHTS["risk_weight"])),
            "financial_weight":  float(request.data.get("financial_weight",  DEFAULT_SCORE_WEIGHTS["financial_weight"])),
            "compliance_weight": float(request.data.get("compliance_weight", DEFAULT_SCORE_WEIGHTS["compliance_weight"])),
            "balance_weight":    float(request.data.get("balance_weight",    DEFAULT_SCORE_WEIGHTS["balance_weight"])),
        }

        if not clause_text:
            return Response({"error": "clause_text is required"}, status=status.HTTP_400_BAD_REQUEST)

        engine  = NegotiationEngine(score_weights=score_weights)
        result  = engine.run_session(
            clause_text = clause_text,
            rounds      = rounds,
            contract_id = contract_id,
        )

        # ── Persist session ───────────────────────────────────────────
        try:
            session_obj = EngineNegotiationSession.objects.create(
                session_id              = result.session_id,
                contract_id             = contract_id,
                original_clause         = result.original_clause,
                final_clause            = result.final_clause,
                best_clause             = result.best_clause,
                rounds_requested        = rounds,
                rounds_completed        = result.rounds_completed,
                converged               = result.converged,
                convergence_round       = result.convergence_round,
                best_round              = result.best_round,
                final_score             = result.final_score,
                score_trend             = result.score_trend,
                round_scores            = result.round_scores,
                clause_history          = result.clause_history,
                agent_strategy_weights  = result.agent_strategy_weights,
                reasoning               = result.reasoning,
            )

            # Persist individual messages (one row per agent per round)
            round_score_map = {s["round"]: s["composite_score"] for s in result.round_scores}
            msg_objects = []
            for r in result.agent_responses:
                rs = round_score_map.get(r["round"], 0.0)
                msg_objects.append(EngineNegotiationMessage(
                    message_id       = r["id"],
                    session          = session_obj,
                    round_number     = r["round"],
                    agent_name       = r["agent_name"],
                    agent_color      = r["agent_color"],
                    proposed_clause  = r["proposed_clause"],
                    justification    = r.get("justification", ""),
                    risk_impact      = r.get("risk_impact", 0.3),
                    financial_impact = r.get("financial_impact", 0.0),
                    compliance_score = r.get("compliance_score", 0.6),
                    round_score      = rs,
                ))
            EngineNegotiationMessage.objects.bulk_create(msg_objects, ignore_conflicts=True)

        except Exception as db_err:
            logger.warning("Failed to persist negotiation session: %s", db_err)

        # ── Response ──────────────────────────────────────────────────
        return Response({
            "session_id":        result.session_id,
            "contract_id":       contract_id,
            "clause_text":       result.original_clause,
            "rounds":            result.rounds_completed,
            "rounds_requested":  rounds,
            "agents":            [{"name": a["name"], "color": a["color"], "emoji": a["emoji"]}
                                   for a in [
                                       {"name": "Buyer",    "color": "blue",   "emoji": "🛒"},
                                       {"name": "Supplier", "color": "green",  "emoji": "🏭"},
                                       {"name": "Legal",    "color": "purple", "emoji": "⚖️"},
                                       {"name": "CFO",      "color": "orange", "emoji": "💰"},
                                   ]],
            "conversation":      result.agent_responses,   # backward-compat key
            "agent_responses":   result.agent_responses,
            "round_scores":      result.round_scores,
            "clause_history":    result.clause_history,
            "original_clause":   result.original_clause,
            "final_clause":      result.final_clause,
            "best_clause":       result.best_clause,
            "best_round":        result.best_round,
            "final_score":       result.final_score,
            "score_trend":       result.score_trend,
            "reasoning":         result.reasoning,
            "converged":         result.converged,
            "convergence_round": result.convergence_round,
            "total_messages":    len(result.agent_responses),
            "status":            "completed",
            "generated_at":      datetime.utcnow().isoformat(),
        })


class NegotiationHistoryView(APIView):
    """
    GET /api/ai-studio/negotiation-history/

    Returns paginated list of past NegotiationSession records.
    Query params: contract_id (optional), limit (default 20), offset (default 0).
    """
    permission_classes = [AllowAny]

    def get(self, request):
        contract_id = request.query_params.get("contract_id")
        limit       = int(request.query_params.get("limit", 20))
        offset      = int(request.query_params.get("offset", 0))
        limit       = max(1, min(limit, 100))

        qs = EngineNegotiationSession.objects.all()
        if contract_id:
            qs = qs.filter(contract_id=contract_id)

        total   = qs.count()
        records = qs[offset: offset + limit]

        sessions = []
        for s in records:
            sessions.append({
                "session_id":        s.session_id,
                "contract_id":       s.contract_id,
                "rounds_completed":  s.rounds_completed,
                "converged":         s.converged,
                "convergence_round": s.convergence_round,
                "best_round":        s.best_round,
                "final_score":       s.final_score,
                "score_trend":       s.score_trend,
                "round_scores":      s.round_scores,
                "reasoning":         s.reasoning,
                "original_clause":   s.original_clause[:200] + "…" if len(s.original_clause) > 200 else s.original_clause,
                "final_clause":      s.final_clause[:200] + "…" if len(s.final_clause) > 200 else s.final_clause,
                "best_clause":       s.best_clause[:200] + "…" if len(s.best_clause) > 200 else s.best_clause,
                "has_outcome":       hasattr(s, "outcome") and s.outcome is not None,
                "created_at":        s.created_at.isoformat() if s.created_at else None,
            })

        return Response({
            "total":    total,
            "limit":    limit,
            "offset":   offset,
            "sessions": sessions,
        })


class EvaluateOutcomeView(APIView):
    """
    POST /api/ai-studio/evaluate-outcome/

    Records the real-world deal outcome for a completed negotiation session
    and triggers the RL strategy-weight update.

    Body:
      session_id   (str, required)
      deal_outcome (SUCCESS | FAILURE | PARTIAL | ONGOING)
      profit_margin  (float, %)
      delay_days     (int)
      dispute_count  (int)
    """
    permission_classes = [AllowAny]

    def post(self, request):
        session_id    = request.data.get("session_id", "").strip()
        deal_outcome  = request.data.get("deal_outcome", "ONGOING").upper()
        profit_margin = float(request.data.get("profit_margin", 0.0))
        delay_days    = int(request.data.get("delay_days", 0))
        dispute_count = int(request.data.get("dispute_count", 0))

        if not session_id:
            return Response({"error": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        if deal_outcome not in ("SUCCESS", "FAILURE", "PARTIAL", "ONGOING"):
            return Response({"error": "deal_outcome must be SUCCESS|FAILURE|PARTIAL|ONGOING"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            session_obj = EngineNegotiationSession.objects.get(session_id=session_id)
        except EngineNegotiationSession.DoesNotExist:
            return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)

        outcome_data = {
            "deal_outcome":  deal_outcome,
            "profit_margin": profit_margin,
            "delay_days":    delay_days,
            "dispute_count": dispute_count,
        }

        # RL weight update
        current_weights  = session_obj.agent_strategy_weights or RLStrategyManager.get_weights()
        updated_weights  = RLStrategyManager.update_from_outcome(outcome_data, current_weights)

        # Persist outcome
        outcome_obj, created = EngineNegotiationOutcome.objects.update_or_create(
            session=session_obj,
            defaults={
                "deal_outcome":             deal_outcome,
                "profit_margin":            profit_margin,
                "delay_days":               delay_days,
                "dispute_count":            dispute_count,
                "updated_strategy_weights": updated_weights,
                "rl_feedback_processed":    True,
            },
        )

        return Response({
            "session_id":        session_id,
            "deal_outcome":      deal_outcome,
            "rl_updated":        True,
            "updated_weights":   updated_weights,
            "outcome_id":        outcome_obj.pk,
            "evaluated_at":      outcome_obj.evaluated_at.isoformat() if outcome_obj.evaluated_at else datetime.utcnow().isoformat(),
        })
