"""
Add missing columns to intent_compliance_mappings table.
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

print('Adding missing columns to intent_compliance_mappings...')

columns_to_add = [
    ('detectedAt', """
        ALTER TABLE intent_compliance_mappings
        ADD COLUMN detectedAt DATETIME NULL
        AFTER riskScore
    """),
    ('lastReviewedAt', """
        ALTER TABLE intent_compliance_mappings
        ADD COLUMN lastReviewedAt DATETIME NULL
        AFTER detectedAt
    """),
    ('reviewedBy', """
        ALTER TABLE intent_compliance_mappings
        ADD COLUMN reviewedBy CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL
        AFTER lastReviewedAt,
        ADD CONSTRAINT intent_compliance_mappings_reviewedBy_fk
            FOREIGN KEY (reviewedBy)
            REFERENCES users(id)
            ON DELETE SET NULL
    """),
]

for column_name, alter_sql in columns_to_add:
    try:
        # Check if column already exists
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = 'intent_compliance_mappings'
            AND COLUMN_NAME = %s
        """, (db_config['NAME'], column_name))

        if cursor.fetchone():
            print(f'[INFO] {column_name} column already exists. Skipping.')
        else:
            cursor.execute(alter_sql)
            conn.commit()
            print(f'[OK] {column_name} column added successfully!')

    except MySQLdb.Error as e:
        print(f'[ERROR] Failed to add {column_name}: {e}')
        conn.rollback()

cursor.close()
conn.close()

print('\nDone!')
