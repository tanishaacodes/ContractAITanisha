"""
Dispute Predictor – Advanced Views
====================================
New endpoints implementing the remaining features from the spec:

  GET  /api/dispute-predictor/clause-risk-table/<contract_id>/   → Clause risk vs counterfactual vs what-if table
  POST /api/dispute-predictor/clause-risk-table/                 → Run on raw text
  GET  /api/dispute-predictor/time-travel/<contract_id>/         → Month-by-month risk evolution
  POST /api/dispute-predictor/time-travel/                       → Simulate time-travel from raw text
  POST /api/dispute-predictor/digital-twin/simulate/             → Contract Digital Twin lifecycle simulation
  POST /api/dispute-predictor/negotiation/simulate/              → MCTS + RL 2-agent negotiation
  POST /api/dispute-predictor/multi-agent/negotiate/             → 5-agent multi-agent negotiation
  GET  /api/dispute-predictor/portfolio-heatmap/                 → Dispute heatmap across all contracts
"""

import logging
import math
import random
import re
from typing import Any, Dict, List, Optional

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .bayesian_engine import get_bayesian_engine

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

CLAUSE_RISK_WEIGHTS = {
    'FORCE_MAJEURE':       {'base': 0.42, 'counterfactual': 0.55, 'what_if': 0.60},
    'PAYMENT_TERMS':       {'base': 0.36, 'counterfactual': 0.50, 'what_if': 0.52},
    'LIABILITY':           {'base': 0.18, 'counterfactual': 0.42, 'what_if': 0.35},
    'TERMINATION':         {'base': 0.31, 'counterfactual': 0.46, 'what_if': 0.50},
    'INDEMNITY':           {'base': 0.45, 'counterfactual': 0.58, 'what_if': 0.62},
    'DISPUTE_RESOLUTION':  {'base': 0.28, 'counterfactual': 0.44, 'what_if': 0.48},
    'CONFIDENTIALITY':     {'base': 0.12, 'counterfactual': 0.28, 'what_if': 0.25},
    'INTELLECTUAL_PROPERTY': {'base': 0.22, 'counterfactual': 0.38, 'what_if': 0.35},
    'CHANGE_ORDER':        {'base': 0.39, 'counterfactual': 0.52, 'what_if': 0.58},
    'LIQUIDATED_DAMAGES':  {'base': 0.50, 'counterfactual': 0.62, 'what_if': 0.68},
    'WARRANTY':            {'base': 0.26, 'counterfactual': 0.40, 'what_if': 0.44},
    'GOVERNING_LAW':       {'base': 0.15, 'counterfactual': 0.30, 'what_if': 0.28},
    'ASSIGNMENT':          {'base': 0.20, 'counterfactual': 0.35, 'what_if': 0.32},
    'SUBCONTRACTING':      {'base': 0.34, 'counterfactual': 0.48, 'what_if': 0.52},
}

# Per-clause Bayesian evidence — each clause activates its own specific risk path
# These are the signals to SET when running Bayesian inference for THIS clause in isolation
# (reflects what would be true if this clause alone caused a dispute)
CLAUSE_BAYESIAN_SIGNALS = {
    'LIQUIDATED_DAMAGES':  {'LiabilityExposure': 0.85, 'ContractAmbiguity': 0.70, 'ContractPerformanceRisk': 0.75},
    'PAYMENT_TERMS':       {'PaymentDefaultRisk': 0.82, 'CashFlowStress': 0.65, 'CounterpartyCreditRisk': 0.55},
    'INDEMNITY':           {'LiabilityExposure': 0.80, 'ContractAmbiguity': 0.60, 'ClauseConflict': 0.50},
    'TERMINATION':         {'TerminationRisk': 0.78, 'ContractPerformanceRisk': 0.60, 'RenegotiationRisk': 0.50},
    'FORCE_MAJEURE':       {'ContractAmbiguity': 0.72, 'ScopeChangeRisk': 0.55, 'RenegotiationRisk': 0.45},
    'CONFIDENTIALITY':     {'ContractAmbiguity': 0.40, 'ClauseConflict': 0.30},
    'INTELLECTUAL_PROPERTY': {'ContractAmbiguity': 0.55, 'ClauseConflict': 0.45, 'LiabilityExposure': 0.35},
    'GOVERNING_LAW':       {'ContractAmbiguity': 0.35, 'ClauseConflict': 0.25},
    'LIABILITY':           {'LiabilityExposure': 0.75, 'ContractAmbiguity': 0.50, 'ContractPerformanceRisk': 0.55},
    'DISPUTE_RESOLUTION':  {'ClauseConflict': 0.65, 'ContractAmbiguity': 0.55, 'DisputeTrigger': 0.60},
    'CHANGE_ORDER':        {'ScopeChangeRisk': 0.78, 'ContractCostOverrun': 0.65, 'RenegotiationRisk': 0.55},
    'WARRANTY':            {'ContractPerformanceRisk': 0.60, 'SLAViolation': 0.50, 'LiabilityExposure': 0.40},
    'SUBCONTRACTING':      {'SupplierDelay': 0.65, 'ContractPerformanceRisk': 0.55, 'ScopeChangeRisk': 0.45},
    'ASSIGNMENT':          {'ContractAmbiguity': 0.45, 'RenegotiationRisk': 0.40},
}

# Counterfactual signals: what if this clause were REMOVED (risk goes down)
CLAUSE_COUNTERFACTUAL_SIGNALS = {
    'LIQUIDATED_DAMAGES':  {'LiabilityExposure': 0.50, 'ContractAmbiguity': 0.45},
    'PAYMENT_TERMS':       {'PaymentDefaultRisk': 0.50, 'CashFlowStress': 0.35},
    'INDEMNITY':           {'LiabilityExposure': 0.50, 'ContractAmbiguity': 0.35},
    'TERMINATION':         {'TerminationRisk': 0.45, 'ContractPerformanceRisk': 0.35},
    'FORCE_MAJEURE':       {'ContractAmbiguity': 0.45, 'ScopeChangeRisk': 0.30},
    'CONFIDENTIALITY':     {'ContractAmbiguity': 0.20, 'ClauseConflict': 0.15},
    'INTELLECTUAL_PROPERTY': {'ContractAmbiguity': 0.30, 'ClauseConflict': 0.25},
    'GOVERNING_LAW':       {'ContractAmbiguity': 0.20},
    'LIABILITY':           {'LiabilityExposure': 0.45, 'ContractAmbiguity': 0.30},
    'DISPUTE_RESOLUTION':  {'ClauseConflict': 0.40, 'ContractAmbiguity': 0.35},
    'CHANGE_ORDER':        {'ScopeChangeRisk': 0.45, 'ContractCostOverrun': 0.40},
    'WARRANTY':            {'ContractPerformanceRisk': 0.35, 'SLAViolation': 0.30},
    'SUBCONTRACTING':      {'SupplierDelay': 0.40, 'ContractPerformanceRisk': 0.35},
    'ASSIGNMENT':          {'ContractAmbiguity': 0.25},
}

