"""
AI Suggestion Service
Provides intelligent suggestions for contract text using Qwen LLM
"""

import logging
import requests
from typing import Dict, List
from django.conf import settings

logger = logging.getLogger(__name__)


class AISuggestionService:
    """Service for generating AI-powered contract text suggestions"""

    def __init__(self):
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL

    def suggest_improvement(self, selected_text: str, context: str = "") -> Dict:
        """
        Generate AI suggestions to improve selected contract text

        Args:
            selected_text: The text user selected for improvement
            context: Surrounding context for better suggestions (optional)

        Returns:
            Dict with suggestions and reasoning
        """
        try:
            # Build prompt for Qwen
            prompt = self._build_improvement_prompt(selected_text, context)

            # Call Ollama API
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 500,
                    }
                },
                timeout=30
            )

            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': 'AI service temporarily unavailable'
                }

            result = response.json()
            ai_response = result.get('response', '').strip()

            # Parse the AI response
            parsed = self._parse_ai_response(ai_response, selected_text)

            return {
                'success': True,
                'original_text': selected_text,
                'suggested_text': parsed['suggested_text'],
                'improvements': parsed['improvements'],
                'reasoning': parsed['reasoning'],
            }

        except requests.Timeout:
            logger.error("Ollama API timeout")
            return {
                'success': False,
                'error': 'AI suggestion request timed out'
            }
        except Exception as e:
            logger.error(f"Error generating AI suggestion: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def suggest_alternatives(self, selected_text: str, num_alternatives: int = 3) -> Dict:
        """
        Generate multiple alternative phrasings for selected text

        Args:
            selected_text: The text to generate alternatives for
            num_alternatives: Number of alternatives to generate (default: 3)

        Returns:
            Dict with list of alternative suggestions
        """
        try:
            prompt = f"""You are a legal contract expert. Provide {num_alternatives} alternative ways to phrase the following contract clause, each with different levels of risk/protection:

ORIGINAL TEXT:
{selected_text}

Please provide:
1. A more protective version (lower risk for your side)
2. A balanced version (fair to both parties)
3. A more lenient version (more flexibility)

Format each as:
ALTERNATIVE 1: [text]
RISK LEVEL: [LOW/MEDIUM/HIGH]
REASON: [brief explanation]

ALTERNATIVE 2: [text]
RISK LEVEL: [LOW/MEDIUM/HIGH]
REASON: [brief explanation]

ALTERNATIVE 3: [text]
RISK LEVEL: [LOW/MEDIUM/HIGH]
REASON: [brief explanation]
"""

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.8,
                        "max_tokens": 800,
                    }
                },
                timeout=45
            )

            if response.status_code != 200:
                return {'success': False, 'error': 'AI service error'}

            result = response.json()
            ai_response = result.get('response', '').strip()

            # Parse alternatives from response
            alternatives = self._parse_alternatives(ai_response)

            return {
                'success': True,
                'original_text': selected_text,
                'alternatives': alternatives,
            }

        except Exception as e:
            logger.error(f"Error generating alternatives: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _build_improvement_prompt(self, text: str, context: str) -> str:
        """Build a prompt for text improvement"""

        context_section = f"\n\nSURROUNDING CONTEXT:\n{context}" if context else ""

        prompt = f"""You are an expert contract attorney. A user has selected the following text from a contract and wants suggestions to improve it.

SELECTED TEXT:
{text}{context_section}

Please analyze this text and provide:
1. An improved version that is clearer, more protective, and reduces legal risk
2. List 2-3 specific improvements you made
3. Brief reasoning for why these changes help

Format your response EXACTLY as:
SUGGESTED TEXT:
[Your improved version here]

IMPROVEMENTS:
- [Improvement 1]
- [Improvement 2]
- [Improvement 3]

REASONING:
[Your explanation of why these changes reduce risk and improve clarity]
"""
        return prompt

    def _parse_ai_response(self, ai_response: str, original_text: str) -> Dict:
        """Parse structured AI response into components"""

        try:
            parts = {}

            # Extract SUGGESTED TEXT
            if "SUGGESTED TEXT:" in ai_response:
                suggested_start = ai_response.find("SUGGESTED TEXT:") + len("SUGGESTED TEXT:")
                suggested_end = ai_response.find("IMPROVEMENTS:")
                if suggested_end == -1:
                    suggested_end = len(ai_response)
                parts['suggested_text'] = ai_response[suggested_start:suggested_end].strip()
            else:
                parts['suggested_text'] = original_text

            # Extract IMPROVEMENTS
            improvements = []
            if "IMPROVEMENTS:" in ai_response:
                improvements_start = ai_response.find("IMPROVEMENTS:") + len("IMPROVEMENTS:")
                improvements_end = ai_response.find("REASONING:")
                if improvements_end == -1:
                    improvements_end = len(ai_response)
                improvements_text = ai_response[improvements_start:improvements_end].strip()

                # Split by bullet points or newlines
                for line in improvements_text.split('\n'):
                    line = line.strip()
                    if line.startswith('-') or line.startswith('•'):
                        improvements.append(line[1:].strip())

            parts['improvements'] = improvements if improvements else ["Text clarity improved", "Legal language strengthened"]

            # Extract REASONING
            if "REASONING:" in ai_response:
                reasoning_start = ai_response.find("REASONING:") + len("REASONING:")
                parts['reasoning'] = ai_response[reasoning_start:].strip()
            else:
                parts['reasoning'] = "The suggested text provides better clarity and protection."

            return parts

        except Exception as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            return {
                'suggested_text': original_text,
                'improvements': ["Unable to parse suggestions"],
                'reasoning': "Error processing AI response"
            }

    def _parse_alternatives(self, ai_response: str) -> List[Dict]:
        """Parse alternative suggestions from AI response"""

        alternatives = []
        try:
            # Split by ALTERNATIVE markers
            sections = ai_response.split("ALTERNATIVE ")

            for section in sections[1:]:  # Skip first empty section
                alt = {}

                # Extract text
                if ":" in section:
                    text_start = section.find(":") + 1
                    text_end = section.find("RISK LEVEL:")
                    if text_end == -1:
                        text_end = section.find("\n\n")
                    alt['text'] = section[text_start:text_end].strip()

                # Extract risk level
                if "RISK LEVEL:" in section:
                    risk_start = section.find("RISK LEVEL:") + len("RISK LEVEL:")
                    risk_end = section.find("REASON:")
                    if risk_end == -1:
                        risk_end = section.find("\n", risk_start)
                    alt['risk_level'] = section[risk_start:risk_end].strip()

                # Extract reason
                if "REASON:" in section:
                    reason_start = section.find("REASON:") + len("REASON:")
                    alt['reason'] = section[reason_start:].strip()

                if alt:
                    alternatives.append(alt)

            # Fallback if parsing fails
            if not alternatives:
                alternatives = [
                    {
                        'text': "Alternative version could not be generated",
                        'risk_level': "MEDIUM",
                        'reason': "AI response parsing failed"
                    }
                ]

        except Exception as e:
            logger.error(f"Error parsing alternatives: {str(e)}")
            alternatives = [{'text': "Error generating alternatives", 'risk_level': "UNKNOWN", 'reason': str(e)}]

        return alternatives


# Singleton instance
ai_suggestion_service = AISuggestionService()
