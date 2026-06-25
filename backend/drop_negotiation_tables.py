import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    tables = [
        'negotiation_positions',
        'negotiation_clause_suggestions',
        'negotiation_messages',
        'negotiation_sessions'
    ]

    for table in tables:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"Dropped table: {table}")
        except Exception as e:
            print(f"Error dropping {table}: {e}")

print("\nAll negotiation tables dropped successfully!")
