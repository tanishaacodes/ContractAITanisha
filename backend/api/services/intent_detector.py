"""
Contract Intent Detection Service
Uses MiniLM embeddings to detect negotiation intents in contract clauses.
"""

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging

logger = logging.getLogger(__name__)


class IntentDetectorService:
    """
    Detects negotiation intents in contract text using semantic similarity.
    """

    # Intent categories and their semantic anchors
    INTENT_TEMPLATES = {
        "risk_transfer": [
            "party shall bear all risks and liabilities",
            "transfer of risk and liability to contractor",
            "indemnify and hold harmless from all claims",
            "assume full responsibility for damages",
            "at contractor's sole risk and expense",
            "contractor shall defend and indemnify",
            "vendor assumes all risk of loss",
            "party responsible for all consequences"
        ],
        "liability_shielding": [
            "limitation of liability to contract value",
            "exclude all consequential and indirect damages",
            "cap on total damages and liability",
            "no liability for loss of profits or business",
            "maximum aggregate liability shall not exceed",
            "limited to direct damages only",
            "liability capped at fees paid",
            "excluding punitive and exemplary damages"
        ],
        "payment_control": [
            "payment due within thirty days of invoice",
            "advance payment of fifty percent required",
            "payment contingent upon satisfactory delivery",
            "right to withhold payment for defects",
            "milestone-based installment payment schedule",
            "payment net sixty days after completion",
            "invoice payable upon receipt",
            "late payment interest and penalties"
        ],
        "termination_leverage": [
            "either party may terminate without cause",
            "termination with thirty days written notice",
            "immediate termination for material breach",
            "early termination penalty and fees",
            "right to terminate at will upon notice",
            "termination for convenience by either party",
            "notice period required for termination",
            "consequences of early contract termination"
        ],
        "compliance_burden": [
            "comply with all applicable laws and regulations",
            "maintain required licenses and certifications",
            "adhere to industry standards and best practices",
            "subject to third party audits and inspections",
            "regulatory compliance obligations and reporting",
            "certification and quality assurance requirements",
            "compliance with data protection regulations",
            "adherence to safety and environmental standards"
        ]
    }

    def __init__(self):
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2", device='cpu')
        self._intent_embeddings = None

    def _get_intent_embeddings(self):
        """Lazy load and cache intent template embeddings."""
        if self._intent_embeddings is None:
            self._intent_embeddings = {}
            for intent, templates in self.INTENT_TEMPLATES.items():
                embeddings = [self.embedder.encode(t) for t in templates]
                # Average embedding as the intent prototype
                self._intent_embeddings[intent] = np.mean(embeddings, axis=0)
        return self._intent_embeddings

    def detect_intents(self, text):
        """
        Detect all intent strengths in given text.

        Args:
            text: Contract clause or section text

        Returns:
            dict: Intent name -> strength score (0-1)
        """
        try:
            if not text or len(text.strip()) < 10:
                return {intent: 0.0 for intent in self.INTENT_TEMPLATES.keys()}

            # Apply clause name heuristics as boost
            text_lower = text.lower()
            heuristic_boost = {
                "risk_transfer": 0.0,
                "liability_shielding": 0.0,
                "payment_control": 0.0,
                "termination_leverage": 0.0,
                "compliance_burden": 0.0
            }

            # Boost based on clause type keywords
            if any(kw in text_lower for kw in ['indemnif', 'hold harmless', 'defend', 'risk transfer']):
                heuristic_boost["risk_transfer"] = 0.3
            if any(kw in text_lower for kw in ['limitation of liability', 'cap', 'exclude', 'consequential', 'indirect damage']):
                heuristic_boost["liability_shielding"] = 0.3
            if any(kw in text_lower for kw in ['payment', 'invoice', 'fees', 'installment', 'withhold']):
                heuristic_boost["payment_control"] = 0.3
            if any(kw in text_lower for kw in ['terminat', 'cancel', 'notice period', 'early exit']):
                heuristic_boost["termination_leverage"] = 0.3
            if any(kw in text_lower for kw in ['compliance', 'regulat', 'audit', 'certif', 'standard']):
                heuristic_boost["compliance_burden"] = 0.3

            text_embedding = self.embedder.encode(text)
            intent_embeddings = self._get_intent_embeddings()

            intent_scores = {}
            for intent, prototype in intent_embeddings.items():
                similarity = cosine_similarity([text_embedding], [prototype])[0][0]

                # Calibrated scoring for legal text:
                # cosine similarity typically ranges from 0.3 (unrelated) to 0.9 (highly related)
                # We need to map this to a 0-1 scale with better differentiation

                if similarity < 0.35:
                    # Very weak/no intent
                    score = 0.0
                elif similarity < 0.5:
                    # Weak intent - map 0.35-0.5 to 0.0-0.3
                    score = (similarity - 0.35) / (0.5 - 0.35) * 0.3
                elif similarity < 0.65:
                    # Moderate intent - map 0.5-0.65 to 0.3-0.6
                    score = 0.3 + (similarity - 0.5) / (0.65 - 0.5) * 0.3
                else:
                    # Strong intent - map 0.65-1.0 to 0.6-1.0
                    score = 0.6 + (similarity - 0.65) / (1.0 - 0.65) * 0.4

                # Apply heuristic boost
                boosted_score = min(1.0, score + heuristic_boost.get(intent, 0.0))
                intent_scores[intent] = round(float(max(0.0, boosted_score)), 3)

            return intent_scores

        except Exception as e:
            logger.error(f"Error detecting intents: {e}")
            return {intent: 0.0 for intent in self.INTENT_TEMPLATES.keys()}

    def detect_section_intents(self, sections):
        """
        Detect intents for multiple contract sections.

        Args:
            sections: List of dicts with 'name' and 'text' keys

        Returns:
            list: Section intent mappings
        """
        results = []
        for section in sections:
            intents = self.detect_intents(section.get('text', ''))
            results.append({
                'section': section.get('name', 'Unknown'),
                **intents
            })
        return results

    def calculate_intent_drift(self, old_intents, new_intents):
        """
        Calculate drift between two intent vectors.

        Args:
            old_intents: dict of intent scores
            new_intents: dict of intent scores

        Returns:
            float: Drift score (0-1)
        """
        try:
            if not old_intents or not new_intents:
                return 0.0

            drift_sum = 0
            count = 0
            for intent in self.INTENT_TEMPLATES.keys():
                old_val = old_intents.get(intent, 0)
                new_val = new_intents.get(intent, 0)
                drift_sum += abs(old_val - new_val)
                count += 1

            # Average drift
            avg_drift = drift_sum / count if count > 0 else 0
            return round(float(avg_drift), 3)

        except Exception as e:
            logger.error(f"Error calculating intent drift: {e}")
            return 0.0

    def detect_counterparty_bias(self, intents):
        """
        Estimate counterparty bias from intent vector.

        High risk_transfer + high termination_leverage = biased toward one party

        Args:
            intents: dict of intent scores

        Returns:
            dict: bias level and score
        """
        try:
            # Heuristic: high risk transfer + termination leverage = bias
            risk_transfer = intents.get('risk_transfer', 0)
            termination = intents.get('termination_leverage', 0)
            liability = intents.get('liability_shielding', 0)

            # Weighted bias calculation
            bias_score = (risk_transfer * 0.4) + (termination * 0.3) + (liability * 0.3)

            if bias_score > 0.7:
                level = "HIGH"
            elif bias_score > 0.4:
                level = "MEDIUM"
            else:
                level = "LOW"

            return {
                "level": level,
                "score": round(float(bias_score), 3)
            }

        except Exception as e:
            logger.error(f"Error detecting counterparty bias: {e}")
            return {"level": "LOW", "score": 0.0}

    def get_dominant_intent(self, intents):
        """Get the strongest intent from an intent vector."""
        if not intents:
            return None

        max_intent = max(intents.items(), key=lambda x: x[1])
        return {
            "intent": max_intent[0],
            "strength": max_intent[1]
        }


# Singleton instance
_intent_detector_instance = None

def get_intent_detector():
    """Get singleton instance of IntentDetectorService."""
    global _intent_detector_instance
    if _intent_detector_instance is None:
        _intent_detector_instance = IntentDetectorService()
    return _intent_detector_instance
