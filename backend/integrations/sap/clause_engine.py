"""
Clause Suggestion Engine

Generates clause improvement recommendations based on risk analysis.
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ClauseEngine:
    """
    AI Clause Suggestion Engine

    Analyzes contract risk and generates specific clause recommendations
    to mitigate identified risks.
    """

    def suggest(self, contract: Dict[str, Any], risk_score: int) -> List[str]:
        """
        Generate clause suggestions based on contract analysis

        Args:
            contract: SAP contract data
            risk_score: Calculated risk score (0-100)

        Returns:
            List of clause improvement suggestions
        """
        try:
            suggestions = []
            data = contract.get('d', contract)

            # Extract text
            description = data.get('PurchaseContractDesc', '').upper()
            text = data.get('ContractText', '').upper()
            combined_text = f"{description} {text}"

            # High risk contracts need immediate attention
            if risk_score > 80:
                suggestions.append(
                    "🔴 CRITICAL: This contract requires immediate legal review "
                    "due to high risk score"
                )

            # Liability clause recommendations
            if 'UNLIMITED' in combined_text and 'INDEMNITY' in combined_text:
                suggestions.extend([
                    "⚠️ Add liability cap: Limit indemnity to the contract value",
                    "⚠️ Add specific exclusions: Exclude indirect, consequential, "
                    "and punitive damages",
                    "⚠️ Add insurance requirement: Require counterparty to maintain "
                    "appropriate insurance coverage"
                ])

            if 'INDEMNITY' in combined_text and 'LIABILITY CAP' not in combined_text:
                suggestions.append(
                    "💡 Insert liability limitation clause: "
                    "'Liability under this contract shall not exceed the total "
                    "contract value'"
                )

            # Payment terms recommendations
            payment_terms = str(data.get('PaymentTerms', ''))
            if '90' in payment_terms or '120' in payment_terms:
                suggestions.extend([
                    "💰 Consider shorter payment terms to reduce financial exposure",
                    "💰 Add milestone-based payment schedule",
                    "💰 Include early payment discount incentive"
                ])

            # Termination recommendations
            if 'TERMINATION' in combined_text:
                if 'TERMINATION FOR CONVENIENCE' not in combined_text:
                    suggestions.append(
                        "📋 Add mutual termination for convenience clause with "
                        "60-day notice period"
                    )

            # Dispute resolution
            if 'ARBITRATION' not in combined_text and 'DISPUTE' not in combined_text:
                suggestions.append(
                    "⚖️ Add arbitration clause: Include binding arbitration provision "
                    "for dispute resolution"
                )

            # Force majeure
            if 'FORCE MAJEURE' not in combined_text and risk_score > 50:
                suggestions.append(
                    "🌪️ Add force majeure clause to protect against unforeseeable events"
                )

            # Confidentiality
            if 'CONFIDENTIAL' not in combined_text:
                suggestions.append(
                    "🔒 Add confidentiality and non-disclosure provisions"
                )

            # IP protection
            if 'INTELLECTUAL PROPERTY' in combined_text or 'IP' in combined_text:
                if 'RETAIN' not in combined_text:
                    suggestions.append(
                        "🧠 Clarify IP ownership: Ensure pre-existing IP remains "
                        "with originating party"
                    )

            # Audit rights
            if risk_score > 60:
                suggestions.append(
                    "📊 Add audit rights clause: Include right to audit compliance "
                    "with contract terms"
                )

            # Warranty
            if 'WARRANTY' not in combined_text and risk_score > 40:
                suggestions.append(
                    "✅ Add warranty provisions for goods/services quality"
                )

            # Currency hedge
            currency = data.get('DocumentCurrency', '')
            if currency not in ['INR', '']:
                suggestions.append(
                    f"💱 Consider currency hedge for {currency} exposure"
                )

            # Default if no suggestions
            if not suggestions:
                suggestions.append(
                    "✓ Contract terms appear standard. No critical modifications required."
                )

            return suggestions

        except Exception as e:
            logger.error(f"Error generating clause suggestions: {e}")
            return ["Unable to generate suggestions due to analysis error"]

    def generate_redline_summary(
        self,
        contract: Dict[str, Any],
        suggestions: List[str]
    ) -> str:
        """
        Generate a formatted redline summary for SAP notes

        Args:
            contract: SAP contract data
            suggestions: List of clause suggestions

        Returns:
            Formatted text suitable for SAP note
        """
        try:
            data = contract.get('d', contract)
            contract_id = data.get('PurchaseContract', 'Unknown')

            summary = f"""
AI CONTRACT ANALYSIS - {contract_id}
Generated: {self._get_timestamp()}

RECOMMENDED MODIFICATIONS:
{'=' * 50}

"""
            for i, suggestion in enumerate(suggestions, 1):
                summary += f"{i}. {suggestion}\n\n"

            summary += f"""
{'=' * 50}
This analysis was performed by PrimeContractAI.
Please review with legal counsel before execution.
"""

            return summary

        except Exception as e:
            logger.error(f"Error generating redline summary: {e}")
            return "Error generating summary"

    @staticmethod
    def _get_timestamp() -> str:
        """Get formatted timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
