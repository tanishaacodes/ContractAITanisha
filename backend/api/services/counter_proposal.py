"""
Counter-Proposal Generation Service
=====================================
Generate AI-powered counter-proposals for contract negotiations.

Features:
1. Analyze proposed clauses
2. Generate counter-proposals that address concerns
3. Suggest compromises and alternatives
4. Assess likelihood of acceptance
5. Track negotiation strategy
"""

import logging
from typing import Dict, Any, Optional, List
from .ai_clause_rewriter import AIClauseRewriter

logger = logging.getLogger(__name__)


class CounterProposalGenerator:
    """
    Generate counter-proposals for contract negotiations.
    """

    COUNTER_PROPOSAL_PROMPT = """You are an expert contract negotiator.

Given a proposed clause, generate a counter-proposal that:
1. Addresses the underlying business concern
2. Protects your client's interests
3. Offers a balanced, reasonable alternative
4. Maintains a constructive negotiating tone
5. Includes brief rationale for changes

Format your response as:

COUNTER-PROPOSAL:
[The alternative clause text]

RATIONALE:
[Brief explanation of why this addresses concerns while protecting interests]

COMPROMISE SUGGESTIONS:
[Optional: Suggest 2-3 middle-ground positions]"""

    def __init__(self, provider: str = 'openai'):
        """Initialize counter-proposal generator"""
        self.rewriter = AIClauseRewriter(provider=provider)
        self.logger = logger

    def generate_counter_proposal(
        self,
        proposed_clause: str,
        concerns: Optional[List[str]] = None,
        your_position: Optional[str] = None,
        counterparty_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a counter-proposal for a proposed clause.

        Args:
            proposed_clause: The clause being proposed
            concerns: List of concerns about the proposed clause
            your_position: Your negotiating position (client/vendor)
            counterparty_profile: Optional counterparty behavior profile

        Returns:
            Dict with counter-proposal and analysis
        """
        try:
            # Build custom instructions
            instructions = self._build_counter_proposal_instructions(
                concerns=concerns,
                your_position=your_position,
                counterparty_profile=counterparty_profile
            )

            # Use AI rewriter in counter-proposal mode
            result = self.rewriter.rewrite_clause(
                clause_text=proposed_clause,
                rewrite_mode='counter_proposal',
                custom_instructions=instructions,
                num_alternatives=3
            )

            if not result['success']:
                return result

            # Parse counter-proposals
            counter_proposals = self._parse_counter_proposals(result['alternatives'])

            # Assess acceptance likelihood
            for proposal in counter_proposals:
                proposal['acceptance_likelihood'] = self._assess_acceptance_likelihood(
                    proposed_clause,
                    proposal['text'],
                    counterparty_profile
                )

            # Sort by acceptance likelihood
            counter_proposals.sort(key=lambda x: x['acceptance_likelihood'], reverse=True)

            return {
                'success': True,
                'proposed_clause': proposed_clause,
                'concerns': concerns or [],
                'counter_proposals': counter_proposals,
                'recommended_proposal': counter_proposals[0] if counter_proposals else None,
                'negotiation_strategy': self._generate_negotiation_strategy(
                    proposed_clause,
                    counter_proposals
                )
            }

        except Exception as e:
            self.logger.error(f"[COUNTER-PROPOSAL] Error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _build_counter_proposal_instructions(
        self,
        concerns: Optional[List[str]],
        your_position: Optional[str],
        counterparty_profile: Optional[Dict[str, Any]]
    ) -> str:
        """Build custom instructions for counter-proposal"""
        instructions = []

        if concerns:
            instructions.append(f"Address these specific concerns: {'; '.join(concerns)}")

        if your_position:
            if your_position.lower() == 'client':
                instructions.append("You represent the client/buyer. Strengthen protections while being reasonable.")
            elif your_position.lower() == 'vendor':
                instructions.append("You represent the vendor/supplier. Limit liability reasonably while maintaining client confidence.")

        if counterparty_profile:
            aggressiveness = counterparty_profile.get('aggressiveness_score', 0.5)
            if aggressiveness > 0.7:
                instructions.append("This counterparty is aggressive. Propose firm but fair positions.")
            elif aggressiveness < 0.3:
                instructions.append("This counterparty is flexible. Propose collaborative solutions.")

        return " ".join(instructions) if instructions else None

    def _parse_counter_proposals(self, alternatives: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse counter-proposals from AI responses"""
        proposals = []

        for i, alt in enumerate(alternatives):
            text = alt['text']

            # Try to extract structured parts
            counter_proposal_text = text
            rationale = ""
            compromises = []

            # Parse structured response if present
            if "COUNTER-PROPOSAL:" in text:
                parts = text.split("RATIONALE:")
                if len(parts) >= 2:
                    counter_proposal_text = parts[0].replace("COUNTER-PROPOSAL:", "").strip()
                    rationale_part = parts[1].split("COMPROMISE SUGGESTIONS:")[0].strip()
                    rationale = rationale_part

                    if "COMPROMISE SUGGESTIONS:" in text:
                        compromise_text = text.split("COMPROMISE SUGGESTIONS:")[1].strip()
                        compromises = [c.strip() for c in compromise_text.split('\n') if c.strip()]

            proposals.append({
                'text': counter_proposal_text,
                'rationale': rationale,
                'compromises': compromises,
                'rank': i + 1,
                'quality_score': alt.get('quality_score', 0.5),
                'changes': alt.get('changes', [])
            })

        return proposals

    def _assess_acceptance_likelihood(
        self,
        proposed: str,
        counter: str,
        counterparty_profile: Optional[Dict[str, Any]]
    ) -> float:
        """
        Assess likelihood that counter-proposal will be accepted.

        Factors:
        - Similarity to original (closer = more likely)
        - Counterparty profile (flexible vs aggressive)
        - Reasonableness of changes
        """
        likelihood = 0.5  # Base 50% chance

        # Factor 1: Similarity to original
        similarity = self._calculate_similarity(proposed, counter)
        likelihood += 0.3 * similarity

        # Factor 2: Counterparty profile
        if counterparty_profile:
            aggressiveness = counterparty_profile.get('aggressiveness_score', 0.5)
            # More aggressive counterparties less likely to accept changes
            likelihood -= 0.2 * aggressiveness

            # Flexibility/elasticity
            elasticity = counterparty_profile.get('elasticity_score', 0.5)
            likelihood += 0.1 * elasticity

        # Cap at 0-1 range
        return min(max(likelihood, 0.0), 0.95)  # Max 95% (never certain)

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate word-based similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _generate_negotiation_strategy(
        self,
        proposed_clause: str,
        counter_proposals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate negotiation strategy recommendations"""
        best_proposal = counter_proposals[0] if counter_proposals else None

        if not best_proposal:
            return {
                'approach': 'REJECT',
                'reasoning': 'Unable to generate acceptable counter-proposal',
                'suggested_action': 'Request significant changes or reject clause'
            }

        acceptance_likelihood = best_proposal.get('acceptance_likelihood', 0.5)

        if acceptance_likelihood >= 0.7:
            approach = 'CONFIDENT'
            reasoning = 'Counter-proposal is reasonable and likely to be accepted'
            action = 'Present counter-proposal confidently'
        elif acceptance_likelihood >= 0.5:
            approach = 'COLLABORATIVE'
            reasoning = 'Counter-proposal has moderate chance of acceptance'
            action = 'Present counter-proposal and be ready to discuss compromises'
        else:
            approach = 'CAUTIOUS'
            reasoning = 'Counter-proposal may face resistance'
            action = 'Present counter-proposal with strong rationale and be ready for multiple rounds'

        return {
            'approach': approach,
            'reasoning': reasoning,
            'suggested_action': action,
            'acceptance_likelihood': round(acceptance_likelihood * 100, 1),
            'fallback_positions': best_proposal.get('compromises', [])
        }

    def analyze_clause_for_negotiation(
        self,
        clause_text: str,
        clause_type: str,
        counterparty_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a clause to determine if negotiation is needed.

        Returns:
            Dict with risk analysis and negotiation recommendations
        """
        try:
            # Identify risk factors
            risk_keywords = {
                'unlimited': 'high',
                'without limitation': 'high',
                'consequential damages': 'high',
                'indirect damages': 'high',
                'punitive damages': 'high',
                'indemnify': 'medium',
                'sole liability': 'medium',
                'termination': 'medium',
                'breach': 'medium',
            }

            clause_lower = clause_text.lower()
            detected_risks = []

            for keyword, severity in risk_keywords.items():
                if keyword in clause_lower:
                    detected_risks.append({
                        'keyword': keyword,
                        'severity': severity
                    })

            # Calculate overall risk score
            risk_score = 0.3  # Base
            for risk in detected_risks:
                if risk['severity'] == 'high':
                    risk_score += 0.2
                elif risk['severity'] == 'medium':
                    risk_score += 0.1

            risk_score = min(risk_score, 1.0)

            # Determine if negotiation is recommended
            should_negotiate = risk_score >= 0.6 or len(detected_risks) >= 3

            return {
                'success': True,
                'clause_text': clause_text,
                'clause_type': clause_type,
                'risk_score': round(risk_score, 2),
                'detected_risks': detected_risks,
                'should_negotiate': should_negotiate,
                'recommendation': self._generate_negotiation_recommendation(
                    risk_score,
                    detected_risks,
                    counterparty_profile
                )
            }

        except Exception as e:
            self.logger.error(f"[CLAUSE-ANALYSIS] Error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_negotiation_recommendation(
        self,
        risk_score: float,
        risks: List[Dict[str, Any]],
        counterparty_profile: Optional[Dict[str, Any]]
    ) -> str:
        """Generate recommendation text"""
        if risk_score >= 0.8:
            return (
                f"⚠️ HIGH RISK: This clause has {len(risks)} risk factors. "
                "Strong negotiation recommended. Consider counter-proposal or rejection."
            )
        elif risk_score >= 0.6:
            return (
                f"⚠️ MODERATE RISK: This clause has {len(risks)} risk factors. "
                "Negotiation recommended to add protections or limitations."
            )
        else:
            return (
                f"✅ LOW RISK: This clause appears reasonable. "
                "Minor adjustments may be beneficial but not critical."
            )


# Convenience functions
def generate_counter_proposal(
    proposed_clause: str,
    concerns: Optional[List[str]] = None,
    provider: str = 'openai'
) -> Dict[str, Any]:
    """Generate counter-proposal for a clause"""
    generator = CounterProposalGenerator(provider=provider)
    return generator.generate_counter_proposal(proposed_clause, concerns)


def analyze_for_negotiation(
    clause_text: str,
    clause_type: str
) -> Dict[str, Any]:
    """Analyze if a clause needs negotiation"""
    generator = CounterProposalGenerator()
    return generator.analyze_clause_for_negotiation(clause_text, clause_type)
