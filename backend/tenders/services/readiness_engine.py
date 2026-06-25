"""
Bid Readiness Engine
====================
Computes Bid Readiness Index (0-100) from:
  - Data completeness (60% weight): BOQ, Risks, Scenarios, Proposal, Negotiations
  - Action completion (40% weight): % of BidActionItems marked Completed

Also persists a BidReadinessSnapshot for trend tracking.
"""

import logging
from decimal import Decimal

from django.db.models import Sum, Count, Q

from tenders.models import (
    Tender, TenderWorkItem, TenderRisk, BidScenario, TenderProposal,
    TenderNegotiation, BidActionItem, BidReadinessSnapshot,
)

logger = logging.getLogger(__name__)


def _data_readiness(tender: Tender) -> float:
    """
    0-100 score based on how much tender data has been extracted.
    Each check contributes 1/5 of the 100 points.
    """
    checks = [
        TenderWorkItem.objects.filter(tender=tender).exists(),
        TenderRisk.objects.filter(tender=tender).exists(),
        BidScenario.objects.filter(tender=tender).exists(),
        TenderProposal.objects.filter(tender=tender).exists(),
        TenderNegotiation.objects.filter(tender=tender).exists(),
    ]
    passed = sum(1 for c in checks if c)
    return (passed / len(checks)) * 100


def _task_completion(tender: Tender) -> tuple:
    """
    Returns (completion_pct, total, completed, critical_pending).
    """
    actions = BidActionItem.objects.filter(tender=tender)
    total     = actions.count()
    completed = actions.filter(status='Completed').count()
    critical  = actions.filter(
        priority='Critical'
    ).exclude(status='Completed').count()

    pct = (completed / total * 100) if total > 0 else 0.0
    return pct, total, completed, critical


def calculate_readiness(tender: Tender) -> dict:
    """
    Compute and return a full readiness report.

    Returns:
        {
            'readiness_index':   float 0-100,
            'data_readiness':    float 0-100,
            'task_completion':   float 0-100,
            'total_actions':     int,
            'completed_actions': int,
            'critical_pending':  int,
            'total_exposure':    Decimal,
            'steps': [
                {'label': str, 'done': bool}
            ]
        }
    """
    data_pct   = _data_readiness(tender)
    task_pct, total, completed, critical = _task_completion(tender)

    # Blended index: 60% data readiness + 40% task completion
    index = round((data_pct * 0.6) + (task_pct * 0.4), 1)

    total_exposure = (
        BidActionItem.objects
        .filter(tender=tender)
        .aggregate(s=Sum('financial_exposure'))
        ['s'] or Decimal('0')
    )

    # Readiness step labels
    steps = [
        {
            'label': 'BOQ Items Extracted',
            'done':  TenderWorkItem.objects.filter(tender=tender).exists(),
        },
        {
            'label': 'Risk Analysis Complete',
            'done':  TenderRisk.objects.filter(tender=tender).exists(),
        },
        {
            'label': 'Win Probability Calculated',
            'done':  BidScenario.objects.filter(tender=tender).exists(),
        },
        {
            'label': 'Proposal Generated',
            'done':  TenderProposal.objects.filter(tender=tender).exists(),
        },
        {
            'label': 'Negotiations Initiated',
            'done':  TenderNegotiation.objects.filter(tender=tender).exists(),
        },
    ]

    return {
        'readiness_index':   index,
        'data_readiness':    round(data_pct, 1),
        'task_completion':   round(task_pct, 1),
        'total_actions':     total,
        'completed_actions': completed,
        'critical_pending':  critical,
        'total_exposure':    total_exposure,
        'steps':             steps,
    }


def snapshot_readiness(tender: Tender) -> BidReadinessSnapshot:
    """Persist current readiness metrics as a snapshot row."""
    report = calculate_readiness(tender)
    snap   = BidReadinessSnapshot.objects.create(
        tender=tender,
        readiness_index=report['readiness_index'],
        data_readiness=report['data_readiness'],
        task_completion=report['task_completion'],
        total_actions=report['total_actions'],
        completed_actions=report['completed_actions'],
        critical_pending=report['critical_pending'],
        total_exposure=report['total_exposure'],
    )
    logger.info(
        f"[Readiness] Snapshot saved for tender {tender.id}: "
        f"{snap.readiness_index}%"
    )
    return snap


def get_readiness_trend(tender: Tender, limit: int = 10) -> list:
    """Return last N readiness snapshots for trend display."""
    snaps = (
        BidReadinessSnapshot.objects
        .filter(tender=tender)
        .order_by('-created_at')[:limit]
    )
    return [
        {
            'date':            s.created_at.isoformat(),
            'readiness_index': s.readiness_index,
            'data_readiness':  s.data_readiness,
            'task_completion': s.task_completion,
            'total_actions':   s.total_actions,
            'completed':       s.completed_actions,
        }
        for s in snaps
    ]
