"""
Missing Safeguard Detection Service
Feature 2: Contract Obligation Leakage & Missed Safeguards Detection

Detects what is MISSING in a contract:
- Missing termination for convenience
- No penalty / liquidated damages
- Absent IP ownership clause
- No data protection / confidentiality

Uses semantic expectation modeling to detect absence.
"""

import logging
from typing import List, Dict, Optional
from django.db import transaction

from core.models import (
    Clause, Contract, ExpectedObligation, MissingSafeguardDetection,
    ClauseEmbedding
)
from api.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class SafeguardDetectionService:
    """
    Service for detecting missing or weak safeguards using semantic absence detection.
    Most ContractAI tools cannot detect absence - this is a unique capability.
    """

    def __init__(self):
        self.embedding_service = EmbeddingService()

    def detect_missing_safeguards(
        self,
        contract_id: str,
        contract_type: Optional[str] = None
    ) -> Dict:
        """
        Detect missing or weak safeguards in a contract.

        Args:
            contract_id: ID of the contract to analyze
            contract_type: Type of contract (e.g., 'SaaS Agreement', 'Service Agreement')

        Returns:
            Dictionary with safeguard detection results
        """
        try:
            # Get contract
            contract = Contract.objects.get(id=contract_id)
            if not contract_type:
                contract_type = contract.contract_type

            # Get all clauses in the contract
            clauses = Clause.objects.filter(contract_id=contract_id, found=True)

            # Get clause embeddings
            clause_embeddings = {}
            for clause in clauses:
                try:
                    emb_obj = ClauseEmbedding.objects.get(clause_id=clause.id)
                    # Skip embeddings with wrong dimensions - re-generate below
                    if emb_obj.embedding and len(emb_obj.embedding) == self.embedding_service.dimensions:
                        clause_embeddings[clause.id] = {
                            'embedding': emb_obj.embedding,
                            'text': clause.extracted_text,
                            'clause_name': clause.clause_name
                        }
                        continue
                except ClauseEmbedding.DoesNotExist:
                    pass

                # If no cached embedding or wrong dimensions, generate new one
                if clause.extracted_text and clause.extracted_text.strip():
                    embedding = self.embedding_service.embed_text(clause.extracted_text)
                    clause_embeddings[clause.id] = {
                        'embedding': embedding,
                        'text': clause.extracted_text,
                        'clause_name': clause.clause_name
                    }

            # Get expected obligations for this contract type
            expected_obligations = ExpectedObligation.objects.filter(
                is_active=True
            )

            # Filter by contract type if specified
            if contract_type:
                expected_obligations = expected_obligations.filter(
                    contract_type__isnull=True
                ) | expected_obligations.filter(
                    contract_type=contract_type
                )

            # Check each expected obligation
            safeguard_results = []
            for obligation in expected_obligations:
                result = self._check_obligation_presence(
                    obligation, clause_embeddings, contract_id
                )
                safeguard_results.append(result)

                # Save to database
                self._save_safeguard_detection(result)

            # Generate summary
            summary = self._generate_summary(safeguard_results)

            return {
                'contract_id': contract_id,
                'contract_type': contract_type,
                'total_obligations_checked': len(safeguard_results),
                'missing_count': summary['missing_count'],
                'weak_count': summary['weak_count'],
                'present_count': summary['present_count'],
                'critical_missing': summary['critical_missing'],
                'safeguard_results': safeguard_results,
                'summary': summary
            }

        except Contract.DoesNotExist:
            logger.error(f"Contract {contract_id} not found")
            return {'error': 'Contract not found', 'contract_id': contract_id}
        except Exception as e:
            logger.error(f"Error detecting missing safeguards: {e}")
            return {'error': str(e), 'contract_id': contract_id}

    def _check_obligation_presence(
        self,
        obligation: ExpectedObligation,
        clause_embeddings: Dict,
        contract_id: str
    ) -> Dict:
        """
        Check if an expected obligation is present in the contract.

        Uses semantic similarity to detect presence/absence.
        """
        if not obligation.embedding or len(obligation.embedding) != self.embedding_service.dimensions:
            # Generate embedding if missing or wrong dimensions
            obligation.embedding = self.embedding_service.embed_text(
                obligation.expected_clause_text
            )
            obligation.embedding_model = self.embedding_service.active_model_name
            obligation.save()

        best_match_clause_id = None
        best_similarity = 0.0
        best_clause_text = None
        best_clause_name = None

        # Compare obligation embedding to all clause embeddings
        for clause_id, clause_data in clause_embeddings.items():
            similarity = self.embedding_service.cosine_similarity(
                obligation.embedding,
                clause_data['embedding']
            )

            if similarity > best_similarity:
                best_similarity = similarity
                best_match_clause_id = clause_id
                best_clause_text = clause_data['text']
                best_clause_name = clause_data['clause_name']

        # Determine status based on similarity threshold
        if best_similarity >= obligation.presence_threshold:
            status = 'PRESENT'
            confidence = best_similarity
        elif best_similarity >= (obligation.presence_threshold * 0.7):
            # Partially present but weak
            status = 'WEAK'
            confidence = best_similarity
        else:
            status = 'MISSING'
            confidence = 1.0 - best_similarity  # High confidence that it's missing

        # Generate AI insight
        ai_insight = self._generate_ai_insight(
            obligation, status, best_similarity, best_clause_name
        )

        return {
            'contract_id': contract_id,
            'obligation_id': obligation.id,
            'obligation_name': obligation.obligation_name,
            'obligation_category': obligation.obligation_category,
            'criticality': obligation.criticality,
            'status': status,
            'confidence': confidence,
            'matched_clause_id': best_match_clause_id if status != 'MISSING' else None,
            'matched_clause_name': best_clause_name if status != 'MISSING' else None,
            'matched_similarity': best_similarity,
            'ai_insight': ai_insight,
            'risk_explanation': obligation.absence_risk_description if status != 'PRESENT' else None,
            'suggested_action': self._generate_suggested_action(obligation, status),
            'suggested_clause_text': obligation.suggested_clause_text if status == 'MISSING' else None
        }

    def _generate_ai_insight(
        self,
        obligation: ExpectedObligation,
        status: str,
        similarity: float,
        matched_clause_name: Optional[str]
    ) -> str:
        """Generate AI insight for the safeguard detection."""
        if status == 'PRESENT':
            return (
                f"{obligation.obligation_name} is adequately covered "
                f"(similarity: {similarity:.2%}). "
                f"Found in clause: {matched_clause_name or 'unknown'}."
            )
        elif status == 'WEAK':
            return (
                f"{obligation.obligation_name} is present but weak "
                f"(similarity: {similarity:.2%}). "
                f"The existing clause '{matched_clause_name or 'unknown'}' "
                f"partially addresses this obligation but may need strengthening."
            )
        else:  # MISSING
            return (
                f"{obligation.obligation_name} is missing from the contract. "
                f"No clause with adequate semantic similarity was found "
                f"(best match: {similarity:.2%}). "
                f"{obligation.absence_risk_description}"
            )

    def _generate_suggested_action(
        self,
        obligation: ExpectedObligation,
        status: str
    ) -> str:
        """Generate suggested action based on detection status."""
        if status == 'PRESENT':
            return "No action required - safeguard is adequately present."
        elif status == 'WEAK':
            return (
                f"Review and strengthen the existing clause to better align with "
                f"expected {obligation.obligation_category.replace('_', ' ').lower()} standards."
            )
        else:  # MISSING
            criticality_action = {
                'CRITICAL': 'URGENT: Add this clause before signing. This is a critical safeguard.',
                'IMPORTANT': 'RECOMMENDED: Negotiate to include this safeguard before signing.',
                'RECOMMENDED': 'OPTIONAL: Consider adding this clause for better protection.'
            }
            return criticality_action.get(
                obligation.criticality,
                "Consider adding this safeguard to the contract."
            )

    def _generate_summary(self, safeguard_results: List[Dict]) -> Dict:
        """Generate summary statistics."""
        missing_count = sum(1 for r in safeguard_results if r['status'] == 'MISSING')
        weak_count = sum(1 for r in safeguard_results if r['status'] == 'WEAK')
        present_count = sum(1 for r in safeguard_results if r['status'] == 'PRESENT')

        # Critical missing safeguards
        critical_missing = [
            r for r in safeguard_results
            if r['status'] == 'MISSING' and r['criticality'] == 'CRITICAL'
        ]

        # Important missing safeguards
        important_missing = [
            r for r in safeguard_results
            if r['status'] == 'MISSING' and r['criticality'] == 'IMPORTANT'
        ]

        # Weak safeguards
        weak_safeguards = [
            r for r in safeguard_results
            if r['status'] == 'WEAK'
        ]

        return {
            'missing_count': missing_count,
            'weak_count': weak_count,
            'present_count': present_count,
            'total_checked': len(safeguard_results),
            'critical_missing': critical_missing,
            'important_missing': important_missing,
            'weak_safeguards': weak_safeguards,
            'overall_assessment': self._generate_overall_assessment(
                critical_missing, important_missing, weak_safeguards
            )
        }

    def _generate_overall_assessment(
        self,
        critical_missing: List[Dict],
        important_missing: List[Dict],
        weak_safeguards: List[Dict]
    ) -> str:
        """Generate overall contract assessment."""
        if critical_missing:
            return (
                f"⚠️ HIGH RISK: {len(critical_missing)} critical safeguard(s) missing. "
                f"Do not sign without addressing these gaps."
            )
        elif important_missing:
            return (
                f"⚠️ MEDIUM RISK: {len(important_missing)} important safeguard(s) missing. "
                f"Recommend negotiating to include these protections."
            )
        elif weak_safeguards:
            return (
                f"⚠️ REVIEW NEEDED: {len(weak_safeguards)} safeguard(s) present but weak. "
                f"Consider strengthening these clauses."
            )
        else:
            return "✅ All expected safeguards are adequately present."

    def _save_safeguard_detection(self, result: Dict):
        """Save safeguard detection to database."""
        try:
            with transaction.atomic():
                # Use update_or_create to prevent duplicates for the same obligation
                MissingSafeguardDetection.objects.update_or_create(
                    contract_id=result['contract_id'],
                    expected_obligation_id_id=result['obligation_id'],
                    defaults={
                        'status': result['status'],
                        'confidence': result['confidence'],
                        'matched_clause_id': result.get('matched_clause_id'),
                        'matched_similarity': result.get('matched_similarity'),
                        'ai_insight': result['ai_insight'],
                        'risk_explanation': result.get('risk_explanation', ''),
                        'suggested_action': result['suggested_action'],
                        'suggested_clause_text': result.get('suggested_clause_text')
                    }
                )
        except Exception as e:
            logger.error(f"Error saving safeguard detection: {e}")

    def get_safeguard_summary_table(self, contract_id: str) -> List[Dict]:
        """
        Get safeguard summary in table format (for UI display).

        Returns a list of safeguards with status and confidence.
        """
        try:
            detections = MissingSafeguardDetection.objects.filter(
                contract_id=contract_id
            ).select_related('expected_obligation_id')

            table_rows = []
            for detection in detections:
                obligation = detection.expected_obligation_id

                # Map status to emoji/symbol
                status_symbol = {
                    'MISSING': '❌',
                    'WEAK': '⚠️',
                    'PRESENT': '✅'
                }.get(detection.status, '?')

                table_rows.append({
                    'safeguard': obligation.obligation_name,
                    'category': obligation.obligation_category.replace('_', ' ').title(),
                    'status': detection.status,
                    'status_symbol': status_symbol,
                    'confidence': detection.confidence,
                    'criticality': obligation.criticality,
                    'ai_insight': detection.ai_insight,
                    'suggested_action': detection.suggested_action
                })

            return table_rows

        except Exception as e:
            logger.error(f"Error generating safeguard summary table: {e}")
            return []
