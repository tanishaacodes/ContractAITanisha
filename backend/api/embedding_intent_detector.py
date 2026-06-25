"""
Embedding-Based Intent Detector
Deterministic intent detection using semantic similarity (no LLM)
Identifies what a clause is trying to achieve legally
"""

from typing import List, Dict, Optional
from core.models import Clause, IntentTemplate, ClauseEmbedding
from api.embedding_service import embedding_service
import logging

logger = logging.getLogger(__name__)


class EmbeddingIntentDetector:
    """
    Detects legal intent of clauses using embedding similarity to intent templates.
    100% deterministic - no generative AI.
    """

    def __init__(self):
        self.embedding_service = embedding_service

    def detect_clause_intent(
        self,
        clause: Clause,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Detect the legal intent of a clause.

        Args:
            clause: Clause object to analyze
            top_k: Number of top intents to return

        Returns:
            List of detected intents with confidence scores
        """
        # Get or create clause embedding
        clause_embedding = self._get_clause_embedding(clause)

        if not clause_embedding:
            logger.warning(f"No embedding available for clause {clause.id}")
            return []

        # Load active intent templates
        templates = self._load_intent_templates()

        if not templates:
            logger.warning("No intent templates available")
            return []

        # Find top matching intents
        matches = []

        for template in templates:
            similarity = self.embedding_service.cosine_similarity(
                clause_embedding,
                template['embedding']
            )

            # Check if meets threshold
            if similarity >= template.get('similarity_threshold', 0.65):
                matches.append({
                    'intent_name': template['intent_name'],
                    'intent_category': template['intent_category'],
                    'intent_description': template['intent_description'],
                    'confidence': round(similarity, 3),
                    'party_impact': template['party_impact'],
                    'risk_level': template['risk_level'],
                    'negotiation_guidance': template.get('negotiation_guidance'),
                    'risk_mitigation': template.get('risk_mitigation')
                })

        # Sort by confidence descending
        matches.sort(key=lambda x: x['confidence'], reverse=True)

        return matches[:top_k]

    def detect_primary_intent(self, clause: Clause) -> Optional[Dict]:
        """
        Detect the primary (highest confidence) intent of a clause.

        Args:
            clause: Clause object to analyze

        Returns:
            Primary intent dict or None
        """
        intents = self.detect_clause_intent(clause, top_k=1)

        return intents[0] if intents else None

    def analyze_contract_intents(self, clauses: List[Clause]) -> Dict:
        """
        Analyze intents across all clauses in a contract.

        Args:
            clauses: List of Clause objects from a contract

        Returns:
            Dict with intent distribution and summary
        """
        all_intents = []
        clause_intent_map = {}

        for clause in clauses:
            try:
                intents = self.detect_clause_intent(clause, top_k=1)

                if intents:
                    primary_intent = intents[0]
                    all_intents.append(primary_intent)
                    clause_intent_map[clause.id] = primary_intent

            except Exception as e:
                logger.error(f"Error detecting intent for clause {clause.id}: {e}")

        # Compute statistics
        intent_distribution = {}
        category_distribution = {}
        party_impact_distribution = {}
        risk_distribution = {}

        for intent in all_intents:
            # Intent name distribution
            intent_name = intent['intent_name']
            intent_distribution[intent_name] = intent_distribution.get(intent_name, 0) + 1

            # Category distribution
            category = intent['intent_category']
            category_distribution[category] = category_distribution.get(category, 0) + 1

            # Party impact distribution
            party_impact = intent['party_impact']
            party_impact_distribution[party_impact] = party_impact_distribution.get(party_impact, 0) + 1

            # Risk level distribution
            risk_level = intent['risk_level']
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1

        # Sort distributions by count
        intent_distribution = dict(sorted(intent_distribution.items(), key=lambda x: x[1], reverse=True))
        category_distribution = dict(sorted(category_distribution.items(), key=lambda x: x[1], reverse=True))

        # Identify concerning intents
        concerning_intents = [
            intent for intent in all_intents
            if intent['party_impact'] == 'FAVOR_COUNTERPARTY' and intent['risk_level'] in ['MEDIUM', 'HIGH']
        ]

        # Calculate average confidence
        avg_confidence = sum(i['confidence'] for i in all_intents) / len(all_intents) if all_intents else 0

        return {
            'total_clauses_analyzed': len(clauses),
            'intents_detected': len(all_intents),
            'intent_distribution': intent_distribution,
            'category_distribution': category_distribution,
            'party_impact_distribution': party_impact_distribution,
            'risk_distribution': risk_distribution,
            'concerning_intents': concerning_intents,
            'average_confidence': round(avg_confidence, 3),
            'clause_intent_map': clause_intent_map
        }

    def find_clauses_by_intent(
        self,
        clauses: List[Clause],
        intent_name: str = None,
        intent_category: str = None,
        party_impact: str = None,
        min_confidence: float = 0.7
    ) -> List[Dict]:
        """
        Find clauses matching specific intent criteria.

        Args:
            clauses: List of Clause objects
            intent_name: Specific intent name to match
            intent_category: Intent category to match
            party_impact: Party impact to match
            min_confidence: Minimum confidence threshold

        Returns:
            List of matching clauses with intent details
        """
        matches = []

        for clause in clauses:
            intents = self.detect_clause_intent(clause, top_k=3)

            for intent in intents:
                if intent['confidence'] < min_confidence:
                    continue

                # Apply filters
                if intent_name and intent['intent_name'] != intent_name:
                    continue

                if intent_category and intent['intent_category'] != intent_category:
                    continue

                if party_impact and intent['party_impact'] != party_impact:
                    continue

                matches.append({
                    'clause_id': clause.id,
                    'clause_name': clause.clause_name,
                    'clause_text': clause.extracted_text or '',
                    **intent
                })

        # Sort by confidence descending
        matches.sort(key=lambda x: x['confidence'], reverse=True)

        return matches

    def _get_clause_embedding(self, clause: Clause) -> Optional[List[float]]:
        """Get or generate embedding for a clause"""
        try:
            # Try to get existing embedding
            clause_emb = ClauseEmbedding.objects.filter(clause_id=str(clause.id)).first()

            if clause_emb and clause_emb.embedding:
                # Verify text hasn't changed AND model matches
                text_to_embed = clause.extracted_text or clause.clause_name
                current_hash = self.embedding_service.compute_text_hash(text_to_embed)
                active_model = self.embedding_service.active_model_name

                if current_hash == clause_emb.embedded_text_hash and clause_emb.embedding_model == active_model:
                    return clause_emb.embedding

            # Generate new embedding
            text_to_embed = clause.extracted_text or clause.clause_name

            if not text_to_embed or not text_to_embed.strip():
                return None

            embedding = self.embedding_service.embed_text(text_to_embed)
            text_hash = self.embedding_service.compute_text_hash(text_to_embed)

            # Save embedding
            ClauseEmbedding.objects.update_or_create(
                clause_id=str(clause.id),
                defaults={
                    'embedding': embedding,
                    'embedded_text_hash': text_hash,
                    'embedding_model': self.embedding_service.active_model_name
                }
            )

            return embedding

        except Exception as e:
            logger.error(f"Error getting clause embedding: {e}")
            return None

    def _load_intent_templates(self) -> List[Dict]:
        """Load active intent templates from database"""
        try:
            templates_qs = IntentTemplate.objects.filter(is_active=True)

            templates = []
            for template in templates_qs:
                if template.embedding and len(template.embedding) == self.embedding_service.dimensions:
                    templates.append({
                        'id': template.id,
                        'intent_name': template.intent_name,
                        'intent_category': template.intent_category,
                        'intent_description': template.intent_description,
                        'party_impact': template.party_impact,
                        'risk_level': template.risk_level,
                        'similarity_threshold': template.similarity_threshold,
                        'embedding': template.embedding,
                        'negotiation_guidance': template.negotiation_guidance,
                        'risk_mitigation': template.risk_mitigation
                    })

            return templates

        except Exception as e:
            logger.error(f"Error loading intent templates: {e}")
            return []


# Global instance
embedding_intent_detector = EmbeddingIntentDetector()
