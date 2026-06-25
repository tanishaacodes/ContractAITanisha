"""
Delete Bids Helper Script
Usage: python delete_bids.py [options]
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from tenders.models import Tender, Vendor, VendorBid, VendorClause


def delete_bids_for_tender(tender_id):
    """Delete all bids for a specific tender."""
    VendorClause.objects.filter(vendor_bid__tender_id=tender_id).delete()
    count = VendorBid.objects.filter(tender_id=tender_id).delete()[0]
    print(f'Deleted {count} bids for Tender {tender_id}')
    return count


def delete_specific_bid(bid_id):
    """Delete a specific bid by ID."""
    try:
        bid = VendorBid.objects.get(id=bid_id)
        VendorClause.objects.filter(vendor_bid=bid).delete()
        bid.delete()
        print(f'Deleted bid {bid_id}')
        return True
    except VendorBid.DoesNotExist:
        print(f'Bid {bid_id} not found')
        return False


def delete_all_vendors_and_bids():
    """Complete cleanup - delete all vendors and bids."""
    VendorClause.objects.all().delete()
    bid_count = VendorBid.objects.all().delete()[0]
    vendor_count = Vendor.objects.all().delete()[0]
    print(f'Deleted {vendor_count} vendors and {bid_count} bids')
    return vendor_count, bid_count


if __name__ == '__main__':
    print('=' * 80)
    print('BID DELETION TOOL')
    print('=' * 80)

    if len(sys.argv) < 2:
        print('\nUsage:')
        print('  python delete_bids.py tender <tender_id>     - Delete all bids for a tender')
        print('  python delete_bids.py bid <bid_id>           - Delete specific bid')
        print('  python delete_bids.py all                    - Delete ALL vendors and bids')
        print('\nExamples:')
        print('  python delete_bids.py tender 38')
        print('  python delete_bids.py bid 55')
        print('  python delete_bids.py all')
        sys.exit(1)

    action = sys.argv[1].lower()

    if action == 'tender':
        if len(sys.argv) < 3:
            print('ERROR: Please specify tender ID')
            sys.exit(1)
        tender_id = int(sys.argv[2])
        delete_bids_for_tender(tender_id)

    elif action == 'bid':
        if len(sys.argv) < 3:
            print('ERROR: Please specify bid ID')
            sys.exit(1)
        bid_id = int(sys.argv[2])
        delete_specific_bid(bid_id)

    elif action == 'all':
        confirm = input('Are you sure you want to delete ALL vendors and bids? (yes/no): ')
        if confirm.lower() == 'yes':
            delete_all_vendors_and_bids()
        else:
            print('Cancelled')

    else:
        print(f'ERROR: Unknown action "{action}"')
        sys.exit(1)

    print('=' * 80)
    print('DONE!')
