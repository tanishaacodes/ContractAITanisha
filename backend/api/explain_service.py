import os
"""
Clause Explanation Service
===========================
LLM-powered clause explanation with risk analysis and mitigation suggestions.

Part of RRIE (Risk & Responsibility Intelligence Engine) enhancement.
"""

import requests
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ClauseExplainerService:
    """
    Provides natural language explanations for contract clauses.
    Uses Qwen LLM to explain clause meaning, risks, and mitigation strategies.
    """

    def __init__(self):
        from django.conf import settings
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")) + "/api/generate"
        self.model_name = getattr(settings, 'OLLAMA_MODEL', 'qwen2.5:7b')
        logger.info("ClauseExplainerService initialized with Qwen model")

    def explain_clause(
        self,
        clause_text: str,
        sentence_type: Optional[str] = None,
        party: Optional[str] = None,
        risk_score: Optional[float] = None,
        keywords: Optional[Dict] = None
    ) -> Dict:
        """
        Generate comprehensive explanation for a clause.

        Args:
            clause_text: The clause text to explain
            sentence_type: HEADING/DEFINITION/OBLIGATION/RISK/RIGHT
            party: CONTRACTOR/EMPLOYER/SHARED
            risk_score: Normalized risk score (0-1)
            keywords: Dict of detected risk keywords and weights

        Returns:
            Dict with:
                - meaning: Plain language explanation
                - risk_explanation: Why this clause is risky
                - impact: Business/legal impact
                - mitigation: Suggested risk mitigation strategies
                - success: bool
                - error: Optional error message
        """
        try:
            # Build context-aware prompt
            prompt = self._build_explanation_prompt(
                clause_text, sentence_type, party, risk_score, keywords
            )

            # Call Qwen LLM
            response = self._call_llm(prompt)

            if not response:
                return {
                    'success': False,
                    'error': 'Failed to generate explanation from LLM'
                }

            # Parse structured response
            parsed = self._parse_llm_response(response)

            return {
                'success': True,
                'meaning': parsed.get('meaning', ''),
                'risk_explanation': parsed.get('risk_explanation', ''),
                'impact': parsed.get('impact', ''),
                'mitigation': parsed.get('mitigation', ''),
                'metadata': {
                    'sentence_type': sentence_type,
                    'party': party,
                    'risk_score': risk_score,
                    'risk_level': self._get_risk_level(risk_score)
                }
            }

        except Exception as e:
            logger.error(f"Clause explanation failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _build_explanation_prompt(
        self,
        clause_text: str,
        sentence_type: Optional[str],
        party: Optional[str],
        risk_score: Optional[float],
        keywords: Optional[Dict]
    ) -> str:
        """Build context-aware prompt for LLM."""

        # Base prompt
        prompt = f"""You are a legal contract expert. Analyze this clause and provide a clear explanation.

CLAUSE TEXT:
{clause_text}

METADATA:
- Type: {sentence_type or 'Unknown'}
- Party: {party or 'Unknown'}
- Risk Score: {risk_score if risk_score else 'Not assessed'}
- Risk Keywords: {', '.join(keywords.keys()) if keywords else 'None'}

Provide a structured response with these sections:

1. MEANING: Explain what this clause means in simple terms (2-3 sentences)

2. RISK EXPLANATION: Why is this clause risky? What are the potential issues? (2-3 sentences)

3. IMPACT: What is the business/legal impact of this clause? (2-3 sentences)

4. MITIGATION: Suggest 2-3 specific ways to reduce the risk

Keep each section concise and practical. Use bullet points for mitigation strategies.
"""

        return prompt

    def _call_llm(self, prompt: str, max_retries: int = 2) -> Optional[str]:
        """Call Qwen LLM via Ollama API."""

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Lower temperature for more consistent explanations
                "top_p": 0.9,
                "max_tokens": 800
            }
        }

        for attempt in range(max_retries):
            try:
                logger.info(f"Calling Qwen LLM (attempt {attempt + 1}/{max_retries})")

                response = requests.post(
                    self.ollama_url,
                    json=payload,
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    explanation = result.get('response', '').strip()

                    if explanation:
                        logger.info(f"LLM explanation generated ({len(explanation)} chars)")
                        return explanation
                    else:
                        logger.warning("LLM returned empty response")
                else:
                    logger.error(f"LLM API error: {response.status_code} - {response.text}")

            except requests.exceptions.Timeout:
                logger.warning(f"LLM request timeout (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"LLM call failed: {e}")

        return None

    def _parse_llm_response(self, response_text: str) -> Dict:
        """Parse structured sections from LLM response."""

        sections = {
            'meaning': '',
            'risk_explanation': '',
            'impact': '',
            'mitigation': ''
        }

        # Simple section parser
        current_section = None
        lines = response_text.split('\n')

        for line in lines:
            line_lower = line.lower().strip()

            # Detect section headers
            if 'meaning:' in line_lower or line_lower.startswith('1.'):
                current_section = 'meaning'
                continue
            elif 'risk explanation:' in line_lower or line_lower.startswith('2.'):
                current_section = 'risk_explanation'
                continue
            elif 'impact:' in line_lower or line_lower.startswith('3.'):
                current_section = 'impact'
                continue
            elif 'mitigation:' in line_lower or line_lower.startswith('4.'):
                current_section = 'mitigation'
                continue

            # Append content to current section
            if current_section and line.strip():
                if sections[current_section]:
                    sections[current_section] += '\n' + line.strip()
                else:
                    sections[current_section] = line.strip()

        # Fallback: if parsing failed, put everything in meaning
        if not any(sections.values()):
            sections['meaning'] = response_text.strip()

        return sections

    def _get_risk_level(self, risk_score: Optional[float]) -> str:
        """Convert risk score to level."""
        if risk_score is None:
            return 'UNKNOWN'
        if risk_score >= 0.7:
            return 'HIGH'
        elif risk_score >= 0.4:
            return 'MEDIUM'
        else:
            return 'LOW'


# Singleton instance
_explainer_instance = None


def get_clause_explainer() -> ClauseExplainerService:
    """Get singleton instance of clause explainer."""
    global _explainer_instance
    if _explainer_instance is None:
        _explainer_instance = ClauseExplainerService()
    return _explainer_instance
