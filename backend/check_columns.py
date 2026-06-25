import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SHOW COLUMNS FROM contract_risks")
    columns = cursor.fetchall()
    print("\nCOLUMNS IN contract_risks table:")
    for col in columns:
        print(f"  {col[0]} - {col[1]}")
