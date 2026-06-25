import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')

import django
django.setup()

from core.models import User, Role
import bcrypt

# Delete existing admin user if exists
User.objects.filter(email='admin@example.com').delete()

# Create Admin role
admin_role, _ = Role.objects.get_or_create(
    name='Admin',
    defaults={'description': 'Full system access'}
)

# Create new admin user with password 'vansh123'
password = 'vansh123'
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

print("Admin user reset successfully!")
print(f"Email: admin@example.com")
print(f"Password: vansh123")
print(f"Role: Admin")
print(f"User ID: {admin_user.id}")

# Test the password
test_password = 'vansh123'
is_correct = bcrypt.checkpw(test_password.encode('utf-8'), hashed_password.encode('utf-8'))
print(f"\nPassword verification: {is_correct}")
