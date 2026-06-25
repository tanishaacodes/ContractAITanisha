"""
Reassign all contracts to a specific user
Useful when contracts are owned by the wrong user
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, User


def reassign_contracts(target_user_email: str):
    """Reassign all contracts to the specified user"""
    print("\n" + "="*60)
    print("REASSIGN CONTRACTS TO USER")
    print("="*60)

    # Get target user
    try:
        target_user = User.objects.get(email=target_user_email)
        print(f"\n[INFO] Target user: {target_user.email}")
        print(f"  User ID: {str(target_user.id)[:8]}...")
    except User.DoesNotExist:
        print(f"\n[ERROR] User '{target_user_email}' not found!")
        print("\nAvailable users:")
        for user in User.objects.all():
            print(f"  - {user.email}")
        print("="*60)
        return

    # Get all contracts
    all_contracts = Contract.objects.all()
    total_count = all_contracts.count()

    print(f"\n[INFO] Total contracts to reassign: {total_count}")

    if total_count == 0:
        print("\n[OK] No contracts to reassign!")
        print("="*60)
        return

    # Show current ownership
    print("\n[INFO] Current ownership:")
    current_owners = {}
    for contract in all_contracts:
        user_id = str(contract.user_id)
        if user_id not in current_owners:
            try:
                user = User.objects.get(id=contract.user_id)
                current_owners[user_id] = {'email': user.email, 'count': 0}
            except:
                current_owners[user_id] = {'email': 'Unknown', 'count': 0}
        current_owners[user_id]['count'] += 1

    for user_id, info in current_owners.items():
        print(f"  {info['email']}: {info['count']} contracts")

    # Confirm reassignment
    print(f"\n[WARNING] This will reassign all {total_count} contracts to {target_user.email}")
    print("  [INFO] Proceeding with reassignment...")

    # Reassign all contracts
    print(f"\n[INFO] Reassigning contracts...")
    updated = all_contracts.update(user=target_user)

    print(f"\n[OK] Successfully reassigned {updated} contracts to {target_user.email}")
    print("="*60)
    print("\nNext steps:")
    print("  1. Refresh your dashboard in the browser")
    print("  2. All contracts should now be visible")
    print("="*60)


if __name__ == '__main__':
    # Get user email from command line or use default
    if len(sys.argv) > 1:
        email = sys.argv[1]
    else:
        # Show available users and prompt
        print("\n" + "="*60)
        print("AVAILABLE USERS:")
        print("="*60)
        for idx, user in enumerate(User.objects.all(), 1):
            print(f"  {idx}. {user.email}")
        print("="*60)
        print("\nUsage: python reassign_contracts.py <user_email>")
        print("Example: python reassign_contracts.py user@example.com")
        print("="*60)
        sys.exit(1)

    try:
        reassign_contracts(email)
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Reassignment failed: {e}")
        import traceback
        traceback.print_exc()