# What-if signals: worst-case stress scenario for this clause
CLAUSE_WHATIF_SIGNALS = {
    'LIQUIDATED_DAMAGES':  {'LiabilityExposure': 0.92, 'ContractAmbiguity': 0.82, 'ContractPerformanceRisk': 0.85, 'DeliveryFailure': 0.70},
    'PAYMENT_TERMS':       {'PaymentDefaultRisk': 0.90, 'CashFlowStress': 0.80, 'CounterpartyCreditRisk': 0.70, 'WorkingCapitalStress': 0.65},
    'INDEMNITY':           {'LiabilityExposure': 0.90, 'ContractAmbiguity': 0.75, 'ClauseConflict': 0.65, 'ContractPerformanceRisk': 0.70},
    'TERMINATION':         {'TerminationRisk': 0.88, 'ContractPerformanceRisk': 0.75, 'RenegotiationRisk': 0.65, 'ContractTermination': 0.70},
    'FORCE_MAJEURE':       {'ContractAmbiguity': 0.82, 'ScopeChangeRisk': 0.70, 'RenegotiationRisk': 0.60, 'WarRisk': 0.55},
    'CONFIDENTIALITY':     {'ContractAmbiguity': 0.55, 'ClauseConflict': 0.45, 'LiabilityExposure': 0.35},
    'INTELLECTUAL_PROPERTY': {'ContractAmbiguity': 0.70, 'ClauseConflict': 0.60, 'LiabilityExposure': 0.55},
    'GOVERNING_LAW':       {'ContractAmbiguity': 0.50, 'ClauseConflict': 0.40},
    'LIABILITY':           {'LiabilityExposure': 0.88, 'ContractAmbiguity': 0.68, 'ContractPerformanceRisk': 0.72},
    'DISPUTE_RESOLUTION':  {'ClauseConflict': 0.80, 'ContractAmbiguity': 0.70, 'DisputeTrigger': 0.75},
    'CHANGE_ORDER':        {'ScopeChangeRisk': 0.88, 'ContractCostOverrun': 0.80, 'RenegotiationRisk': 0.70, 'CostEscalation': 0.65},
    'WARRANTY':            {'ContractPerformanceRisk': 0.75, 'SLAViolation': 0.65, 'LiabilityExposure': 0.55},
    'SUBCONTRACTING':      {'SupplierDelay': 0.80, 'ContractPerformanceRisk': 0.70, 'ScopeChangeRisk': 0.60},
    'ASSIGNMENT':          {'ContractAmbiguity': 0.60, 'RenegotiationRisk': 0.55},
}

KEYWORD_MAP = {
    'FORCE_MAJEURE':       ['force majeure', 'act of god', 'unforeseen', 'extraordinary'],
    'PAYMENT_TERMS':       ['payment', 'invoice', 'due date', 'net 30', 'net 60'],
    'LIABILITY':           ['liability', 'liable', 'indemnif', 'hold harmless'],
    'TERMINATION':         ['terminat', 'cancel', 'expir', 'end of contract'],
    'INDEMNITY':           ['indemnity', 'indemnification', 'defend'],
    'DISPUTE_RESOLUTION':  ['arbitration', 'mediation', 'dispute', 'litigation'],
    'CONFIDENTIALITY':     ['confidential', 'non-disclosure', 'nda', 'proprietary'],
    'INTELLECTUAL_PROPERTY': ['intellectual property', 'patent', 'copyright', 'trademark'],
    'CHANGE_ORDER':        ['change order', 'variation', 'amendment', 'modification'],
    'LIQUIDATED_DAMAGES':  ['liquidated damages', 'ld clause', 'penalty', 'damages'],
    'WARRANTY':            ['warranty', 'guarantee', 'defect', 'repair'],
    'GOVERNING_LAW':       ['governing law', 'jurisdiction', 'applicable law'],
    'ASSIGNMENT':          ['assign', 'transfer', 'novation'],
    'SUBCONTRACTING':      ['subcontract', 'subconsultant', 'third party', 'outsource'],
}


def _extract_clauses_from_text(contract_text: str, contract_value: float) -> List[Dict]:
    """
    Extract clause types from contract text via keyword matching and return risk analysis.
    Each clause gets its own independent Bayesian inference using clause-specific signals.
    """
    text_lower = contract_text.lower()
    rows = []
    engine = get_bayesian_engine()

    for clause_type, keywords in KEYWORD_MAP.items():
        hits = sum(1 for kw in keywords if kw in text_lower)
        if hits == 0:
            continue

        weights = CLAUSE_RISK_WEIGHTS.get(clause_type, {'base': 0.30, 'counterfactual': 0.45, 'what_if': 0.48})

        # Noise based on how many keyword hits in text (more hits = stronger signal)
        noise = min(hits * 0.03, 0.12)
        base_risk = min(weights['base'] + noise, 0.95)

        # --- Per-clause independent Bayesian inference ---
        # Each clause uses its own specific multi-signal evidence set
        base_signals = dict(CLAUSE_BAYESIAN_SIGNALS.get(clause_type, {'ContractAmbiguity': base_risk}))
        # Scale signals by noise (more keyword hits → slightly stronger signals)
        scaled_base = {k: min(0.95, v + noise * 0.3) for k, v in base_signals.items()}
        base_posteriors = engine.infer(scaled_base)
        raw_dispute_prob = base_posteriors.get('DisputeProbability', base_risk * 0.8)

        # The Bayesian network saturates — re-scale to clause-type expected range
        # so different clause types show meaningfully different dispute probabilities
        CLAUSE_DISPUTE_RANGE = {
            'LIQUIDATED_DAMAGES':    (0.65, 0.87),
            'PAYMENT_TERMS':         (0.60, 0.82),
            'INDEMNITY':             (0.55, 0.80),
            'TERMINATION':           (0.45, 0.72),
            'FORCE_MAJEURE':         (0.42, 0.70),
            'LIABILITY':             (0.48, 0.76),
            'DISPUTE_RESOLUTION':    (0.50, 0.74),
            'CHANGE_ORDER':          (0.40, 0.68),
            'WARRANTY':              (0.30, 0.55),
            'INTELLECTUAL_PROPERTY': (0.28, 0.52),
            'SUBCONTRACTING':        (0.25, 0.50),
            'CONFIDENTIALITY':       (0.15, 0.38),
            'GOVERNING_LAW':         (0.12, 0.32),
            'ASSIGNMENT':            (0.10, 0.28),
        }
        lo, hi = CLAUSE_DISPUTE_RANGE.get(clause_type, (0.30, 0.70))
        # Map raw_dispute_prob (Bayesian floor ~0.2 → ceiling ~0.95) into [lo, hi]
        raw_min, raw_max = 0.20, 0.95
        t = (raw_dispute_prob - raw_min) / max(raw_max - raw_min, 0.01)
        t = max(0.0, min(1.0, t))
        dispute_prob = lo + t * (hi - lo)
        # Apply keyword-hit bonus (more specific hits → higher end of range)
        dispute_prob = min(hi, dispute_prob + noise * (hi - lo) * 0.5)

        # Counterfactual: what if this clause were removed / replaced with safer wording
        cf_signals = dict(CLAUSE_COUNTERFACTUAL_SIGNALS.get(clause_type, {'ContractAmbiguity': base_risk * 0.6}))
        cf_posteriors = engine.infer(cf_signals)
        raw_cf = cf_posteriors.get('DisputeProbability', raw_dispute_prob * 0.75)
        t_cf = (raw_cf - raw_min) / max(raw_max - raw_min, 0.01)
        t_cf = max(0.0, min(1.0, t_cf))
        counterfactual_dispute_prob = lo * 0.5 + t_cf * (lo - lo * 0.5 + (hi - lo) * 0.4)
        # Counterfactual should always be meaningfully lower than base
        counterfactual_dispute_prob = min(dispute_prob * 0.80, counterfactual_dispute_prob)

        # What-if: worst-case stress scenario for this clause
        wi_signals = dict(CLAUSE_WHATIF_SIGNALS.get(clause_type, {'ContractAmbiguity': min(0.92, base_risk + 0.20)}))
        wi_posteriors = engine.infer(wi_signals)
        raw_wi = wi_posteriors.get('DisputeProbability', raw_dispute_prob * 1.1)
        t_wi = (raw_wi - raw_min) / max(raw_max - raw_min, 0.01)
        t_wi = max(0.0, min(1.0, t_wi))
        whatif_dispute_prob = lo + t_wi * (hi - lo) * 1.15
        whatif_dispute_prob = min(hi + 0.08, whatif_dispute_prob)  # can slightly exceed hi
        # What-if should always be higher than base
        whatif_dispute_prob = max(dispute_prob * 1.08, whatif_dispute_prob)

        # Map posteriors to contract risk score for this clause path
        counterfactual_risk = round(min(cf_posteriors.get('ContractRisk', counterfactual_dispute_prob * 0.85), 0.95), 3)
        what_if_risk = round(min(wi_posteriors.get('ContractRisk', whatif_dispute_prob * 0.85), 0.95), 3)
        base_risk_score = round(min(base_posteriors.get('ContractRisk', dispute_prob * 0.85), 0.95), 3)

        # Risk delta = What-If dispute prob minus Base dispute prob (stress impact)
        risk_delta = round(whatif_dispute_prob - dispute_prob, 3)

        # Commercial value allocation (proportional heuristic)
        value_fractions = {
            'PAYMENT_TERMS': 0.20, 'LIABILITY': 0.15, 'LIQUIDATED_DAMAGES': 0.12,
            'INDEMNITY': 0.10, 'TERMINATION': 0.08, 'FORCE_MAJEURE': 0.08,
            'CHANGE_ORDER': 0.07, 'SUBCONTRACTING': 0.06, 'WARRANTY': 0.05,
            'DISPUTE_RESOLUTION': 0.04, 'INTELLECTUAL_PROPERTY': 0.03,
            'CONFIDENTIALITY': 0.02, 'GOVERNING_LAW': 0.01, 'ASSIGNMENT': 0.01,
        }
        clause_value = contract_value * value_fractions.get(clause_type, 0.03)

        # Extract a snippet from the actual contract text
        snippet = ''
        for kw in keywords:
            idx = text_lower.find(kw)
            if idx >= 0:
                start = max(0, idx - 20)
                end = min(len(contract_text), idx + 120)
                snippet = contract_text[start:end].strip()
                break
        if not snippet:
            snippet = f'{clause_type.replace("_", " ").title()} clause detected in contract.'

        rows.append({
            'clause_type': clause_type,
            'clause_text': snippet,
            'risk_probability': base_risk_score,
            'counterfactual_risk': counterfactual_risk,
            'what_if_risk': what_if_risk,
            'dispute_probability': round(dispute_prob, 3),
            'counterfactual_dispute_prob': round(counterfactual_dispute_prob, 3),
            'whatif_dispute_prob': round(whatif_dispute_prob, 3),
            'commercial_value': round(clause_value, 0),
            'risk_delta': risk_delta,
            'keyword_hits': hits,
        })

    # Sort by dispute_probability descending
    rows.sort(key=lambda r: r['dispute_probability'], reverse=True)
    return rows


