"""
LLM Risk Scoring Service
Uses Qwen 7B (via Ollama) to score clause risk
"""
import requests
import json
import logging
import re
from django.conf import settings

logger = logging.getLogger(__name__)


class LLMRiskScorer:
    """
    Service class for LLM-based risk scoring of contract clauses.
    Uses Qwen 7B via Ollama for risk analysis.
    """

    def __init__(self):
        """Initialize LLM risk scorer"""
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        logger.info(f"LLM Risk Scorer initialized with model: {self.model}")

    def score_clause_risk(self, clause_text, clause_category=None):
        """
        Score risk of a contract clause using LLM.

        Args:
            clause_text: Text of the clause to analyze
            clause_category: Optional category (Indemnity, Liability, etc.)

        Returns:
            Dictionary with risk_score (0-1), risk_level, and explanation
        """
        try:
            # Construct prompt
            prompt = self._build_risk_scoring_prompt(clause_text, clause_category)

            # Call Ollama API
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower temperature for consistent scoring
                        "num_predict": 256
                    }
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                llm_output = result.get("response", "")

                # Parse LLM output
                risk_data = self._parse_risk_output(llm_output)

                logger.info(f"Scored clause risk: {risk_data['risk_score']:.2f}")
                return risk_data
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return self._default_risk_score()

        except Exception as e:
            logger.error(f"Error scoring clause risk: {e}")
            return self._default_risk_score()

    def _build_risk_scoring_prompt(self, clause_text, clause_category=None):
        """Build prompt for risk scoring"""
        category_context = f"This is a '{clause_category}' clause. " if clause_category else ""

        prompt = f"""You are a legal risk analyst. {category_context}Analyze the following contract clause and rate its legal risk.

Clause:
{clause_text}

Rate the legal risk on a scale from 0.0 to 1.0, where:
- 0.0-0.3 = Low Risk (standard industry practice, protective)
- 0.3-0.6 = Medium Risk (some concerning terms, negotiable)
- 0.6-0.8 = High Risk (unfavorable terms, significant exposure)
- 0.8-1.0 = Critical Risk (highly problematic, immediate action needed)

Respond ONLY in this format:
RISK_SCORE: [number between 0.0 and 1.0]
RISK_LEVEL: [LOW, MEDIUM, HIGH, or CRITICAL]
EXPLANATION: [brief 1-2 sentence explanation]

Example:
RISK_SCORE: 0.75
RISK_LEVEL: HIGH
EXPLANATION: Unlimited liability cap with no time restrictions creates significant financial exposure.
"""
        return prompt

    def _parse_risk_output(self, llm_output):
        """Parse LLM output to extract risk data"""
        try:
            # Extract risk score
            score_match = re.search(r'RISK_SCORE:\s*(0?\.\d+|1\.0)', llm_output, re.IGNORECASE)
            risk_score = float(score_match.group(1)) if score_match else 0.5

            # Ensure score is in valid range
            risk_score = max(0.0, min(1.0, risk_score))

            # Extract risk level
            level_match = re.search(r'RISK_LEVEL:\s*(LOW|MEDIUM|HIGH|CRITICAL)', llm_output, re.IGNORECASE)
            risk_level = level_match.group(1).upper() if level_match else self._score_to_level(risk_score)

            # Extract explanation
            explanation_match = re.search(r'EXPLANATION:\s*(.+?)(?:\n|$)', llm_output, re.IGNORECASE | re.DOTALL)
            explanation = explanation_match.group(1).strip() if explanation_match else "Risk analysis completed."

            return {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "explanation": explanation,
                "raw_output": llm_output
            }

        except Exception as e:
            logger.error(f"Error parsing LLM output: {e}")
            return self._default_risk_score()

    def _score_to_level(self, score):
        """Convert numeric risk score to risk level"""
        if score < 0.3:
            return "LOW"
        elif score < 0.6:
            return "MEDIUM"
        elif score < 0.8:
            return "HIGH"
        else:
            return "CRITICAL"

    def _default_risk_score(self):
        """Return default risk score when LLM fails"""
        return {
            "risk_score": 0.5,
            "risk_level": "MEDIUM",
            "explanation": "Unable to analyze risk. Manual review recommended.",
            "raw_output": ""
        }

    def batch_score_clauses(self, clauses):
        """
        Score multiple clauses in batch.

        Args:
            clauses: List of dicts with 'text' and optional 'category'

        Returns:
            List of risk scores in same order as input
        """
        results = []

        for clause in clauses:
            clause_text = clause.get("text", "")
            clause_category = clause.get("category")

            if clause_text:
                risk_data = self.score_clause_risk(clause_text, clause_category)
                results.append(risk_data)
            else:
                results.append(self._default_risk_score())

        logger.info(f"Batch scored {len(results)} clauses")
        return results

    def analyze_contract_risk(self, clauses_data):
        """
        Analyze overall contract risk based on multiple clauses.

        Args:
            clauses_data: List of clause risk scores

        Returns:
            Aggregated contract risk analysis
        """
        if not clauses_data:
            return {
                "overall_risk_score": 0.0,
                "risk_level": "LOW",
                "critical_clauses": 0,
                "high_risk_clauses": 0,
                "medium_risk_clauses": 0,
                "low_risk_clauses": 0
            }

        # Calculate statistics
        risk_scores = [c.get("risk_score", 0) for c in clauses_data]
        avg_risk = sum(risk_scores) / len(risk_scores)
        max_risk = max(risk_scores)

        # Count by risk level
        critical_count = sum(1 for c in clauses_data if c.get("risk_level") == "CRITICAL")
        high_count = sum(1 for c in clauses_data if c.get("risk_level") == "HIGH")
        medium_count = sum(1 for c in clauses_data if c.get("risk_level") == "MEDIUM")
        low_count = sum(1 for c in clauses_data if c.get("risk_level") == "LOW")

        # Overall risk is weighted average (max risk has 40% weight, avg has 60%)
        overall_risk = (max_risk * 0.4) + (avg_risk * 0.6)

        return {
            "overall_risk_score": round(overall_risk, 2),
            "risk_level": self._score_to_level(overall_risk),
            "max_clause_risk": max_risk,
            "avg_clause_risk": round(avg_risk, 2),
            "critical_clauses": critical_count,
            "high_risk_clauses": high_count,
            "medium_risk_clauses": medium_count,
            "low_risk_clauses": low_count,
            "total_clauses_analyzed": len(clauses_data)
        }

    def detect_cross_contract_risks(self, similar_clauses_data):
        """
        Detect systemic risks across multiple contracts with similar clauses.

        Args:
            similar_clauses_data: List of similar clauses from different contracts

        Returns:
            Cross-contract risk analysis
        """
        if not similar_clauses_data:
            return {
                "systemic_risk_detected": False,
                "risk_score": 0.0,
                "affected_contracts": 0
            }

        # Count unique contracts
        contract_ids = set()
        risk_scores = []

        for clause in similar_clauses_data:
            if clause.get("contract_id"):
                contract_ids.add(clause["contract_id"])
            if clause.get("risk_score"):
                risk_scores.append(clause["risk_score"])

        affected_contracts = len(contract_ids)
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0

        # Systemic risk is detected if same risky clause appears in 3+ contracts
        systemic_risk = affected_contracts >= 3 and avg_risk >= 0.6

        return {
            "systemic_risk_detected": systemic_risk,
            "risk_score": round(avg_risk, 2),
            "affected_contracts": affected_contracts,
            "risk_explanation": f"Similar risky clause found in {affected_contracts} contracts"
            if systemic_risk else "No systemic risk pattern detected"
        }


# Singleton instance
_llm_risk_scorer = None


def get_llm_risk_scorer():
    """Get or create LLM risk scorer instance"""
    global _llm_risk_scorer
    if _llm_risk_scorer is None:
        _llm_risk_scorer = LLMRiskScorer()
    return _llm_risk_scorer
