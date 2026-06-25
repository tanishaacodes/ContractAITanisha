import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    # Check contracts table structure
    cursor.execute("SHOW CREATE TABLE contracts")
    result = cursor.fetchone()
    print("CONTRACTS TABLE:")
    print(result[1])
    print("\n" + "="*80 + "\n")

    # Check clause_events table structure (which successfully references contracts)
    cursor.execute("SHOW CREATE TABLE clause_events")
    result = cursor.fetchone()
    print("CLAUSE_EVENTS TABLE:")
    print(result[1])