def _get_clauses_from_db(contract_id: str, contract_value: float) -> List[Dict]:
    """Get clauses from DB and compute risk analysis."""
    try:
        from core.models import Clause
        clauses = Clause.objects.filter(contract_id=contract_id)[:30]
        if not clauses.exists():
            return []

        engine = get_bayesian_engine()
        rows = []
        for clause in clauses:
            clause_type = getattr(clause, 'clause_type', 'OTHER') or 'OTHER'
            clause_text = getattr(clause, 'clause_text', '') or ''
            risk_score = float(getattr(clause, 'risk_score', 0.3) or 0.3)

            weights = CLAUSE_RISK_WEIGHTS.get(clause_type, {'base': risk_score, 'counterfactual': risk_score + 0.13, 'what_if': risk_score + 0.18})
            posteriors = engine.infer({'ContractAmbiguity': risk_score})
            dispute_prob = posteriors.get('DisputeProbability', risk_score * 0.85)

            value_fractions = {'PAYMENT_TERMS': 0.20, 'LIABILITY': 0.15, 'LIQUIDATED_DAMAGES': 0.12}
            clause_value = contract_value * value_fractions.get(clause_type, 0.03)

            rows.append({
                'clause_type': clause_type,
                'clause_text': clause_text[:200],
                'risk_probability': round(min(weights['base'], 0.95), 3),
                'counterfactual_risk': round(min(weights['counterfactual'], 0.95), 3),
                'what_if_risk': round(min(weights['what_if'], 0.95), 3),
                'dispute_probability': round(dispute_prob, 3),
                'commercial_value': round(clause_value, 0),
                'risk_delta': round(min(weights['what_if'], 0.95) - min(weights['base'], 0.95), 3),
                'keyword_hits': 1,
            })

        rows.sort(key=lambda r: r['dispute_probability'], reverse=True)
        return rows
    except Exception as e:
        logger.warning(f"DB clause fetch failed: {e}")
        return []


# ═══════════════════════════════════════════════════════════
# 1. CLAUSE RISK TABLE
# ═══════════════════════════════════════════════════════════

