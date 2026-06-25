"""
Quick script to create a SuperAdmin user for testing.
Usage: python manage.py shell < create_superadmin.py
"""

from core.models import User, Role

print("=" * 60)
print("Creating SuperAdmin User")
print("=" * 60)

# Check if SuperAdmin role exists
try:
    superadmin_role = Role.objects.get(name='SuperAdmin')
    print(f"✅ Found SuperAdmin role: {superadmin_role.name}")
except Role.DoesNotExist:
    print("❌ SuperAdmin role not found!")
    print("   Run: python manage.py initialize_roles")
    exit(1)

# Check if SuperAdmin user already exists
existing = User.objects.filter(email='superadmin@test.com').first()
if existing:
    print(f"⚠️  User already exists: {existing.email}")
    print(f"   Role: {existing.role.name}")
    print(f"   Fivetran Access: {existing.fivetran_access}")
    print(f"   Kafka Access: {existing.kafka_access}")
    print(f"   Active: {existing.is_active}")
    print("\nTo reset password, run:")
    print("   user = User.objects.get(email='superadmin@test.com')")
    print("   user.set_password('admin123')")
    print("   user.save()")
else:
    # Create new SuperAdmin
    admin = User.objects.create(
        email='superadmin@test.com',
        first_name='Super',
        last_name='Admin',
        role=superadmin_role,
        fivetran_access=True,
        kafka_access=True,
        is_active=True
    )
    admin.set_password('admin123')
    admin.save()

    print(f"✅ SuperAdmin created successfully!")
    print(f"   Email: {admin.email}")
    print(f"   Password: admin123")
    print(f"   Role: {admin.role.name}")
    print(f"   Fivetran Access: {admin.fivetran_access}")
    print(f"   Kafka Access: {admin.kafka_access}")

print("\n" + "=" * 60)
print("Next Steps:")
print("=" * 60)
print("1. Start server: python manage.py runserver")
print("2. Login:")
print('   curl -X POST http://localhost:8000/api/auth/login \\')
print('     -H "Content-Type: application/json" \\')
print('     -d \'{"email": "superadmin@test.com", "password": "admin123"}\'')
print("\n3. Use the returned token for API calls")
print("=" * 60)
