"""
Action Item Generator
Generates BidActionItems from existing tender data:
  - TenderWorkItem (BOQ)  → Civil / Mechanical / Electrical / MEP actions
  - TenderRisk            → Legal / HSE / Finance / QA/QC actions
  - TenderNegotiation     → Finance / Legal actions
  - TenderEligibility     → Procurement / Planning / QA/QC actions
  - Static items          → 11 standard enterprise items per tender

No new backend calls needed — purely maps from existing MySQL data.
Also provides an LLM-powered generator for richer descriptions (optional).
"""

import logging
from decimal import Decimal

from django.db import transaction

from tenders.models import (
    Tender, TenderWorkItem, TenderRisk, TenderNegotiation,
    TenderEligibility, BidDepartment, BidActionItem,
)
from tenders.services.department_classifier import (
    classify_from_boq_category, classify_from_risk_category, classify_from_text,
)

logger = logging.getLogger(__name__)


# ─── Priority helpers ────────────────────────────────────────────────────────

def _cost_to_priority(estimated_cost) -> str:
    """Map financial exposure to priority level."""
    try:
        val = float(estimated_cost or 0)
    except (TypeError, ValueError):
        val = 0.0
    if val >= 500_000_000:   # ≥ ₹50 Cr
        return 'Critical'
    if val >= 100_000_000:   # ≥ ₹10 Cr
        return 'High'
    if val >= 10_000_000:    # ≥ ₹1 Cr
        return 'Medium'
    return 'Low'


def _severity_to_priority(severity: str) -> str:
    mapping = {'CRITICAL': 'Critical', 'HIGH': 'High', 'MEDIUM': 'Medium', 'LOW': 'Low'}
    return mapping.get(severity, 'Medium')


def _cost_to_risk(estimated_cost) -> float:
    """Normalise financial cost to 0-1 risk score (capped)."""
    try:
        val = float(estimated_cost or 0)
    except (TypeError, ValueError):
        val = 0.0
    # ₹1000 Cr → 0.9 max
    return min(0.9, val / 10_000_000_000)


def _get_or_create_dept(name: str) -> BidDepartment:
    dept, _ = BidDepartment.objects.get_or_create(name=name)
    return dept


def _validate_financial_exposure(exposure: Decimal, tender: Tender) -> Decimal:
    """
    Validate and cap financial exposure to prevent unreasonable values.

    Rules:
    1. Cap at 30% of total tender value (individual items shouldn't exceed this)
    2. Absolute cap at ₹100 Cr per item (1,000,000,000)

    Args:
        exposure: Raw exposure value from BOQ/Risk/etc.
        tender: The tender object (for getting total estimated_value)

    Returns:
        Validated and capped exposure value
    """
    try:
        val = float(exposure or 0)
    except (TypeError, ValueError):
        val = 0.0

    # Get tender value for percentage cap
    tender_value = float(tender.estimated_value or 0)

    # Cap at 30% of tender value if tender value exists
    if tender_value > 0:
        max_item_cost = tender_value * 0.3
        val = min(val, max_item_cost)

    # Absolute cap at ₹100 Cr
    val = min(val, 1000000000)

    return Decimal(str(val))


# ─── Static items per tender ─────────────────────────────────────────────────

