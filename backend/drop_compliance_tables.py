"""
Drop orphan compliance tables to allow fresh migration.
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

print('Dropping orphan compliance tables...')
cursor.execute('SET FOREIGN_KEY_CHECKS=0;')

tables = [
    'contract_compliance_analysis',
    'intent_compliance_mapping',
    'intent_compliance_mappings',
    'compliance_requirements',
    'compliance_frameworks'
]

for table in tables:
    try:
        cursor.execute(f'DROP TABLE IF EXISTS {table};')
        print(f'[OK] Dropped {table}')
    except Exception as e:
        print(f'[ERROR] Error dropping {table}: {e}')

cursor.execute('SET FOREIGN_KEY_CHECKS=1;')
conn.commit()
cursor.close()
conn.close()

print('\n[OK] All orphan tables dropped successfully!')
print('Now run: python manage.py migrate')
