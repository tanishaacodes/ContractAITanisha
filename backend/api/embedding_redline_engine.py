"""
Embedding-Based Redline Engine
Deterministic redlining using pre-approved clause library (no LLM)
Zero hallucination - only suggests approved legal language
"""

from typing import List, Dict, Optional
from difflib import unified_diff
from core.models import Clause, ApprovedClause, ClauseEmbedding, Contract
from api.embedding_service import embedding_service
from api.embedding_intent_detector import embedding_intent_detector
from api.embedding_risk_scorer import embedding_risk_scorer
import logging

logger = logging.getLogger(__name__)


class EmbeddingRedlineEngine:
    """
    Suggests safer clause alternatives using pre-approved clause library.
    Workflow: Detect Intent → Match Approved Clause → Generate Diff
    """

    def __init__(self):
        self.embedding_service = embedding_service
        self.intent_detector = embedding_intent_detector
        self.risk_scorer = embedding_risk_scorer

    def suggest_redline(
        self,
        clause: Clause,
        protection_level: str = 'BALANCED',
        jurisdiction: str = None
    ) -> Optional[Dict]:
        """
        Suggest a safer alternative for a risky clause.

        Args:
            clause: Clause object to redline
            protection_level: Desired protection level (MAXIMUM, BALANCED, MINIMUM)
            jurisdiction: Optional jurisdiction filter

        Returns:
            Dict with suggested clause, redline diff, and rationale
        """
        # Step 1: Check if clause is risky
        risk_analysis = self.risk_scorer.score_clause(clause, jurisdiction)

        if risk_analysis['risk_level'] == 'LOW':
            return None  # No redline needed for low-risk clauses

        # Step 2: Detect intent
        primary_intent = self.intent_detector.detect_primary_intent(clause)

        if not primary_intent:
            logger.warning(f"Could not detect intent for clause {clause.id}")
            return None

        # Step 3: Get clause embedding
        clause_embedding = self._get_clause_embedding(clause)

        if not clause_embedding:
            return None

        # Step 4: Find matching approved clause
        approved_clause = self._find_approved_clause(
            clause_embedding=clause_embedding,
            intent_name=primary_intent['intent_name'],
            clause_type=risk_analysis.get('risk_type'),
            protection_level=protection_level,
            jurisdiction=jurisdiction
        )

        if not approved_clause:
            logger.warning(f"No approved clause found for intent: {primary_intent['intent_name']}")
            return None

        # Step 5: Generate redline diff
        original_text = clause.extracted_text or clause.clause_name
        suggested_text = approved_clause['clause_text']

        redline_diff = self._generate_diff(original_text, suggested_text)

        # Step 6: Build rationale
        rationale = self._build_rationale(
            risk_analysis=risk_analysis,
            primary_intent=primary_intent,
            approved_clause=approved_clause
        )

        return {
            'clause_id': clause.id,
            'clause_name': clause.clause_name,
            'original_text': original_text,
            'suggested_text': suggested_text,
            'redline_diff': redline_diff,
            'rationale': rationale,
            'risk_reduction': self._calculate_risk_reduction(risk_analysis, approved_clause),
            'intent_detected': primary_intent['intent_name'],
            'approved_clause_id': approved_clause['id'],
            'approved_clause_name': approved_clause['clause_name'],
            'protection_level': approved_clause['protection_level'],
            'similarity_to_original': round(approved_clause.get('similarity', 0) * 100, 1)
        }

    def suggest_redlines_for_contract(
        self,
        contract: Contract,
        protection_level: str = 'BALANCED',
        min_risk_level: str = 'MEDIUM'
    ) -> List[Dict]:
        """
        Suggest redlines for all risky clauses in a contract.

        Args:
            contract: Contract object
            protection_level: Desired protection level
            min_risk_level: Minimum risk level to redline (LOW, MEDIUM, HIGH)

        Returns:
            List of redline suggestions
        """
        clauses = contract.clauses.all()

        suggestions = []
        risk_level_order = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
        min_risk_threshold = risk_level_order.get(min_risk_level, 1)

        for clause in clauses:
            try:
                # Check risk level first
                risk_analysis = self.risk_scorer.score_clause(clause, contract.jurisdiction)

                if risk_level_order.get(risk_analysis['risk_level'], 0) < min_risk_threshold:
                    continue  # Skip low-risk clauses

                suggestion = self.suggest_redline(
                    clause=clause,
                    protection_level=protection_level,
                    jurisdiction=contract.jurisdiction
                )

                if suggestion:
                    suggestions.append(suggestion)

            except Exception as e:
                logger.error(f"Error suggesting redline for clause {clause.id}: {e}")

        # Sort by risk score descending
        suggestions.sort(key=lambda x: x.get('risk_reduction', 0), reverse=True)

        return suggestions

    def _get_clause_embedding(self, clause: Clause) -> Optional[List[float]]:
        """Get or generate embedding for a clause"""
        try:
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

    def _find_approved_clause(
        self,
        clause_embedding: List[float],
        intent_name: str,
        clause_type: str = None,
        protection_level: str = 'BALANCED',
        jurisdiction: str = None
    ) -> Optional[Dict]:
        """Find best matching approved clause"""
        try:
            # Build query
            approved_qs = ApprovedClause.objects.filter(is_active=True)

            # Filter by intent
            if intent_name:
                approved_qs = approved_qs.filter(intent_name=intent_name)

            # Filter by clause type if available
            if clause_type:
                approved_qs = approved_qs.filter(clause_type=clause_type)

            # Filter by jurisdiction
            if jurisdiction:
                approved_qs = approved_qs.filter(jurisdiction__in=[jurisdiction, 'Common Law'])

            # Prefer matching protection level
            protection_matches = approved_qs.filter(protection_level=protection_level)

            if not protection_matches.exists():
                protection_matches = approved_qs

            # Find best similarity match
            best_match = None
            best_similarity = 0.0

            for approved_clause in protection_matches:
                if not approved_clause.embedding or len(approved_clause.embedding) != self.embedding_service.dimensions:
                    continue

                similarity = self.embedding_service.cosine_similarity(
                    clause_embedding,
                    approved_clause.embedding
                )

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = {
                        'id': approved_clause.id,
                        'clause_name': approved_clause.clause_name,
                        'clause_type': approved_clause.clause_type,
                        'clause_text': approved_clause.clause_text,
                        'intent_name': approved_clause.intent_name,
                        'protection_level': approved_clause.protection_level,
                        'jurisdiction': approved_clause.jurisdiction,
                        'legal_notes': approved_clause.legal_notes,
                        'similarity': similarity
                    }

            return best_match if best_similarity > 0.3 else None

        except Exception as e:
            logger.error(f"Error finding approved clause: {e}")
            return None

    def _generate_diff(self, original_text: str, suggested_text: str) -> str:
        """Generate unified diff between original and suggested text"""
        try:
            original_lines = original_text.splitlines(keepends=True)
            suggested_lines = suggested_text.splitlines(keepends=True)

            diff = unified_diff(
                original_lines,
                suggested_lines,
                fromfile='Original',
                tofile='Suggested',
                lineterm=''
            )

            return '\n'.join(diff)

        except Exception as e:
            logger.error(f"Error generating diff: {e}")
            return ""

    def _build_rationale(
        self,
        risk_analysis: Dict,
        primary_intent: Dict,
        approved_clause: Dict
    ) -> str:
        """Build human-readable rationale for the suggestion"""
        rationale = f"""
**Why This Change Is Recommended:**

The original clause has been identified as {risk_analysis['risk_level']} risk with a risk score of {risk_analysis['risk_score']}/100.

**Risk Detected:** {risk_analysis.get('matched_risk', 'Unfavorable terms')}

**Intent:** This clause appears to {primary_intent['intent_description'].lower()}

**Party Impact:** {primary_intent['party_impact'].replace('_', ' ').title()}

**Suggested Alternative:**
We recommend replacing this with a pre-approved clause ({approved_clause['clause_name']}) that provides {approved_clause['protection_level'].lower()} protection while achieving the same legal purpose.

**Benefits:**
- Reduces risk from {risk_analysis['risk_level']} to LOW
- Uses legally-vetted language approved by your legal team
- Maintains the intended legal purpose
- Better protects your company's interests

**Legal Context:** {approved_clause.get('legal_notes', 'Standard industry practice')}
""".strip()

        return rationale

    def _calculate_risk_reduction(self, risk_analysis: Dict, approved_clause: Dict) -> float:
        """Calculate estimated risk reduction percentage"""
        # Original risk score
        original_risk = risk_analysis['risk_score']

        # Approved clauses are assumed to be low risk (10-20% risk)
        approved_risk = 15.0

        reduction = max(0, original_risk - approved_risk)

        return round(reduction, 1)


# Global instance
embedding_redline_engine = EmbeddingRedlineEngine()
