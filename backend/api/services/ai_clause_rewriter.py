"""
AI Clause Rewriting Service
============================
Uses AI (OpenAI GPT-4 or Anthropic Claude) to rewrite contract clauses.

Features:
1. Rewrite clauses to reduce risk
2. Rewrite for clarity/simplicity
3. Make clauses more favorable to specific party
4. Generate counter-proposals
5. Suggest multiple alternatives

Supports:
- OpenAI GPT-4
- Anthropic Claude
- Fallback to template-based rewriting
"""

import logging
from typing import Dict, Any, Optional, List
import os
import requests

logger = logging.getLogger(__name__)


class AIClauseRewriter:
    """
    AI-powered clause rewriting using LLMs.
    """

    # System prompts for different rewrite modes
    SYSTEM_PROMPTS = {
        'reduce_risk': """You are an expert contract lawyer specializing in risk mitigation.
Your task is to rewrite contract clauses to reduce legal risk while preserving the core intent.

Guidelines:
- Remove or qualify unlimited liability language
- Add reasonable limitations and caps
- Include appropriate carve-outs and exceptions
- Ensure balanced obligations
- Maintain professional legal tone
- Preserve key business terms""",

        'simplify': """You are an expert contract lawyer who specializes in plain language contracts.
Your task is to rewrite complex legal clauses into clear, simple language that is easy to understand.

Guidelines:
- Use simple, everyday words instead of legalese
- Break long sentences into shorter ones
- Remove unnecessary Latin phrases
- Maintain legal validity while improving clarity
- Keep the same legal meaning
- Use active voice when possible""",

        'favor_client': """You are an expert contract negotiator representing the client/buyer side.
Your task is to rewrite clauses to be more favorable to the client while remaining reasonable.

Guidelines:
- Strengthen client protections
- Add favorable terms and conditions
- Reduce client obligations where possible
- Add client-friendly exceptions and carve-outs
- Ensure reasonable balance (don't be unreasonable)
- Maintain enforceability""",

        'favor_vendor': """You are an expert contract negotiator representing the vendor/supplier side.
Your task is to rewrite clauses to be more favorable to the vendor while remaining reasonable.

Guidelines:
- Protect vendor interests
- Limit vendor liability reasonably
- Add vendor-friendly terms
- Reduce vendor obligations where appropriate
- Ensure contract remains acceptable to clients
- Maintain market standards""",

        'counter_proposal': """You are an expert contract negotiator.
Your task is to generate a counter-proposal that addresses concerns while protecting your client's interests.

Guidelines:
- Address the underlying concern
- Propose balanced alternative language
- Offer compromises where appropriate
- Protect key business interests
- Maintain reasonable negotiating position
- Include brief explanation of changes""",
    }

    def __init__(self, provider: str = 'openai'):
        """
        Initialize AI rewriter.

        Args:
            provider: 'openai' or 'anthropic'
        """
        self.provider = provider.lower()
        self.api_key = self._get_api_key()
        self.logger = logger

    def _get_api_key(self) -> Optional[str]:
        """Get API key for the provider"""
        if self.provider == 'openai':
            return os.getenv('OPENAI_API_KEY')
        elif self.provider == 'anthropic':
            return os.getenv('ANTHROPIC_API_KEY')
        return None

    def rewrite_clause(
        self,
        clause_text: str,
        rewrite_mode: str = 'reduce_risk',
        custom_instructions: Optional[str] = None,
        clause_type: Optional[str] = None,
        num_alternatives: int = 1
    ) -> Dict[str, Any]:
        """
        Rewrite a clause using AI.

        Args:
            clause_text: Original clause text
            rewrite_mode: Mode - reduce_risk, simplify, favor_client, favor_vendor, counter_proposal
            custom_instructions: Optional custom instructions
            clause_type: Optional clause type for context
            num_alternatives: Number of alternative rewrites to generate (1-3)

        Returns:
            Dict with rewritten clause(s) and analysis
        """
        try:
            # Validate mode
            if rewrite_mode not in self.SYSTEM_PROMPTS:
                return {
                    'success': False,
                    'error': f'Invalid rewrite mode: {rewrite_mode}'
                }

            # Check if API key is available
            if not self.api_key:
                self.logger.warning(f"[AI-REWRITE] No API key for {self.provider}, using fallback")
                return self._fallback_rewrite(clause_text, rewrite_mode)

            # Build prompt
            user_prompt = self._build_user_prompt(
                clause_text,
                rewrite_mode,
                custom_instructions,
                clause_type
            )

            # Call AI provider
            if self.provider == 'openai':
                result = self._call_openai(
                    system_prompt=self.SYSTEM_PROMPTS[rewrite_mode],
                    user_prompt=user_prompt,
                    num_alternatives=num_alternatives
                )
            elif self.provider == 'anthropic':
                result = self._call_anthropic(
                    system_prompt=self.SYSTEM_PROMPTS[rewrite_mode],
                    user_prompt=user_prompt,
                    num_alternatives=num_alternatives
                )
            else:
                return self._fallback_rewrite(clause_text, rewrite_mode)

            if not result['success']:
                return result

            # Post-process and analyze
            return self._post_process_rewrites(
                original_text=clause_text,
                rewrites=result['rewrites'],
                mode=rewrite_mode
            )

        except Exception as e:
            self.logger.error(f"[AI-REWRITE] Error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _build_user_prompt(
        self,
        clause_text: str,
        mode: str,
        custom_instructions: Optional[str],
        clause_type: Optional[str]
    ) -> str:
        """Build user prompt for AI"""
        prompt = f"Original Clause:\n{clause_text}\n\n"

        if clause_type:
            prompt += f"Clause Type: {clause_type}\n\n"

        if custom_instructions:
            prompt += f"Additional Instructions:\n{custom_instructions}\n\n"

        prompt += "Please rewrite this clause following the guidelines. "
        prompt += "Provide ONLY the rewritten clause text without explanations or preamble."

        return prompt

    def _call_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        num_alternatives: int = 1
    ) -> Dict[str, Any]:
        """Call OpenAI API"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            data = {
                'model': 'gpt-4',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'temperature': 0.7,
                'n': num_alternatives,
                'max_tokens': 1000
            }

            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code != 200:
                self.logger.error(f"[OPENAI] API error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'OpenAI API error: {response.status_code}'
                }

            result = response.json()
            rewrites = [choice['message']['content'].strip() for choice in result['choices']]

            return {
                'success': True,
                'rewrites': rewrites
            }

        except Exception as e:
            self.logger.error(f"[OPENAI] Error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _call_anthropic(
        self,
        system_prompt: str,
        user_prompt: str,
        num_alternatives: int = 1
    ) -> Dict[str, Any]:
        """Call Anthropic API"""
        try:
            headers = {
                'x-api-key': self.api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }

            rewrites = []

            # Anthropic doesn't support n parameter, so call multiple times
            for _ in range(num_alternatives):
                data = {
                    'model': 'claude-3-opus-20240229',
                    'max_tokens': 1000,
                    'system': system_prompt,
                    'messages': [
                        {'role': 'user', 'content': user_prompt}
                    ],
                    'temperature': 0.7
                }

                response = requests.post(
                    'https://api.anthropic.com/v1/messages',
                    headers=headers,
                    json=data,
                    timeout=30
                )

                if response.status_code != 200:
                    self.logger.error(f"[ANTHROPIC] API error: {response.status_code} - {response.text}")
                    return {
                        'success': False,
                        'error': f'Anthropic API error: {response.status_code}'
                    }

                result = response.json()
                rewrite = result['content'][0]['text'].strip()
                rewrites.append(rewrite)

            return {
                'success': True,
                'rewrites': rewrites
            }

        except Exception as e:
            self.logger.error(f"[ANTHROPIC] Error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _fallback_rewrite(self, clause_text: str, mode: str) -> Dict[str, Any]:
        """
        Fallback template-based rewriting when AI is not available.
        Simple rule-based transformations.
        """
        self.logger.info(f"[AI-REWRITE] Using fallback for mode: {mode}")

        text = clause_text

        if mode == 'reduce_risk':
            # Add limitation language
            if 'unlimited' in text.lower():
                text = text.replace('unlimited', 'reasonable')
                text = text.replace('Unlimited', 'Reasonable')

            if 'without limitation' in text.lower():
                text = text.replace('without limitation', 'subject to reasonable limitations')

            # Add cap if not present
            if 'indemnif' in text.lower() and 'not exceed' not in text.lower():
                text += " provided that such indemnification shall not exceed the total contract value."

        elif mode == 'simplify':
            # Simple replacements
            replacements = {
                'shall': 'will',
                'herein': 'in this contract',
                'hereof': 'of this contract',
                'hereunder': 'under this contract',
                'notwithstanding': 'despite',
                'pursuant to': 'according to',
            }
            for old, new in replacements.items():
                text = text.replace(old, new)
                text = text.replace(old.capitalize(), new.capitalize())

        return {
            'success': True,
            'alternatives': [{
                'text': text,
                'explanation': f'Template-based {mode} rewrite (AI not available)',
                'confidence': 0.6
            }],
            'using_fallback': True
        }

    def _post_process_rewrites(
        self,
        original_text: str,
        rewrites: List[str],
        mode: str
    ) -> Dict[str, Any]:
        """Post-process AI rewrites and add analysis"""
        alternatives = []

        for i, rewrite_text in enumerate(rewrites):
            # Calculate similarity (simple word overlap)
            similarity = self._calculate_similarity(original_text, rewrite_text)

            # Assess quality
            quality_score = self._assess_rewrite_quality(
                original_text, rewrite_text, mode
            )

            alternatives.append({
                'text': rewrite_text,
                'similarity_to_original': similarity,
                'quality_score': quality_score,
                'changes': self._identify_key_changes(original_text, rewrite_text),
                'word_count': len(rewrite_text.split()),
                'rank': i + 1
            })

        # Sort by quality score
        alternatives.sort(key=lambda x: x['quality_score'], reverse=True)

        # Re-rank after sorting
        for i, alt in enumerate(alternatives):
            alt['rank'] = i + 1

        return {
            'success': True,
            'original_text': original_text,
            'mode': mode,
            'alternatives': alternatives,
            'num_alternatives': len(alternatives),
            'best_alternative': alternatives[0] if alternatives else None
        }

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple word-based similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _assess_rewrite_quality(self, original: str, rewrite: str, mode: str) -> float:
        """Assess quality of rewrite (0-1)"""
        score = 0.5  # Base score

        # Check length is reasonable
        orig_len = len(original.split())
        rewrite_len = len(rewrite.split())

        if mode == 'simplify':
            # Prefer shorter rewrites for simplification
            if rewrite_len < orig_len:
                score += 0.2
        else:
            # For other modes, similar length is good
            length_ratio = min(orig_len, rewrite_len) / max(orig_len, rewrite_len)
            score += 0.2 * length_ratio

        # Check for completeness (not truncated)
        if rewrite.strip().endswith(('.', '!', '?', '"', "'")):
            score += 0.2
        else:
            score -= 0.1

        # Check for proper formatting
        if rewrite[0].isupper() and any(c.isupper() for c in rewrite[1:]):
            score += 0.1

        return min(max(score, 0.0), 1.0)

    def _identify_key_changes(self, original: str, rewrite: str) -> List[str]:
        """Identify key changes between original and rewrite"""
        changes = []

        orig_lower = original.lower()
        rewrite_lower = rewrite.lower()

        # Check for added limitations
        if 'limitation' in rewrite_lower and 'limitation' not in orig_lower:
            changes.append('Added liability limitations')

        if ('cap' in rewrite_lower or 'not exceed' in rewrite_lower) and \
           ('cap' not in orig_lower and 'not exceed' not in orig_lower):
            changes.append('Added financial cap')

        # Check for removed risky terms
        if 'unlimited' in orig_lower and 'unlimited' not in rewrite_lower:
            changes.append('Removed unlimited liability')

        if 'consequential' in orig_lower and 'consequential' not in rewrite_lower:
            changes.append('Removed consequential damages')

        # Check for simplification
        orig_words = len(original.split())
        rewrite_words = len(rewrite.split())

        if rewrite_words < orig_words * 0.8:
            changes.append(f'Simplified language (reduced {orig_words - rewrite_words} words)')

        return changes


# Convenience function
def rewrite_clause_with_ai(
    clause_text: str,
    mode: str = 'reduce_risk',
    custom_instructions: Optional[str] = None,
    provider: str = 'openai'
) -> Dict[str, Any]:
    """Rewrite clause using AI"""
    rewriter = AIClauseRewriter(provider=provider)
    return rewriter.rewrite_clause(clause_text, mode, custom_instructions)
