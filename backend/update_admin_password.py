import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')

import django
django.setup()

from core.models import User, Role
import bcrypt

# Get admin user
try:
    admin_user = User.objects.get(email='admin@example.com')

    # Set the correct password
    password = 'Vansh123'
    salt = bcrypt.gensalt(rounds=10)
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    admin_user.password = hashed_password
    admin_user.save()

    print("Admin password updated successfully!")
    print(f"Email: {admin_user.email}")
    print(f"Password: Vansh123")
    print(f"Role: {admin_user.role.name}")
    print(f"\nYou can now login at http://localhost:5173")

except User.DoesNotExist:
    print("Admin user not found. Creating new admin user...")

    admin_role, _ = Role.objects.get_or_create(
        name='Admin',
        defaults={'description': 'Full system access'}
    )

    password = 'Vansh123'
    salt = bcrypt.gensalt(rounds=10)
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    admin_user = User.objects.create(
        email='admin@example.com',
        password=hashed_password,
        first_name='Admin',
        last_name='User',
        role=admin_role,
        is_active=True
    )

    print("Admin user created successfully!")
    print(f"Email: admin@example.com")
    print(f"Password: Vansh123")
    print(f"Role: Admin")
