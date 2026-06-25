"""
Negotiation Counter-Proposal Engine
=====================================
Given an original clause, the counterparty's stated position, and our risk
tolerance, generates a balanced counter-proposal clause that is commercially
reasonable and improves the probability of agreement.

Architecture mirrors ClauseRewriteEngine:
- LLM-first via Qwen / Ollama.
- Deterministic rule-based fallback when LLM is unavailable.
- risk_tolerance: "low" | "medium" | "high"
"""

import logging
from typing import Dict, List

from django.conf import settings
import requests

logger = logging.getLogger(__name__)


class CounterProposalEngine:
    """
    Generates negotiation counter-proposals using LLM + fallback.
    """

    def __init__(self):
        self.ollama_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.model = getattr(settings, "OLLAMA_MODEL", "qwen2.5:0.5b")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate(
        self,
        original_clause: str,
        counterparty_position: str,
        risk_tolerance: str = "medium"
    ) -> Dict:
        """
        Generate a counter-proposal clause.

        Args:
            original_clause: The clause as currently written.
            counterparty_position: What the other side wants (free text).
            risk_tolerance: "low" | "medium" | "high"

        Returns:
            {
                "original_clause": str,
                "counterparty_position": str,
                "risk_tolerance": str,
                "counter_proposal": str,
                "method": "llm" | "fallback",
                "confidence": float,
                "negotiation_tips": List[str]
            }
        """
        if not original_clause or not counterparty_position:
            return {
                "original_clause": original_clause or "",
                "counterparty_position": counterparty_position or "",
                "risk_tolerance": risk_tolerance,
                "counter_proposal": original_clause or "",
                "method": "none",
                "confidence": 0.0,
                "negotiation_tips": [],
                "error": "original_clause and counterparty_position are required"
            }

        # Normalise tolerance
        risk_tolerance = risk_tolerance.lower() if risk_tolerance else "medium"
        if risk_tolerance not in ("low", "medium", "high"):
            risk_tolerance = "medium"

        # Try LLM
        proposal = self._call_llm(original_clause, counterparty_position, risk_tolerance)

        if proposal:
            return {
                "original_clause": original_clause,
                "counterparty_position": counterparty_position,
                "risk_tolerance": risk_tolerance,
                "counter_proposal": proposal,
                "method": "llm",
                "confidence": 0.80,
                "negotiation_tips": self._get_tips(risk_tolerance)
            }

        # Fallback
        logger.warning("LLM unavailable for counter-proposal — using rule-based fallback")
        proposal = self._fallback_proposal(original_clause, counterparty_position, risk_tolerance)
        return {
            "original_clause": original_clause,
            "counterparty_position": counterparty_position,
            "risk_tolerance": risk_tolerance,
            "counter_proposal": proposal,
            "method": "fallback",
            "confidence": 0.50,
            "negotiation_tips": self._get_tips(risk_tolerance)
        }

    # ------------------------------------------------------------------
    # LLM call
    # ------------------------------------------------------------------
    # Per-tolerance directives.  Qwen 0.5B needs very concrete, imperative
    # instructions or it simply echoes / concatenates the two inputs.
    _TOLERANCE_INSTRUCTIONS = {
        "low": (
            "Our side wants to PROTECT its position. You MUST keep the core obligations "
            "from OUR ORIGINAL CLAUSE and only make the minimum concessions needed to "
            "show good faith. You MUST add a liability cap of no more than 1x annual "
            "contract value. You MUST NOT accept any open-ended or unlimited terms from "
            "the counterparty's position. If the counterparty wants longer payment terms, "
            "accept at most 15 extra days beyond what the original clause states."
        ),
        "medium": (
            "Both sides should end up with a fair deal. You MUST split the difference "
            "on any numeric terms (payment deadlines, notice periods, caps) — calculate "
            "the midpoint explicitly. You MUST keep mutual obligations: anything one side "
            "owes, the other owes too. You MUST include a liability cap equal to 1x annual "
            "contract value for direct damages and explicitly exclude consequential damages."
        ),
        "high": (
            "We want to close the deal fast. You MUST accept most of the counterparty's "
            "requested terms. However, you MUST still add ONE protective carve-out: a "
            "mutual force-majeure clause, OR a cap on liability for indirect damages, OR "
            "a 30-day termination notice period — whichever is most relevant to the clause. "
            "You MUST NOT leave any term completely open-ended."
        ),
    }

    def _call_llm(self, original_clause: str, counterparty_position: str, risk_tolerance: str) -> str:
        specific_instruction = self._TOLERANCE_INSTRUCTIONS.get(
            risk_tolerance, self._TOLERANCE_INSTRUCTIONS["medium"]
        )

        prompt = (
            "You are a senior commercial contract lawyer drafting a COUNTER-PROPOSAL clause.\n\n"
            "RULES:\n"
            "- Output ONLY the final counter-proposal clause. Do not explain. Do not list both sides' positions.\n"
            "- The output MUST be a SINGLE coherent paragraph (or short numbered list of terms). "
            "Do NOT copy either input verbatim. SYNTHESIZE them into NEW language.\n"
            "- Do NOT repeat the original clause. Do NOT repeat the counterparty position. "
            "Write entirely NEW clause text that blends both.\n\n"
            f"TOLERANCE-SPECIFIC REQUIREMENTS:\n{specific_instruction}\n\n"
            f"OUR CURRENT CLAUSE:\n{original_clause}\n\n"
            f"COUNTERPARTY WANTS:\n{counterparty_position}\n\n"
            "COUNTER-PROPOSAL CLAUSE:\n"
        )

        try:
            resp = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.35, "num_predict": 800}
                },
                timeout=50
            )
            resp.raise_for_status()
            text = resp.json().get("response", "").strip()

            # Strip any leading labels the model might add
            for prefix in ("Counter-Proposal Clause:", "Counter-Proposal:", "Counter Proposal:", "---", "**Counter"):
                if text.startswith(prefix):
                    text = text[len(prefix):].strip()

            return text if len(text) > 30 else ""
        except Exception as e:
            logger.error(f"CounterProposalEngine LLM call failed: {e}")
            return ""

    # ------------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_key_terms(text: str) -> Dict:
        """
        Pull numeric / date terms out of free text so the fallback can blend them.
        Returns a dict with optional keys: payment_days, notice_days, liability_cap, penalty_rate.
        """
        import re
        terms: Dict = {}

        # Payment window  – e.g. "Net 60", "60 days", "payment within 45 days"
        m = re.search(r'net\s*(\d+)', text, re.IGNORECASE)
        if not m:
            m = re.search(r'(?:within\s*|payment\s+(?:terms?\s+of\s+)?)?(\d+)\s*(?:calendar\s+)?days?', text, re.IGNORECASE)
        if m:
            terms["payment_days"] = int(m.group(1))

        # Notice period – e.g. "30 days notice", "60-day notice period"
        m = re.search(r'(\d+)[- ]?day[s]?\s+(?:written\s+)?notice', text, re.IGNORECASE)
        if m:
            terms["notice_days"] = int(m.group(1))

        # Liability / damages cap – e.g. "$500,000", "500000", "1x annual"
        m = re.search(r'\$\s*([\d,]+)', text)
        if m:
            terms["liability_cap"] = "$" + m.group(1).replace(",", ",")
        elif re.search(r'(\d+)[x×]\s*annual', text, re.IGNORECASE):
            terms["liability_cap"] = re.search(r'(\d+)[x×]\s*annual', text, re.IGNORECASE).group(0)

        # Late-payment / penalty rate – e.g. "2% per annum", "1.5% monthly"
        m = re.search(r'([\d.]+)\s*%\s*(?:per\s+)?(?:annum|month|year)', text, re.IGNORECASE)
        if m:
            terms["penalty_rate"] = m.group(0)

        return terms

    @staticmethod
    def _fallback_proposal(original_clause: str, counterparty_position: str, risk_tolerance: str) -> str:
        """
        Produce a blended counter-proposal by extracting key numeric terms from
        both inputs and synthesising them according to risk tolerance.
        """
        our_terms  = CounterProposalEngine._extract_key_terms(original_clause)
        their_terms = CounterProposalEngine._extract_key_terms(counterparty_position)

        # ---- blend numeric values ----
        def _pick(key: str, ours_default: str = "") -> str:
            """Return blended value for a key based on tolerance."""
            ours  = our_terms.get(key)
            theirs = their_terms.get(key)
            if ours is None and theirs is None:
                return ours_default
            if ours is None:
                return str(theirs)
            if theirs is None:
                return str(ours)
            # Both present and numeric → blend
            if key in ("payment_days", "notice_days"):
                o, t = int(ours), int(theirs)
                if risk_tolerance == "low":
                    return str(min(o, t))       # keep our tighter term
                elif risk_tolerance == "high":
                    return str(max(o, t))       # accept their longer term
                else:
                    return str((o + t) // 2)    # midpoint
            # Non-numeric keys: low keeps ours, high takes theirs, medium keeps ours with note
            if risk_tolerance == "high":
                return str(theirs)
            return str(ours)

        payment_days = _pick("payment_days", "30")
        notice_days  = _pick("notice_days", "30")
        liability_cap = _pick("liability_cap", "1x annual contract value")
        penalty_rate  = _pick("penalty_rate", "1.5% per annum")

        # ---- assemble the counter-proposal per tolerance ----
        if risk_tolerance == "low":
            proposal = (
                f"The parties agree to the following terms: Payment shall be due within "
                f"{payment_days} days of a valid invoice. Late payments shall accrue interest at "
                f"{penalty_rate} simple interest. Total liability of each party shall not exceed "
                f"{liability_cap}, except in cases of gross negligence or wilful misconduct. "
                f"Either party may terminate this agreement with not less than {notice_days} days' "
                f"written notice. All termination and liability obligations shall be mutual."
            )
        elif risk_tolerance == "high":
            proposal = (
                f"In order to facilitate agreement, the parties agree: Payment shall be due within "
                f"{payment_days} days of invoice receipt. A mutual force-majeure clause shall apply "
                f"covering acts of God, war, pandemic, and government action. Liability shall be "
                f"capped at {liability_cap} for direct damages; indirect and consequential damages "
                f"are excluded. Either party may terminate on {notice_days} days' written notice. "
                f"Late fees shall not exceed {penalty_rate}."
            )
        else:  # medium
            proposal = (
                f"The parties agree to the following balanced terms: Payment is due within "
                f"{payment_days} days from receipt of invoice. Late payments accrue simple interest "
                f"at {penalty_rate}. Each party's liability is capped at {liability_cap} for direct "
                f"damages only; consequential and punitive damages are excluded. Termination by "
                f"either party requires {notice_days} days' prior written notice. All obligations "
                f"herein are mutual."
            )

        return proposal

    # ------------------------------------------------------------------
    # Negotiation tips (static, keyed by tolerance)
    # ------------------------------------------------------------------
    @staticmethod
    def _get_tips(risk_tolerance: str) -> List[str]:
        tips = {
            "low": [
                "Anchor the negotiation on your standard terms first.",
                "Request mutual obligations wherever the counterparty asks for one-sided provisions.",
                "Insist on a liability cap no higher than 1× annual contract value.",
            ],
            "medium": [
                "Propose a 30-day notice period for any termination clause.",
                "Suggest splitting liability caps (direct vs. consequential) to balance risk.",
                "Offer early-payment discounts as a trade-off for tighter payment terms.",
            ],
            "high": [
                "Accept the counterparty's liability cap but add a carve-out for IP infringement.",
                "Agree to their payment terms but request a mutual force-majeure clause.",
                "Close quickly — include a short negotiation-validity window (e.g. 10 business days).",
            ],
        }
        return tips.get(risk_tolerance, tips["medium"])
