import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')

import django
django.setup()

from core.models import User
import uuid

# Check the user we just created
user = User.objects.get(email='testuser1764777113@example.com')
print(f"User ID type: {type(user.id)}")
print(f"User ID value: {user.id}")
print(f"User ID repr: {repr(user.id)}")
print(f"User ID str: {str(user.id)}")

# Try different ways to query
uuid_str = '62c2730a-1aac-480e-8a7d-66de318e9a87'
uuid_obj = uuid.UUID(uuid_str)

print(f"\n=== Query attempts ===")
try:
    u = User.objects.get(id=uuid_str)
    print(f"Found by string: {u.email}")
except User.DoesNotExist:
    print(f"NOT found by string: {uuid_str}")

try:
    u = User.objects.get(id=uuid_obj)
    print(f"Found by UUID object: {u.email}")
except User.DoesNotExist:
    print(f"NOT found by UUID object: {uuid_obj}")

try:
    u = User.objects.get(id__exact=uuid_str)
    print(f"Found by exact string: {u.email}")
except User.DoesNotExist:
    print(f"NOT found by exact string: {uuid_str}")
