"""
Initialize total_contracts_uploaded for existing users
This script sets the lifetime upload count to the current contract count
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import User, Contract

def initialize_counts():
    users = User.objects.all()

    for user in users:
        current_count = Contract.objects.filter(user=user).count()
        user.total_contracts_uploaded = current_count
        user.save(update_fields=['total_contracts_uploaded'])

        print(f"[OK] {user.email}: Set total_contracts_uploaded to {current_count}")

    print(f"\n[DONE] Initialized contract counts for {users.count()} users")

if __name__ == '__main__':
    initialize_counts()
