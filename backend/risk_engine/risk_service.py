"""
Risk Scoring Engine
====================
Standalone risk computation module that scores contract clauses and
overall contracts based on multiple risk dimensions:
  - Clause-level: penalty exposure, termination, IP, liability
  - Contract-level: aggregate risk, party balance, obligation density
"""

import re
import logging

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Risk signal keywords (weighted)
# ─────────────────────────────────────────────
RISK_SIGNALS = {
    "penalty": {
        "keywords": [
            "penalty", "liquidated damages", "ld clause", "late payment", "breach",
            "default", "failure to deliver", "non-performance",
        ],
        "weight": 0.25,
    },
    "termination": {
        "keywords": [
            "termination", "terminate", "cancellation", "void", "nullify",
            "rescind", "exit clause", "break clause",
        ],
        "weight": 0.20,
    },
    "liability": {
        "keywords": [
            "indemnify", "indemnification", "unlimited liability", "consequential",
            "indirect damages", "hold harmless", "gross negligence",
        ],
        "weight": 0.25,
    },
    "ip_risk": {
        "keywords": [
            "intellectual property", "ip assignment", "work for hire", "proprietary",
            "trade secret", "patent", "copyright transfer",
        ],
        "weight": 0.15,
    },
    "exclusivity": {
        "keywords": [
            "exclusive", "non-compete", "non-solicitation", "restraint of trade",
            "exclusivity period",
        ],
        "weight": 0.10,
    },
    "ambiguity": {
        "keywords": [
            "reasonable", "best efforts", "as soon as possible", "material breach",
            "substantially", "at our discretion",
        ],
        "weight": 0.05,
    },
}

PROTECTIVE_SIGNALS = {
    "keywords": [
        "force majeure", "limitation of liability", "cap on liability",
        "dispute resolution", "arbitration", "mutual agreement", "good faith",
        "cure period", "notice period",
    ],
    "weight": -0.15,  # reduces risk score
}


# ─────────────────────────────────────────────
# Core scoring functions
# ─────────────────────────────────────────────
def compute_clause_risk(clause_text: str) -> dict:
    """
    Score an individual clause for risk.

    Returns:
        {
            "score": float (0.0–1.0),
            "level": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
            "signals": [str, ...],
            "protective_factors": [str, ...]
        }
    """
    if not clause_text:
        return {"score": 0.0, "level": "LOW", "signals": [], "protective_factors": []}

    text_lower = clause_text.lower()
    total_score = 0.0
    triggered_signals = []
    protective_factors = []

    # Check risk signals
    for category, config in RISK_SIGNALS.items():
        matches = [kw for kw in config["keywords"] if kw in text_lower]
        if matches:
            total_score += config["weight"]
            triggered_signals.extend([f"{category}: {m}" for m in matches[:2]])

    # Check protective signals (reduce score)
    protective_matches = [kw for kw in PROTECTIVE_SIGNALS["keywords"] if kw in text_lower]
    if protective_matches:
        total_score += PROTECTIVE_SIGNALS["weight"]  # negative weight
        protective_factors = protective_matches[:3]

    score = max(0.0, min(1.0, total_score))
    level = _score_to_level(score)

    return {
        "score": round(score, 4),
        "level": level,
        "signals": triggered_signals[:5],
        "protective_factors": protective_factors,
    }


def compute_risk_score(text: str, contract_value: float = 0.0, clause_count: int = 0) -> dict:
    """
    Compute overall risk score for a contract or text block.

    Args:
        text: Contract or clause text
        contract_value: Contract value in local currency (for financial exposure)
        clause_count: Total number of clauses (for obligation density)

    Returns:
        {
            "overall_score": float,
            "risk_level": str,
            "financial_exposure_factor": float,
            "obligation_density_factor": float,
            "clause_risk": dict,
            "summary": str
        }
    """
    clause_risk = compute_clause_risk(text)

    # Financial exposure factor: higher contract value = higher stakes
    financial_factor = 0.0
    if contract_value > 0:
        if contract_value >= 100_000_000:    # 10 Cr+
            financial_factor = 0.20
        elif contract_value >= 10_000_000:   # 1 Cr+
            financial_factor = 0.12
        elif contract_value >= 1_000_000:    # 10L+
            financial_factor = 0.06
        else:
            financial_factor = 0.02

    # Obligation density: many clauses = complex contract
    density_factor = 0.0
    if clause_count > 50:
        density_factor = 0.10
    elif clause_count > 20:
        density_factor = 0.05
    elif clause_count > 10:
        density_factor = 0.02

    overall = min(1.0, clause_risk["score"] + financial_factor + density_factor)

    return {
        "overall_score": round(overall, 4),
        "risk_level": _score_to_level(overall),
        "financial_exposure_factor": round(financial_factor, 4),
        "obligation_density_factor": round(density_factor, 4),
        "clause_risk": clause_risk,
        "summary": _generate_summary(overall, clause_risk["signals"]),
    }


def score_multiple_clauses(clauses: list) -> dict:
    """
    Score a list of clause text strings.

    Returns:
        {
            "clause_scores": [dict, ...],
            "aggregate_score": float,
            "high_risk_count": int,
            "critical_count": int,
        }
    """
    scores = [compute_clause_risk(c) for c in clauses]
    aggregate = sum(s["score"] for s in scores) / len(scores) if scores else 0.0
    return {
        "clause_scores": scores,
        "aggregate_score": round(aggregate, 4),
        "aggregate_level": _score_to_level(aggregate),
        "high_risk_count": sum(1 for s in scores if s["level"] in ("HIGH", "CRITICAL")),
        "critical_count": sum(1 for s in scores if s["level"] == "CRITICAL"),
    }


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _score_to_level(score: float) -> str:
    if score >= 0.70:
        return "CRITICAL"
    elif score >= 0.45:
        return "HIGH"
    elif score >= 0.20:
        return "MEDIUM"
    return "LOW"


def _generate_summary(score: float, signals: list) -> str:
    level = _score_to_level(score)
    if not signals:
        return f"Risk level: {level}. No significant risk signals detected."
    top = ", ".join(signals[:3])
    return f"Risk level: {level}. Key signals: {top}."
