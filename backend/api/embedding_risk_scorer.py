"""
Embedding-Based Risk Scorer
Deterministic risk scoring using semantic similarity (no LLM)
Formula: Risk = Similarity × Severity Weight
"""

from typing import List, Dict, Tuple
from core.models import Clause, RiskPlaybook, ClauseEmbedding
from api.embedding_service import embedding_service
import logging

logger = logging.getLogger(__name__)


class EmbeddingRiskScorer:
    """
    Scores contract clauses for risk using embedding similarity to risk playbooks.
    100% deterministic - same input always produces same output.
    """

    def __init__(self):
        self.embedding_service = embedding_service

    def score_clause(self, clause: Clause, jurisdiction: str = None) -> Dict:
        """
        Score a single clause for risk.

        Args:
            clause: Clause object to score
            jurisdiction: Optional jurisdiction filter

        Returns:
            Dict with risk score, matched playbook, and explanation
        """
        # Get or create clause embedding
        clause_embedding = self._get_clause_embedding(clause)

        if not clause_embedding:
            logger.warning(f"No embedding available for clause {clause.id}")
            return {
                'risk_score': 0.0,
                'risk_level': 'LOW',
                'matched_risk': None,
                'explanation': 'Unable to compute risk score - no embedding available'
            }

        # Load active risk playbooks
        playbooks = self._load_risk_playbooks(jurisdiction)

        if not playbooks:
            logger.warning("No risk playbooks available")
            return {
                'risk_score': 0.0,
                'risk_level': 'LOW',
                'matched_risk': None,
                'explanation': 'No risk patterns configured'
            }

        # Compute risk using embedding similarity
        matched_playbook, risk_score = self.embedding_service.compute_risk_score(
            clause_embedding,
            playbooks
        )

        # Convert to risk level
        risk_level = self._score_to_level(risk_score)

        # Build explanation
        explanation = self._build_explanation(matched_playbook, risk_score, clause.clause_name)

        return {
            'risk_score': round(risk_score * 100, 1),  # Convert to 0-100 scale
            'risk_level': risk_level,
            'matched_risk': matched_playbook['risk_name'] if matched_playbook else None,
            'risk_type': matched_playbook['risk_type'] if matched_playbook else None,
            'similarity': round(matched_playbook['similarity'] * 100, 1) if matched_playbook else 0,
            'severity_weight': matched_playbook['severity_weight'] if matched_playbook else 0,
            'explanation': explanation,
            'legal_reference': matched_playbook.get('legal_reference') if matched_playbook else None,
            'court_treatment': matched_playbook.get('court_treatment') if matched_playbook else None
        }

    def score_multiple_clauses(self, clauses: List[Clause], jurisdiction: str = None) -> List[Dict]:
        """
        Score multiple clauses efficiently.

        Args:
            clauses: List of Clause objects
            jurisdiction: Optional jurisdiction filter

        Returns:
            List of risk score dicts
        """
        results = []

        for clause in clauses:
            try:
                score = self.score_clause(clause, jurisdiction)
                results.append({
                    'clause_id': clause.id,
                    'clause_name': clause.clause_name,
                    **score
                })
            except Exception as e:
                logger.error(f"Error scoring clause {clause.id}: {e}")
                results.append({
                    'clause_id': clause.id,
                    'clause_name': clause.clause_name,
                    'risk_score': 0.0,
                    'risk_level': 'LOW',
                    'error': str(e)
                })

        return results

    def _get_clause_embedding(self, clause: Clause) -> List[float]:
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

    def _load_risk_playbooks(self, jurisdiction: str = None) -> List[Dict]:
        """Load active risk playbooks from database"""
        try:
            playbooks_qs = RiskPlaybook.objects.filter(is_active=True)

            if jurisdiction:
                # Filter by jurisdiction or include global playbooks (null jurisdiction)
                playbooks_qs = playbooks_qs.filter(
                    jurisdiction__in=[jurisdiction, None, '']
                )

            playbooks = []
            for pb in playbooks_qs:
                if pb.embedding and len(pb.embedding) == self.embedding_service.dimensions:
                    playbooks.append({
                        'id': pb.id,
                        'risk_name': pb.risk_name,
                        'risk_type': pb.risk_type,
                        'risk_description': pb.risk_description,
                        'severity_weight': pb.severity_weight,
                        'similarity_threshold': pb.similarity_threshold,
                        'embedding': pb.embedding,
                        'legal_reference': pb.legal_reference,
                        'court_treatment': pb.court_treatment
                    })

            return playbooks

        except Exception as e:
            logger.error(f"Error loading risk playbooks: {e}")
            return []

    def _score_to_level(self, risk_score: float) -> str:
        """Convert risk score to risk level"""
        if risk_score >= 0.7:
            return 'HIGH'
        elif risk_score >= 0.4:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _build_explanation(self, matched_playbook: Dict, risk_score: float, clause_name: str) -> str:
        """Build human-readable risk explanation"""
        if not matched_playbook:
            return f"This clause '{clause_name}' does not match any known risk patterns."

        similarity = matched_playbook.get('similarity', 0)
        severity = matched_playbook.get('severity_weight', 0)
        risk_name = matched_playbook.get('risk_name', 'Unknown Risk')
        risk_description = matched_playbook.get('risk_description', '')

        explanation = (
            f"This clause matches the risk pattern: '{risk_name}' "
            f"with {similarity*100:.1f}% similarity. "
            f"The severity weight of this risk is {severity:.2f}. "
            f"\n\nRisk Details: {risk_description}"
        )

        return explanation


# Global instance
embedding_risk_scorer = EmbeddingRiskScorer()
