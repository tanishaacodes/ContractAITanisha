import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')

import django
django.setup()

from core.models import User

# Check if the user exists
user_id = '62c2730a-1aac-480e-8a7d-66de318e9a87'
email = 'testuser1764777113@example.com'

try:
    user = User.objects.get(id=user_id)
    print(f"User found by ID: {user.email}")
except User.DoesNotExist:
    print(f"User NOT found by ID: {user_id}")

try:
    user = User.objects.get(email=email)
    print(f"User found by email: {user.email}, ID: {user.id}")
except User.DoesNotExist:
    print(f"User NOT found by email: {email}")

# List all users
print("\n=== All users in database ===")
for user in User.objects.all():
    print(f"ID: {user.id}, Email: {user.email}")
