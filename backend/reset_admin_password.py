"""
Reset admin password
"""
import os
import django
import bcrypt

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from django.db import connection

def reset_password():
    email = 'admin@example.com'
    new_password = 'Admin123!'

    print(f"\n{'='*60}")
    print(f"Resetting password for: {email}")
    print(f"New password: {new_password}")
    print(f"{'='*60}\n")

    # Hash the new password
    salt = bcrypt.gensalt(rounds=10)
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), salt).decode('utf-8')

    # Update the password in database
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE users
            SET password = %s, updatedAt = NOW()
            WHERE email = %s
        """, [hashed_password, email])

    print("✅ Password reset successfully!")
    print(f"\nLogin credentials:")
    print(f"  Email: {email}")
    print(f"  Password: {new_password}")
    print(f"\n{'='*60}\n")

if __name__ == '__main__':
    reset_password()
