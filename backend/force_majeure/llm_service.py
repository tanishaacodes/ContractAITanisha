"""
LLM Service for Force Majeure Clause Generation and Rewriting
Uses OpenAI GPT-4 for intelligent clause generation
"""

import os
from openai import OpenAI
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))


class LLMClauseService:
    """Service for LLM-powered clause generation and rewriting"""

    def __init__(self):
        self.model = "gpt-4"  # Use GPT-4 for best results

    def generate_clause(
        self,
        clause_type: str,
        missing_events: List[str],
        contract_context: Optional[Dict] = None,
        industry_standard: str = "FIDIC"
    ) -> str:
        """
        Generate a comprehensive FM clause covering specified events

        Args:
            clause_type: Type of clause (e.g., "force_majeure", "war_risk", "pandemic")
            missing_events: List of FM events to cover
            contract_context: Additional contract context (value, jurisdiction, etc.)
            industry_standard: Standard to follow (FIDIC, NEC, ICC)

        Returns:
            Generated clause text
        """
        prompt = self._build_generation_prompt(
            clause_type, missing_events, contract_context, industry_standard
        )

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent output
                max_tokens=2000
            )

            generated_clause = response.choices[0].message.content
            return generated_clause.strip()

        except Exception as e:
            logger.error(f"LLM clause generation failed: {e}")
            return self._get_fallback_clause(clause_type, missing_events)

    def rewrite_weak_clause(
        self,
        existing_clause: str,
        weakness_analysis: Dict,
        improvement_suggestions: List[str]
    ) -> Dict:
        """
        Rewrite an existing weak FM clause to make it stronger

        Args:
            existing_clause: The current FM clause text
            weakness_analysis: Analysis of weaknesses (missing events, vague language, etc.)
            improvement_suggestions: Specific improvements needed

        Returns:
            Dict with:
                - rewritten_clause: Improved clause text
                - changes_made: List of specific improvements
                - risk_reduction: Estimated risk reduction percentage
        """
        prompt = f"""
Analyze and rewrite the following Force Majeure clause to address its weaknesses:

CURRENT CLAUSE:
{existing_clause}

IDENTIFIED WEAKNESSES:
{self._format_weaknesses(weakness_analysis)}

REQUIRED IMPROVEMENTS:
{chr(10).join(f"- {s}" for s in improvement_suggestions)}

Please rewrite this clause to:
1. Cover all missing FM events
2. Remove vague or ambiguous language
3. Add specific notice requirements
4. Include clear risk allocation mechanisms
5. Define extension-of-time provisions
6. Specify suspension and termination rights

Provide the rewritten clause in a professional legal format suitable for an EPC contract.
"""

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2500
            )

            rewritten_clause = response.choices[0].message.content.strip()

            # Analyze improvements
            changes_made = self._extract_changes(existing_clause, rewritten_clause)
            risk_reduction = self._estimate_risk_reduction(weakness_analysis, changes_made)

            return {
                "rewritten_clause": rewritten_clause,
                "changes_made": changes_made,
                "risk_reduction": risk_reduction,
                "original_clause": existing_clause
            }

        except Exception as e:
            logger.error(f"LLM clause rewriting failed: {e}")
            return {
                "rewritten_clause": existing_clause,
                "changes_made": [],
                "risk_reduction": 0,
                "error": str(e)
            }

    def optimize_multiple_clauses(
        self,
        clauses: List[Dict],
        optimization_goals: List[str]
    ) -> List[Dict]:
        """
        Optimize multiple FM-related clauses for consistency and completeness

        Args:
            clauses: List of clause dicts with {type, text, coverage}
            optimization_goals: Goals like "maximize_protection", "balance_risk", etc.

        Returns:
            List of optimized clauses with recommendations
        """
        results = []

        for clause in clauses:
            optimized = self._optimize_single_clause(clause, optimization_goals)
            results.append(optimized)

        return results

    def generate_negotiation_alternative(
        self,
        original_clause: str,
        party_position: str,
        counterparty_concerns: List[str]
    ) -> Dict:
        """
        Generate alternative clause language for negotiation

        Args:
            original_clause: Current proposed clause
            party_position: "buyer" or "seller"
            counterparty_concerns: List of concerns raised by other party

        Returns:
            Alternative clause with justification
        """
        prompt = f"""
Generate an alternative Force Majeure clause that addresses counterparty concerns while maintaining protection for the {party_position}.

ORIGINAL CLAUSE:
{original_clause}

COUNTERPARTY CONCERNS:
{chr(10).join(f"- {c}" for c in counterparty_concerns)}

Provide:
1. Revised clause that addresses concerns
2. Key compromises made
3. Protections retained
4. Suggested talking points for negotiation
"""

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_negotiation_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=2000
            )

            content = response.choices[0].message.content.strip()

            return {
                "alternative_clause": content,
                "original_clause": original_clause,
                "position": party_position
            }

        except Exception as e:
            logger.error(f"Negotiation alternative generation failed: {e}")
            return {
                "alternative_clause": original_clause,
                "error": str(e)
            }

    def _build_generation_prompt(
        self,
        clause_type: str,
        missing_events: List[str],
        contract_context: Optional[Dict],
        industry_standard: str
    ) -> str:
        """Build prompt for clause generation"""

        context_str = ""
        if contract_context:
            context_str = f"""
CONTRACT CONTEXT:
- Contract Value: ${contract_context.get('value', 'N/A'):,}
- Jurisdiction: {contract_context.get('jurisdiction', 'N/A')}
- Industry: {contract_context.get('industry', 'EPC')}
- Project Duration: {contract_context.get('duration', 'N/A')} months
"""

        prompt = f"""
Generate a comprehensive {clause_type.replace('_', ' ').title()} clause for an EPC construction contract following {industry_standard} standards.

{context_str}

EVENTS TO COVER:
{chr(10).join(f"- {event}" for event in missing_events)}

The clause must include:
1. Clear definition of Force Majeure events
2. Notice requirements (timing, format, content)
3. Mitigation obligations for both parties
4. Extension of time mechanisms
5. Cost allocation provisions
6. Suspension and termination rights
7. Insurance and risk management
8. Dispute resolution procedures

Provide professional legal language suitable for a major construction contract.
"""
        return prompt

    def _get_system_prompt(self) -> str:
        """Get system prompt for general clause work"""
        return """You are an expert construction contract attorney specializing in Force Majeure clauses for EPC (Engineering, Procurement, Construction) contracts.

Your expertise includes:
- FIDIC, NEC, and ICC contract standards
- International construction law
- Risk allocation in major projects
- Force Majeure event definitions and case law
- Pandemic, war, and geopolitical risk clauses

Provide clear, legally sound clause language that balances protection for both parties while clearly allocating risk. Use precise legal terminology and follow industry best practices."""

    def _get_negotiation_prompt(self) -> str:
        """Get system prompt for negotiation scenarios"""
        return """You are an experienced contract negotiator specializing in EPC construction contracts.

Your goal is to find mutually acceptable clause language that:
- Addresses legitimate concerns of both parties
- Maintains essential protections
- Facilitates deal closure
- Follows industry standards

Provide practical, balanced solutions with clear rationale."""

    def _format_weaknesses(self, weakness_analysis: Dict) -> str:
        """Format weakness analysis for prompt"""
        formatted = []

        if "missing_events" in weakness_analysis:
            formatted.append(f"Missing Events: {', '.join(weakness_analysis['missing_events'])}")

        if "weak_events" in weakness_analysis:
            formatted.append(f"Weak Coverage: {', '.join(weakness_analysis['weak_events'])}")

        if "vague_language" in weakness_analysis:
            formatted.append(f"Vague Language: {weakness_analysis['vague_language']}")

        if "missing_protections" in weakness_analysis:
            formatted.append(f"Missing Protections: {', '.join(weakness_analysis['missing_protections'])}")

        return "\n".join(formatted)

    def _extract_changes(self, original: str, rewritten: str) -> List[str]:
        """Extract key changes made in rewrite"""
        # Simple heuristic - in production, use more sophisticated diff
        changes = []

        # Check for new event coverage
        original_lower = original.lower()
        rewritten_lower = rewritten.lower()

        fm_events = [
            "pandemic", "epidemic", "war", "terrorism", "cyber", "sanctions",
            "earthquake", "flood", "hurricane", "wildfire", "strike"
        ]

        for event in fm_events:
            if event in rewritten_lower and event not in original_lower:
                changes.append(f"Added coverage for {event}")

        # Check for new provisions
        provisions = {
            "notice": "Added notice requirements",
            "mitigation": "Added mitigation obligations",
            "extension": "Added extension of time provisions",
            "suspension": "Added suspension rights",
            "insurance": "Added insurance provisions"
        }

        for keyword, change_desc in provisions.items():
            if keyword in rewritten_lower and keyword not in original_lower:
                changes.append(change_desc)

        if not changes:
            changes.append("General language improvements and clarifications")

        return changes

    def _estimate_risk_reduction(self, weakness_analysis: Dict, changes_made: List[str]) -> float:
        """Estimate risk reduction percentage from improvements"""
        # Simple scoring model
        base_score = 0.0

        # Score for each missing event covered
        missing_count = len(weakness_analysis.get("missing_events", []))
        if missing_count > 0:
            base_score += min(30.0, missing_count * 3.0)

        # Score for provisions added
        provision_count = len([c for c in changes_made if "Added" in c])
        base_score += min(25.0, provision_count * 5.0)

        # Score for weak events strengthened
        weak_count = len(weakness_analysis.get("weak_events", []))
        if weak_count > 0:
            base_score += min(20.0, weak_count * 4.0)

        # Cap at 75% (never claim 100% risk elimination)
        return min(75.0, base_score)

    def _get_fallback_clause(self, clause_type: str, missing_events: List[str]) -> str:
        """Return fallback clause if LLM fails"""
        events_str = ", ".join(missing_events[:5])  # Limit to 5 events

        return f"""
FORCE MAJEURE

1. Definition. "Force Majeure Event" means any event beyond the reasonable control of a Party, including but not limited to: {events_str}, which directly prevents or delays the performance of obligations under this Contract.

2. Notice. The affected Party shall promptly notify the other Party in writing of the Force Majeure Event, including its expected duration and impact.

3. Consequences. Upon occurrence of a Force Majeure Event:
   (a) The affected Party's obligations shall be suspended to the extent prevented by such event;
   (b) Time for performance shall be extended by the duration of the Force Majeure Event;
   (c) Neither Party shall be liable for damages arising from delays or non-performance due to Force Majeure.

4. Mitigation. Both Parties shall use reasonable efforts to mitigate the effects of the Force Majeure Event.

5. Termination. If a Force Majeure Event continues for more than [180] days, either Party may terminate this Contract upon [30] days' written notice.

[Note: This is a template clause. Please have it reviewed by legal counsel before use.]
"""

    def _optimize_single_clause(self, clause: Dict, goals: List[str]) -> Dict:
        """Optimize a single clause based on goals"""
        # Simplified implementation - full version would use LLM
        return {
            **clause,
            "optimized": True,
            "recommendations": [
                "Consider adding specific notice timeline",
                "Define mitigation obligations more clearly",
                "Specify cost allocation mechanism"
            ]
        }


# Global instance
llm_clause_service = LLMClauseService()


def generate_fm_clause(
    missing_events: List[str],
    contract_value: float = None,
    jurisdiction: str = None,
    industry_standard: str = "FIDIC"
) -> str:
    """
    Convenience function to generate FM clause
    """
    context = {}
    if contract_value:
        context["value"] = contract_value
    if jurisdiction:
        context["jurisdiction"] = jurisdiction

    return llm_clause_service.generate_clause(
        "force_majeure",
        missing_events,
        context,
        industry_standard
    )


def rewrite_clause(
    existing_clause: str,
    missing_events: List[str],
    weak_events: List[str]
) -> Dict:
    """
    Convenience function to rewrite a weak clause
    """
    weakness_analysis = {
        "missing_events": missing_events,
        "weak_events": weak_events
    }

    improvements = [
        f"Add coverage for: {', '.join(missing_events)}",
        f"Strengthen coverage for: {', '.join(weak_events)}",
        "Add clear notice requirements",
        "Define mitigation obligations"
    ]

    return llm_clause_service.rewrite_weak_clause(
        existing_clause,
        weakness_analysis,
        improvements
    )
