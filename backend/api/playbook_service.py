"""
Playbook Automation Service
----------------------------
Three responsibilities:
1. evaluate_clause  – cosine-similarity check against a LegalPlaybook entry
2. generate_fallback – Qwen-constrained rewrite (only when clause is non-standard)
3. run_playbook_check – full pipeline: evaluate every clause in a contract,
   persist ClausePlaybookResult rows, and return the results.

Design rules inherited from the rest of the embedding stack:
  • MiniLM / embedding_service for all similarity maths (deterministic).
  • Qwen via Ollama HTTP only for constrained rewriting – never for decisions.
  • Playbook thresholds, not the LLM, decide what is "standard".
"""

import logging
import requests
from typing import List, Dict, Optional

from django.conf import settings
from django.db.models import Avg, Count

from core.models import (
    Clause,
    LegalPlaybook,
    ClausePlaybookResult,
    PlaybookDriftSnapshot,
    PlaybookUpdateSuggestion,
)
from api.embedding_service import embedding_service

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Drift-detection governance constants
# ---------------------------------------------------------------------------
DRIFT_SIMILARITY_THRESHOLD = 0.75   # avg similarity must fall below this …
DRIFT_RATE_THRESHOLD = 0.40         # … AND non-standard rate must exceed this …
MIN_SAMPLE_SIZE = 10                # … with at least this many evaluated clauses


