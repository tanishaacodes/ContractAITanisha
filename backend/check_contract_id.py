import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SHOW CREATE TABLE contracts")
    result = cursor.fetchone()
    print("\nCONTRACTS TABLE DEFINITION:")
    print(result[1])
