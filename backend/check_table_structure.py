"""
Check contracts table structure
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("DESCRIBE contracts")
    columns = cursor.fetchall()

    print("\nContracts table structure:")
    print("="*70)
    for col in columns:
        print(f"{col[0]:<20} {col[1]:<30} {col[2]:<5} {col[3]:<5}")
