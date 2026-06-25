"""
Check which user owns the contracts in the database
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, User
from django.db.models import Count


def check_contract_users():
    """Check contract ownership and user info"""
    print("\n" + "="*60)
    print("CONTRACT OWNERSHIP ANALYSIS")
    print("="*60)

    # Get all users
    print("\n[1/3] Users in system:")
    users = User.objects.all()
    for idx, user in enumerate(users, 1):
        print(f"  {idx}. {user.email} (ID: {str(user.id)[:8]}...)")

    # Get contract counts by user
    print("\n[2/3] Contracts by user:")
    contract_counts = Contract.objects.values('user_id').annotate(count=Count('id'))

    total_contracts = 0
    for item in contract_counts:
        user_id = item['user_id']
        count = item['count']
        total_contracts += count

        try:
            user = User.objects.get(id=user_id)
            print(f"  User: {user.email}")
            print(f"    Contracts: {count}")
            print(f"    User ID: {str(user_id)[:8]}...")
        except User.DoesNotExist:
            print(f"  [WARNING] Unknown user ID: {str(user_id)[:8]}...")
            print(f"    Contracts: {count}")

    print(f"\n  Total contracts: {total_contracts}")

    # Show sample contracts
    print("\n[3/3] Sample contracts (first 10):")
    sample_contracts = Contract.objects.all().order_by('-uploaded_at')[:10]

    for c in sample_contracts:
        try:
            user = User.objects.get(id=c.user_id)
            user_email = user.email
        except:
            user_email = "Unknown"

        print(f"  - {c.original_filename or c.filename}")
        print(f"    User: {user_email}")
        print(f"    Uploaded: {c.uploaded_at}")
        print(f"    Has text: {'Yes' if c.full_text else 'No'}")
        print(f"    Contract type: {c.contract_type or 'Unknown'}")
        print()

    print("="*60)
    print("\nRECOMMENDATIONS:")
    print("  If contracts belong to a different user than you're logged in as,")
    print("  you have two options:")
    print("  1. Log in with the correct user account in the frontend")
    print("  2. Run reassign_contracts.py to move contracts to your user")
    print("="*60)


if __name__ == '__main__':
    try:
        check_contract_users()
    except Exception as e:
        print(f"\n\n[ERROR] Check failed: {e}")
        import traceback
        traceback.print_exc()
