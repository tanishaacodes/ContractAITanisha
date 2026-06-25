import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')

import django
django.setup()

from core.models import User, Role
from core.authentication import generate_token

# Create or get Admin role
admin_role, _ = Role.objects.get_or_create(
    name='Admin',
    defaults={'description': 'Full system access'}
)

# Create or get a test admin user
test_admin, created = User.objects.get_or_create(
    email='test_admin@example.com',
    defaults={
        'password': 'Test123!',
        'first_name': 'Test',
        'last_name': 'Admin',
        'role': admin_role
    }
)

if created:
    print("Test admin user created")

print(f"Test admin user created: {test_admin.email}")
print(f"User ID: {test_admin.id}")
print(f"Role: {test_admin.role.name}")

# Generate token for testing
token = generate_token(test_admin)
print(f"\nGenerated token: {token}")
print(f"\nYou can now use this token to test the role creation endpoint:")
print(f"\nPOST /api/admin/roles")
print(f"Authorization: Bearer {token}")
print(f'Body: {{"name": "Custom Role", "description": "A custom role", "permissions": {{}}}}')
