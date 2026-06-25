"""
Clause Deviation Detection Service
Feature 1: Clause Deviation & Negotiation Intelligence

Detects how far a clause deviates from:
- Gold-standard templates
- Industry benchmarks
- Past accepted contracts

Uses MiniLM embeddings for deterministic, explainable scoring.
"""

import logging
from typing import List, Dict, Tuple, Optional
from django.db import transaction

from core.models import (
    Clause, Contract, GoldStandardTemplate, IndustryBenchmark,
    ClauseDeviationScore, ClauseEmbedding
)
from api.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class DeviationDetectionService:
    """
    Service for detecting clause deviations using MiniLM embeddings.
    Provides deterministic, court-defensible deviation scoring.
    """

    def __init__(self):
        self.embedding_service = EmbeddingService()

    def analyze_clause_deviation(
        self,
        clause_id: str,
        contract_id: str,
        clause_text: str,
        clause_category: str
    ) -> Dict:
        """
        Analyze how far a clause deviates from approved standards.

        Args:
            clause_id: ID of the clause being analyzed
            contract_id: ID of the parent contract
            clause_text: Text of the clause to analyze
            clause_category: Category of the clause (LIABILITY, TERMINATION, etc.)

        Returns:
            Dictionary with deviation analysis results
        """
        try:
            # Generate embedding for the clause
            clause_embedding = self.embedding_service.embed_text(clause_text)

            # Find best matching gold-standard template
            gold_standard_result = self._find_best_gold_standard(
                clause_embedding, clause_category
            )

            # Find best matching industry benchmark
            industry_benchmark_result = self._find_best_industry_benchmark(
                clause_embedding, clause_category
            )

            # Find similarity to past accepted contracts
            past_accepted_result = self._find_past_accepted_similarity(
                clause_embedding, clause_category, contract_id
            )

            # Calculate overall deviation score
            overall_score, risk_level = self._calculate_overall_deviation(
                gold_standard_result['similarity'] if gold_standard_result else None,
                industry_benchmark_result['similarity'] if industry_benchmark_result else None,
                past_accepted_result['avg_similarity'] if past_accepted_result else None
            )

            # Determine risk type and suggested replacement
            risk_type = self._determine_risk_type(
                clause_category, risk_level, overall_score
            )
            suggested_replacement = self._get_suggested_replacement(
                gold_standard_result, clause_category
            )

            # Save deviation score to database
            deviation_score = self._save_deviation_score(
                clause_id=clause_id,
                contract_id=contract_id,
                gold_standard_result=gold_standard_result,
                industry_benchmark_result=industry_benchmark_result,
                past_accepted_result=past_accepted_result,
                overall_score=overall_score,
                risk_level=risk_level,
                risk_type=risk_type,
                suggested_replacement=suggested_replacement
            )

            return {
                'clause_id': clause_id,
                'deviation_score': overall_score,
                'risk_level': risk_level,
                'risk_type': risk_type,
                'gold_standard': gold_standard_result,
                'industry_benchmark': industry_benchmark_result,
                'past_accepted': past_accepted_result,
                'suggested_replacement': suggested_replacement,
                'explanation': self._generate_explanation(
                    overall_score, risk_level, risk_type,
                    gold_standard_result, industry_benchmark_result
                ),
                'court_precedent': gold_standard_result.get('legal_notes') if gold_standard_result else None
            }

        except Exception as e:
            logger.error(f"Error analyzing clause deviation: {e}")
            return {
                'error': str(e),
                'clause_id': clause_id,
                'deviation_score': 0.0,
                'risk_level': 'UNKNOWN'
            }

    def analyze_contract_deviations(self, contract_id: str) -> Dict:
        """
        Analyze all clauses in a contract for deviations.

        Args:
            contract_id: ID of the contract to analyze

        Returns:
            Dictionary with contract-level deviation summary
        """
        try:
            # Get all clauses for the contract
            clauses = Clause.objects.filter(contract_id=contract_id, found=True)

            clause_results = []
            total_score = 0
            high_risk_count = 0
            review_count = 0
            safe_count = 0

            for clause in clauses:
                if not clause.extracted_text or not clause.extracted_text.strip():
                    continue

                # Analyze each clause
                result = self.analyze_clause_deviation(
                    clause_id=clause.id,
                    contract_id=contract_id,
                    clause_text=clause.extracted_text,
                    clause_category=self._map_clause_name_to_category(clause.clause_name)
                )

                clause_results.append(result)
                total_score += result.get('deviation_score', 0)

                # Count risk levels
                if result.get('risk_level') == 'HIGH_RISK':
                    high_risk_count += 1
                elif result.get('risk_level') == 'REVIEW':
                    review_count += 1
                elif result.get('risk_level') == 'SAFE':
                    safe_count += 1

            avg_score = total_score / len(clause_results) if clause_results else 0

            return {
                'contract_id': contract_id,
                'total_clauses_analyzed': len(clause_results),
                'average_deviation_score': avg_score,
                'high_risk_count': high_risk_count,
                'review_count': review_count,
                'safe_count': safe_count,
                'clause_results': clause_results
            }

        except Exception as e:
            logger.error(f"Error analyzing contract deviations: {e}")
            return {'error': str(e), 'contract_id': contract_id}

    def _find_best_gold_standard(
        self,
        clause_embedding: List[float],
        clause_category: str
    ) -> Optional[Dict]:
        """Find the best matching gold-standard template."""
        try:
            templates = GoldStandardTemplate.objects.filter(
                clause_category=clause_category,
                is_active=True
            )

            if not templates.exists():
                logger.warning(f"No gold-standard templates found for {clause_category}")
                return None

            best_match = None
            best_similarity = 0.0

            for template in templates:
                if not template.embedding or len(template.embedding) != self.embedding_service.dimensions:
                    continue

                similarity = self.embedding_service.cosine_similarity(
                    clause_embedding, template.embedding
                )

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = template

            if best_match:
                return {
                    'template_id': best_match.id,
                    'template_name': best_match.template_name,
                    'similarity': best_similarity,
                    'approved_text': best_match.approved_clause_text,
                    'legal_notes': best_match.legal_notes,
                    'jurisdiction': best_match.jurisdiction,
                    'safe_threshold': best_match.safe_threshold,
                    'review_threshold': best_match.review_threshold
                }

            return None

        except Exception as e:
            logger.error(f"Error finding gold-standard template: {e}")
            return None

    def _find_best_industry_benchmark(
        self,
        clause_embedding: List[float],
        clause_category: str
    ) -> Optional[Dict]:
        """Find the best matching industry benchmark."""
        try:
            benchmarks = IndustryBenchmark.objects.filter(
                clause_category=clause_category,
                is_active=True
            )

            if not benchmarks.exists():
                return None

            best_match = None
            best_similarity = 0.0

            for benchmark in benchmarks:
                if not benchmark.embedding or len(benchmark.embedding) != self.embedding_service.dimensions:
                    continue

                similarity = self.embedding_service.cosine_similarity(
                    clause_embedding, benchmark.embedding
                )

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = benchmark

            if best_match:
                return {
                    'benchmark_id': best_match.id,
                    'benchmark_name': best_match.benchmark_name,
                    'similarity': best_similarity,
                    'benchmark_text': best_match.benchmark_clause_text,
                    'industry': best_match.industry,
                    'adoption_rate': best_match.adoption_rate,
                    'source': best_match.source
                }

            return None

        except Exception as e:
            logger.error(f"Error finding industry benchmark: {e}")
            return None

    def _find_past_accepted_similarity(
        self,
        clause_embedding: List[float],
        clause_category: str,
        current_contract_id: str
    ) -> Optional[Dict]:
        """Find similarity to past accepted contracts."""
        try:
            # Get past accepted clauses (excluding current contract)
            # This assumes you have a way to mark contracts as "accepted"
            # For now, we'll use clauses from other contracts
            past_clauses = Clause.objects.filter(
                clause_name__icontains=clause_category.replace('_', ' ')
            ).exclude(
                contract_id=current_contract_id
            )[:20]  # Limit to 20 most recent

            if not past_clauses.exists():
                return None

            similarities = []
            for clause in past_clauses:
                # Get clause embedding
                try:
                    clause_emb_obj = ClauseEmbedding.objects.get(clause_id=clause.id)
                    # Skip embeddings with wrong dimensions
                    if not clause_emb_obj.embedding or len(clause_emb_obj.embedding) != self.embedding_service.dimensions:
                        continue
                    similarity = self.embedding_service.cosine_similarity(
                        clause_embedding, clause_emb_obj.embedding
                    )
                    similarities.append(similarity)
                except ClauseEmbedding.DoesNotExist:
                    continue

            if similarities:
                import numpy as np
                avg_similarity = float(np.mean(similarities))
                max_similarity = float(np.max(similarities))

                return {
                    'avg_similarity': avg_similarity,
                    'max_similarity': max_similarity,
                    'sample_count': len(similarities)
                }

            return None

        except Exception as e:
            logger.error(f"Error finding past accepted similarity: {e}")
            return None

    def _calculate_overall_deviation(
        self,
        gold_standard_similarity: Optional[float],
        industry_benchmark_similarity: Optional[float],
        past_accepted_similarity: Optional[float]
    ) -> Tuple[float, str]:
        """
        Calculate overall deviation score and risk level.

        Uses weighted average of available similarities.
        Higher similarity = lower deviation = lower risk.
        """
        similarities = []
        weights = []

        # Gold-standard has highest weight
        if gold_standard_similarity is not None:
            similarities.append(gold_standard_similarity)
            weights.append(0.5)

        # Industry benchmark
        if industry_benchmark_similarity is not None:
            similarities.append(industry_benchmark_similarity)
            weights.append(0.3)

        # Past accepted
        if past_accepted_similarity is not None:
            similarities.append(past_accepted_similarity)
            weights.append(0.2)

        if not similarities:
            return 0.0, 'UNKNOWN'

        # Normalize weights
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]

        # Calculate weighted average similarity
        import numpy as np
        overall_similarity = float(np.average(similarities, weights=normalized_weights))

        # Determine risk level based on similarity
        # Higher similarity = safer
        if overall_similarity >= 0.90:
            risk_level = 'SAFE'
        elif overall_similarity >= 0.75:
            risk_level = 'REVIEW'
        else:
            risk_level = 'HIGH_RISK'

        return overall_similarity, risk_level

    def _determine_risk_type(
        self,
        clause_category: str,
        risk_level: str,
        deviation_score: float
    ) -> str:
        """Determine the type of risk based on clause category and deviation."""
        risk_type_map = {
            'LIABILITY': 'Unlimited liability exposure',
            'TERMINATION': 'Unfavorable termination rights',
            'INDEMNIFICATION': 'Broad indemnification obligations',
            'IP_OWNERSHIP': 'IP ownership transfer risk',
            'CONFIDENTIALITY': 'Weak confidentiality protection',
            'PAYMENT': 'Unfavorable payment terms',
            'GOVERNING_LAW': 'Disadvantageous jurisdiction',
            'SLA_PENALTIES': 'Missing performance penalties',
            'WARRANTY': 'Weak warranty protection',
            'DATA_PRIVACY': 'Data protection gaps'
        }

        if risk_level == 'SAFE':
            return 'No significant risk'

        return risk_type_map.get(clause_category, 'Deviation from standard')

    def _get_suggested_replacement(
        self,
        gold_standard_result: Optional[Dict],
        clause_category: str
    ) -> Optional[str]:
        """Get suggested replacement text from gold-standard template."""
        if gold_standard_result:
            return gold_standard_result.get('approved_text')

        # Fallback: try to find any active template for this category
        try:
            template = GoldStandardTemplate.objects.filter(
                clause_category=clause_category,
                is_active=True
            ).first()

            return template.approved_clause_text if template else None

        except Exception as e:
            logger.error(f"Error getting suggested replacement: {e}")
            return None

    def _generate_explanation(
        self,
        overall_score: float,
        risk_level: str,
        risk_type: str,
        gold_standard_result: Optional[Dict],
        industry_benchmark_result: Optional[Dict]
    ) -> str:
        """Generate human-readable explanation of the deviation."""
        if risk_level == 'SAFE':
            return (
                f"This clause closely matches your approved standards "
                f"(similarity: {overall_score:.2%}). No significant deviations detected."
            )

        explanation_parts = [
            f"This clause shows {risk_level.lower().replace('_', ' ')} deviation "
            f"from approved standards (similarity: {overall_score:.2%})."
        ]

        if gold_standard_result:
            explanation_parts.append(
                f"Compared to your gold-standard template '{gold_standard_result['template_name']}', "
                f"similarity is {gold_standard_result['similarity']:.2%}."
            )

        if industry_benchmark_result:
            explanation_parts.append(
                f"Industry benchmark similarity is {industry_benchmark_result['similarity']:.2%} "
                f"(based on {industry_benchmark_result.get('industry', 'general')} standards)."
            )

        explanation_parts.append(f"Risk type: {risk_type}")

        return ' '.join(explanation_parts)

    def _save_deviation_score(
        self,
        clause_id: str,
        contract_id: str,
        gold_standard_result: Optional[Dict],
        industry_benchmark_result: Optional[Dict],
        past_accepted_result: Optional[Dict],
        overall_score: float,
        risk_level: str,
        risk_type: str,
        suggested_replacement: Optional[str]
    ) -> ClauseDeviationScore:
        """Save deviation score to database."""
        try:
            with transaction.atomic():
                # Use update_or_create to prevent duplicates for the same clause
                # Match only on clause_id since each clause can only have one deviation score
                deviation_score, created = ClauseDeviationScore.objects.update_or_create(
                    clause_id=clause_id,
                    defaults={
                        'contract_id': contract_id,
                        'gold_standard_id': gold_standard_result['template_id'] if gold_standard_result else None,
                        'gold_standard_similarity': gold_standard_result['similarity'] if gold_standard_result else None,
                        'industry_benchmark_id': industry_benchmark_result['benchmark_id'] if industry_benchmark_result else None,
                        'industry_benchmark_similarity': industry_benchmark_result['similarity'] if industry_benchmark_result else None,
                        'past_accepted_similarity': past_accepted_result['avg_similarity'] if past_accepted_result else None,
                        'overall_risk_level': risk_level,
                        'overall_deviation_score': overall_score,
                        'risk_type': risk_type,
                        'suggested_replacement_text': suggested_replacement,
                        'suggested_from_template_id': gold_standard_result['template_id'] if gold_standard_result else None,
                        'explanation': self._generate_explanation(
                            overall_score, risk_level, risk_type,
                            gold_standard_result, industry_benchmark_result
                        ),
                        'court_precedent': gold_standard_result.get('legal_notes') if gold_standard_result else None
                    }
                )

                return deviation_score

        except Exception as e:
            logger.error(f"Error saving deviation score: {e}")
            raise

    def _map_clause_name_to_category(self, clause_name: str) -> str:
        """Map clause name to standardized category."""
        clause_name_lower = clause_name.lower()

        category_map = {
            'liability': 'LIABILITY',
            'termination': 'TERMINATION',
            'indemnification': 'INDEMNIFICATION',
            'indemnity': 'INDEMNIFICATION',
            'ip': 'IP_OWNERSHIP',
            'intellectual property': 'IP_OWNERSHIP',
            'confidentiality': 'CONFIDENTIALITY',
            'payment': 'PAYMENT',
            'governing law': 'GOVERNING_LAW',
            'force majeure': 'FORCE_MAJEURE',
            'data privacy': 'DATA_PRIVACY',
            'data protection': 'DATA_PRIVACY',
            'non-compete': 'NON_COMPETE',
            'damages': 'LIMITATION_OF_DAMAGES',
            'assignment': 'ASSIGNMENT',
            'renewal': 'RENEWAL',
            'dispute': 'DISPUTE_RESOLUTION',
            'arbitration': 'DISPUTE_RESOLUTION',
            'sla': 'SLA_PENALTIES',
            'penalty': 'SLA_PENALTIES',
            'warranty': 'WARRANTY',
            'warranties': 'WARRANTY'
        }

        for keyword, category in category_map.items():
            if keyword in clause_name_lower:
                return category

        return 'OTHER'
