"""
Bid Readiness Calculator
Calculates overall bid preparation readiness index
"""
from typing import Dict
from django.db.models import Count, Q
from apps.bid_actions.models import ActionItem, DepartmentActionSummary
from apps.tenders.models import Tender


def calculate_bid_readiness(tender: Tender) -> Dict:
    """
    Calculate comprehensive bid readiness metrics

    Args:
        tender: Tender instance

    Returns:
        Dict with readiness scores and breakdown
    """
    # Get action items
    actions = ActionItem.objects.filter(tender=tender)
    total_actions = actions.count()

    if total_actions == 0:
        return {
            'readiness_index': 0,
            'data_readiness': 0,
            'action_completion': 0,
            'readiness_steps': [],
            'overall_score': 0
        }

    # 1. Action completion percentage
    completed_actions = actions.filter(status='Completed').count()
    action_completion_pct = (completed_actions / total_actions) * 100 if total_actions > 0 else 0

    # 2. Data readiness checklist
    readiness_steps = [
        {
            'label': 'BOQ Items Extracted',
            'done': tender.work_items.exists() if hasattr(tender, 'work_items') else False
        },
        {
            'label': 'Risk Analysis Complete',
            'done': tender.risks.exists() if hasattr(tender, 'risks') else False
        },
        {
            'label': 'Win Probability Calculated',
            'done': (tender.bid_scenarios.exists() if hasattr(tender, 'bid_scenarios') else False)
        },
        {
            'label': 'Proposal Generated',
            'done': hasattr(tender, 'proposal') and tender.proposal is not None
        },
        {
            'label': 'Negotiations Initiated',
            'done': tender.negotiations.exists() if hasattr(tender, 'negotiations') else False
        },
    ]

    completed_steps = sum(1 for step in readiness_steps if step['done'])
    data_readiness_pct = (completed_steps / len(readiness_steps)) * 100

    # 3. Weighted readiness index
    # 60% data readiness + 40% action completion
    readiness_index = round((data_readiness_pct * 0.6) + (action_completion_pct * 0.4), 2)

    # 4. Risk-weighted score (penalize high-risk pending items)
    risk_weighted_completion = 0
    for action in actions:
        if action.status == 'Completed':
            weight = action.risk_score + action.complexity_score
            risk_weighted_completion += weight

    total_weight = sum(
        action.risk_score + action.complexity_score
        for action in actions
    )

    risk_adjusted_score = (
        (risk_weighted_completion / total_weight * 100)
        if total_weight > 0 else 0
    )

    return {
        'readiness_index': readiness_index,
        'data_readiness': round(data_readiness_pct, 2),
        'action_completion': round(action_completion_pct, 2),
        'risk_adjusted_score': round(risk_adjusted_score, 2),
        'readiness_steps': readiness_steps,
        'total_actions': total_actions,
        'completed_actions': completed_actions,
        'overall_score': readiness_index
    }


def calculate_department_summaries(tender: Tender) -> list:
    """
    Calculate aggregated statistics per department

    Args:
        tender: Tender instance

    Returns:
        List of department summary dicts
    """
    from django.db.models import Avg, Sum

    summaries = ActionItem.objects.filter(tender=tender).values(
        'department__id',
        'department__name',
        'department__code',
        'department__color_hex'
    ).annotate(
        total_actions=Count('id'),
        completed_actions=Count('id', filter=Q(status='Completed')),
        avg_risk_score=Avg('risk_score'),
        total_exposure=Sum('financial_exposure')
    )

    results = []
    for summary in summaries:
        completion_pct = 0
        if summary['total_actions'] > 0:
            completion_pct = (summary['completed_actions'] / summary['total_actions']) * 100

        results.append({
            'department_id': summary['department__id'],
            'department_name': summary['department__name'],
            'department_code': summary['department__code'],
            'color_hex': summary['department__color_hex'],
            'total_actions': summary['total_actions'],
            'completed_actions': summary['completed_actions'],
            'completion_percentage': round(completion_pct, 2),
            'avg_risk_score': round(summary['avg_risk_score'] or 0, 3),
            'total_exposure': float(summary['total_exposure'] or 0)
        })

    return results


def update_cached_summaries(tender: Tender) -> int:
    """
    Update DepartmentActionSummary cache table

    Args:
        tender: Tender instance

    Returns:
        Number of summaries updated
    """
    summaries = calculate_department_summaries(tender)

    count = 0
    for summary in summaries:
        DepartmentActionSummary.objects.update_or_create(
            tender=tender,
            department_id=summary['department_id'],
            defaults={
                'total_actions': summary['total_actions'],
                'completed_actions': summary['completed_actions'],
                'avg_risk_score': summary['avg_risk_score'],
                'total_financial_exposure': summary['total_exposure']
            }
        )
        count += 1

    return count


def get_portfolio_readiness(tenders: list = None) -> Dict:
    """
    Calculate portfolio-wide readiness across multiple tenders

    Args:
        tenders: List of Tender instances (None = all tenders)

    Returns:
        Dict with portfolio metrics
    """
    if tenders is None:
        tenders = Tender.objects.all()

    portfolio_data = []

    for tender in tenders:
        readiness = calculate_bid_readiness(tender)
        portfolio_data.append({
            'tender_id': str(tender.id),
            'tender_title': tender.title,
            'readiness_index': readiness['readiness_index'],
            'total_actions': readiness['total_actions'],
            'completed_actions': readiness['completed_actions']
        })

    # Calculate averages
    avg_readiness = sum(p['readiness_index'] for p in portfolio_data) / len(portfolio_data) if portfolio_data else 0
    total_actions = sum(p['total_actions'] for p in portfolio_data)
    total_completed = sum(p['completed_actions'] for p in portfolio_data)

    return {
        'portfolio_count': len(portfolio_data),
        'avg_readiness': round(avg_readiness, 2),
        'total_actions': total_actions,
        'total_completed': total_completed,
        'completion_rate': round((total_completed / total_actions * 100) if total_actions > 0 else 0, 2),
        'tenders': portfolio_data
    }
