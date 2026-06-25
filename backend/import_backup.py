"""
Import data from SQL backup into Django database.
Following the backup import pattern from MEMORY.md.
"""
import os
import sys
import django
import re
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

# Read SQL backup
backup_path = r'C:\Users\Chiku\Downloads\contractai_backup (14).sql'
print(f"Reading backup from: {backup_path}")

with open(backup_path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Extract INSERT statements
pattern = r"INSERT INTO `([^`]+)` VALUES\s+(.*?);"
matches = re.findall(pattern, content, re.DOTALL)

print(f"\nFound {len(matches)} tables with data")

# Tables to import (excluding Django internal tables and tables that might conflict)
SKIP_TABLES = {
    'auth_permission',  # Django internal
    'django_content_type',  # Django internal
    'django_migrations',  # Django internal
    'auth_user',  # Django user model - might conflict
}

# Tables to import (high priority data)
PRIORITY_TABLES = [
    'contracts',
    'clauses',
    'clause_versions',
    'clause_risks',
    'clause_embeddings',
    'clause_events',
    'clause_health_metrics',
    'clause_intents',
    'intents',
    'legal_playbooks',
    'clause_playbook_results',
    'playbook_drift_snapshots',
    'playbook_update_suggestions',
    'negotiation_sessions',
    'negotiation_messages',
    'parties',
    'users',
    'counterparties',
    'contract_intelligence',
    'contract_graph_meta',
    'system_settings',
]

def import_table(table_name, values_str):
    """Import data for a single table."""
    cursor = connection.cursor()

    try:
        # Truncate table first (be careful!)
        print(f"  Truncating {table_name}...")
        cursor.execute(f"SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute(f"TRUNCATE TABLE `{table_name}`;")

        # Insert data
        print(f"  Inserting data into {table_name}...")
        sql = f"INSERT INTO `{table_name}` VALUES {values_str};"
        cursor.execute(sql)

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`;")
        count = cursor.fetchone()[0]
        print(f"  ✓ Imported {count} rows into {table_name}")

        cursor.execute(f"SET FOREIGN_KEY_CHECKS = 1;")
        return True, count

    except Exception as e:
        print(f"  ✗ Error importing {table_name}: {str(e)[:200]}")
        return False, 0
    finally:
        cursor.close()

# Main import
print("\n" + "=" * 80)
print("BACKUP IMPORT - Starting")
print("=" * 80)

# Create dict of all tables
all_tables = {table: values for table, values in matches}

# First, import priority tables
imported_count = 0
failed_count = 0
total_rows = 0

print("\n--- Phase 1: Importing Priority Tables ---")
for table_name in PRIORITY_TABLES:
    if table_name in all_tables and table_name not in SKIP_TABLES:
        success, rows = import_table(table_name, all_tables[table_name])
        if success:
            imported_count += 1
            total_rows += rows
        else:
            failed_count += 1

# Then import remaining tables
print("\n--- Phase 2: Importing Remaining Tables ---")
for table_name, values in all_tables.items():
    if table_name not in PRIORITY_TABLES and table_name not in SKIP_TABLES:
        success, rows = import_table(table_name, values)
        if success:
            imported_count += 1
            total_rows += rows
        else:
            failed_count += 1

# Summary
print("\n" + "=" * 80)
print("BACKUP IMPORT - Complete")
print("=" * 80)
print(f"Successfully imported: {imported_count} tables")
print(f"Failed: {failed_count} tables")
print(f"Total rows imported: {total_rows}")
print(f"Skipped (Django internal): {len(SKIP_TABLES)} tables")
print("=" * 80)
