"""
Intent Detection Engine

Classifies contract intent and identifies liability patterns.
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class IntentEngine:
    """
    Contract Intent Classification Engine

    Detects contract intent categories:
    - HIGH_LIABILITY: Unlimited indemnity, uncapped liability
    - TERMINATION_SENSITIVE: Asymmetric termination clauses
    - EXCLUSIVITY_RISK: Exclusivity or lock-in clauses
    - STANDARD: Standard commercial terms
    - PROTECTIVE: Favorable protective clauses
    """

    # Intent patterns
    INTENT_PATTERNS = {
        'HIGH_LIABILITY': [
            'unlimited indemnity',
            'unlimited liability',
            'indemnify and hold harmless',
            'no limitation of liability',
            'uncapped liability',
            'joint and several liability'
        ],
        'TERMINATION_SENSITIVE': [
            'termination',
            'termination for convenience',
            'immediate termination',
            'termination without cause',
            'early termination penalty'
        ],
        'EXCLUSIVITY_RISK': [
            'exclusivity',
            'exclusive',
            'non-compete',
            'sole supplier',
            'preferred supplier',
            'lock-in'
        ],
        'IP_TRANSFER': [
            'intellectual property',
            'ip rights',
            'patent',
            'copyright',
            'transfer of rights',
            'work for hire'
        ],
        'REGULATORY_COMPLIANCE': [
            'compliance',
            'regulatory',
            'gdpr',
            'data protection',
            'sox compliance',
            'audit rights'
        ]
    }

    def detect(self, contract: Dict[str, Any]) -> str:
        """
        Detect primary contract intent

        Args:
            contract: SAP contract data

        Returns:
            Intent category string
        """
        try:
            data = contract.get('d', contract)

            # Extract text fields
            description = data.get('PurchaseContractDesc', '').lower()
            contract_type = data.get('PurchaseContractType', '').lower()
            text = data.get('ContractText', '').lower()

            combined_text = f"{description} {contract_type} {text}"

            # Check patterns
            detected_intents = []

            for intent, patterns in self.INTENT_PATTERNS.items():
                for pattern in patterns:
                    if pattern in combined_text:
                        detected_intents.append(intent)
                        break

            # Return highest risk intent
            if 'HIGH_LIABILITY' in detected_intents:
                return 'HIGH_LIABILITY'
            elif 'TERMINATION_SENSITIVE' in detected_intents:
                return 'TERMINATION_SENSITIVE'
            elif 'EXCLUSIVITY_RISK' in detected_intents:
                return 'EXCLUSIVITY_RISK'
            elif 'IP_TRANSFER' in detected_intents:
                return 'IP_TRANSFER'
            elif 'REGULATORY_COMPLIANCE' in detected_intents:
                return 'REGULATORY_COMPLIANCE'
            else:
                return 'STANDARD'

        except Exception as e:
            logger.error(f"Error detecting intent: {e}")
            return 'STANDARD'

    def detect_all(self, contract: Dict[str, Any]) -> List[str]:
        """
        Detect all applicable intents

        Args:
            contract: SAP contract data

        Returns:
            List of detected intent categories
        """
        try:
            data = contract.get('d', contract)

            description = data.get('PurchaseContractDesc', '').lower()
            contract_type = data.get('PurchaseContractType', '').lower()
            text = data.get('ContractText', '').lower()

            combined_text = f"{description} {contract_type} {text}"

            detected_intents = []

            for intent, patterns in self.INTENT_PATTERNS.items():
                for pattern in patterns:
                    if pattern in combined_text:
                        detected_intents.append(intent)
                        break

            return detected_intents if detected_intents else ['STANDARD']

        except Exception as e:
            logger.error(f"Error detecting intents: {e}")
            return ['STANDARD']

    def get_intent_description(self, intent: str) -> str:
        """Get human-readable description of intent"""
        descriptions = {
            'HIGH_LIABILITY': 'Contains unlimited or uncapped liability clauses',
            'TERMINATION_SENSITIVE': 'Contains asymmetric termination provisions',
            'EXCLUSIVITY_RISK': 'Contains exclusivity or lock-in clauses',
            'IP_TRANSFER': 'Involves intellectual property rights transfer',
            'REGULATORY_COMPLIANCE': 'Subject to regulatory compliance requirements',
            'STANDARD': 'Standard commercial terms'
        }
        return descriptions.get(intent, 'Unknown intent')
