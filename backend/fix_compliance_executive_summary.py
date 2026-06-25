"""
Add missing executiveSummary column to contract_compliance_analysis table.
"""
import MySQLdb
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from django.conf import settings

db_config = settings.DATABASES['default']

conn = MySQLdb.connect(
    host=db_config['HOST'],
    user=db_config['USER'],
    password=db_config['PASSWORD'],
    database=db_config['NAME']
)

cursor = conn.cursor()

print('Adding missing executiveSummary column...')

try:
    # Check if column already exists
    cursor.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s
        AND TABLE_NAME = 'contract_compliance_analysis'
        AND COLUMN_NAME = 'executiveSummary'
    """, (db_config['NAME'],))

    if cursor.fetchone():
        print('[INFO] executiveSummary column already exists. Nothing to do.')
    else:
        # Add the column
        cursor.execute("""
            ALTER TABLE contract_compliance_analysis
            ADD COLUMN executiveSummary TEXT NULL
            AFTER lowViolations
        """)
        conn.commit()
        print('[OK] executiveSummary column added successfully!')

except MySQLdb.Error as e:
    print(f'[ERROR] Failed to add column: {e}')
    conn.rollback()

finally:
    cursor.close()
    conn.close()

print('\nDone!')
