"""
Show CREATE TABLE for contracts
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SHOW CREATE TABLE contracts")
    result = cursor.fetchone()
    print("\nCREATE TABLE statement for contracts:")
    print("="*70)
    print(result[1])
