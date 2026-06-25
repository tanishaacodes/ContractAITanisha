"""
Clause Drift Detection Engine
==============================
Detects when clause language has drifted from organizational standards
using BERT cosine similarity across contracts over time.

Features:
- Compare clause text across contracts by clause type
- Flag clauses that deviate > threshold from the standard template
- Drift timeline per clause type
- Cross-contract drift heatmap
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from django.db.models import Avg, Max, Min, Count
from core.models import Contract, Clause

from .clause_clustering import get_clusterer

logger = logging.getLogger(__name__)

DRIFT_THRESHOLD = 0.75  # Below this similarity = drifted


class ClauseDriftDetector:
    """Detects clause drift across contracts using BERT cosine similarity."""

    def __init__(self, threshold: float = DRIFT_THRESHOLD):
        self.threshold = threshold
        self.clusterer = get_clusterer()

    def _embed(self, texts: List[str]) -> np.ndarray:
        """Generate BERT embeddings for a list of texts."""
        return np.array(self.clusterer.embed_clauses(texts, batch_size=16))

    def _get_standard_template(self, clause_type: str, user=None) -> Optional[Dict]:
        """
        Get the 'standard' clause for a given type.
        Standard = the clause with highest confidence for that type across all contracts.
        """
        qs = Clause.objects.filter(clause_type=clause_type).exclude(extracted_text='')
        if user:
            qs = qs.filter(contract__user=user)

        # Standard = highest confidence clause
        standard = qs.order_by('-confidence').first()
        if not standard:
            return None
        return {
            'id': str(standard.id),
            'contract_id': str(standard.contract_id),
            'contract_name': standard.contract.original_filename if standard.contract else '',
            'text': standard.extracted_text or '',
            'confidence': float(standard.confidence or 0),
        }

    def compute_drift_for_type(self, clause_type: str, user=None) -> Dict:
        """
        Compute drift for all clauses of a given type compared to the standard.

        Returns:
            Dict with standard clause, per-clause drift scores, drifted clauses, timeline
        """
        standard = self._get_standard_template(clause_type, user)
        if not standard or not standard['text']:
            return {
                'clause_type': clause_type,
                'error': 'No standard template found',
                'clauses': [],
                'drifted_count': 0,
                'avg_similarity': None,
            }

        qs = Clause.objects.filter(clause_type=clause_type).exclude(extracted_text='')
        if user:
            qs = qs.filter(contract__user=user)

        clauses = list(qs.select_related('contract').order_by('contract__created_at'))
        if not clauses:
            return {
                'clause_type': clause_type,
                'standard': standard,
                'clauses': [],
                'drifted_count': 0,
                'avg_similarity': None,
            }

        # Get all clause texts
        texts = [c.extracted_text or '' for c in clauses]
        all_texts = [standard['text']] + texts

        try:
            embeddings = self._embed(all_texts)
            std_emb = embeddings[0:1]
            clause_embs = embeddings[1:]

            # Cosine similarity of each clause vs standard
            sims = cosine_similarity(clause_embs, std_emb).flatten()
        except Exception as e:
            logger.error(f"Embedding failed for drift detection: {e}")
            sims = np.zeros(len(clauses))

        results = []
        drifted_count = 0
        for i, clause in enumerate(clauses):
            sim = float(sims[i])
            is_drifted = sim < self.threshold
            if is_drifted:
                drifted_count += 1

            results.append({
                'id': str(clause.id),
                'clause_name': clause.clause_name or '',
                'contract_id': str(clause.contract_id),
                'contract_name': clause.contract.original_filename if clause.contract else '',
                'contract_date': clause.contract.created_at.isoformat() if clause.contract and clause.contract.created_at else None,
                'similarity': round(sim, 4),
                'drift_score': round(1 - sim, 4),
                'is_drifted': is_drifted,
                'risk_level': clause.risk_level or 'UNKNOWN',
                'confidence': float(clause.confidence or 0),
                'text_preview': (clause.extracted_text or '')[:200],
            })

        avg_sim = float(np.mean(sims)) if len(sims) > 0 else None

        return {
            'clause_type': clause_type,
            'standard': standard,
            'clauses': results,
            'total_count': len(results),
            'drifted_count': drifted_count,
            'avg_similarity': round(avg_sim, 4) if avg_sim is not None else None,
            'drift_rate': round(drifted_count / len(results), 4) if results else 0,
        }

    def _clean_clause_type(self, raw: str) -> str:
        """Normalize clause_type: truncate long LLM descriptions, strip junk."""
        if not raw:
            return 'Uncategorized'
        # Truncate long LLM descriptions (e.g. "Contract Clause Category Name: Insurance Terms ...")
        for prefix in ('Contract Clause Category Name:', 'Category Name:', 'Clause Category:'):
            if raw.startswith(prefix):
                raw = raw[len(prefix):].strip()
        # Strip trailing ellipsis / trailing dots
        raw = raw.rstrip('. ')
        # If still >60 chars (LLM ramble), keep first 50 chars up to last space
        if len(raw) > 60:
            raw = raw[:50].rsplit(' ', 1)[0] + '...'
        return raw.strip()

    def get_drift_summary(self, user=None) -> List[Dict]:
        """
        Get drift summary across all clause types.
        Returns a list of {clause_type, drifted_count, total, drift_rate, avg_similarity}.
        Deduplicates clause types after normalizing names to avoid repeated cards.
        """
        qs = Clause.objects.exclude(clause_type__isnull=True).exclude(clause_type='')
        if user:
            qs = qs.filter(contract__user=user)

        raw_types = list(qs.values_list('clause_type', flat=True).distinct())

        # Normalize and deduplicate — map cleaned_name → first raw name found
        seen = {}
        for raw in raw_types:
            cleaned = self._clean_clause_type(raw)
            if cleaned not in seen:
                seen[cleaned] = raw  # keep original raw for DB lookup

        summary = []
        for cleaned_name, raw_type in seen.items():
            drift_data = self.compute_drift_for_type(raw_type, user)
            if 'error' not in drift_data:
                summary.append({
                    'clause_type': cleaned_name,  # show clean name in UI
                    'raw_clause_type': raw_type,   # used for detail drill-down
                    'total_count': drift_data['total_count'],
                    'drifted_count': drift_data['drifted_count'],
                    'drift_rate': drift_data['drift_rate'],
                    'avg_similarity': drift_data['avg_similarity'],
                    'status': 'critical' if drift_data['drift_rate'] > 0.5
                              else 'warning' if drift_data['drift_rate'] > 0.2
                              else 'healthy',
                })

        # Sort by drift_rate descending
        summary.sort(key=lambda x: x['drift_rate'], reverse=True)
        return summary

    def get_cross_contract_matrix(self, clause_type: str, user=None, max_contracts: int = 10) -> Dict:
        """
        Build a cross-contract similarity matrix for a given clause type.
        Returns NxN matrix where each cell is the similarity between two contracts' clause.
        """
        qs = Clause.objects.filter(clause_type=clause_type).exclude(extracted_text='')
        if user:
            qs = qs.filter(contract__user=user)

        clauses = list(qs.select_related('contract')[:max_contracts])
        if len(clauses) < 2:
            return {'error': 'Need at least 2 contracts for comparison', 'matrix': []}

        texts = [c.extracted_text or '' for c in clauses]
        labels = [c.contract.original_filename[:20] if c.contract else str(c.id)[:8]
                  for c in clauses]

        try:
            embeddings = self._embed(texts)
            matrix = cosine_similarity(embeddings)
        except Exception as e:
            logger.error(f"Matrix computation failed: {e}")
            matrix = np.eye(len(clauses))

        return {
            'clause_type': clause_type,
            'labels': labels,
            'matrix': [[round(float(v), 4) for v in row] for row in matrix],
            'contract_ids': [str(c.contract_id) for c in clauses],
        }

    def get_drift_timeline(self, clause_type: str, user=None) -> List[Dict]:
        """
        Get similarity score over time (sorted by contract creation date).
        Returns data points suitable for a line chart.
        """
        result = self.compute_drift_for_type(clause_type, user)
        if 'error' in result or not result['clauses']:
            return []

        # Sort by contract date
        timeline = [c for c in result['clauses'] if c['contract_date']]
        timeline.sort(key=lambda x: x['contract_date'])

        return [
            {
                'date': c['contract_date'],
                'contract_name': c['contract_name'],
                'similarity': c['similarity'],
                'drift_score': c['drift_score'],
                'is_drifted': c['is_drifted'],
            }
            for c in timeline
        ]


_drift_detector = None


def get_drift_detector() -> ClauseDriftDetector:
    global _drift_detector
    if _drift_detector is None:
        _drift_detector = ClauseDriftDetector()
    return _drift_detector
