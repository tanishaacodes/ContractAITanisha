"""
Add has_arbitration column to contracts table if it doesn't exist
"""
import os
import django
import MySQLdb

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from django.conf import settings

# Connect to database
db_settings = settings.DATABASES['default']
conn = MySQLdb.connect(
    host=db_settings['HOST'],
    user=db_settings['USER'],
    passwd=db_settings['PASSWORD'],
    db=db_settings['NAME']
)

cursor = conn.cursor()

# Check if column exists
cursor.execute("""
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = %s
    AND TABLE_NAME = 'contracts'
    AND COLUMN_NAME = 'hasArbitration'
""", (db_settings['NAME'],))

column_exists = cursor.fetchone()[0] > 0

if not column_exists:
    print("Adding hasArbitration column to contracts table...")
    cursor.execute("""
        ALTER TABLE contracts
        ADD COLUMN hasArbitration TINYINT(1) NOT NULL DEFAULT 0
        AFTER liabilityLevel
    """)
    conn.commit()
    print("Column added successfully!")
else:
    print("Column already exists, skipping...")

cursor.close()
conn.close()
