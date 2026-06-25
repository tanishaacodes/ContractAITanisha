"""
BOQ Comparison Service
======================
Compares contractor's quoted BOQ rates against tender estimates.
Identifies gaps, risks, and pricing opportunities.

Features:
  - Item-by-item gap analysis
  - Risk flagging (±15% threshold)
  - Category-wise summary
  - Total bid value calculation
  - Optimization recommendations
"""

import logging
from decimal import Decimal
from typing import List, Dict, Tuple

from django.db.models import Sum, Avg, Count, Q
from django.db import transaction

logger = logging.getLogger(__name__)

# Risk threshold (±15%)
RISK_THRESHOLD = 0.15


# ─────────────────────────────────────────────────────────────────────────────
# Single Item Comparison
# ─────────────────────────────────────────────────────────────────────────────

def compare_boq_item(tender_item, bid_item) -> Dict:
    """
    Compare single BOQ item quote against tender estimate.

    Args:
        tender_item: TenderWorkItem instance
        bid_item: BidBOQ instance

    Returns:
        Comparison dict with gap analysis
    """
    tender_rate = float(tender_item.estimated_cost or 0)
    quantity = float(tender_item.quantity or 1)
    quoted_rate = float(bid_item.quoted_rate or 0)

    tender_total = tender_rate * quantity
    quoted_total = quoted_rate * quantity
    gap = quoted_total - tender_total
    gap_pct = (gap / tender_total * 100) if tender_total > 0 else 0

    is_risky = abs(gap_pct) > (RISK_THRESHOLD * 100)

    return {
        "item_code": tender_item.item_code,
        "description": tender_item.description[:100],
        "category": tender_item.category,
        "quantity": quantity,
        "unit": tender_item.unit,
        "tender_rate": round(tender_rate, 2),
        "quoted_rate": round(quoted_rate, 2),
        "tender_total": round(tender_total, 2),
        "quoted_total": round(quoted_total, 2),
        "gap": round(gap, 2),
        "gap_percentage": round(gap_pct, 2),
        "is_risky": is_risky,
        "risk_level": _classify_risk(gap_pct),
    }


def _classify_risk(gap_pct: float) -> str:
    """Classify risk level based on gap percentage."""
    abs_gap = abs(gap_pct)
    if abs_gap > 25:
        return "CRITICAL"
    elif abs_gap > 15:
        return "HIGH"
    elif abs_gap > 10:
        return "MEDIUM"
    else:
        return "LOW"


# ─────────────────────────────────────────────────────────────────────────────
# Bulk Comparison
# ─────────────────────────────────────────────────────────────────────────────

def compare_all_boq_items(tender) -> Dict:
    """
    Compare all BOQ items for a tender.

    Args:
        tender: Tender instance

    Returns:
        {
            "items": [...],
            "summary": {...},
            "category_summary": [...],
            "recommendations": [...]
        }
    """
    from tenders.models import TenderWorkItem, BidBOQ

    work_items = TenderWorkItem.objects.filter(tender=tender).prefetch_related('bid_quotes')

    items_comparison = []
    total_tender_value = 0
    total_quoted_value = 0
    risky_items = []

    for work_item in work_items:
        bid_quotes = work_item.bid_quotes.all()

        if not bid_quotes:
            # No quote yet
            continue

        bid_item = bid_quotes.first()  # Take first quote (could support multiple bidders)
        comparison = compare_boq_item(work_item, bid_item)
        items_comparison.append(comparison)

        total_tender_value += comparison['tender_total']
        total_quoted_value += comparison['quoted_total']

        if comparison['is_risky']:
            risky_items.append(comparison)

    total_gap = total_quoted_value - total_tender_value
    total_gap_pct = (total_gap / total_tender_value * 100) if total_tender_value > 0 else 0

    # Category-wise summary
    category_summary = _calculate_category_summary(items_comparison)

    # Recommendations
    recommendations = _generate_recommendations(items_comparison, total_gap_pct)

    return {
        "items": items_comparison,
        "summary": {
            "total_items": len(items_comparison),
            "total_tender_value": round(total_tender_value, 2),
            "total_quoted_value": round(total_quoted_value, 2),
            "total_gap": round(total_gap, 2),
            "total_gap_percentage": round(total_gap_pct, 2),
            "risky_items_count": len(risky_items),
            "over_estimated_items": sum(1 for i in items_comparison if i['gap'] > 0),
            "under_estimated_items": sum(1 for i in items_comparison if i['gap'] < 0),
        },
        "category_summary": category_summary,
        "risky_items": risky_items[:10],  # Top 10 risky items
        "recommendations": recommendations,
    }