class PlaybookService:
    """Stateless service – instantiate or use the module-level singleton."""

    # --------------------------------------------------------------- helpers
    def _get_clause_embedding(self, clause: Clause) -> Optional[List[float]]:
        """Generate (or re-use cached) embedding for a clause's text."""
        text = (clause.extracted_text or clause.clause_name or "").strip()
        if not text:
            return None
        return embedding_service.embed_text(text)

    # Mapping from common lower-case / variant clause_type values to the
    # canonical upper-case choices used on LegalPlaybook.
    _TYPE_ALIASES = {
        'indemnity': 'INDEMNIFICATION',
        'force_majeure': 'FORCE_MAJEURE',
        'dispute_resolution': 'DISPUTE_RESOLUTION',
        'governing_law': 'GOVERNING_LAW',
        'ip_ownership': 'IP_OWNERSHIP',
        'limitation_of_damages': 'LIMITATION_OF_DAMAGES',
        'non_compete': 'NON_COMPETE',
        'data_privacy': 'DATA_PRIVACY',
    }

    def _load_playbooks(self, clause_type: str, jurisdiction: str) -> List[LegalPlaybook]:
        """
        Return playbooks that match clause_type AND either the given
        jurisdiction or 'global'. Normalises clause_type to upper-case and
        resolves known aliases before querying.

        IMPORTANT: Only returns playbooks matching the active embedding model's dimensions.
        """
        normalised = clause_type.strip().upper()
        normalised = self._TYPE_ALIASES.get(clause_type.strip().lower(), normalised)

        playbooks_qs = LegalPlaybook.objects.filter(
            clause_type=normalised,
            jurisdiction__in=[jurisdiction, 'global'],
        )

        # Filter by embedding dimensions to match active model
        filtered_playbooks = []
        active_model = embedding_service.active_model_name
        active_dims = embedding_service.dimensions

        for pb in playbooks_qs:
            # Only include playbooks with embeddings matching current model dimensions
            if pb.embedding and len(pb.embedding) == active_dims:
                filtered_playbooks.append(pb)

        return filtered_playbooks

    # -------------------------------------------------------------- evaluate
    def evaluate_clause(self, clause: Clause, playbook: LegalPlaybook) -> Dict:
        """
        Compute cosine similarity between a clause and a playbook's
        standard_clause embedding.

        Returns:
            {similarity_score, is_standard}
        """
        clause_emb = self._get_clause_embedding(clause)
        if not clause_emb:
            return {'similarity_score': 0.0, 'is_standard': False}

        # Ensure playbook has an embedding matching current model dimensions
        pb_emb = playbook.embedding
        if not pb_emb or len(pb_emb) != embedding_service.dimensions:
            # Re-generate embedding with active model
            pb_emb = embedding_service.embed_text(playbook.standard_clause)
            playbook.embedding = pb_emb
            playbook.embedding_model = embedding_service.active_model_name
            playbook.save(update_fields=['embedding', 'embedding_model'])

        score = embedding_service.cosine_similarity(clause_emb, pb_emb)
        is_standard = score >= playbook.similarity_threshold
        return {'similarity_score': round(score, 4), 'is_standard': is_standard}

    # ---------------------------------------------------------- fallback gen
    def generate_fallback(self, clause_text: str, playbook: LegalPlaybook) -> str:
        """
        Call Qwen (via Ollama) to rewrite *clause_text* so it aligns with the
        playbook's fallback_clause.  The prompt is heavily constrained so the
        LLM cannot introduce new obligations or change intent.

        Falls back to the raw fallback_clause text if Ollama is unreachable.
        """
        prompt = (
            "Rewrite the incoming clause so it matches the company's approved "
            "fallback language.\n\n"
            "Rules:\n"
            "- Do NOT change the intent of the clause.\n"
            "- Use the Fallback Clause as the primary reference.\n"
            "- Do NOT introduce new obligations or rights.\n"
            "- Keep a professional legal tone.\n"
            "- Output ONLY the revised clause text, nothing else.\n\n"
            f"Fallback Clause:\n{playbook.fallback_clause}\n\n"
            f"Incoming Clause:\n{clause_text}\n\n"
            "Revised Clause:"
        )

        try:
            response = requests.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,   # low – stay close to fallback
                        "top_p": 0.85,
                        "max_tokens": 600,
                    },
                },
                timeout=45,
            )
            if response.status_code == 200:
                text = response.json().get("response", "").strip()
                if text:
                    return text
        except (requests.Timeout, requests.ConnectionError) as exc:
            logger.warning("Ollama unreachable for fallback generation: %s", exc)
        except Exception as exc:
            logger.error("Fallback generation error: %s", exc)

        # Safe fallback – return the pre-approved text verbatim
        return playbook.fallback_clause

    # ---------------------------------------------------------- full pipeline
    def run_playbook_check(self, contract, jurisdiction: str = "global") -> List[Dict]:
        """
        For every clause in *contract*:
          1. Look up matching playbooks.
          2. Evaluate similarity.
          3. If non-standard → generate fallback via Qwen.
          4. Persist ClausePlaybookResult.

        Returns a list of result dicts ready to send to the frontend.
        """
        # Delete existing results for this contract to prevent duplicates
        clause_ids = list(contract.clauses.values_list('id', flat=True))
        ClausePlaybookResult.objects.filter(clause_id__in=clause_ids).delete()

        clauses: List[Clause] = list(contract.clauses.filter(found=True))
        if not clauses:
            return []

        results = []
        for clause in clauses:
            # Determine which playbooks apply – use clause_type if enriched,
            # otherwise fall back to clause_name as a best-effort match.
            clause_type = clause.clause_type or clause.clause_name or "OTHER"
            playbooks = self._load_playbooks(clause_type, jurisdiction)

            if not playbooks:
                continue  # no governance for this clause type – skip

            for pb in playbooks:
                evaluation = self.evaluate_clause(clause, pb)
                suggestion = None

                if not evaluation['is_standard']:
                    clause_text = clause.extracted_text or clause.clause_name or ""
                    suggestion = self.generate_fallback(clause_text, pb)

                result = ClausePlaybookResult.objects.create(
                    clause_id=clause.id,
                    playbook_id=pb.id,
                    similarity_score=evaluation['similarity_score'],
                    is_standard=evaluation['is_standard'],
                    suggested_text=suggestion,
                )

                results.append({
                    'id': result.id,
                    'clause_id': str(clause.id),
                    'clause_name': clause.clause_name,
                    'playbook_id': str(pb.id),
                    'clause_type': pb.clause_type,
                    'jurisdiction': pb.jurisdiction,
                    'similarity_score': result.similarity_score,
                    'is_standard': result.is_standard,
                    'suggested_text': result.suggested_text,
                    'mandatory': pb.mandatory,
                    'fallback_accepted': result.fallback_accepted,
                })

        return results

    # --------------------------------------------------------- accept fallback
    @staticmethod
    def accept_fallback(result_id: str) -> Optional[ClausePlaybookResult]:
        """Mark a ClausePlaybookResult as accepted and stamp the time."""
        from django.utils import timezone
        try:
            result = ClausePlaybookResult.objects.get(id=result_id)
            result.fallback_accepted = True
            result.accepted_at = timezone.now()
            result.save(update_fields=['fallback_accepted', 'accepted_at'])
            return result
        except ClausePlaybookResult.DoesNotExist:
            return None

    # ---------------------------------------------------------- drift capture
    @staticmethod
    def capture_playbook_drift():
        """
        Aggregate all ClausePlaybookResult rows by (clause_type, jurisdiction)
        and write a PlaybookDriftSnapshot.  Designed to be called once per day
        via cron / Celery.

        IMPORTANT: Only aggregates results from playbooks matching the active embedding model
        to avoid mixing results from different embedding dimensions.
        """
        from collections import defaultdict

        # Get active model dimensions to filter playbooks
        active_dims = embedding_service.dimensions

        # Build a map of playbook_id -> (clause_type, jurisdiction)
        # Only include playbooks matching active model dimensions
        playbooks = {
            str(pb.id): (pb.clause_type, pb.jurisdiction)
            for pb in LegalPlaybook.objects.all()
            if pb.embedding and len(pb.embedding) == active_dims
        }

        # Group results by (clause_type, jurisdiction)
        # Only include results from playbooks matching active model
        type_buckets = defaultdict(lambda: {'scores': [], 'non_standard': 0})
        for r in ClausePlaybookResult.objects.all():
            key = str(r.playbook_id)
            if key not in playbooks:
                continue  # Skip results from playbooks with different embedding dimensions
            ct, jur = playbooks[key]
            type_buckets[(ct, jur)]['scores'].append(r.similarity_score)
            if not r.is_standard:
                type_buckets[(ct, jur)]['non_standard'] += 1

        for (ct, jur), data in type_buckets.items():
            total = len(data['scores'])
            if total == 0:
                continue
            PlaybookDriftSnapshot.objects.create(
                clause_type=ct,
                jurisdiction=jur,
                avg_similarity=round(sum(data['scores']) / total, 4),
                non_standard_rate=round(data['non_standard'] / total, 4),
            )

    # ------------------------------------------------------- update detection
    @staticmethod
    def detect_playbook_update_candidates():
        """
        Scan PlaybookDriftSnapshot for sustained deviation.  If thresholds
        are breached and no OPEN suggestion already exists, create one.
        """
        snapshots = PlaybookDriftSnapshot.objects.all()
        for s in snapshots:
            if (
                s.avg_similarity < DRIFT_SIMILARITY_THRESHOLD
                and s.non_standard_rate > DRIFT_RATE_THRESHOLD
            ):
                already_open = PlaybookUpdateSuggestion.objects.filter(
                    clause_type=s.clause_type,
                    jurisdiction=s.jurisdiction,
                    status='OPEN',
                ).exists()
                if already_open:
                    continue

                # Pull the current fallback text as the suggested new standard
                playbook = LegalPlaybook.objects.filter(
                    clause_type=s.clause_type,
                    jurisdiction__in=[s.jurisdiction, 'global'],
                ).first()

                suggested_text = playbook.fallback_clause if playbook else ""

                PlaybookUpdateSuggestion.objects.create(
                    clause_type=s.clause_type,
                    jurisdiction=s.jurisdiction,
                    avg_similarity=s.avg_similarity,
                    non_standard_rate=s.non_standard_rate,
                    reason=(
                        "Sustained deviation from standard language detected "
                        "across incoming contracts."
                    ),
                    suggested_standard=suggested_text,
                )

    # ---------------------------------------------------------- coverage calc
    @staticmethod
    def compute_playbook_coverage() -> Dict:
        """
        How much of the contract clause universe is governed by a playbook?
        """
        governed_types = set(
            LegalPlaybook.objects.values_list('clause_type', flat=True)
        )
        total_clauses = Clause.objects.filter(found=True).count()
        governed_clauses = (
            Clause.objects.filter(found=True, clause_type__in=governed_types).count()
            if governed_types else 0
        )
        coverage_pct = (
            round(governed_clauses / total_clauses * 100, 2)
            if total_clauses else 0.0
        )

        # Ungoverned clause types with counts
        ungoverned = (
            Clause.objects.filter(found=True)
            .exclude(clause_type__in=governed_types)
            .values('clause_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        return {
            'total_clauses': total_clauses,
            'governed_clauses': governed_clauses,
            'coverage_pct': coverage_pct,
            'ungoverned': list(ungoverned),
        }

    # -------------------------------------------------------- heatmap overlay
    @staticmethod
    def clause_heatmap_with_drift() -> List[Dict]:
        """
        Aggregate drift snapshots by clause_type for the heatmap overlay.
        """
        data = (
            PlaybookDriftSnapshot.objects
            .values('clause_type')
            .annotate(
                avg_similarity=Avg('avg_similarity'),
                avg_non_standard=Avg('non_standard_rate'),
            )
            .order_by('clause_type')
        )
        return list(data)


# Module-level singleton
playbook_service = PlaybookService()
