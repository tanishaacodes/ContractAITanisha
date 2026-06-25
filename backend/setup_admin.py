import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')

import django
django.setup()

from core.models import User, Role
import bcrypt

# Get or create Admin role
admin_role, created = Role.objects.get_or_create(
    name='Admin',
    defaults={'description': 'Full system access'}
)

# Create or update admin user with your credentials
email = 'admin@example.com'
password = 'Vansh123'

try:
    admin_user = User.objects.get(email=email)
    print(f"Admin user already exists: {admin_user.email}")
except User.DoesNotExist:
    # Hash the password
    salt = bcrypt.gensalt(rounds=10)
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    admin_user = User.objects.create(
        email=email,
        password=hashed_password,
        first_name='Admin',
        last_name='User',
        role=admin_role,
        is_active=True
    )
    print(f"[OK] Admin user created successfully!")

print(f"\n=== Admin Details ===")
print(f"Email: {admin_user.email}")
print(f"Role: {admin_user.role.name}")
print(f"Status: {'Active' if admin_user.is_active else 'Inactive'}")
print(f"User ID: {admin_user.id}")

print(f"\n=== ADMIN SETUP COMPLETE ===")
print(f"\nYou can now login at the site with:")
print(f"Email: admin@example.com")
print(f"Password: Vansh123")
print(f"\nGo to Admin Dashboard → Roles Management to create new roles!")
