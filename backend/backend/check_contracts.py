#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from core.models import Contract, User

contracts = Contract.objects.all()
print(f"Total contracts: {contracts.count()}")
print("\n--- Contract Details ---")
for c in contracts:
    print(f"File: {c.original_filename or c.filename}")
    print(f"  User ID: {c.user_id}")
    print(f"  Uploaded: {c.uploaded_at}")
    print()

print("\n--- Users ---")
users = User.objects.all()
for u in users[:10]:
    contract_count = Contract.objects.filter(user_id=str(u.id)).count()
    print(f"Email: {u.email}, ID: {u.id}, Contracts: {contract_count}")
