"""
Real Vendor Bid Import Script
Usage: python import_real_bids.py
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from tenders.models import Tender, Vendor, VendorBid, VendorClause


def import_vendors(vendor_data):
    """
    Import vendors from list of dicts.

    Example vendor_data:
    [
        {
            'name': 'ABC Construction Ltd',
            'registration_number': 'REG001',
            'financial_rating': 0.85,
            'past_performance_score': 0.78
        },
        ...
    ]
    """
    created_vendors = []
    for v in vendor_data:
        vendor, created = Vendor.objects.get_or_create(
            name=v['name'],
            defaults={
                'registration_number': v.get('registration_number', ''),
                'financial_rating': v.get('financial_rating', 0.5),
                'past_performance_score': v.get('past_performance_score', 0.5),
            }
        )
        created_vendors.append(vendor)
        print(f"{'Created' if created else 'Found'} vendor: {vendor.name}")
    return created_vendors


def import_bids(tender_id, bid_data):
    """
    Import bids for a specific tender.

    Example bid_data:
    [
        {
            'vendor_name': 'ABC Construction Ltd',
            'round_number': 1,
            'total_price': 5000000000,  # ₹500 Cr
            'technical_score': 85.5,
            'commercial_score': 78.2,
            'legal_risk_score': 0.25,
            'delay_probability': 0.15,
            'deviation_score': 0.18,
            'notes': 'Initial bid submission'
        },
        ...
    ]
    """
    try:
        tender = Tender.objects.get(id=tender_id)
    except Tender.DoesNotExist:
        print(f"❌ Tender {tender_id} not found!")
        return []

    created_bids = []
    for b in bid_data:
        try:
            vendor = Vendor.objects.get(name=b['vendor_name'])
        except Vendor.DoesNotExist:
            print(f"⚠️  Vendor {b['vendor_name']} not found. Skipping...")
            continue

        bid, created = VendorBid.objects.update_or_create(
            tender=tender,
            vendor=vendor,
            round_number=b['round_number'],
            defaults={
                'total_price': b['total_price'],
                'technical_score': b.get('technical_score', 0),
                'commercial_score': b.get('commercial_score', 0),
                'legal_risk_score': b.get('legal_risk_score', 0),
                'delay_probability': b.get('delay_probability', 0),
                'deviation_score': b.get('deviation_score', 0),
                'notes': b.get('notes', ''),
            }
        )
        created_bids.append(bid)
        print(f"{'Created' if created else 'Updated'} bid: {vendor.name} - Round {b['round_number']} - ₹{b['total_price']:,.0f}")

    return created_bids


def import_clauses(bid_id, clause_data):
    """
    Import clause deviations for a specific bid.

    Example clause_data:
    [
        {
            'clause_type': 'PAYMENT_TERMS',
            'clause_text': 'Payment within 60 days instead of 30 days',
            'deviation_score': 0.35,
            'risk_score': 0.42
        },
        ...
    ]
    """
    try:
        bid = VendorBid.objects.get(id=bid_id)
    except VendorBid.DoesNotExist:
        print(f"❌ Bid {bid_id} not found!")
        return []

    created_clauses = []
    for c in clause_data:
        clause, created = VendorClause.objects.get_or_create(
            vendor_bid=bid,
            clause_type=c['clause_type'],
            defaults={
                'clause_text': c['clause_text'],
                'deviation_score': c['deviation_score'],
                'risk_score': c['risk_score'],
            }
        )
        created_clauses.append(clause)
        print(f"{'Created' if created else 'Found'} clause: {c['clause_type']} (deviation: {c['deviation_score']:.2f})")

    return created_clauses


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE USAGE - CUSTOMIZE THIS WITH YOUR REAL DATA
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 80)
    print("REAL BID IMPORT SCRIPT")
    print("=" * 80)

    # ─────────────────────────────────────────────────────────────────────────
    # 1. IMPORT VENDORS
    # ─────────────────────────────────────────────────────────────────────────
    print("\n📦 Step 1: Importing Vendors...")

    vendors = [
        {
            'name': 'Example Vendor A',
            'registration_number': 'REG-2024-001',
            'financial_rating': 0.85,
            'past_performance_score': 0.78
        },
        {
            'name': 'Example Vendor B',
            'registration_number': 'REG-2024-002',
            'financial_rating': 0.72,
            'past_performance_score': 0.81
        },
        {
            'name': 'Example Vendor C',
            'registration_number': 'REG-2024-003',
            'financial_rating': 0.90,
            'past_performance_score': 0.85
        },
    ]

    created_vendors = import_vendors(vendors)

    # ─────────────────────────────────────────────────────────────────────────
    # 2. IMPORT BIDS
    # ─────────────────────────────────────────────────────────────────────────
    print("\n📊 Step 2: Importing Bids...")

    TENDER_ID = 38  # Change this to your actual tender ID

    bids = [
        # Vendor A - Round 1
        {
            'vendor_name': 'Example Vendor A',
            'round_number': 1,
            'total_price': 5500000000,  # ₹550 Cr
            'technical_score': 85.5,
            'commercial_score': 78.2,
            'legal_risk_score': 0.25,
            'delay_probability': 0.15,
            'deviation_score': 0.18,
            'notes': 'Initial bid - Round 1'
        },
        # Vendor A - Round 2
        {
            'vendor_name': 'Example Vendor A',
            'round_number': 2,
            'total_price': 5350000000,  # ₹535 Cr (reduced)
            'technical_score': 87.0,
            'commercial_score': 80.5,
            'legal_risk_score': 0.22,
            'delay_probability': 0.12,
            'deviation_score': 0.15,
            'notes': 'Revised bid - Round 2'
        },
        # Vendor B - Round 1
        {
            'vendor_name': 'Example Vendor B',
            'round_number': 1,
            'total_price': 5200000000,  # ₹520 Cr
            'technical_score': 82.3,
            'commercial_score': 85.1,
            'legal_risk_score': 0.30,
            'delay_probability': 0.18,
            'deviation_score': 0.22,
            'notes': 'Initial bid - Round 1'
        },
        # Vendor C - Round 1
        {
            'vendor_name': 'Example Vendor C',
            'round_number': 1,
            'total_price': 5800000000,  # ₹580 Cr
            'technical_score': 90.5,
            'commercial_score': 88.0,
            'legal_risk_score': 0.10,
            'delay_probability': 0.08,
            'deviation_score': 0.05,
            'notes': 'Premium bid with low risk'
        },
    ]

    created_bids = import_bids(TENDER_ID, bids)

    # ─────────────────────────────────────────────────────────────────────────
    # 3. IMPORT CLAUSE DEVIATIONS (Optional)
    # ─────────────────────────────────────────────────────────────────────────
    print("\n📝 Step 3: Importing Clause Deviations...")

    if created_bids:
        # Example: Add clauses for first bid
        first_bid = created_bids[0]
        clauses = [
            {
                'clause_type': 'PAYMENT_TERMS',
                'clause_text': 'Payment within 60 days instead of standard 30 days',
                'deviation_score': 0.35,
                'risk_score': 0.42
            },
            {
                'clause_type': 'LIQUIDATED_DAMAGES',
                'clause_text': 'LD capped at 5% instead of 10%',
                'deviation_score': 0.55,
                'risk_score': 0.68
            },
        ]
        import_clauses(first_bid.id, clauses)

    print("\n" + "=" * 80)
    print("✅ IMPORT COMPLETE!")
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"   Vendors: {len(created_vendors)}")
    print(f"   Bids: {len(created_bids)}")
    print(f"\n🌐 View dashboard at: http://localhost:5173/tenders/{TENDER_ID}/buyer")
