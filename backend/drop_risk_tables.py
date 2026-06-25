import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from django.db import connection

tables_to_drop = [
    'vendor_exposures',
    'cross_contract_correlations',
    'clause_risks',
    'contract_risks',
    'risk_nodes',
    'party_partitions',
    'parties'
]

with connection.cursor() as cursor:
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    for table in tables_to_drop:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"Dropped table: {table}")
        except Exception as e:
            print(f"Error dropping {table}: {e}")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    print("\nAll risk tables dropped successfully!")