STATIC_ITEMS = [
    # (dept, title, description, priority, risk_score, complexity)
    ('Planning',    'Develop Baseline Programme',
     'Prepare P6/Primavera baseline schedule with WBS, milestones and critical path.',
     'High', 0.5, 0.6),
    ('Procurement', 'Identify Long Lead Items',
     'List all imported / specialised equipment with lead times > 16 weeks.',
     'High', 0.55, 0.5),
    ('HSE',         'Prepare Method Statement & HIRA',
     'Develop method statements and Hazard Identification & Risk Assessment.',
     'High', 0.4, 0.45),
    ('Legal',       'Review FIDIC Clause Deviations',
     'Clause-by-clause review against FIDIC Silver/Yellow book; flag non-standard terms.',
     'Critical', 0.7, 0.7),
    ('Civil',       'Geotechnical Investigation Review',
     'Review soil investigation report; assess bearing capacity, settlement and pile design.',
     'High', 0.5, 0.6),
    ('Electrical',  'Electrical Load Calculation',
     'Prepare detailed load schedule, transformer sizing, switchgear grading.',
     'Medium', 0.35, 0.45),
    ('QA/QC',       'Prepare Inspection Test Plan',
     'Develop ITP for all major work activities; define hold points and witness points.',
     'High', 0.4, 0.5),
    ('Finance',     'Cashflow Forecast Model',
     'Prepare monthly cashflow projection aligned to program and payment milestones.',
     'High', 0.45, 0.55),
    ('Mechanical',  'Equipment Procurement Strategy',
     'Develop procurement strategy for all major mechanical packages with vendor list.',
     'Medium', 0.4, 0.45),
    ('Signaling',   'Signaling Interface Management',
     'Prepare interface matrix with civil, electrical and telecom subcontractors.',
     'High', 0.55, 0.6),
    ('MEP',         'MEP Coordination Drawing Review',
     'Clash-detection review of MEP services in confined spaces using BIM/Navisworks.',
     'High', 0.45, 0.55),
]


# ─── Main Generator ──────────────────────────────────────────────────────────

