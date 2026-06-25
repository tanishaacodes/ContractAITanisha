"""
CFO Financial Analytics Dashboard Views
=========================================
Provides CFO-level financial exposure metrics from clause data:
- Loss by Clause Type
- Loss by Contract
- Cash Flow Projection (risk exposure timeline)
- Risk Heatmap (clause_type x contract matrix)
- Predictive Risk (Prophet/rule-based)
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Avg, Count, Max, Min, Q
from django.db.models.functions import TruncMonth
from core.models import Contract, Clause
import logging
import json
from datetime import datetime, timedelta
import calendar

logger = logging.getLogger(__name__)


FINANCIAL_MULTIPLIER = 50_000.0  # risk_score × ₹50,000 → financial exposure (per spec)


def _scope_qs(qs, request):
    """Optionally filter by a single contract if ?contract_id= is provided."""
    contract_id = request.query_params.get('contract_id', '').strip()
    if contract_id:
        qs = qs.filter(contract_id=contract_id)
    return qs


def _clean_clause_type(raw: str) -> str:
    """Normalize clause_type names — strip LLM prefix garbage, truncate long descriptions."""
    if not raw:
        return 'Uncategorized'
    for prefix in ('Contract Clause Category Name:', 'Category Name:', 'Clause Category:'):
        if raw.startswith(prefix):
            raw = raw[len(prefix):].strip()
    raw = raw.rstrip('. ')
    if len(raw) > 50:
        raw = raw[:50].rsplit(' ', 1)[0] + '...'
    return raw.strip() or 'Uncategorized'


def _fi(risk_score) -> float:
    """Compute financial impact on-the-fly: risk_score × 50,000. No RRIE dependency."""
    return round(float(risk_score or 0) * FINANCIAL_MULTIPLIER, 2)


class LossByClauseTypeView(APIView):
    """
    GET /api/analytics/cfo/loss-by-type/
    Aggregated financial exposure by clause type.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            qs = _scope_qs(Clause.objects.filter(
                contract__user=request.user,
                risk_score__isnull=False,
            ), request).values('clause_type').annotate(
                avg_risk=Avg('risk_score'),
                max_risk=Max('risk_score'),
                count=Count('id'),
            ).order_by('-avg_risk')

            merged = {}
            for row in qs:
                if not row['clause_type']:
                    continue
                clean = _clean_clause_type(row['clause_type'])
                avg_r = float(row['avg_risk'] or 0)
                max_r = float(row['max_risk'] or 0)
                cnt = row['count']
                if clean not in merged:
                    merged[clean] = {'risk_sum': 0.0, 'max_risk': 0.0, 'clause_count': 0}
                merged[clean]['risk_sum'] += avg_r * cnt
                merged[clean]['max_risk'] = max(merged[clean]['max_risk'], max_r)
                merged[clean]['clause_count'] += cnt

            results = []
            for clean, m in merged.items():
                avg_risk = m['risk_sum'] / max(m['clause_count'], 1)
                total_loss = _fi(avg_risk) * m['clause_count']
                results.append({
                    'clause_type': clean,
                    'total_loss': round(total_loss, 2),
                    'avg_loss': round(_fi(avg_risk), 2),
                    'max_loss': round(_fi(m['max_risk']), 2),
                    'clause_count': m['clause_count'],
                    'avg_risk_score': round(avg_risk, 4),
                })
            results.sort(key=lambda x: x['total_loss'], reverse=True)
            total_exposure = sum(r['total_loss'] for r in results)

            return Response({
                'data': results,
                'total_exposure': round(total_exposure, 2),
                'total_clause_types': len(results),
            })
        except Exception as e:
            logger.error(f"Loss by clause type failed: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LossByContractView(APIView):
    """
    GET /api/analytics/cfo/loss-by-contract/
    Financial exposure aggregated per contract.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            qs = _scope_qs(Clause.objects.filter(
                contract__user=request.user,
                risk_score__isnull=False,
            ), request).values(
                'contract__id', 'contract__original_filename', 'contract__created_at'
            ).annotate(
                avg_risk=Avg('risk_score'),
                high_risk_count=Count('id', filter=Q(risk_level='HIGH')),
                clause_count=Count('id'),
            ).order_by('-avg_risk')

            results = []
            for row in qs:
                avg_risk = float(row['avg_risk'] or 0)
                total_loss = _fi(avg_risk) * row['clause_count']
                results.append({
                    'contract_id': str(row['contract__id']),
                    'contract_name': row['contract__original_filename'] or 'Unknown',
                    'total_loss': round(total_loss, 2),
                    'avg_risk_score': round(avg_risk, 4),
                    'clause_count': row['clause_count'],
                    'created_at': row['contract__created_at'].isoformat() if row['contract__created_at'] else None,
                })
            results.sort(key=lambda x: x['total_loss'], reverse=True)
            total_exposure = sum(r['total_loss'] for r in results)

            return Response({
                'data': results,
                'total_exposure': round(total_exposure, 2),
                'total_contracts': len(results),
            })
        except Exception as e:
            logger.error(f"Loss by contract failed: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CashFlowProjectionView(APIView):
    """
    GET /api/analytics/cfo/cash-flow/
    Projects when financial risk exposure materializes over the next 12 months.
    Uses contract creation date + clause type weights to estimate timeline.
    """
    permission_classes = [IsAuthenticated]

    # Risk materialization weights per clause type (months to materialize)
    TYPE_MATURITY = {
        'payment': 1,
        'indemnification': 3,
        'liability': 6,
        'termination': 2,
        'arbitration': 12,
        'dispute': 9,
        'intellectual property': 18,
        'confidentiality': 3,
        'governing law': 24,
        'warranty': 6,
    }

    def _get_maturity_months(self, clause_type: str) -> int:
        if not clause_type:
            return 6
        low = clause_type.lower()
        for key, months in self.TYPE_MATURITY.items():
            if key in low:
                return months
        return 6  # default

    def get(self, request):
        try:
            clauses = _scope_qs(Clause.objects.filter(
                contract__user=request.user,
                risk_score__isnull=False,
            ), request).select_related('contract')

            # Project each clause's financial impact onto a future month
            monthly = {}
            today = datetime.now()

            for clause in clauses:
                maturity_months = self._get_maturity_months(clause.clause_type)
                base_date = clause.contract.created_at if clause.contract and clause.contract.created_at else today
                materialize_date = base_date + timedelta(days=maturity_months * 30)
                key = materialize_date.strftime('%Y-%m')

                if key not in monthly:
                    monthly[key] = {'month': key, 'exposure': 0.0, 'clause_count': 0}
                monthly[key]['exposure'] += _fi(clause.risk_score)
                monthly[key]['clause_count'] += 1

            # Generate next 24 months skeleton
            projection = []
            for i in range(24):
                m = (today + timedelta(days=i * 30)).strftime('%Y-%m')
                entry = monthly.get(m, {'month': m, 'exposure': 0.0, 'clause_count': 0})
                projection.append(entry)

            # Add cumulative
            cumulative = 0.0
            for p in projection:
                cumulative += p['exposure']
                p['cumulative'] = round(cumulative, 2)
                p['exposure'] = round(p['exposure'], 2)

            return Response({
                'projection': projection,
                'total_projected_exposure': round(cumulative, 2),
                'months': 24,
            })
        except Exception as e:
            logger.error(f"Cash flow projection failed: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RiskHeatmapView(APIView):
    """
    GET /api/analytics/cfo/risk-heatmap/
    Clause type × contract risk heatmap.
    Returns a matrix of avg risk_score indexed by clause_type and contract_name.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            clauses = _scope_qs(Clause.objects.filter(
                contract__user=request.user,
            ), request).select_related('contract').exclude(clause_type__isnull=True).exclude(clause_type='')

            # Build matrix: rows = clause types, cols = contracts
            clause_types = set()
            contracts = {}
            matrix_data = {}

            for clause in clauses:
                ctype = _clean_clause_type(clause.clause_type)
                cid = str(clause.contract_id)
                cname = (clause.contract.original_filename or cid)[:30] if clause.contract else cid
                risk = float(clause.risk_score or 0)

                clause_types.add(ctype)
                if cid not in contracts:
                    contracts[cid] = cname

                key = (ctype, cid)
                if key not in matrix_data:
                    matrix_data[key] = {'risk_scores': [], 'clause_count': 0}
                matrix_data[key]['risk_scores'].append(risk)
                matrix_data[key]['clause_count'] += 1

            clause_types = sorted(clause_types)
            contract_ids = list(contracts.keys())
            contract_names = [contracts[cid] for cid in contract_ids]

            rows = []
            for ctype in clause_types:
                row = {'clause_type': ctype, 'values': []}
                for cid in contract_ids:
                    key = (ctype, cid)
                    if key in matrix_data:
                        avg_risk = sum(matrix_data[key]['risk_scores']) / len(matrix_data[key]['risk_scores'])
                        row['values'].append({
                            'risk': round(avg_risk, 4),
                            'financial': round(_fi(avg_risk) * matrix_data[key]['clause_count'], 2),
                        })
                    else:
                        row['values'].append({'risk': 0, 'financial': 0})
                rows.append(row)

            return Response({
                'clause_types': clause_types,
                'contracts': contract_names,
                'contract_ids': contract_ids,
                'rows': rows,
            })
        except Exception as e:
            logger.error(f"Risk heatmap failed: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CFOSummaryView(APIView):
    """
    GET /api/analytics/cfo/summary/
    Top-level KPI summary for the CFO dashboard.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            clauses = _scope_qs(Clause.objects.filter(contract__user=request.user), request)

            total_clauses = clauses.count()
            scored_clauses = clauses.filter(risk_score__isnull=False)
            avg_risk = float(scored_clauses.aggregate(avg=Avg('risk_score'))['avg'] or 0)
            # Sum financial impact per clause individually
            total_exposure = sum(_fi(r) for r in scored_clauses.values_list('risk_score', flat=True))
            high_risk_count = clauses.filter(risk_level='HIGH').count()
            contract_id_filter = request.query_params.get('contract_id', '').strip()
            if contract_id_filter:
                contracts_count = Contract.objects.filter(user=request.user, id=contract_id_filter).count()
            else:
                contracts_count = Contract.objects.filter(user=request.user).count()

            # Top 5 highest exposure clauses — ordered by risk_score (no RRIE dependency)
            top_clauses = clauses.filter(
                risk_score__isnull=False
            ).select_related('contract').order_by('-risk_score')[:5]

            top_list = [{
                'id': str(c.id),
                'clause_name': c.clause_name,
                'clause_type': _clean_clause_type(c.clause_type),
                'financial_impact': _fi(c.risk_score),
                'risk_level': c.risk_level,
                'risk_score': float(c.risk_score or 0),
                'contract_name': c.contract.original_filename if c.contract else '',
            } for c in top_clauses]

            return Response({
                'kpis': {
                    'total_exposure': round(total_exposure, 2),
                    'avg_risk_score': round(float(avg_risk), 4),
                    'high_risk_clauses': high_risk_count,
                    'total_clauses': total_clauses,
                    'total_contracts': contracts_count,
                    'exposure_per_contract': round(float(total_exposure) / max(contracts_count, 1), 2),
                },
                'top_exposure_clauses': top_list,
            })
        except Exception as e:
            logger.error(f"CFO summary failed: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
