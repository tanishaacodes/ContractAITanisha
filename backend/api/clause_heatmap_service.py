"""
Clause Heatmap Service
Aggregates clause-level risk across entire portfolio
"""
from django.db.models import Count, Avg, Q, F
from django.utils import timezone
from core.models import Clause, Contract
from .risk_scoring_model import clause_risk_enricher
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class ClauseHeatmapService:
    """Portfolio-wide clause risk analysis"""

    def enrich_clause_risk(self, clause: Clause) -> Dict:
        """
        Enrich a single clause with risk scoring.
        Maps ClauseRiskEnricher output to likelihood/impact.
        """
        # Extract clause text
        clause_text = clause.extracted_text or clause.context_sentences or ""
        intent_name = clause.clause_type or clause.clause_name

        if not clause_text:
            logger.warning(f"No text found for clause {clause.id}, skipping enrichment")
            return None

        # Use existing ClauseRiskEnricher
        enrichment = clause_risk_enricher.enrich_risk(
            clause_text=clause_text,
            intent_name=intent_name,
            party="COUNTERPARTY",  # Default assumption
            base_risk=0.5,  # Neutral starting point
        )

        # Map to likelihood/impact (1-5 scale)
        # Likelihood = based on clause_strength and party_bias
        likelihood = self._calculate_likelihood(
            enrichment['clause_strength'],
            enrichment['party_bias']
        )

        # Impact = based on missing_safeguards and financial_factor
        impact = self._calculate_impact(
            enrichment['missing_safeguards'],
            enrichment['financial_factor'],
            enrichment['final_risk']
        )

        # Update clause model
        clause.risk_score = enrichment['final_risk']
        clause.risk_level = enrichment['severity']
        clause.risk_factors = {
            'clause_strength': enrichment['clause_strength'],
            'party_bias': enrichment['party_bias'],
            'missing_safeguards': enrichment['missing_safeguards'],
            'temporal_factor': enrichment['temporal_factor'],
            'financial_factor': enrichment['financial_factor'],
            'explanation': enrichment['explanation'],
            'risk_factors': enrichment['risk_factors'],
        }
        clause.likelihood_score = likelihood
        clause.impact_score = impact
        clause.enriched_at = timezone.now()
        clause.save()

        return enrichment

    def _calculate_likelihood(self, strength: float, bias: float) -> float:
        """Map strength/bias to likelihood (1-5)"""
        # Combine strength and bias factors
        combined = (strength + bias) / 2
        # Map to 1-5 scale
        likelihood = combined * 3.0
        return min(max(1.0, likelihood), 5.0)

    def _calculate_impact(self, safeguards: float, financial: float, final_risk: float) -> float:
        """Map safeguards/financial to impact (1-5)"""
        # Higher missing safeguards + financial exposure = higher impact
        combined = (safeguards + financial) / 2
        # Weighted by final_risk
        impact = combined * final_risk * 5.0
        return min(max(1.0, impact), 5.0)

    def get_portfolio_heatmap(self, user_id: str) -> Dict:
        """
        Generate portfolio-wide clause risk heatmap.
        Returns matrix data + metrics.
        """
        # Get all clauses for user's contracts
        clauses = Clause.objects.filter(
            contract__user_id=user_id,
            found=True
        ).select_related('contract')

        total_clauses = clauses.count()

        if total_clauses == 0:
            return {
                'matrix': [],
                'metrics': {
                    'total_clauses': 0,
                    'high_risk_count': 0,
                    'medium_risk_count': 0,
                    'low_risk_count': 0,
                    'average_risk': 0,
                    'portfolio_health': 100,
                    'controls_implemented': 0
                },
                'top_risks': [],
                'type_breakdown': [],
                'total_clauses': 0,
                'contracts_analyzed': 0
            }

        # Check if enrichment needed
        unenriched_count = clauses.filter(risk_score__isnull=True).count()
        if unenriched_count > 0:
            logger.info(f"Enriching {unenriched_count} clauses...")
            # Enrich up to 100 clauses at a time (to avoid timeout)
            for clause in clauses.filter(risk_score__isnull=True)[:100]:
                try:
                    self.enrich_clause_risk(clause)
                except Exception as e:
                    logger.error(f"Failed to enrich clause {clause.id}: {str(e)}")

        # Fetch enriched data
        enriched_clauses = clauses.exclude(risk_score__isnull=True)

        # Build heatmap matrix (5x5 aggregated grid)
        matrix = self._build_risk_matrix(enriched_clauses)

        # Calculate metrics
        metrics = self._calculate_metrics(enriched_clauses)

        # Get top risky clauses
        top_risks = self._get_top_risky_clauses(enriched_clauses, limit=10)

        # Risk breakdown by clause type
        type_breakdown = self._get_risk_by_type(enriched_clauses)

        return {
            'matrix': matrix,
            'metrics': metrics,
            'top_risks': top_risks,
            'type_breakdown': type_breakdown,
            'total_clauses': enriched_clauses.count(),
            'contracts_analyzed': enriched_clauses.values('contract').distinct().count()
        }

    def _build_risk_matrix_individual(self, clauses) -> List[Dict]:
        """
        Build matrix with individual clause points (not aggregated cells).
        Returns one entry per clause for more granular visualization.
        """
        matrix_data = []

        for clause in clauses:
            if clause.likelihood_score and clause.impact_score:
                matrix_data.append({
                    'likelihood': round(clause.likelihood_score, 1),
                    'impact': round(clause.impact_score, 1),
                    'count': 1,  # Individual clause
                    'severity': clause.risk_level or 'MEDIUM',
                    'contracts': [clause.contract.original_filename],
                    'clause_name': clause.clause_name,
                    'clause_type': clause.clause_type or 'Unclassified',
                    'risk_score': clause.risk_score
                })

        return matrix_data

    def _build_risk_matrix(self, clauses) -> List[Dict]:
        """
        Build 5x5 risk matrix with counts.
        Returns: [
            {likelihood: 1, impact: 1, count: 5, severity: 'LOW', contracts: ['file1.pdf', 'file2.pdf']},
            {likelihood: 5, impact: 5, count: 12, severity: 'CRITICAL', contracts: [...]},
            ...
        ]
        """
        matrix_data = []

        for likelihood in range(1, 6):
            for impact in range(1, 6):
                # Get clauses in this cell
                cell_clauses = clauses.filter(
                    likelihood_score__gte=likelihood - 0.5,
                    likelihood_score__lt=likelihood + 0.5,
                    impact_score__gte=impact - 0.5,
                    impact_score__lt=impact + 0.5
                )

                count = cell_clauses.count()

                # Get unique contract names (limit to top 5 to avoid huge tooltips)
                contract_names = list(
                    cell_clauses.values_list('contract__original_filename', flat=True)
                    .distinct()[:5]
                )

                # Determine severity based on actual clause risk levels in this cell
                if count > 0:
                    # Get the highest risk level among clauses in this cell
                    risk_levels = cell_clauses.values_list('risk_level', flat=True)
                    if 'HIGH' in risk_levels:
                        severity = 'HIGH'
                    elif 'MEDIUM' in risk_levels:
                        severity = 'MEDIUM'
                    elif 'LOW' in risk_levels:
                        severity = 'LOW'
                    else:
                        # Fallback to position-based if no risk_level set
                        if likelihood >= 4 and impact >= 4:
                            severity = 'CRITICAL'
                        elif likelihood >= 3 and impact >= 3:
                            severity = 'HIGH'
                        elif likelihood >= 2 or impact >= 2:
                            severity = 'MEDIUM'
                        else:
                            severity = 'LOW'
                else:
                    # Empty cell - use position-based severity
                    if likelihood >= 4 and impact >= 4:
                        severity = 'CRITICAL'
                    elif likelihood >= 3 and impact >= 3:
                        severity = 'HIGH'
                    elif likelihood >= 2 or impact >= 2:
                        severity = 'MEDIUM'
                    else:
                        severity = 'LOW'

                matrix_data.append({
                    'likelihood': likelihood,
                    'impact': impact,
                    'count': count,
                    'severity': severity,
                    'contracts': contract_names
                })

        return matrix_data

    def _calculate_metrics(self, clauses) -> Dict:
        """Calculate key metrics for dashboard cards"""
        total = clauses.count()

        if total == 0:
            return {
                'total_clauses': 0,
                'high_risk_count': 0,
                'medium_risk_count': 0,
                'low_risk_count': 0,
                'average_risk': 0,
                'portfolio_health': 100,
                'controls_implemented': 0
            }

        high_risk = clauses.filter(risk_level='HIGH').count()
        medium_risk = clauses.filter(risk_level='MEDIUM').count()
        low_risk = clauses.filter(risk_level='LOW').count()
        avg_risk = clauses.aggregate(Avg('risk_score'))['risk_score__avg'] or 0

        # Portfolio health score (0-100, inverse of risk)
        portfolio_health = max(0, 100 - (avg_risk * 100))

        # Controls implemented = clauses with safeguards (missing_safeguards < 1.2)
        controls = 0
        for clause in clauses:
            if clause.risk_factors and isinstance(clause.risk_factors, dict):
                missing_safeguards = clause.risk_factors.get('missing_safeguards', 1.5)
                if missing_safeguards < 1.2:
                    controls += 1

        controls_pct = (controls / total) * 100 if total > 0 else 0

        return {
            'total_clauses': total,
            'high_risk_count': high_risk,
            'medium_risk_count': medium_risk,
            'low_risk_count': low_risk,
            'average_risk': round(avg_risk, 3),
            'portfolio_health': round(portfolio_health, 1),
            'controls_implemented': round(controls_pct, 1)
        }

    def _get_top_risky_clauses(self, clauses, limit=10) -> List[Dict]:
        """Get top N riskiest clauses"""
        top = clauses.order_by('-risk_score')[:limit]

        return [
            {
                'id': str(c.id),
                'clause_name': c.clause_name,
                'clause_type': c.clause_type or 'Unclassified',
                'risk_score': round(c.risk_score, 3) if c.risk_score else 0,
                'risk_level': c.risk_level or 'UNKNOWN',
                'likelihood': round(c.likelihood_score, 1) if c.likelihood_score else 0,
                'impact': round(c.impact_score, 1) if c.impact_score else 0,
                'contract_name': c.contract.original_filename,
                'contract_id': str(c.contract.id),
                'explanation': c.risk_factors.get('explanation', '') if c.risk_factors else '',
                'extracted_text': c.extracted_text[:200] if c.extracted_text else ''
            }
            for c in top
        ]

    def _get_risk_by_type(self, clauses) -> List[Dict]:
        """Aggregate risk by clause type"""
        type_stats = clauses.values('clause_type').annotate(
            count=Count('id'),
            avg_risk=Avg('risk_score'),
            high_count=Count('id', filter=Q(risk_level='HIGH'))
        ).order_by('-avg_risk')[:10]

        return [
            {
                'clause_type': stat['clause_type'] or 'Unclassified',
                'count': stat['count'],
                'avg_risk': round(stat['avg_risk'], 3) if stat['avg_risk'] else 0,
                'high_risk_count': stat['high_count']
            }
            for stat in type_stats
        ]


# Global service instance
clause_heatmap_service = ClauseHeatmapService()