@transaction.atomic
def generate_action_items(tender: Tender, regenerate: bool = False) -> int:
    """
    Generate BidActionItem rows for the given tender.
    Returns count of items created.

    Args:
        tender:     Tender instance
        regenerate: If True, delete existing items first.
    """
    if regenerate:
        BidActionItem.objects.filter(tender=tender).delete()
        logger.info(f"[ActionGen] Cleared existing items for tender {tender.id}")

    # Skip if items already exist (idempotent)
    if BidActionItem.objects.filter(tender=tender).exists():
        logger.info(f"[ActionGen] Items already exist for tender {tender.id}, skipping")
        return BidActionItem.objects.filter(tender=tender).count()

    created = 0
    items_to_create = []

    # ── 1. BOQ Work Items ────────────────────────────────────────────────────
    for wi in TenderWorkItem.objects.filter(tender=tender):
        dept_name = classify_from_boq_category(wi.category)
        dept      = _get_or_create_dept(dept_name)
        raw_exposure = wi.estimated_cost or wi.final_unit_cost or Decimal('0')
        exposure  = _validate_financial_exposure(raw_exposure, tender)
        priority  = _cost_to_priority(exposure)
        risk      = _cost_to_risk(exposure)

        items_to_create.append(BidActionItem(
            tender=tender,
            department=dept,
            source_type='BOQ',
            source_ref=wi.item_code,
            title=f"BOQ: {wi.description[:120]}",
            description=(
                f"Category: {wi.category} | Qty: {wi.quantity} {wi.unit} | "
                f"Estimated cost: ₹{exposure:,.2f}"
            ),
            priority=priority,
            complexity_score=min(0.9, risk + 0.1),
            risk_score=risk,
            financial_exposure=exposure,
            ai_generated=False,
        ))

    # ── 2. Identified Risks ──────────────────────────────────────────────────
    for risk in TenderRisk.objects.filter(tender=tender):
        dept_name = classify_from_risk_category(risk.category)
        dept      = _get_or_create_dept(dept_name)
        raw_exposure = risk.financial_exposure or Decimal('0')
        exposure  = _validate_financial_exposure(raw_exposure, tender)

        items_to_create.append(BidActionItem(
            tender=tender,
            department=dept,
            source_type='Risk',
            source_ref=risk.category,
            title=f"Risk: {risk.description[:120]}",
            description=(
                f"Severity: {risk.severity} | "
                f"Mitigation: {(risk.mitigation_suggestion or '')[:200]} | "
                f"Exposure: ₹{exposure:,.2f}"
            ),
            priority=_severity_to_priority(risk.severity),
            complexity_score=min(0.95, (risk.severity_score or 0.5)),
            risk_score=min(0.99, (risk.severity_score or 0.5)),
            financial_exposure=exposure,
            ai_generated=False,
        ))

    # ── 3. Negotiations ──────────────────────────────────────────────────────
    for neg in TenderNegotiation.objects.filter(tender=tender):
        dept_name = classify_from_text(neg.issue_type + ' ' + (neg.original_clause or ''))
        dept      = _get_or_create_dept(dept_name)

        items_to_create.append(BidActionItem(
            tender=tender,
            department=dept,
            source_type='Negotiation',
            source_ref=neg.clause_reference,
            title=f"Negotiate: {neg.issue_type[:120]}",
            description=(
                f"Original: {(neg.original_clause or '')[:200]} | "
                f"Counter: {(neg.counter_proposal or '')[:200]} | "
                f"Accept probability: {neg.acceptance_probability:.0%}"
            ),
            priority='High',
            complexity_score=0.6,
            risk_score=max(0.3, 1.0 - (neg.acceptance_probability or 0.5)),
            financial_exposure=Decimal('0'),
            ai_generated=False,
        ))

    # ── 4. Eligibility ───────────────────────────────────────────────────────
    try:
        elig = TenderEligibility.objects.get(tender=tender)
        if elig.min_turnover:
            items_to_create.append(BidActionItem(
                tender=tender,
                department=_get_or_create_dept('Finance'),
                source_type='Eligibility',
                source_ref='turnover',
                title='Compile Turnover Certificates',
                description=f"Required minimum annual turnover: ₹{elig.min_turnover:,.2f}",
                priority='Critical',
                complexity_score=0.5,
                risk_score=0.6,
                financial_exposure=Decimal('0'),
                ai_generated=False,
            ))
        if elig.similar_work_required:
            items_to_create.append(BidActionItem(
                tender=tender,
                department=_get_or_create_dept('Procurement'),
                source_type='Eligibility',
                source_ref='similar_work',
                title='Compile Similar Work Experience Certificates',
                description=(
                    f"Minimum {elig.min_projects} projects of ≥ "
                    f"₹{elig.min_project_value:,.0f} each required."
                ),
                priority='Critical',
                complexity_score=0.4,
                risk_score=0.55,
                financial_exposure=Decimal('0'),
                ai_generated=False,
            ))
        if elig.technical_criteria:
            items_to_create.append(BidActionItem(
                tender=tender,
                department=_get_or_create_dept('QA/QC'),
                source_type='Eligibility',
                source_ref='technical_criteria',
                title='Gather Technical Qualification Documents',
                description='Compile ISO certifications, key equipment list, and personnel CVs.',
                priority='High',
                complexity_score=0.45,
                risk_score=0.5,
                financial_exposure=Decimal('0'),
                ai_generated=False,
            ))
    except TenderEligibility.DoesNotExist:
        pass

    # ── 5. Static Enterprise Items ───────────────────────────────────────────
    for (dept_name, title, desc, priority, risk, complexity) in STATIC_ITEMS:
        dept = _get_or_create_dept(dept_name)
        items_to_create.append(BidActionItem(
            tender=tender,
            department=dept,
            source_type='Static',
            source_ref=None,
            title=title,
            description=desc,
            priority=priority,
            complexity_score=complexity,
            risk_score=risk,
            financial_exposure=Decimal('0'),
            ai_generated=False,
        ))

    # ── Bulk create ───────────────────────────────────────────────────────────
    BidActionItem.objects.bulk_create(items_to_create, ignore_conflicts=True)
    created = len(items_to_create)
    logger.info(f"[ActionGen] Created {created} action items for tender {tender.id}")
    return created


def seed_departments() -> None:
    """Ensure all 11 departments exist in DB. Safe to run multiple times."""
    dept_names = [
        'Civil', 'Mechanical', 'Electrical', 'MEP', 'Signaling',
        'Planning', 'Procurement', 'Finance', 'Legal', 'HSE', 'QA/QC',
    ]
    for name in dept_names:
        BidDepartment.objects.get_or_create(name=name)
    logger.info("[ActionGen] Departments seeded.")