def _calculate_category_summary(items: List[Dict]) -> List[Dict]:
    """Calculate summary per BOQ category."""
    from collections import defaultdict

    category_data = defaultdict(lambda: {
        'count': 0,
        'tender_total': 0,
        'quoted_total': 0,
        'risky_count': 0
    })

    for item in items:
        cat = item['category']
        category_data[cat]['count'] += 1
        category_data[cat]['tender_total'] += item['tender_total']
        category_data[cat]['quoted_total'] += item['quoted_total']
        if item['is_risky']:
            category_data[cat]['risky_count'] += 1

    summary = []
    for cat, data in category_data.items():
        gap = data['quoted_total'] - data['tender_total']
        gap_pct = (gap / data['tender_total'] * 100) if data['tender_total'] > 0 else 0

        summary.append({
            'category': cat,
            'items_count': data['count'],
            'tender_total': round(data['tender_total'], 2),
            'quoted_total': round(data['quoted_total'], 2),
            'gap': round(gap, 2),
            'gap_percentage': round(gap_pct, 2),
            'risky_items': data['risky_count'],
        })

    return sorted(summary, key=lambda x: abs(x['gap']), reverse=True)


def _generate_recommendations(items: List[Dict], total_gap_pct: float) -> List[str]:
    """Generate optimization recommendations."""
    recommendations = []

    # Overall bid position
    if total_gap_pct > 10:
        recommendations.append(
            f"⚠️ Your bid is {total_gap_pct:.1f}% above tender estimate. Consider reviewing overpriced items."
        )
    elif total_gap_pct < -10:
        recommendations.append(
            f"✓ Your bid is {abs(total_gap_pct):.1f}% below tender estimate. Strong competitive position."
        )

    # High-risk items
    critical_items = [i for i in items if i['risk_level'] == 'CRITICAL']
    if critical_items:
        recommendations.append(
            f"🚨 {len(critical_items)} items have critical pricing gaps (>25%). Review: " +
            ", ".join([i['item_code'] for i in critical_items[:3]])
        )

    # Category-specific
    high_gap_items = sorted([i for i in items if i['gap'] > 0], key=lambda x: x['gap'], reverse=True)[:3]
    if high_gap_items:
        recommendations.append(
            f"💰 Top overpriced items: " +
            ", ".join([f"{i['item_code']} (+{i['gap_percentage']:.1f}%)" for i in high_gap_items])
        )

    # Optimization opportunity
    low_gap_items = sorted([i for i in items if i['gap'] < 0], key=lambda x: x['gap'])[:3]
    if low_gap_items:
        recommendations.append(
            f"💡 Consider increasing margin on: " +
            ", ".join([f"{i['item_code']} ({i['gap_percentage']:.1f}%)" for i in low_gap_items])
        )

    return recommendations


# ─────────────────────────────────────────────────────────────────────────────
# Auto-create BidBOQ from Tender BOQ (with default rates)
# ─────────────────────────────────────────────────────────────────────────────

@transaction.atomic
def auto_populate_bid_boq(tender, margin_percentage: float = 10.0) -> int:
    """
    Auto-create BidBOQ entries from TenderWorkItem with default margin.

    Args:
        tender: Tender instance
        margin_percentage: Default margin to apply

    Returns:
        Number of BidBOQ items created
    """
    from tenders.models import TenderWorkItem, BidBOQ

    work_items = TenderWorkItem.objects.filter(tender=tender)

    created_count = 0

    for work_item in work_items:
        # Skip if already quoted
        if BidBOQ.objects.filter(tender=tender, tender_work_item=work_item).exists():
            continue

        tender_rate = work_item.estimated_cost or Decimal('0')
        quantity = work_item.quantity or 1

        # Apply margin
        quoted_rate = tender_rate * Decimal(1 + margin_percentage / 100)
        quoted_total = quoted_rate * Decimal(quantity)

        gap_pct = margin_percentage
        is_risky = abs(gap_pct) > (RISK_THRESHOLD * 100)

        BidBOQ.objects.create(
            tender=tender,
            tender_work_item=work_item,
            quoted_rate=quoted_rate,
            quoted_total=quoted_total,
            gap_percentage=gap_pct,
            is_risky=is_risky,
        )

        created_count += 1

    logger.info(f"[BOQComparison] Auto-populated {created_count} BidBOQ items for tender {tender.id}")
    return created_count


# ─────────────────────────────────────────────────────────────────────────────
# Update Gap Analysis
# ─────────────────────────────────────────────────────────────────────────────

@transaction.atomic
def recalculate_gaps(tender) -> int:
    """
    Recalculate gap percentages and risk flags for all BidBOQ items.

    Args:
        tender: Tender instance

    Returns:
        Number of items updated
    """
    from tenders.models import BidBOQ

    bid_items = BidBOQ.objects.filter(tender=tender).select_related('tender_work_item')

    updated_count = 0

    for bid_item in bid_items:
        work_item = bid_item.tender_work_item
        tender_rate = float(work_item.estimated_cost or 0)
        quantity = float(work_item.quantity or 1)
        quoted_rate = float(bid_item.quoted_rate or 0)

        tender_total = tender_rate * quantity
        quoted_total = quoted_rate * quantity
        gap_pct = ((quoted_total - tender_total) / tender_total * 100) if tender_total > 0 else 0

        bid_item.gap_percentage = gap_pct
        bid_item.is_risky = abs(gap_pct) > (RISK_THRESHOLD * 100)
        bid_item.quoted_total = Decimal(quoted_total)
        bid_item.save()

        updated_count += 1

    logger.info(f"[BOQComparison] Recalculated gaps for {updated_count} items")
    return updated_count
