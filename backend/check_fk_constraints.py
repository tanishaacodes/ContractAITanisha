import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    # Check foreign key constraints on clause_events
    cursor.execute("""
        SELECT
            CONSTRAINT_NAME,
            TABLE_NAME,
            COLUMN_NAME,
            REFERENCED_TABLE_NAME,
            REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'clause_events'
        AND REFERENCED_TABLE_NAME IS NOT NULL
    """)

    print("FOREIGN KEYS ON clause_events:")
    for row in cursor.fetchall():
        print(f"  Constraint: {row[0]}")
        print(f"    Column: {row[2]} -> {row[3]}.{row[4]}")

    print("\n" + "="*80 + "\n")

    # Check what charset/collation the contracts.id field has
    cursor.execute("""
        SELECT COLUMN_NAME, COLUMN_TYPE, CHARACTER_SET_NAME, COLLATION_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'contracts'
        AND COLUMN_NAME = 'id'
    """)

    print("CONTRACTS.ID COLUMN:")
    for row in cursor.fetchall():
        print(f"  Column: {row[0]}")
        print(f"  Type: {row[1]}")
        print(f"  Charset: {row[2]}")
        print(f"  Collation: {row[3]}")