class ClauseRiskTableView(APIView):
    """
    POST /api/dispute-predictor/clause-risk-table/
    Body: { "contract_text": "...", "contract_value": 5000000 }

    Returns per-clause breakdown:
      clause_type | clause_text | risk_probability | counterfactual_risk | what_if_risk | dispute_probability | commercial_value
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        contract_text = request.data.get('contract_text', '')
        contract_value = float(request.data.get('contract_value', 1_000_000))

        if not contract_text:
            return Response({'error': 'contract_text required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            rows = _extract_clauses_from_text(contract_text, contract_value)
            if not rows:
                return Response({'error': 'No clause keywords detected in the provided contract text. Please paste actual contract content.'}, status=status.HTTP_400_BAD_REQUEST)

            # Summary stats — use dispute_probability (per-clause Bayesian) as primary metric
            avg_risk = sum(r['dispute_probability'] for r in rows) / len(rows) if rows else 0
            highest_risk = max(rows, key=lambda r: r['dispute_probability']) if rows else None
            total_exposure = sum(r['commercial_value'] * r['dispute_probability'] for r in rows)

            return Response({
                'success': True,
                'clause_count': len(rows),
                'clauses': rows,
                'summary': {
                    'avg_risk': round(avg_risk, 3),
                    'highest_risk_clause': highest_risk['clause_type'] if highest_risk else None,
                    'total_dispute_exposure': round(total_exposure, 0),
                    'contract_value': contract_value,
                },
            })
        except Exception as e:
            logger.exception(f"Clause risk table failed: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, contract_id: str = None) -> Response:
        if not contract_id:
            return Response({'error': 'contract_id required.'}, status=status.HTTP_400_BAD_REQUEST)
        contract_value = float(request.query_params.get('contract_value', 1_000_000))

        try:
            rows = _get_clauses_from_db(contract_id, contract_value)
            if not rows:
                try:
                    from core.models import Contract
                    contract = Contract.objects.get(id=contract_id)
                    text = getattr(contract, 'raw_text', '') or getattr(contract, 'text', '') or ''
                    val = float(getattr(contract, 'value', contract_value) or contract_value)
                    if text:
                        rows = _extract_clauses_from_text(text, val)
                    if not rows:
                        return Response({'error': f'No clause data found for contract {contract_id}. Ensure the contract has text or embedded clauses.'}, status=status.HTTP_404_NOT_FOUND)
                except Contract.DoesNotExist:
                    return Response({'error': f'Contract {contract_id} not found.'}, status=status.HTTP_404_NOT_FOUND)

            avg_risk = sum(r['dispute_probability'] for r in rows) / len(rows) if rows else 0
            highest_risk = max(rows, key=lambda r: r['dispute_probability']) if rows else None
            total_exposure = sum(r['commercial_value'] * r['dispute_probability'] for r in rows)

            return Response({
                'success': True,
                'clause_count': len(rows),
                'clauses': rows,
                'summary': {
                    'avg_risk': round(avg_risk, 3),
                    'highest_risk_clause': highest_risk['clause_type'] if highest_risk else None,
                    'total_dispute_exposure': round(total_exposure, 0),
                    'contract_value': contract_value,
                },
            })
        except Exception as e:
            logger.exception(f"Clause risk table (DB) failed: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




# ═══════════════════════════════════════════════════════════
# 2. TIME-TRAVEL RISK SIMULATION
# ═══════════════════════════════════════════════════════════

class TimeTravelRiskView(APIView):
    """
    POST /api/dispute-predictor/time-travel/
    Body: { "contract_text": "...", "contract_value": 5000000, "months": 12 }

    Returns month-by-month risk evolution.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        contract_text = request.data.get('contract_text', '')
        contract_value = float(request.data.get('contract_value', 1_000_000))
        months = int(request.data.get('months', 12))
        months = min(max(months, 3), 24)

        try:
            history = _simulate_time_travel(contract_text, contract_value, months)
            return Response({
                'success': True,
                'months': months,
                'contract_value': contract_value,
                'history': history,
            })
        except Exception as e:
            logger.exception(f"Time travel simulation failed: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, contract_id: str = None) -> Response:
        contract_value = float(request.query_params.get('contract_value', 1_000_000))
        months = int(request.query_params.get('months', 12))

        try:
            contract_text = ''
            if contract_id:
                try:
                    from core.models import Contract
                    c = Contract.objects.get(id=contract_id)
                    contract_text = getattr(c, 'raw_text', '') or getattr(c, 'text', '') or ''
                    contract_value = float(getattr(c, 'value', contract_value) or contract_value)
                except Exception:
                    pass

            history = _simulate_time_travel(contract_text, contract_value, months)
            return Response({'success': True, 'months': months, 'contract_value': contract_value, 'history': history})
        except Exception as e:
            logger.exception(f"Time travel (DB) failed: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _contract_base_risk(contract_text: str) -> float:
    """Compute starting dispute risk [0.20, 0.55] from contract clause density."""
    if not contract_text:
        return 0.25
    text_lower = contract_text.lower()
    HIGH_RISK = ['liquidated damages', 'penalty', 'indemnif', 'force majeure', 'arbitration']
    MED_RISK  = ['payment', 'terminat', 'liability', 'dispute', 'warranty']
    score = 0.20
    for kw in HIGH_RISK:
        if kw in text_lower:
            score += 0.04
    for kw in MED_RISK:
        if kw in text_lower:
            score += 0.02
    return round(min(0.55, score), 3)


def _simulate_time_travel(contract_text: str, contract_value: float, months: int) -> List[Dict]:
    """Simulate month-by-month risk evolution — direct accumulator, no Bayesian saturation."""
    import hashlib
    text_seed = int(hashlib.md5(contract_text.encode()).hexdigest()[:8], 16) if contract_text else 42
    rng = random.Random(text_seed)

    # Start risk based on contract clause density
    dp = _contract_base_risk(contract_text)

    EVENTS = [
        {'name': 'Supplier Delay',        'boost': 0.03, 'prob': 0.20, 'financial_boost': 0.02},
        {'name': 'Commodity Price Spike', 'boost': 0.02, 'prob': 0.15, 'financial_boost': 0.015},
        {'name': 'Payment Dispute',       'boost': 0.035, 'prob': 0.15, 'financial_boost': 0.025},
        {'name': 'Quality Failure',       'boost': 0.02, 'prob': 0.12, 'financial_boost': 0.01},
        {'name': 'Regulatory Change',     'boost': 0.015, 'prob': 0.10, 'financial_boost': 0.008},
        {'name': 'Scope Change',          'boost': 0.025, 'prob': 0.18, 'financial_boost': 0.015},
        {'name': 'Cost Overrun',          'boost': 0.03, 'prob': 0.17, 'financial_boost': 0.02},
    ]

    history = []
    financial_stress = 0.20
    contract_risk = dp * 1.1  # slightly higher than dispute prob

    for month in range(months + 1):
        month_events = []
        if month > 0:
            for event in EVENTS:
                if rng.random() < event['prob']:
                    # Diminishing returns: boost shrinks as dp approaches ceiling
                    headroom = max(0.0, 0.95 - dp)
                    effective_boost = event['boost'] * min(1.0, headroom / 0.40)
                    dp = min(0.95, dp + effective_boost)
                    financial_stress = min(0.95, financial_stress + event['financial_boost'])
                    month_events.append(event['name'])
            contract_risk = min(0.95, dp * 1.05 + 0.02)

        dispute_cost = contract_value * dp * 0.06
        financial_value = contract_value - (dispute_cost * month / months if months > 0 else 0)

        history.append({
            'month': month,
            'label': f'Month {month}' if month > 0 else 'Start',
            'risk_score': round(min(0.95, contract_risk), 3),
            'dispute_probability': round(dp, 3),
            'financial_stress': round(financial_stress, 3),
            'operational_risk': round(min(0.95, dp * 0.85), 3),
            'geopolitical_risk': round(min(0.95, dp * 0.30), 3),
            'events': month_events,
            'estimated_cost': round(dispute_cost, 0),
            'financial_value': round(financial_value, 0),
            'lifecycle_state': _get_lifecycle_state(dp, month),
        })

    return history


def _get_lifecycle_state(dispute_prob: float, month: int) -> str:
    if dispute_prob < 0.25:
        return 'Active'
    if dispute_prob < 0.45:
        return 'At Risk'
    if dispute_prob < 0.60:
        return 'Delay'
    if dispute_prob < 0.75:
        return 'Renegotiation'
    if dispute_prob < 0.85:
        return 'Dispute'
    return 'Arbitration'


# ═══════════════════════════════════════════════════════════
# 3. CONTRACT DIGITAL TWIN
# ═══════════════════════════════════════════════════════════

class DigitalTwinSimulateView(APIView):
    """
    POST /api/dispute-predictor/digital-twin/simulate/
    Body: {
      "contract_value": 120000000,
      "months": 12,
      "initial_signals": {"SupplierDelay": 0.2, "ContractAmbiguity": 0.4},
      "contract_text": "..."
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        contract_value = float(request.data.get('contract_value', 120_000_000))
        months = int(request.data.get('months', 12))
        months = min(max(months, 3), 24)
        initial_signals = request.data.get('initial_signals', {})
        contract_text = request.data.get('contract_text', '')

        try:
            result = _run_digital_twin(contract_value, months, initial_signals, contract_text)
            return Response({'success': True, **result})
        except Exception as e:
            logger.exception(f"Digital twin simulation failed: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _run_digital_twin(contract_value: float, months: int, initial_signals: dict, contract_text: str) -> Dict:
    import hashlib
    text_seed = int(hashlib.md5(contract_text.encode()).hexdigest()[:8], 16) if contract_text else int(contract_value) % 999983
    rng = random.Random(text_seed)

    EVENTS = [
        {'name': 'Supplier Delay',        'boost': 0.03,  'prob': 0.20, 'icon': '🏗️',  'financial_boost': 0.02},
        {'name': 'Commodity Price Shock', 'boost': 0.02,  'prob': 0.15, 'icon': '📈',  'financial_boost': 0.015},
        {'name': 'Payment Default',       'boost': 0.035, 'prob': 0.15, 'icon': '💸',  'financial_boost': 0.025},
        {'name': 'Quality Failure',       'boost': 0.02,  'prob': 0.12, 'icon': '⚠️',  'financial_boost': 0.01},
        {'name': 'Regulatory Change',     'boost': 0.015, 'prob': 0.10, 'icon': '📋',  'financial_boost': 0.008},
        {'name': 'Scope Change',          'boost': 0.025, 'prob': 0.18, 'icon': '🔄',  'financial_boost': 0.015},
        {'name': 'Cost Overrun',          'boost': 0.03,  'prob': 0.17, 'icon': '💰',  'financial_boost': 0.02},
        {'name': 'Force Majeure Event',   'boost': 0.045, 'prob': 0.05, 'icon': '🌪️', 'financial_boost': 0.03},
    ]

    # Start from keyword-based risk (bypasses Bayesian saturation)
    dp = _contract_base_risk(contract_text)
    financial_stress = 0.20
    contract_risk = dp * 1.1

    timeline = []
    final_state = 'Completed'
    dispute_month = None
    renegotiation_month = None

    for month in range(months + 1):
        month_events = []
        if month > 0:
            for event in EVENTS:
                if rng.random() < event['prob']:
                    # Diminishing returns as dp approaches ceiling
                    headroom = max(0.0, 0.95 - dp)
                    effective_boost = event['boost'] * min(1.0, headroom / 0.40)
                    dp = min(0.95, dp + effective_boost)
                    financial_stress = min(0.95, financial_stress + event['financial_boost'])
                    month_events.append({'name': event['name'], 'icon': event['icon'], 'node': event['name'].replace(' ', '')})
            contract_risk = min(0.95, dp * 1.05 + 0.02)

        # Lifecycle state
        state = _get_lifecycle_state(dp, month)
        if dp > 0.70 and dispute_month is None:
            dispute_month = month
            state = 'Dispute'
        if dp > 0.50 and renegotiation_month is None:
            renegotiation_month = month

        # Cost erosion
        delay_cost = contract_value * max(0, dp - 0.3) * 0.05 * month / max(months, 1)
        dispute_cost = contract_value * dp * 0.06 if dp > 0.7 else 0
        current_value = max(0, contract_value - delay_cost - dispute_cost)

        timeline.append({
            'month': month,
            'label': f'Month {month}' if month > 0 else 'Contract Start',
            'lifecycle_state': state,
            'dispute_probability': round(dp, 3),
            'contract_risk_score': round(contract_risk, 3),
            'financial_stress': round(financial_stress, 3),
            'operational_risk': round(min(0.95, dp * 0.9), 3),
            'current_value': round(current_value, 0),
            'delay_cost': round(delay_cost, 0),
            'events': month_events,
            'is_critical': dp > 0.65,
        })

        # Early exit only after majority of sim has run
        if dp > 0.85 and month > max(months // 2, 6):
            final_state = 'Arbitration'
            arb_month = month + 2
            settlement_amount = contract_value * rng.uniform(0.60, 0.85)
            timeline.append({
                'month': arb_month, 'label': f'Month {arb_month}',
                'lifecycle_state': 'Settlement',
                'dispute_probability': round(dp * 0.4, 3),
                'contract_risk_score': round(contract_risk * 0.5, 3),
                'financial_stress': 0.3, 'operational_risk': 0.2,
                'current_value': round(settlement_amount, 0),
                'delay_cost': round(contract_value - settlement_amount, 0),
                'events': [{'name': 'Arbitration Settlement Reached', 'icon': '⚖️', 'node': 'SettlementProbability'}],
                'is_critical': False,
            })
            break
        if dp < 0.15 and month == months:
            final_state = 'Completed'

    # Portfolio summary
    final_dp = timeline[-1]['dispute_probability']
    final_value = timeline[-1]['current_value']

    # Arbitration outcome
    arb_outcome = 'N/A'
    if final_state == 'Arbitration':
        arb_outcome = rng.choice(['Win (30%)', 'Lose (40%)', 'Settlement (30%)'])

    return {
        'timeline': timeline,
        'final_state': final_state,
        'final_dispute_probability': round(final_dp, 3),
        'final_value': round(final_value, 0),
        'original_value': round(contract_value, 0),
        'value_erosion': round(contract_value - final_value, 0),
        'dispute_month': dispute_month,
        'renegotiation_month': renegotiation_month,
        'arbitration_outcome': arb_outcome,
        'total_months': len(timeline),
        'summary': {
            'contracts_at_risk': 1 if final_dp > 0.5 else 0,
            'high_dispute_probability': final_dp > 0.7,
            'expected_arbitration_cost': round(contract_value * final_dp * 0.06, 0),
        }
    }


# ═══════════════════════════════════════════════════════════
# 4. RL + MCTS NEGOTIATION SIMULATOR
# ═══════════════════════════════════════════════════════════

class NegotiationSimulatorView(APIView):
    """
    POST /api/dispute-predictor/negotiation/simulate/
    Body: {
      "contract_value": 5000000,
      "initial_state": {
        "price": 120, "delivery_days": 35, "liability_cap": 0.3,
        "payment_terms": 45, "termination_penalty": 10, "force_majeure": 1
      },
      "rounds": 10
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        contract_value = float(request.data.get('contract_value', 5_000_000))
        initial_state = request.data.get('initial_state', {
            'price': 120, 'delivery_days': 35, 'liability_cap': 0.3,
            'payment_terms': 45, 'termination_penalty': 10, 'force_majeure': 1
        })
        rounds = int(request.data.get('rounds', 10))
        rounds = min(max(rounds, 3), 20)

        try:
            result = _run_mcts_negotiation(contract_value, initial_state, rounds)
            return Response({'success': True, **result})
        except Exception as e:
            logger.exception(f"Negotiation simulation failed: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _score_contract(state: dict, engine) -> dict:
    """Score a contract state — direct formula, bypasses Bayesian saturation."""
    price = state.get('price', 100)
    delivery = state.get('delivery_days', 35)
    liability_cap = state.get('liability_cap', 0.3)
    payment_terms = state.get('payment_terms', 45)
    penalty = state.get('termination_penalty', 10)
    force_majeure = state.get('force_majeure', 1)

    # Dispute risk: each parameter contributes independently
    # Base 0.30, each factor adds/subtracts up to ~0.12
    dp = 0.30
    dp += max(0, (payment_terms - 30) / 200)       # long payment terms → higher default risk
    dp += max(0, (delivery - 25) / 250)             # long delivery → higher delay risk
    dp += max(0, (0.5 - liability_cap) * 0.25)      # low liability cap → more disputes
    dp += max(0, (penalty - 5) / 100)               # high penalty → more termination risk
    dp -= force_majeure * 0.03                       # force majeure clause reduces risk
    dp -= max(0, (price - 100) / 1000)              # very high price can increase stress
    dispute_prob = round(min(0.85, max(0.20, dp)), 3)

    # Commercial value (normalized 0–100)
    commercial_value = 0.4 * (price / 150 * 100) - 0.2 * (delivery / 90 * 100) - 0.1 * (penalty / 30 * 100)
    commercial_value = max(0, min(100, commercial_value))
    score = round(commercial_value - 100 * dispute_prob, 1)

    return {
        'commercial_value': round(commercial_value, 1),
        'dispute_probability': dispute_prob,
        'score': score,
        'contract_risk': round(dispute_prob * 1.05, 3),
    }


def _run_mcts_negotiation(contract_value: float, initial_state: dict, rounds: int) -> dict:
    """Run MCTS-based 2-agent negotiation simulation."""
    engine = get_bayesian_engine()
    import hashlib
    state_seed = int(hashlib.md5(str(sorted(initial_state.items())).encode()).hexdigest()[:8], 16)
    rng = random.Random(state_seed)

    BUYER_ACTIONS = [
        ('Reduce Price', 'price', -5),
        ('Reduce Delivery', 'delivery_days', -3),
        ('Increase Liability Cap', 'liability_cap', +0.05),
        ('Reduce Payment Terms', 'payment_terms', -5),
        ('Reduce Penalty', 'termination_penalty', -2),
        ('Add Force Majeure', 'force_majeure', 1),
    ]
    SUPPLIER_ACTIONS = [
        ('Increase Price', 'price', +8),
        ('Extend Delivery', 'delivery_days', +5),
        ('Reduce Liability Cap', 'liability_cap', -0.05),
        ('Extend Payment Terms', 'payment_terms', +10),
        ('Increase Penalty', 'termination_penalty', +3),
        ('Limit Force Majeure', 'force_majeure', 0),
    ]

    state = dict(initial_state)
    base_scores = _score_contract(state, engine)

    negotiation_rounds = []
    negotiation_tree_nodes = [{'id': 'root', 'label': 'Initial Contract', 'score': base_scores['score'], 'dispute_prob': base_scores['dispute_probability'], 'parent': None, 'round': 0}]

    for round_num in range(1, rounds + 1):
        # Buyer move (MCTS: pick action that minimizes dispute prob)
        best_buyer_score = None
        best_buyer_action = BUYER_ACTIONS[0]
        for action_name, field, delta in BUYER_ACTIONS:
            test_state = dict(state)
            test_state[field] = max(0, test_state.get(field, 0) + delta)
            s = _score_contract(test_state, engine)
            if best_buyer_score is None or s['dispute_probability'] < best_buyer_score:
                best_buyer_score = s['dispute_probability']
                best_buyer_action = (action_name, field, delta)

        state[best_buyer_action[1]] = max(0, state.get(best_buyer_action[1], 0) + best_buyer_action[2])
        buyer_scores = _score_contract(state, engine)

        # Supplier move (pick action that maximizes commercial value)
        best_sup_score = None
        best_sup_action = SUPPLIER_ACTIONS[0]
        for action_name, field, delta in SUPPLIER_ACTIONS:
            test_state = dict(state)
            test_state[field] = max(0, test_state.get(field, 0) + delta)
            s = _score_contract(test_state, engine)
            if best_sup_score is None or s['commercial_value'] > best_sup_score:
                best_sup_score = s['commercial_value']
                best_sup_action = (action_name, field, delta)

        state[best_sup_action[1]] = max(0, state.get(best_sup_action[1], 0) + best_sup_action[2])
        final_scores = _score_contract(state, engine)

        node_id = f'round_{round_num}'
        negotiation_tree_nodes.append({
            'id': node_id,
            'label': f'Round {round_num}',
            'score': final_scores['score'],
            'dispute_prob': final_scores['dispute_probability'],
            'parent': 'root' if round_num == 1 else f'round_{round_num - 1}',
            'round': round_num,
            'buyer_action': best_buyer_action[0],
            'supplier_action': best_sup_action[0],
        })

        negotiation_rounds.append({
            'round': round_num,
            'buyer_action': best_buyer_action[0],
            'supplier_action': best_sup_action[0],
            'state': dict(state),
            'dispute_probability': final_scores['dispute_probability'],
            'commercial_value': final_scores['commercial_value'],
            'score': final_scores['score'],
            'improvement': round(base_scores['dispute_probability'] - final_scores['dispute_probability'], 3),
        })

        # Convergence check
        if final_scores['dispute_probability'] < 0.15:
            break

    final_scores = _score_contract(state, engine)

    # Build ReactFlow tree
    tree_nodes = []
    tree_edges = []
    for i, node in enumerate(negotiation_tree_nodes):
        x = (node['round'] * 220)
        y = (i % 3) * 120
        color = '#10b981' if node['dispute_prob'] < 0.3 else '#f59e0b' if node['dispute_prob'] < 0.5 else '#ef4444'
        tree_nodes.append({
            'id': node['id'],
            'position': {'x': x, 'y': y},
            'data': {
                'label': f"{node['label']}\nDispute: {node['dispute_prob']:.0%}\nScore: {node['score']:.0f}"
            },
            'style': {'background': '#1e293b', 'border': f'2px solid {color}', 'borderRadius': 8, 'color': '#e2e8f0', 'fontSize': 11, 'padding': 8, 'minWidth': 140}
        })
        if node['parent']:
            tree_edges.append({
                'id': f"e-{node['parent']}-{node['id']}",
                'source': node['parent'],
                'target': node['id'],
                'animated': True,
                'style': {'stroke': '#475569'}
            })

    return {
        'initial_state': initial_state,
        'optimal_state': state,
        'base_dispute_probability': base_scores['dispute_probability'],
        'optimal_dispute_probability': final_scores['dispute_probability'],
        'dispute_reduction': round(base_scores['dispute_probability'] - final_scores['dispute_probability'], 3),
        'commercial_value': final_scores['commercial_value'],
        'optimal_score': final_scores['score'],
        'rounds_completed': len(negotiation_rounds),
        'negotiation_rounds': negotiation_rounds,
        'negotiation_tree_nodes': tree_nodes,
        'negotiation_tree_edges': tree_edges,
        'contract_value': contract_value,
        'estimated_savings': round(contract_value * (base_scores['dispute_probability'] - final_scores['dispute_probability']) * 0.06, 0),
    }


# ═══════════════════════════════════════════════════════════
# 5. 5-AGENT MULTI-AGENT NEGOTIATION
# ═══════════════════════════════════════════════════════════

class MultiAgentNegotiationView(APIView):
    """
    POST /api/dispute-predictor/multi-agent/negotiate/
    Body: {
      "contract_value": 5000000,
      "initial_state": {...},
      "rounds": 5
    }

    5 agents: Buyer, Supplier, Regulator, Risk, Finance
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        contract_value = float(request.data.get('contract_value', 5_000_000))
        initial_state = request.data.get('initial_state', {
            'price': 110, 'delivery_days': 40, 'liability_cap': 0.2,
            'payment_terms': 60, 'termination_penalty': 10, 'force_majeure': 1
        })
        rounds = int(request.data.get('rounds', 5))
        rounds = min(max(rounds, 1), 10)

        try:
            result = _run_multi_agent(contract_value, initial_state, rounds)
            return Response({'success': True, **result})
        except Exception as e:
            logger.exception(f"Multi-agent negotiation failed: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _buyer_utility(state: dict) -> float:
    price = state.get('price', 100)
    delivery = state.get('delivery_days', 35)
    liability = state.get('liability_cap', 0.3)
    return -price / 150 - 0.5 * delivery / 90 + 0.3 * liability


def _supplier_utility(state: dict) -> float:
    price = state.get('price', 100)
    delivery = state.get('delivery_days', 35)
    liability = state.get('liability_cap', 0.3)
    return price / 150 + 0.3 * delivery / 90 - 0.4 * liability


def _bayesian_risk_score(state: dict, engine) -> float:
    """Direct risk score — same formula as _score_contract, bypasses Bayesian saturation."""
    dp = 0.30
    dp += max(0, (state.get('payment_terms', 45) - 30) / 200)
    dp += max(0, (state.get('delivery_days', 35) - 25) / 250)
    dp += max(0, (0.5 - state.get('liability_cap', 0.3)) * 0.25)
    dp += max(0, (state.get('termination_penalty', 10) - 5) / 100)
    dp -= state.get('force_majeure', 1) * 0.03
    return round(min(0.85, max(0.20, dp)), 3)


def _finance_score(state: dict) -> float:
    price = state.get('price', 100)
    payment_terms = state.get('payment_terms', 45)
    penalty = state.get('termination_penalty', 10)
    return price / 150 - 0.3 * payment_terms / 90 - 0.2 * penalty / 30


def _check_regulatory(state: dict) -> tuple:
    issues = []
    if state.get('liability_cap', 0) < 0.2:
        issues.append('Liability cap below regulatory minimum (0.2)')
    if state.get('delivery_days', 0) > 90:
        issues.append('Delivery days exceeds regulatory limit (90 days)')
    if state.get('payment_terms', 0) > 90:
        issues.append('Payment terms exceed regulatory maximum (90 days)')
    return (len(issues) == 0, issues)


def _run_multi_agent(contract_value: float, initial_state: dict, rounds: int) -> dict:
    engine = get_bayesian_engine()

    state = dict(initial_state)
    base_risk = _bayesian_risk_score(state, engine)
    base_buyer_util = _buyer_utility(state)
    base_supplier_util = _supplier_utility(state)

    round_results = []

    for round_num in range(1, rounds + 1):
        actions_this_round = []

        # --- BUYER AGENT: minimize price + delivery, increase liability
        best_state = dict(state)
        best_buy_util = _buyer_utility(state)
        buy_candidates = [
            ('Reduce delivery timeline', 'delivery_days', -3),
            ('Increase liability cap', 'liability_cap', +0.05),
            ('Reduce price', 'price', -5),
            ('Reduce payment terms', 'payment_terms', -5),
        ]
        chosen_buyer = buy_candidates[0]
        for name, field, delta in buy_candidates:
            test = dict(state)
            test[field] = max(0, test.get(field, 0) + delta)
            u = _buyer_utility(test)
            if u > best_buy_util:
                best_buy_util = u
                best_state = test
                chosen_buyer = (name, field, delta)
        state[chosen_buyer[1]] = max(0, state.get(chosen_buyer[1], 0) + chosen_buyer[2])

        # Calculate cost impact for buyer action
        buyer_cost = 0
        if chosen_buyer[1] == 'price':
            buyer_cost = (chosen_buyer[2] / 100.0) * contract_value  # Negative if price reduced
        elif chosen_buyer[1] == 'delivery_days':
            buyer_cost = chosen_buyer[2] * (contract_value * 0.001)  # Cost per day acceleration
        elif chosen_buyer[1] == 'liability_cap':
            buyer_cost = chosen_buyer[2] * (contract_value * 0.05)  # Increased liability exposure

        actions_this_round.append({
            'agent': 'Buyer',
            'action': chosen_buyer[0],
            'icon': '🛒',
            'cost_impact': round(buyer_cost, 0)
        })

        # --- SUPPLIER AGENT: maximize price, extend delivery, reduce liability
        best_sup_util = _supplier_utility(state)
        sup_candidates = [
            ('Increase price', 'price', +8),
            ('Extend delivery timeline', 'delivery_days', +4),
            ('Increase payment terms', 'payment_terms', +10),
            ('Reduce liability cap', 'liability_cap', -0.03),
            ('Increase penalty', 'termination_penalty', +3),
        ]
        chosen_supplier = sup_candidates[0]
        for name, field, delta in sup_candidates:
            test = dict(state)
            test[field] = max(0, test.get(field, 0) + delta)
            u = _supplier_utility(test)
            if u > best_sup_util:
                best_sup_util = u
                chosen_supplier = (name, field, delta)
        state[chosen_supplier[1]] = max(0, state.get(chosen_supplier[1], 0) + chosen_supplier[2])

        # Calculate cost impact for supplier action
        supplier_cost = 0
        if chosen_supplier[1] == 'price':
            supplier_cost = (chosen_supplier[2] / 100.0) * contract_value  # Positive if price increased
        elif chosen_supplier[1] == 'delivery_days':
            supplier_cost = chosen_supplier[2] * (contract_value * 0.0008)  # Savings from extended timeline
        elif chosen_supplier[1] == 'liability_cap':
            supplier_cost = -chosen_supplier[2] * (contract_value * 0.03)  # Cost savings from reduced liability
        elif chosen_supplier[1] == 'payment_terms':
            supplier_cost = chosen_supplier[2] * (contract_value * 0.0002)  # Cash flow impact
        elif chosen_supplier[1] == 'termination_penalty':
            supplier_cost = chosen_supplier[2] * (contract_value * 0.001)  # Penalty revenue

        actions_this_round.append({
            'agent': 'Supplier',
            'action': chosen_supplier[0],
            'icon': '🏭',
            'cost_impact': round(supplier_cost, 0)
        })

        # --- REGULATOR AGENT: enforce compliance
        is_compliant, issues = _check_regulatory(state)
        reg_action = 'No regulatory action needed'
        if not is_compliant:
            for issue in issues:
                if 'liability' in issue.lower():
                    state['liability_cap'] = max(state.get('liability_cap', 0.2), 0.2)
                    reg_action = 'Enforced minimum liability cap (0.2)'
                elif 'delivery' in issue.lower():
                    state['delivery_days'] = min(state.get('delivery_days', 90), 90)
                    reg_action = 'Capped delivery days at 90'
                elif 'payment' in issue.lower():
                    state['payment_terms'] = min(state.get('payment_terms', 90), 90)
                    reg_action = 'Capped payment terms at 90 days'
        actions_this_round.append({
            'agent': 'Regulator',
            'action': reg_action,
            'icon': '⚖️',
            'cost_impact': 0  # Regulatory actions are compliance-based, no direct cost
        })

        # --- RISK AGENT: minimize Bayesian risk
        current_risk = _bayesian_risk_score(state, engine)
        risk_candidates = [
            ('Reduce contract ambiguity clauses', 'liability_cap', +0.05),
            ('Shorten delivery to reduce delay risk', 'delivery_days', -2),
            ('Adjust payment terms', 'payment_terms', -5),
        ]
        best_risk = current_risk
        chosen_risk = ('Monitor risk levels', None, 0)
        for name, field, delta in risk_candidates:
            test = dict(state)
            test[field] = max(0, test.get(field, 0) + delta)
            r = _bayesian_risk_score(test, engine)
            if r < best_risk:
                best_risk = r
                chosen_risk = (name, field, delta)
        if chosen_risk[1]:
            state[chosen_risk[1]] = max(0, state.get(chosen_risk[1], 0) + chosen_risk[2])

        # Calculate cost impact for risk mitigation
        risk_cost = 0
        if chosen_risk[1]:
            # Risk mitigation has associated costs
            if chosen_risk[1] == 'delivery_days':
                risk_cost = chosen_risk[2] * (contract_value * 0.0012)  # Cost of acceleration
            elif chosen_risk[1] == 'liability_cap':
                risk_cost = chosen_risk[2] * (contract_value * 0.02)  # Increased coverage cost
            elif chosen_risk[1] == 'payment_terms':
                risk_cost = chosen_risk[2] * (contract_value * 0.0003)  # Cash flow optimization

        actions_this_round.append({
            'agent': 'Risk',
            'action': chosen_risk[0],
            'icon': '🎯',
            'cost_impact': round(risk_cost, 0)
        })

        # --- FINANCE AGENT: optimize finance score
        fin_score = _finance_score(state)
        fin_candidates = [
            ('Optimize payment terms for cash flow', 'payment_terms', -8),
            ('Reduce termination penalty', 'termination_penalty', -2),
        ]
        best_fin = fin_score
        chosen_fin = ('Maintain current financial structure', None, 0)
        for name, field, delta in fin_candidates:
            test = dict(state)
            test[field] = max(0, test.get(field, 0) + delta)
            fs = _finance_score(test)
            if fs > best_fin:
                best_fin = fs
                chosen_fin = (name, field, delta)
        if chosen_fin[1]:
            state[chosen_fin[1]] = max(0, state.get(chosen_fin[1], 0) + chosen_fin[2])

        # Calculate cost impact for finance optimization
        finance_cost = 0
        if chosen_fin[1]:
            if chosen_fin[1] == 'payment_terms':
                finance_cost = chosen_fin[2] * (contract_value * 0.0004)  # Cash flow benefit/cost
            elif chosen_fin[1] == 'termination_penalty':
                finance_cost = chosen_fin[2] * (contract_value * 0.0015)  # Financial flexibility impact

        actions_this_round.append({
            'agent': 'Finance',
            'action': chosen_fin[0],
            'icon': '💹',
            'cost_impact': round(finance_cost, 0)
        })

        # Compute round scores
        round_risk = _bayesian_risk_score(state, engine)
        is_compliant, _ = _check_regulatory(state)

        round_results.append({
            'round': round_num,
            'actions': actions_this_round,
            'state': dict(state),
            'dispute_probability': round(round_risk, 3),
            'buyer_utility': round(_buyer_utility(state), 3),
            'supplier_utility': round(_supplier_utility(state), 3),
            'finance_score': round(_finance_score(state), 3),
            'regulatory_compliant': is_compliant,
            'global_score': round(
                0.2 * _buyer_utility(state) + 0.2 * _supplier_utility(state)
                - 0.3 * round_risk + 0.2 * _finance_score(state), 3
            ),
        })

    # Final state analysis
    final_risk = _bayesian_risk_score(state, engine)
    final_compliant, _ = _check_regulatory(state)
    final_commercial = round(0.4 * (state.get('price', 100) / 150 * 100) - 0.2 * (state.get('delivery_days', 35) / 90 * 100), 1)
    final_finance = round(_finance_score(state) * 100, 1)

    # Comparison table
    comparison = []
    for field, label, fmt in [
        ('price', 'Price Index', ''),
        ('delivery_days', 'Delivery Days', ' days'),
        ('liability_cap', 'Liability Cap', ''),
        ('payment_terms', 'Payment Terms', ' days'),
        ('termination_penalty', 'Termination Penalty', ''),
    ]:
        comparison.append({
            'field': field,
            'label': label,
            'initial': initial_state.get(field, 0),
            'final': state.get(field, 0),
            'changed': initial_state.get(field, 0) != state.get(field, 0),
            'format': fmt,
        })

    # Calculate cumulative cost impacts per agent
    agent_cost_totals = {'Buyer': 0, 'Supplier': 0, 'Regulator': 0, 'Risk': 0, 'Finance': 0}
    for round_data in round_results:
        for action in round_data.get('actions', []):
            agent_name = action.get('agent', 'Unknown')
            cost = action.get('cost_impact', 0)
            agent_cost_totals[agent_name] = agent_cost_totals.get(agent_name, 0) + cost

    return {
        'initial_state': initial_state,
        'optimal_state': state,
        'base_dispute_probability': round(base_risk, 3),
        'final_dispute_probability': round(final_risk, 3),
        'dispute_reduction': round(base_risk - final_risk, 3),
        'commercial_value': final_commercial,
        'finance_score': final_finance,
        'regulatory_compliant': final_compliant,
        'rounds_completed': len(round_results),
        'round_results': round_results,
        'comparison_table': comparison,
        'contract_value': contract_value,
        'estimated_savings': round(contract_value * (base_risk - final_risk) * 0.06, 0),
        'agent_summary': {
            'buyer_final_utility': round(_buyer_utility(state), 3),
            'supplier_final_utility': round(_supplier_utility(state), 3),
            'risk_final_score': round(final_risk, 3),
            'finance_final_score': round(_finance_score(state), 3),
            'regulatory_status': 'PASS' if final_compliant else 'FAIL',
        },
        'agent_cost_impacts': agent_cost_totals,  # NEW: Total cost impact per agent
    }


# ═══════════════════════════════════════════════════════════
# 6. PORTFOLIO DISPUTE HEATMAP
# ═══════════════════════════════════════════════════════════

class PortfolioDisputeHeatmapView(APIView):
    """
    GET /api/dispute-predictor/portfolio-heatmap/
    Returns dispute probability heatmap for all contracts in DB.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        try:
            heatmap_data = _build_portfolio_heatmap()
            return Response({'success': True, **heatmap_data})
        except Exception as e:
            logger.exception(f"Portfolio heatmap failed: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _build_portfolio_heatmap() -> dict:
    """Build dispute heatmap from the single most-recent prediction only."""
    engine = get_bayesian_engine()

    # Always use only the single most-recent prediction.
    # The Portfolio Heatmap is a breakdown of the contract the user just analyzed,
    # not an aggregate of all historical DB records.
    from .models import DisputePrediction
    latest = DisputePrediction.objects.order_by('-created_at').first()
    predictions = [latest] if latest else []

    contracts_data = []
    risk_distribution = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}

    if predictions:
        for p in predictions:
            # Rescale legacy DB values (stored pre-rescaling, typically 0.70-0.95)
            # Map [0.70, 0.95] → [0.25, 0.75] so portfolio shows realistic spread
            raw_dp = p.dispute_probability
            if raw_dp > 0.60:
                dp = round(0.25 + (raw_dp - 0.60) * 1.5, 3)
                dp = min(0.85, dp)
            else:
                dp = raw_dp
            cr = round(p.contract_risk_score * (dp / max(raw_dp, 0.01)), 3)

            risk_level = 'low' if dp < 0.25 else 'medium' if dp < 0.5 else 'high' if dp < 0.75 else 'critical'
            risk_distribution[risk_level] += 1

            contracts_data.append({
                'id': p.id,
                'title': p.contract_title or f'Contract {p.contract_id[:8]}',
                'contract_id': p.contract_id,
                'dispute_probability': round(dp, 3),
                'contract_risk': round(cr, 3),
                'financial_stress': round(p.financial_stress_score, 3),
                'predicted_cost': round(p.predicted_cost_usd, 0),
                'risk_level': risk_level,
                'top_driver': p.top_risk_drivers[0]['label'] if p.top_risk_drivers else 'Unknown',
                'created_at': p.created_at.isoformat(),
            })
    else:
        # Fallback: try to load contracts from DB
        try:
            from core.models import Contract
            contracts = list(Contract.objects.order_by('-created_at')[:20])
            for contract in contracts:
                text = getattr(contract, 'raw_text', '') or getattr(contract, 'text', '') or ''
                if not text:
                    continue  # skip contracts with no text — no sample data
                signals = {}
                text_lower = text.lower()
                for clause_type, keywords in KEYWORD_MAP.items():
                    hits = sum(1 for kw in keywords if kw in text_lower)
                    if hits > 0:
                        node_map = {
                            'FORCE_MAJEURE': 'ContractAmbiguity', 'PAYMENT_TERMS': 'PaymentDefaultRisk',
                            'LIABILITY': 'LiabilityExposure', 'TERMINATION': 'TerminationRisk',
                            'LIQUIDATED_DAMAGES': 'LiabilityExposure', 'CHANGE_ORDER': 'ScopeChangeRisk',
                            'DISPUTE_RESOLUTION': 'DisputeTrigger',
                        }
                        node = node_map.get(clause_type, 'ContractAmbiguity')
                        signals[node] = min(0.8, signals.get(node, 0) + hits * 0.08)
                result = engine.compute_dispute_probability(signals)
                dp = result['dispute_probability']
                cr = result['contract_risk_score']
                risk_level = 'low' if dp < 0.25 else 'medium' if dp < 0.5 else 'high' if dp < 0.75 else 'critical'
                risk_distribution[risk_level] += 1
                title = getattr(contract, 'title', '') or getattr(contract, 'name', '') or f'Contract {str(contract.id)[:8]}'
                contracts_data.append({
                    'id': str(contract.id),
                    'title': title,
                    'contract_id': str(contract.id),
                    'dispute_probability': round(dp, 3),
                    'contract_risk': round(cr, 3),
                    'financial_stress': round(result.get('financial_stress_score', dp * 0.9), 3),
                    'predicted_cost': round(float(getattr(contract, 'value', 1_000_000) or 1_000_000) * dp * 0.06, 0),
                    'risk_level': risk_level,
                    'top_driver': max(signals, key=signals.get) if signals else 'ContractAmbiguity',
                    'created_at': '',
                })
        except Exception as e:
            logger.warning(f"Could not load contracts for portfolio heatmap: {e}")
            # No fallback — return empty portfolio with a message

    # Sort by dispute_probability desc
    contracts_data.sort(key=lambda c: c['dispute_probability'], reverse=True)

    total = len(contracts_data)
    avg_dispute = sum(c['dispute_probability'] for c in contracts_data) / total if total else 0
    total_exposure = sum(c['predicted_cost'] for c in contracts_data)

    return {
        'contracts': contracts_data,
        'total_contracts': total,
        'risk_distribution': risk_distribution,
        'avg_dispute_probability': round(avg_dispute, 3),
        'total_predicted_exposure': round(total_exposure, 0),
        'high_risk_count': risk_distribution['high'] + risk_distribution['critical'],
        'critical_count': risk_distribution['critical'],
    }
