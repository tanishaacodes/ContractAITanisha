"""
Action Item Generator
Automatically generates action items from tender analysis
"""
from decimal import Decimal
from typing import List, Dict
from django.utils import timezone
from datetime import timedelta

from apps.bid_actions.models import ActionItem, Department
from apps.tenders.models import Tender
from .department_classifier import classify_department, classify_by_category, classify_risk_type


def generate_actions_from_tender(tender: Tender) -> List[ActionItem]:
    """
    Generate comprehensive action items from tender data

    Args:
        tender: Tender instance

    Returns:
        List of created ActionItem instances
    """
    actions = []

    # 1. Generate from BOQ/Work Items
    actions.extend(_generate_boq_actions(tender))

    # 2. Generate from identified risks
    actions.extend(_generate_risk_actions(tender))

    # 3. Generate from negotiations
    actions.extend(_generate_negotiation_actions(tender))

    # 4. Generate from eligibility criteria
    actions.extend(_generate_eligibility_actions(tender))

    # 5. Generate standard bid preparation tasks
    actions.extend(_generate_standard_actions(tender))

    return actions


def _generate_boq_actions(tender: Tender) -> List[ActionItem]:
    """Generate actions from BOQ items"""
    actions = []

    work_items = tender.work_items.all() if hasattr(tender, 'work_items') else []

    for item in work_items:
        # Determine department
        dept_name = classify_by_category(item.category) if hasattr(item, 'category') else 'Civil'

        try:
            department = Department.objects.get(name=dept_name)
        except Department.DoesNotExist:
            department = Department.objects.first()

        # Calculate item cost with validation
        estimated_cost = float(item.estimated_cost or item.final_unit_cost or 0)

        # Safety validation: cap individual item at 30% of total tender value
        if hasattr(tender, 'estimated_value') and tender.estimated_value:
            tender_value = float(tender.estimated_value)
            max_item_cost = tender_value * 0.3

            # If item cost exceeds 30% of tender, it's likely a data error
            if estimated_cost > max_item_cost:
                estimated_cost = min(estimated_cost, max_item_cost)

        # Also cap at reasonable absolute maximum (₹100 Cr per item)
        estimated_cost = min(estimated_cost, 1000000000)

        risk_score = min(0.9, estimated_cost / 50000000)  # Normalize to 0-1

        if estimated_cost > 5000000:
            priority = 'High'
        elif estimated_cost > 1000000:
            priority = 'Medium'
        else:
            priority = 'Low'

        description = getattr(item, 'description', '') or getattr(item, 'item_code', '')

        action = ActionItem.objects.create(
            tender=tender,
            department=department,
            title=f"BOQ: {description[:60]}",
            description=f"Prepare {dept_name} BOQ submission for: {description}",
            source_type='BOQ',
            source_reference=getattr(item, 'item_code', ''),
            priority=priority,
            risk_score=risk_score,
            complexity_score=min(0.8, estimated_cost / 100000000),
            financial_exposure=Decimal(str(estimated_cost))
        )
        actions.append(action)

    return actions


def _generate_risk_actions(tender: Tender) -> List[ActionItem]:
    """Generate actions from risk analysis"""
    actions = []

    risks = tender.risks.all() if hasattr(tender, 'risks') else []

    for risk in risks:
        # Classify department
        risk_type = getattr(risk, 'risk_type', 'TECHNICAL')
        dept_name = classify_risk_type(risk_type)

        try:
            department = Department.objects.get(name=dept_name)
        except Department.DoesNotExist:
            department = Department.objects.first()

        # Map severity to priority
        severity_map = {
            'CRITICAL': 'Critical',
            'HIGH': 'High',
            'MEDIUM': 'Medium',
            'LOW': 'Low'
        }
        priority = severity_map.get(getattr(risk, 'severity', 'MEDIUM'), 'Medium')

        # Risk score from severity
        risk_score_map = {
            'CRITICAL': 0.9,
            'HIGH': 0.7,
            'MEDIUM': 0.4,
            'LOW': 0.2
        }
        risk_score = risk_score_map.get(getattr(risk, 'severity', 'MEDIUM'), 0.4)

        risk_type_display = risk_type.replace('_', ' ').title()

        action = ActionItem.objects.create(
            tender=tender,
            department=department,
            title=f"Risk: {risk_type_display}",
            description=getattr(risk, 'description', '') or getattr(risk, 'mitigation_suggestion', '') or 'Review and mitigate identified risk',
            source_type='Risk',
            source_reference=risk_type,
            priority=priority,
            risk_score=risk_score,
            complexity_score=0.6,
            financial_exposure=Decimal(str(getattr(risk, 'financial_exposure', 0) or 0))
        )
        actions.append(action)

    return actions


