"""
Auto-Promotion & Retirement Engine
Automatically promotes best-performing clauses and retires weak ones
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone

from .scorer import get_health_scorer


class ClausePromoter:
    """
    Handles automatic promotion and retirement of clauses based on health metrics
    """

    def __init__(self):
        self.scorer = get_health_scorer()

    def analyze_clause_family(self, clause_id: str) -> Dict:
        """
        Analyze all versions of a clause and their health metrics

        Args:
            clause_id: ID of the base clause

        Returns:
            Dict with analysis results and recommendations
        """
        from core.models import Clause, ClauseVersion, ClauseEvent, ClauseHealthMetrics

        try:
            clause = Clause.objects.get(id=clause_id)
        except Clause.DoesNotExist:
            return {'error': 'Clause not found'}

        # Get all versions
        versions = ClauseVersion.objects.filter(clause=clause).order_by('-version_number')

        if not versions.exists():
            return {'error': 'No versions found'}

        # Analyze each version
        version_analysis = []
        for version in versions:
            events = ClauseEvent.objects.filter(clause_version=version)
            metrics = self.scorer.compute_health(list(events), usage_count=events.count())
            status = self.scorer.determine_status(metrics['health_score'])

            version_analysis.append({
                'version_id': str(version.id),
                'version_number': version.version_number,
                'metrics': metrics,
                'status': status,
                'event_count': events.count()
            })

        # Find best performing version
        best_version = max(version_analysis, key=lambda x: x['metrics']['health_score'])

        return {
            'clause_id': str(clause_id),
            'clause_name': clause.clause_name,
            'total_versions': len(version_analysis),
            'versions': version_analysis,
            'best_version': best_version,
            'recommendation': self._generate_recommendation(version_analysis)
        }

    def _generate_recommendation(self, version_analysis: List[Dict]) -> str:
        """Generate recommendation based on version analysis"""
        if not version_analysis:
            return "No versions to analyze"

        best = max(version_analysis, key=lambda x: x['metrics']['health_score'])
        worst = min(version_analysis, key=lambda x: x['metrics']['health_score'])

        if best['metrics']['health_score'] >= 0.8:
            return f"Version {best['version_number']} is performing excellently (health: {best['metrics']['health_score']:.2f})"
        elif worst['metrics']['health_score'] < 0.4:
            return f"Consider retiring version {worst['version_number']} (health: {worst['metrics']['health_score']:.2f})"
        else:
            return "All versions performing adequately"

    @transaction.atomic
    def auto_promote_clause(self, clause_id: str, dry_run: bool = False) -> Dict:
        """
        Automatically promote the best-performing clause version

        Args:
            clause_id: ID of the clause
            dry_run: If True, don't actually promote, just analyze

        Returns:
            Dict with promotion results
        """
        from core.models import Clause, ClauseVersion, ClauseEvent, ClauseHealthMetrics

        # Analyze all versions
        analysis = self.analyze_clause_family(clause_id)
        if 'error' in analysis:
            return analysis

        best_version_data = analysis['best_version']
        best_version_id = best_version_data['version_id']

        # Get the actual version object
        try:
            best_version = ClauseVersion.objects.get(id=best_version_id)
            clause = Clause.objects.get(id=clause_id)
        except (ClauseVersion.DoesNotExist, Clause.DoesNotExist):
            return {'error': 'Version or clause not found'}

        # Check if promotion is warranted
        sibling_metrics = [v['metrics'] for v in analysis['versions'] if v['version_id'] != best_version_id]
        should_promote, reason = self.scorer.should_promote(
            best_version_data['metrics'],
            sibling_metrics
        )

        if not should_promote:
            return {
                'promoted': False,
                'reason': reason,
                'best_version': best_version_data
            }

        if dry_run:
            return {
                'promoted': False,
                'dry_run': True,
                'would_promote': True,
                'reason': reason,
                'best_version': best_version_data
            }

        # Perform promotion
        # Update or create health metrics
        health_metrics, created = ClauseHealthMetrics.objects.get_or_create(
            clause=clause,
            defaults=best_version_data['metrics']
        )

        if not created:
            # Update existing metrics
            for key, value in best_version_data['metrics'].items():
                setattr(health_metrics, key, value)

        health_metrics.status = 'ALIVE'
        health_metrics.is_promoted = True
        health_metrics.promoted_at = timezone.now()
        health_metrics.promotion_reason = reason
        health_metrics.save()

        return {
            'promoted': True,
            'reason': reason,
            'best_version': best_version_data,
            'health_metrics_id': str(health_metrics.id)
        }

    @transaction.atomic
    def auto_retire_weak_clauses(self, min_health_score: float = 0.45, dry_run: bool = False) -> Dict:
        """
        Automatically retire clauses with low health scores

        Args:
            min_health_score: Minimum health score to keep alive
            dry_run: If True, don't actually retire, just analyze

        Returns:
            Dict with retirement results
        """
        from core.models import ClauseHealthMetrics

        # Find weak clauses
        weak_clauses = ClauseHealthMetrics.objects.filter(
            health_score__lt=min_health_score,
            status__in=['ALIVE', 'WEAK']
        )

        retired_count = 0
        retired_list = []

        for metrics in weak_clauses:
            should_retire, reason = self.scorer.should_retire(metrics.__dict__)

            if should_retire:
                retired_list.append({
                    'clause_id': str(metrics.clause.id),
                    'clause_name': metrics.clause.clause_name,
                    'health_score': metrics.health_score,
                    'reason': reason
                })

                if not dry_run:
                    metrics.status = 'RETIRED'
                    metrics.save()
                    retired_count += 1

        return {
            'dry_run': dry_run,
            'analyzed': weak_clauses.count(),
            'retired': retired_count if not dry_run else len(retired_list),
            'clauses': retired_list
        }

    def batch_promote_clauses(self, clause_ids: List[str] = None, dry_run: bool = False) -> Dict:
        """
        Batch process multiple clauses for auto-promotion

        Args:
            clause_ids: List of clause IDs to process (None = all)
            dry_run: If True, don't actually promote

        Returns:
            Summary of promotions
        """
        from core.models import Clause

        if clause_ids:
            clauses = Clause.objects.filter(id__in=clause_ids)
        else:
            # Process all clauses with health metrics
            clauses = Clause.objects.filter(health_metrics__isnull=False)

        results = {
            'total': clauses.count(),
            'promoted': 0,
            'skipped': 0,
            'errors': 0,
            'details': []
        }

        for clause in clauses:
            result = self.auto_promote_clause(str(clause.id), dry_run=dry_run)

            if result.get('promoted'):
                results['promoted'] += 1
            elif 'error' in result:
                results['errors'] += 1
            else:
                results['skipped'] += 1

            results['details'].append({
                'clause_id': str(clause.id),
                'clause_name': clause.clause_name,
                'result': result
            })

        return results

    def health_report(self) -> Dict:
        """
        Generate overall health report for all clauses

        Returns:
            Summary statistics and recommendations
        """
        from core.models import ClauseHealthMetrics

        all_metrics = ClauseHealthMetrics.objects.all()

        if not all_metrics.exists():
            return {'error': 'No health metrics available'}

        status_counts = {
            'ALIVE': all_metrics.filter(status='ALIVE').count(),
            'WEAK': all_metrics.filter(status='WEAK').count(),
            'RETIRED': all_metrics.filter(status='RETIRED').count()
        }

        from django.db.models import Avg

        avg_health = all_metrics.aggregate(
            avg_health=Avg('health_score'),
            avg_success=Avg('success_rate'),
            avg_enforce=Avg('enforceability_score')
        )

        # Find top performers
        top_clauses = all_metrics.filter(status='ALIVE').order_by('-health_score')[:5]

        # Find at-risk clauses
        at_risk = all_metrics.filter(
            status='WEAK',
            health_score__lt=0.5
        ).order_by('health_score')[:5]

        return {
            'total_clauses': all_metrics.count(),
            'status_distribution': status_counts,
            'average_metrics': {
                'health_score': round(avg_health.get('avg_health', 0), 3),
                'success_rate': round(avg_health.get('avg_success', 0), 3),
                'enforceability': round(avg_health.get('avg_enforce', 0), 3)
            },
            'top_performers': [{
                'clause_id': str(m.clause.id),
                'clause_name': m.clause.clause_name,
                'health_score': m.health_score
            } for m in top_clauses],
            'at_risk': [{
                'clause_id': str(m.clause.id),
                'clause_name': m.clause.clause_name,
                'health_score': m.health_score
            } for m in at_risk]
        }


# Singleton instance
_promoter = None


def get_promoter() -> ClausePromoter:
    """Get or create singleton promoter"""
    global _promoter
    if _promoter is None:
        _promoter = ClausePromoter()
    return _promoter
