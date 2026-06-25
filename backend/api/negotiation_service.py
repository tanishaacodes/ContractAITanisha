import os
"""
Negotiation Agent Service
=========================
AI-powered clause rewrite suggestions to help users negotiate better contract terms.

Features:
- Analyze clauses for negotiation opportunities
- Generate alternative phrasings that are more favorable
- Assess clause favorability (buyer/seller/neutral)
- Provide negotiation tips and impact analysis
"""

import requests
import json
import logging
from typing import Dict, List
from django.utils import timezone
from core.models import (
    Contract, Clause, ClauseRewriteSuggestion, User
)

logger = logging.getLogger(__name__)


class NegotiationAgentService:
    """Service for generating AI-powered clause rewrite suggestions"""

    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")) + "/api/generate"
        self.model_name = "qwen2.5:0.5b"
        self.timeout = 120
        self.temperature = 0.3  # Slightly higher for creative rewrites

    def analyze_clause_for_negotiation(
        self,
        clause: Clause,
        user: User,
        perspective: str = "BUYER"
    ) -> List[ClauseRewriteSuggestion]:
        """
        Analyze a clause and generate rewrite suggestions.

        Args:
            clause: Clause model instance
            user: User requesting the analysis
            perspective: BUYER or SELLER perspective

        Returns:
            List of ClauseRewriteSuggestion objects
        """
        try:
            clause_text = clause.extracted_text or clause.context_sentences or ""
            if not clause_text.strip():
                logger.warning(f"No text found for clause {clause.id}")
                return []

            logger.info(f"Analyzing clause '{clause.clause_name}' from {perspective} perspective")

            # Generate suggestions using LLM
            suggestions = self._generate_suggestions(
                clause_text=clause_text,
                clause_name=clause.clause_name,
                perspective=perspective
            )

            # Create ClauseRewriteSuggestion records
            suggestion_objs = []
            for suggestion_data in suggestions:
                suggestion = ClauseRewriteSuggestion.objects.create(
                    clause=clause,
                    contract=clause.contract,
                    original_text=clause_text,
                    suggested_text=suggestion_data['suggested_text'],
                    rationale=suggestion_data['rationale'],
                    category=suggestion_data['category'],
                    priority=suggestion_data['priority'],
                    impact_analysis=suggestion_data.get('impact_analysis'),
                    negotiation_tips=suggestion_data.get('negotiation_tips'),
                    confidence_score=suggestion_data.get('confidence_score', 0.7),
                    created_by=user,
                    status='PENDING'
                )
                suggestion_objs.append(suggestion)

            logger.info(f"Generated {len(suggestion_objs)} suggestions for clause {clause.id}")
            return suggestion_objs

        except Exception as e:
            logger.error(f"Error analyzing clause for negotiation: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def _generate_suggestions(
        self,
        clause_text: str,
        clause_name: str,
        perspective: str
    ) -> List[Dict]:
        """
        Use LLM to generate rewrite suggestions.
        """
        prompt = f"""Analyze this contract clause and suggest rewrites from a {perspective} perspective.

CLAUSE TYPE: {clause_name}
CURRENT TEXT: {clause_text[:1000]}

Generate 2-3 rewrite suggestions that:
1. Reduce risk for the {perspective}
2. Make terms more favorable
3. Improve clarity

For each suggestion, provide:
- suggested_text: The rewritten clause (keep it concise)
- rationale: Why this change helps (max 40 words)
- category: RISK_REDUCTION, FAVORABLE_TERMS, CLARITY_IMPROVEMENT, or COMPLIANCE
- priority: HIGH, MEDIUM, or LOW
- impact_analysis: How this affects the contract (max 30 words)
- negotiation_tips: How to propose this change (max 30 words)
- confidence_score: 0.0-1.0

Return ONLY valid JSON array:
[{{
    "suggested_text": "rewritten clause here",
    "rationale": "brief reason",
    "category": "RISK_REDUCTION",
    "priority": "HIGH",
    "impact_analysis": "impact description",
    "negotiation_tips": "negotiation advice",
    "confidence_score": 0.8
}}]

JSON:"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": self.temperature,
                    "options": {
                        "num_predict": 800  # Allow for multiple suggestions
                    }
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()
                suggestions = self._extract_json_array(response_text)

                if suggestions and isinstance(suggestions, list):
                    # Validate and normalize
                    return [self._normalize_suggestion(s) for s in suggestions if isinstance(s, dict)]
                else:
                    logger.warning("LLM did not return valid suggestions array")
                    return []
            else:
                logger.error(f"Ollama request failed with status {response.status_code}")
                return []

        except requests.exceptions.Timeout:
            logger.error(f"LLM request timed out for clause analysis")
            return []
        except Exception as e:
            logger.error(f"Error generating suggestions: {str(e)}")
            return []

    def _extract_json_array(self, text: str) -> List[Dict]:
        """Extract JSON array from LLM response"""
        try:
            # Remove markdown code blocks
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]

            text = text.strip()

            # Clean up common errors
            import re
            text = re.sub(r',\s*}', '}', text)
            text = re.sub(r',\s*]', ']', text)
            text = ''.join(char for char in text if ord(char) >= 32 or char in ['\n', '\t'])

            # Auto-complete if truncated
            open_braces = text.count('{')
            close_braces = text.count('}')
            open_brackets = text.count('[')
            close_brackets = text.count(']')

            if open_braces > close_braces or open_brackets > close_brackets:
                logger.warning("Detected incomplete JSON - auto-completing")
                if text.count('"') % 2 != 0:
                    text += '"'
                text += ']' * (open_brackets - close_brackets)
                text += '}' * (open_braces - close_braces)

            return json.loads(text)
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Problematic text: {text[:200]}")
            return []

    def _normalize_suggestion(self, data: Dict) -> Dict:
        """Normalize and validate suggestion data"""
        valid_categories = ['RISK_REDUCTION', 'CLARITY_IMPROVEMENT', 'FAVORABLE_TERMS', 'COMPLIANCE', 'MUTUAL_BENEFIT', 'STANDARD_PRACTICE']
        valid_priorities = ['HIGH', 'MEDIUM', 'LOW']

        category = data.get('category', 'RISK_REDUCTION')
        if category not in valid_categories:
            category = 'RISK_REDUCTION'

        priority = data.get('priority', 'MEDIUM')
        if priority not in valid_priorities:
            priority = 'MEDIUM'

        return {
            'suggested_text': str(data.get('suggested_text', ''))[:5000],
            'rationale': str(data.get('rationale', 'AI-generated suggestion'))[:500],
            'category': category,
            'priority': priority,
            'impact_analysis': str(data.get('impact_analysis', ''))[:500] or None,
            'negotiation_tips': str(data.get('negotiation_tips', ''))[:500] or None,
            'confidence_score': max(0.0, min(1.0, float(data.get('confidence_score', 0.7))))
        }

    def accept_suggestion(
        self,
        suggestion_id: str,
        user: User,
        modified_text: str = None
    ) -> ClauseRewriteSuggestion:
        """
        Accept a suggestion (optionally with modifications).
        """
        suggestion = ClauseRewriteSuggestion.objects.get(id=suggestion_id)

        if modified_text:
            suggestion.suggested_text = modified_text
            suggestion.status = 'MODIFIED'
        else:
            suggestion.status = 'ACCEPTED'

        suggestion.reviewed_by = user
        suggestion.reviewed_at = timezone.now()
        suggestion.save()

        return suggestion

    def reject_suggestion(
        self,
        suggestion_id: str,
        user: User
    ) -> ClauseRewriteSuggestion:
        """
        Reject a suggestion.
        """
        suggestion = ClauseRewriteSuggestion.objects.get(id=suggestion_id)
        suggestion.status = 'REJECTED'
        suggestion.reviewed_by = user
        suggestion.reviewed_at = timezone.now()
        suggestion.save()

        return suggestion
