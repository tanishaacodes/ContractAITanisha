"""
Fusion Classification Layer
===========================
Combines BERTopic (unsupervised topic modeling) with Contracts-BERT (intent extraction)
to achieve high-accuracy, explainable contract classification.

Architecture:
1. BERTopic → Discovers latent themes/topics (60% weight)
2. Contracts-BERT → Extracts legal intents (40% weight)
3. Fusion → Rule-based scoring engine combines both
"""

from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class FusionClassifier:
    """
    Enterprise-grade contract classification using BERTopic + Contracts-BERT fusion.
    """

    def __init__(self):
        # Contract type rules: maps contract types to expected topics and intents
        self.contract_rules = {
            "Master Service Agreement": {
                "topics": ["service", "msa", "master", "agreement", "professional"],
                "intents": ["Services", "Liability", "Indemnity", "Termination", "Payment"],
                "weights": {"topics": 0.6, "intents": 0.4}
            },
            "Non-Disclosure Agreement": {
                "topics": ["confidential", "nda", "disclosure", "proprietary", "secret"],
                "intents": ["Confidentiality", "Intellectual Property", "Termination"],
                "weights": {"topics": 0.7, "intents": 0.3}
            },
            "Employment Agreement": {
                "topics": ["employment", "employee", "hire", "position", "salary"],
                "intents": ["Payment", "Services", "Confidentiality", "Termination", "Intellectual Property"],
                "weights": {"topics": 0.6, "intents": 0.4}
            },
            "Sales Agreement": {
                "topics": ["sales", "purchase", "buyer", "seller", "goods", "products"],
                "intents": ["Payment", "Delivery", "Warranties", "Liability"],
                "weights": {"topics": 0.65, "intents": 0.35}
            },
            "Vendor Agreement": {
                "topics": ["vendor", "supplier", "supply", "procurement"],
                "intents": ["Payment", "Delivery", "Warranties", "Liability", "Termination"],
                "weights": {"topics": 0.6, "intents": 0.4}
            },
            "Service Level Agreement": {
                "topics": ["sla", "service level", "uptime", "performance", "availability"],
                "intents": ["Services", "Warranties", "Liability", "Termination"],
                "weights": {"topics": 0.7, "intents": 0.3}
            },
            "Consulting Agreement": {
                "topics": ["consulting", "consultant", "advisor", "advisory", "professional"],
                "intents": ["Services", "Payment", "Intellectual Property", "Confidentiality"],
                "weights": {"topics": 0.6, "intents": 0.4}
            },
            "Lease Agreement": {
                "topics": ["lease", "rent", "tenant", "landlord", "property", "premises"],
                "intents": ["Payment", "Termination", "Liability", "Notice"],
                "weights": {"topics": 0.7, "intents": 0.3}
            },
            "Partnership Agreement": {
                "topics": ["partner", "partnership", "joint", "collaboration", "equity"],
                "intents": ["Services", "Payment", "Intellectual Property", "Dispute Resolution", "Termination"],
                "weights": {"topics": 0.6, "intents": 0.4}
            },
            "Licensing Agreement": {
                "topics": ["license", "licensing", "intellectual property", "software", "rights"],
                "intents": ["Intellectual Property", "Payment", "Warranties", "Termination"],
                "weights": {"topics": 0.65, "intents": 0.35}
            }
        }

    def classify_contract(
        self,
        topic_result: Dict,
        intent_distribution: Dict[str, float]
    ) -> Dict:
        """
        Fuse BERTopic and Contracts-BERT results to produce final classification.

        Args:
            topic_result: BERTopic output
                {
                    "contractType": "Topic name",
                    "confidenceScore": 0.75,
                    "topicId": 2
                }
            intent_distribution: BERT intent weights
                {
                    "Payment": 0.35,
                    "Termination": 0.20,
                    ...
                }

        Returns:
            {
                "primary_class": "Master Service Agreement",
                "confidence": 0.87,
                "topics": {...},
                "intents": {...},
                "fused_scores": {"MSA": 0.87, "Sales Agreement": 0.12, ...},
                "explanation": "Classification based on..."
            }
        """
        # Calculate fusion scores for each contract type
        fused_scores = {}

        for contract_type, rules in self.contract_rules.items():
            topic_score = self._calculate_topic_score(topic_result, rules)
            intent_score = self._calculate_intent_score(intent_distribution, rules)

            # Weighted combination
            topic_weight = rules["weights"]["topics"]
            intent_weight = rules["weights"]["intents"]

            fused_score = (topic_weight * topic_score) + (intent_weight * intent_score)
            fused_scores[contract_type] = round(fused_score, 3)

        # Normalize scores to sum to 1.0
        total_score = sum(fused_scores.values())
        if total_score > 0:
            normalized_scores = {
                k: round(v / total_score, 3)
                for k, v in fused_scores.items()
            }
        else:
            # Fallback: use BERTopic result only
            normalized_scores = {topic_result.get("contractType", "Unknown"): 1.0}

        # Get primary classification (highest score)
        primary_class = max(normalized_scores, key=normalized_scores.get)
        confidence = normalized_scores[primary_class]

        # Generate explanation
        explanation = self._generate_explanation(
            primary_class,
            topic_result,
            intent_distribution,
            normalized_scores
        )

        return {
            "primary_class": primary_class,
            "confidence": round(confidence * 100, 2),  # Convert to percentage
            "topics": topic_result,
            "intents": intent_distribution,
            "fused_scores": normalized_scores,
            "explanation": explanation,
            "classifier": "fusion"
        }

    def _calculate_topic_score(self, topic_result: Dict, rules: Dict) -> float:
        """
        Calculate how well the BERTopic result matches the contract type rules.

        Args:
            topic_result: BERTopic classification result
            rules: Contract type rules (expected topics)

        Returns:
            Score between 0.0 and 1.0
        """
        topic_name = topic_result.get("contractType", "").lower()
        topic_confidence = topic_result.get("confidenceScore", 0) / 100.0  # Convert to 0-1
        expected_topics = rules["topics"]

        # Check if any expected topic keywords are in the BERTopic result
        keyword_match_score = 0.0
        for keyword in expected_topics:
            if keyword.lower() in topic_name:
                keyword_match_score += 0.2  # Each match adds 20%

        # Cap at 1.0
        keyword_match_score = min(1.0, keyword_match_score)

        # Combine keyword match with BERTopic confidence
        # 70% keyword match, 30% BERTopic confidence
        final_score = (0.7 * keyword_match_score) + (0.3 * topic_confidence)

        return final_score

    def _calculate_intent_score(self, intent_distribution: Dict[str, float], rules: Dict) -> float:
        """
        Calculate how well the BERT intents match the contract type rules.

        Args:
            intent_distribution: Dict of intent weights
            rules: Contract type rules (expected intents)

        Returns:
            Score between 0.0 and 1.0
        """
        if not intent_distribution:
            return 0.0

        expected_intents = rules["intents"]

        # Sum weights for expected intents
        intent_score = sum(
            intent_distribution.get(intent, 0)
            for intent in expected_intents
        )

        return min(1.0, intent_score)  # Cap at 1.0

    def _generate_explanation(
        self,
        primary_class: str,
        topic_result: Dict,
        intent_distribution: Dict[str, float],
        fused_scores: Dict[str, float]
    ) -> str:
        """Generate human-readable explanation of classification"""

        # Get top 3 intents
        top_intents = sorted(
            intent_distribution.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]

        intent_text = ", ".join([f"{intent} ({weight:.0%})" for intent, weight in top_intents])

        # Get top 3 alternative classifications
        alternatives = sorted(
            fused_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[1:3]  # Skip primary (index 0)

        alt_text = ", ".join([f"{ct} ({score:.0%})" for ct, score in alternatives])

        explanation = (
            f"Classified as '{primary_class}' based on topic analysis ('{topic_result.get('contractType', 'Unknown')}') "
            f"and legal intent distribution ({intent_text}). "
            f"Alternative classifications: {alt_text}."
        )

        return explanation


# Singleton instance
_fusion_classifier = None

def get_fusion_classifier() -> FusionClassifier:
    """Get or create singleton FusionClassifier instance"""
    global _fusion_classifier
    if _fusion_classifier is None:
        _fusion_classifier = FusionClassifier()
    return _fusion_classifier
