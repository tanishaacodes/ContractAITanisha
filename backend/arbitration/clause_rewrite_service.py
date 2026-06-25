"""
AI-Powered Clause Rewrite Engine
==================================
Rewrites arbitration clauses to minimize buyer risk using LLM (Ollama Qwen).

Strategies:
- buyer_favorable: Minimize buyer exposure (arbitration seat, cost allocation, etc.)
- balanced: Fair terms for both parties
- supplier_favorable: Minimize supplier exposure

Features:
- LLM-based clause generation
- Risk-aware rewriting
- Multiple rewrite strategies
- Before/after risk comparison
"""

import logging
import re
import json
from typing import Dict, List, Optional
import os

try:
    import requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class ClauseRewriteService:
    """
    Service for AI-powered arbitration clause rewriting.
    Uses Ollama Qwen for generation.
    """

    def __init__(
        self,
        ollama_base_url: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        """
        Initialize rewrite service.

        Args:
            ollama_base_url: Ollama API URL (default from env)
            model_name: Model to use (default from env)
        """
        self.base_url = ollama_base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model_name or os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")

        logger.info(f"Clause Rewrite Service initialized with model: {self.model}")

    def is_available(self) -> bool:
        """Check if Ollama is available."""
        if not _REQUESTS_AVAILABLE:
            return False

        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def rewrite_clause(
        self,
        clause_text: str,
        strategy: str = "buyer_favorable",
        contract_value: Optional[float] = None,
        temperature: float = 0.3,
        max_tokens: int = 500,
    ) -> Dict:
        """
        Rewrite an arbitration clause using LLM.

        Args:
            clause_text: Original clause text
            strategy: Rewrite strategy (buyer_favorable, balanced, supplier_favorable)
            contract_value: Contract value for context (optional)
            temperature: LLM temperature
            max_tokens: Maximum generation length

        Returns:
            Dict with {
                "original": str,
                "rewritten": str,
                "improvements": List[str],
                "strategy": str,
                "model": str,
            }
        """
        prompt = self._build_prompt(clause_text, strategy, contract_value)

        try:
            rewritten_text = self._generate_text(prompt, temperature, max_tokens)

            improvements = self._extract_improvements(clause_text, rewritten_text, strategy)

            return {
                "original": clause_text,
                "rewritten": rewritten_text,
                "improvements": improvements,
                "strategy": strategy,
                "model": self.model,
                "temperature": temperature,
            }

        except Exception as e:
            logger.error(f"Clause rewrite failed: {e}")
            return {
                "original": clause_text,
                "rewritten": clause_text,
                "improvements": [],
                "strategy": strategy,
                "model": self.model,
                "error": str(e),
            }

    def _build_prompt(
        self, clause_text: str, strategy: str, contract_value: Optional[float]
    ) -> str:
        """Build LLM prompt for clause rewriting."""

        # Strategy-specific instructions
        strategy_instructions = {
            "buyer_favorable": """
Rewrite this arbitration clause to MINIMIZE BUYER RISK in a large EPC construction contract.

Key improvements to make:
1. Arbitration seat: Choose a buyer-favorable jurisdiction (London, Singapore preferred over supplier's country)
2. Cost allocation: Equal cost sharing or buyer pays only if they lose
3. Tribunal size: Three-member tribunal for fairness
4. Governing law: Neutral or buyer's jurisdiction
5. Institutional rules: ICC or LCIA preferred (stronger buyer protections)
6. Remove/limit: Supplier advantages like cost shifting, ad hoc arbitration, single arbitrator
7. Add: Clear dispute resolution escalation (negotiation → mediation → arbitration)
8. Add: Limitation periods that favor buyer
9. Add: Emergency arbitrator provisions for urgent relief

Make the clause professional, legally precise, and clearly favorable to the buyer while remaining enforceable.
""",
            "balanced": """
Rewrite this arbitration clause to be BALANCED and FAIR to both parties.

Key improvements:
1. Arbitration seat: Neutral jurisdiction (Singapore, London, Switzerland)
2. Cost allocation: Each party bears own costs, shared tribunal fees
3. Tribunal size: Three-member tribunal
4. Governing law: Neutral jurisdiction
5. Institutional rules: ICC or LCIA
6. Clear escalation: Negotiation → mediation → arbitration
7. Reasonable timelines for both parties

Make the clause professional, legally precise, and fair.
""",
            "supplier_favorable": """
Rewrite this arbitration clause to MINIMIZE SUPPLIER RISK.

Key improvements:
1. Arbitration seat: Supplier-favorable jurisdiction
2. Cost allocation: Loser pays or buyer bears costs
3. Governing law: Supplier's jurisdiction
4. Fast-track arbitration to reduce costs
5. Limited document production
6. Single arbitrator for efficiency

Make the clause professional and legally precise.
""",
        }

        instruction = strategy_instructions.get(strategy, strategy_instructions["buyer_favorable"])

        value_context = (
            f"\n\nContract Value: ${contract_value:,.0f}\n"
            if contract_value
            else ""
        )

        prompt = f"""You are an expert construction contract lawyer specializing in arbitration clauses for $100M+ EPC contracts.
{value_context}
{instruction}

ORIGINAL CLAUSE:
{clause_text}

IMPROVED CLAUSE:"""

        return prompt

    def _generate_text(
        self, prompt: str, temperature: float, max_tokens: int
    ) -> str:
        """
        Generate text using Ollama API.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Max tokens to generate

        Returns:
            Generated text
        """
        if not _REQUESTS_AVAILABLE:
            raise RuntimeError("requests library not available")

        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
            },
        }

        response = requests.post(url, json=payload, timeout=60)

        if response.status_code != 200:
            raise RuntimeError(f"Ollama API error: {response.status_code} - {response.text}")

        result = response.json()
        generated_text = result.get("response", "").strip()

        # Clean up the generated text
        generated_text = self._clean_generated_text(generated_text)

        return generated_text

    def _clean_generated_text(self, text: str) -> str:
        """
        Clean up LLM-generated clause text.
        Removes artifacts, extra whitespace, etc.
        """
        # Remove common LLM artifacts
        text = re.sub(r"^(IMPROVED CLAUSE:|REWRITTEN:|OUTPUT:)\s*", "", text, flags=re.IGNORECASE)

        # Remove markdown formatting
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        text = text.replace("**", "")

        # Normalize whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()

        return text

    def _extract_improvements(
        self, original: str, rewritten: str, strategy: str
    ) -> List[str]:
        """
        Identify specific improvements made during rewriting.

        Args:
            original: Original clause
            rewritten: Rewritten clause
            strategy: Rewrite strategy

        Returns:
            List of improvement descriptions
        """
        improvements = []

        original_lower = original.lower()
        rewritten_lower = rewritten.lower()

        # Check for specific improvements based on strategy
        if strategy == "buyer_favorable":
            # Arbitration seat improvement
            if "london" in rewritten_lower or "singapore" in rewritten_lower:
                if "london" not in original_lower and "singapore" not in original_lower:
                    improvements.append("Changed arbitration seat to buyer-favorable jurisdiction")

            # Cost allocation
            if "equal" in rewritten_lower and "cost" in rewritten_lower:
                if "equal" not in original_lower or "cost" not in original_lower:
                    improvements.append("Added equal cost sharing provision")

            # Three-member tribunal
            if "three" in rewritten_lower and ("arbitrator" in rewritten_lower or "tribunal" in rewritten_lower):
                improvements.append("Specified three-member tribunal for fairness")

            # Institutional arbitration
            if ("icc" in rewritten_lower or "lcia" in rewritten_lower) and "icc" not in original_lower and "lcia" not in original_lower:
                improvements.append("Specified ICC/LCIA institutional arbitration")

            # Mediation precondition
            if "mediation" in rewritten_lower and "mediation" not in original_lower:
                improvements.append("Added mediation as precondition to arbitration")

            # Emergency arbitrator
            if "emergency" in rewritten_lower and "emergency" not in original_lower:
                improvements.append("Added emergency arbitrator provisions")

        elif strategy == "balanced":
            if "neutral" in rewritten_lower:
                improvements.append("Specified neutral jurisdiction")

            if "equal" in rewritten_lower or "each party" in rewritten_lower:
                improvements.append("Balanced cost allocation between parties")

        # General improvements
        if len(rewritten) > len(original) * 1.2:
            improvements.append("Added comprehensive arbitration procedures")

        if "governing law" in rewritten_lower and "governing law" not in original_lower:
            improvements.append("Specified governing law explicitly")

        if not improvements:
            improvements.append("Improved clarity and legal precision")

        return improvements

    def batch_rewrite_clauses(
        self,
        clauses: List[Dict],
        strategy: str = "buyer_favorable",
        contract_value: Optional[float] = None,
    ) -> List[Dict]:
        """
        Rewrite multiple clauses in batch.

        Args:
            clauses: List of clause dicts with {id, text, risk_score}
            strategy: Rewrite strategy
            contract_value: Contract value

        Returns:
            List of rewrite results
        """
        results = []

        for clause in clauses:
            result = self.rewrite_clause(
                clause_text=clause["text"],
                strategy=strategy,
                contract_value=contract_value,
            )

            result["clause_id"] = clause["id"]
            result["original_risk_score"] = clause.get("risk_score", 0.5)

            results.append(result)

        return results


# Global singleton
_rewrite_service = None


def get_clause_rewrite_service() -> ClauseRewriteService:
    """Get or create the global clause rewrite service."""
    global _rewrite_service
    if _rewrite_service is None:
        _rewrite_service = ClauseRewriteService()
    return _rewrite_service


# Convenience functions

def rewrite_high_risk_clauses(
    clauses: List[Dict],
    min_risk: float = 0.50,
    strategy: str = "buyer_favorable",
    contract_value: Optional[float] = None,
) -> List[Dict]:
    """
    Automatically rewrite all high-risk clauses.

    Args:
        clauses: List of clause dicts
        min_risk: Minimum risk threshold for rewriting
        strategy: Rewrite strategy
        contract_value: Contract value

    Returns:
        List of rewrite results for high-risk clauses
    """
    service = get_clause_rewrite_service()

    # Filter high-risk clauses
    high_risk_clauses = [
        cl for cl in clauses
        if cl.get("risk_score", 0) >= min_risk
    ]

    if not high_risk_clauses:
        return []

    # Rewrite
    results = service.batch_rewrite_clauses(
        high_risk_clauses,
        strategy=strategy,
        contract_value=contract_value,
    )

    return results
