"""
Import Real Bids from CSV
Usage: python import_from_csv.py <tender_id> <csv_file>
Example: python import_from_csv.py 38 real_bids_template.csv
"""
import os
import sys
import csv
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from tenders.models import Tender, Vendor, VendorBid


def import_from_csv(tender_id, csv_file):
    """Import vendors and bids from CSV file."""

    try:
        tender = Tender.objects.get(id=tender_id)
        print(f"✅ Found tender: {tender.title}")
    except Tender.DoesNotExist:
        print(f"❌ Tender ID {tender_id} not found!")
        return

    # Track stats
    vendors_created = 0
    bids_created = 0
    bids_updated = 0

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Create/get vendor
            vendor, created = Vendor.objects.get_or_create(
                name=row['vendor_name'],
                defaults={
                    'registration_number': row.get('registration_number', ''),
                    'financial_rating': float(row.get('financial_rating', 0.5)),
                    'past_performance_score': float(row.get('past_performance_score', 0.5)),
                }
            )
            if created:
                vendors_created += 1
                print(f"  ➕ Created vendor: {vendor.name}")

            # Create/update bid
            bid, bid_created = VendorBid.objects.update_or_create(
                tender=tender,
                vendor=vendor,
                round_number=int(row['round_number']),
                defaults={
                    'total_price': float(row['total_price']),
                    'technical_score': float(row.get('technical_score', 0)),
                    'commercial_score': float(row.get('commercial_score', 0)),
                    'legal_risk_score': float(row.get('legal_risk_score', 0)),
                    'delay_probability': float(row.get('delay_probability', 0)),
                    'deviation_score': float(row.get('deviation_score', 0)),
                    'notes': row.get('notes', ''),
                }
            )

            if bid_created:
                bids_created += 1
                print(f"  ➕ Created bid: {vendor.name} - Round {row['round_number']} - ₹{float(row['total_price']):,.0f}")
            else:
                bids_updated += 1
                print(f"  🔄 Updated bid: {vendor.name} - Round {row['round_number']}")

    print("\n" + "=" * 80)
    print("✅ IMPORT COMPLETE!")
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"   New Vendors: {vendors_created}")
    print(f"   New Bids: {bids_created}")
    print(f"   Updated Bids: {bids_updated}")
    print(f"\n🌐 View dashboard at: http://localhost:5173/tenders/{tender_id}/buyer")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python import_from_csv.py <tender_id> <csv_file>")
        print("Example: python import_from_csv.py 38 real_bids_template.csv")
        sys.exit(1)

    tender_id = int(sys.argv[1])
    csv_file = sys.argv[2]

    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        sys.exit(1)

    print("=" * 80)
    print("CSV IMPORT SCRIPT")
    print("=" * 80)
    print(f"Tender ID: {tender_id}")
    print(f"CSV File: {csv_file}")
    print("=" * 80 + "\n")

    import_from_csv(tender_id, csv_file)