def _generate_negotiation_actions(tender: Tender) -> List[ActionItem]:
    """Generate actions from negotiation points"""
    actions = []

    negotiations = tender.negotiations.all() if hasattr(tender, 'negotiations') else []

    for neg in negotiations:
        try:
            department = Department.objects.get(name='Finance')
        except Department.DoesNotExist:
            department = Department.objects.first()

        issue_type = getattr(neg, 'issue_type', 'GENERAL').replace('_', ' ').title()

        acceptance_prob = getattr(neg, 'acceptance_probability', 0.5)
        priority = 'High' if acceptance_prob < 0.4 else 'Medium'
        risk_score = 1 - acceptance_prob

        action = ActionItem.objects.create(
            tender=tender,
            department=department,
            title=f"Negotiation: {issue_type}",
            description=getattr(neg, 'description', '') or 'Prepare counter-proposal for negotiation point',
            source_type='Negotiation',
            source_reference=issue_type,
            priority=priority,
            risk_score=risk_score,
            complexity_score=0.5
        )
        actions.append(action)

    return actions


def _generate_eligibility_actions(tender: Tender) -> List[ActionItem]:
    """Generate actions from eligibility criteria"""
    actions = []

    if not hasattr(tender, 'eligibility') or not tender.eligibility:
        return actions

    eligibility = tender.eligibility

    # Turnover requirement
    if hasattr(eligibility, 'min_turnover') and eligibility.min_turnover:
        try:
            dept = Department.objects.get(name='Finance')
            action = ActionItem.objects.create(
                tender=tender,
                department=dept,
                title='Eligibility: Turnover Certificate',
                description='Prepare annual turnover documentation and financial statements',
                source_type='Eligibility',
                source_reference='min_turnover',
                priority='High',
                risk_score=0.6,
                complexity_score=0.3
            )
            actions.append(action)
        except Department.DoesNotExist:
            pass

    # Similar projects requirement
    if hasattr(eligibility, 'similar_projects_required') and eligibility.similar_projects_required:
        try:
            dept = Department.objects.get(name='Procurement')
            action = ActionItem.objects.create(
                tender=tender,
                department=dept,
                title='Eligibility: Similar Work Experience',
                description='Compile similar project completion certificates and references',
                source_type='Eligibility',
                source_reference='similar_projects',
                priority='High',
                risk_score=0.6,
                complexity_score=0.4
            )
            actions.append(action)
        except Department.DoesNotExist:
            pass

    # Certifications
    if hasattr(eligibility, 'certifications') and eligibility.certifications:
        try:
            dept = Department.objects.get(name='QA/QC')
            action = ActionItem.objects.create(
                tender=tender,
                department=dept,
                title='Eligibility: Certifications',
                description='Gather required certifications, registrations and compliance documents',
                source_type='Eligibility',
                source_reference='certifications',
                priority='Medium',
                risk_score=0.3,
                complexity_score=0.3
            )
            actions.append(action)
        except Department.DoesNotExist:
            pass

    return actions


def _generate_standard_actions(tender: Tender) -> List[ActionItem]:
    """Generate standard bid preparation tasks"""
    actions = []

    standard_tasks = [
        {
            'dept': 'Planning',
            'title': 'Prepare Bid Schedule Baseline',
            'description': 'Develop CPM schedule baseline for bid submission using Primavera P6',
            'priority': 'High',
            'risk': 0.5,
            'complexity': 0.7
        },
        {
            'dept': 'Procurement',
            'title': 'Identify Long Lead Items',
            'description': 'List imported/long-lead equipment and initiate vendor queries',
            'priority': 'Medium',
            'risk': 0.4,
            'complexity': 0.6
        },
        {
            'dept': 'HSE',
            'title': 'Prepare HSE Method Statement',
            'description': 'Draft safety method statement and risk assessment matrix',
            'priority': 'Medium',
            'risk': 0.3,
            'complexity': 0.5
        },
        {
            'dept': 'Legal',
            'title': 'Review Contract Conditions',
            'description': 'Review general conditions of contract and flag deviations from standard terms',
            'priority': 'Critical',
            'risk': 0.85,
            'complexity': 0.8
        },
        {
            'dept': 'Civil',
            'title': 'Technical Review',
            'description': 'Analyse technical specifications and assess execution methodology',
            'priority': 'High',
            'risk': 0.65,
            'complexity': 0.7
        },
    ]

    for task in standard_tasks:
        try:
            dept = Department.objects.get(name=task['dept'])
            action = ActionItem.objects.create(
                tender=tender,
                department=dept,
                title=task['title'],
                description=task['description'],
                source_type='Auto-generated',
                source_reference='standard_task',
                priority=task['priority'],
                risk_score=task['risk'],
                complexity_score=task['complexity']
            )
            actions.append(action)
        except Department.DoesNotExist:
            continue

    return actions


def regenerate_all_actions(tender: Tender) -> int:
    """
    Delete existing auto-generated actions and regenerate

    Args:
        tender: Tender instance

    Returns:
        Number of actions created
    """
    # Delete old auto-generated actions
    ActionItem.objects.filter(
        tender=tender,
        source_type='Auto-generated'
    ).delete()

    # Generate new actions
    actions = generate_actions_from_tender(tender)

    return len(actions)
