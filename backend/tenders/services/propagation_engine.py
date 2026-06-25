"""
Cross-Department Risk Propagation Engine (DFS Cascade)
=======================================================
Models: Civil → Mechanical → Electrical → MEP → Finance cascade
Stores result in BidDepartmentRiskPropagation (one row per dept per tender).
"""

import logging
from django.db.models import Avg, Count
from tenders.models import (
    Tender, BidActionItem, BidDepartmentRiskPropagation,
)

logger = logging.getLogger(__name__)

# ─── Risk dependency graph (directed weighted edges) ─────────────────────────
RISK_CASCADE = {
    'Civil':       [('Mechanical', 0.7), ('Planning', 0.5)],
    'Mechanical':  [('Electrical', 0.6), ('MEP', 0.5)],
    'Electrical':  [('MEP', 0.5),        ('Finance', 0.4)],
    'MEP':         [('QA/QC', 0.4),      ('HSE', 0.3)],
    'Legal':       [('Finance', 0.7),    ('Procurement', 0.4)],
    'Planning':    [('Procurement', 0.5),('Finance', 0.4)],
    'Procurement': [('Finance', 0.5)],
    'HSE':         [('QA/QC', 0.4)],
}

# ─── Base delay days per department (rule-based) ─────────────────────────────
BASE_DELAY_DAYS = {
    'Civil':       14,
    'Mechanical':  10,
    'Electrical':   8,
    'MEP':          7,
    'Legal':        5,
    'Finance':      3,
    'HSE':          4,
    'Planning':     6,
    'Procurement':  12,
    'QA/QC':        5,
    'Signaling':    10,
}


def _predict_delay(dept_name: str, avg_risk: float, task_count: int) -> int:
    """
    Predicted delay = base_days × (1 + avg_risk) × (1 + task_count × 0.02)
    Reflects higher risk and more tasks → longer delays.
    """
    base = BASE_DELAY_DAYS.get(dept_name, 7)
    days = base * (1 + avg_risk) * (1 + task_count * 0.02)
    return max(1, round(days))


def propagate_and_store(tender: Tender) -> list:
    """
    Run DFS risk cascade for the tender, persist results to
    BidDepartmentRiskPropagation, and return a list of dept dicts.

    Returns:
        [
            {
                'department': 'Civil',
                'base_risk': 0.15,
                'propagated_risk': 0.21,
                'amplification': 0.06,
                'task_count': 42,
                'predicted_delay_days': 18
            },
            ...
        ]
    """
    # ── Aggregate base risk per department from action items ─────────────────
    dept_stats = (
        BidActionItem.objects
        .filter(tender=tender)
        .values('department__name')
        .annotate(
            avg_risk=Avg('risk_score'),
            count=Count('id'),
        )
    )

    risk_map  = {}   # dept_name → propagated risk (mutable)
    count_map = {}   # dept_name → task count

    for row in dept_stats:
        name = row['department__name']
        if name:
            risk_map[name]  = row['avg_risk'] or 0.0
            count_map[name] = row['count'] or 0

    base_risk_map = dict(risk_map)  # snapshot before propagation

    # ── DFS cascade ───────────────────────────────────────────────────────────
    visited = set()

    def dfs(dept_key: str, accumulated: float):
        if dept_key in visited:
            return
        visited.add(dept_key)
        for (target, weight) in RISK_CASCADE.get(dept_key, []):
            propagated = accumulated * weight
            if target in risk_map:
                risk_map[target] = min(0.99, risk_map[target] + propagated)
            dfs(target, propagated)

    # Start from highest-risk departments first
    for key in sorted(risk_map, key=lambda k: risk_map[k], reverse=True):
        dfs(key, risk_map[key])

    # ── Persist & build response ───────────────────────────────────────────────
    results = []
    for dept_name, prop_risk in risk_map.items():
        base    = base_risk_map.get(dept_name, 0.0)
        amp     = round(prop_risk - base, 4)
        t_count = count_map.get(dept_name, 0)
        delay   = _predict_delay(dept_name, prop_risk, t_count)

        BidDepartmentRiskPropagation.objects.update_or_create(
            tender=tender,
            department_name=dept_name,
            defaults={
                'base_risk':            round(base, 4),
                'propagated_risk':      round(prop_risk, 4),
                'amplification':        amp,
                'predicted_delay_days': delay,
                'task_count':           t_count,
            }
        )

        results.append({
            'department':          dept_name,
            'base_risk':           round(base, 4),
            'propagated_risk':     round(prop_risk, 4),
            'amplification':       round(amp, 4),
            'task_count':          t_count,
            'predicted_delay_days': delay,
        })

    logger.info(f"[PropEngine] Propagation complete for tender {tender.id}: "
                f"{len(results)} departments processed")
    return sorted(results, key=lambda x: x['propagated_risk'], reverse=True)


def get_dependency_graph(tender: Tender) -> dict:
    """
    Returns a graph-ready dict: nodes + edges for frontend visualization.
    Nodes are sized by task count; edges weighted by cascade weight.
    """
    propagations = BidDepartmentRiskPropagation.objects.filter(tender=tender)

    nodes = []
    for p in propagations:
        nodes.append({
            'id':    p.department_name,
            'label': p.department_name,
            'risk':  round(p.propagated_risk, 4),
            'count': p.task_count,
            'delay': p.predicted_delay_days,
        })

    dept_names = {p.department_name for p in propagations}
    edges = []
    for src, targets in RISK_CASCADE.items():
        if src in dept_names:
            for (tgt, weight) in targets:
                if tgt in dept_names:
                    edges.append({
                        'from':   src,
                        'to':     tgt,
                        'weight': weight,
                    })

    return {'nodes': nodes, 'edges': edges}
