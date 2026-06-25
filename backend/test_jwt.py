import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')

import django
django.setup()

from django.conf import settings
import jwt

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjYyYzI3MzBhLTFhYWMtNDgwZS04YTdkLTY2ZGUzMThlOWE4NyIsImVtYWlsIjoidGVzdHVzZXIxNzY0Nzc3MTEzQGV4YW1wbGUuY29tIiwiZXhwIjoxNzY0ODYzNTE0LCJpYXQiOjE3NjQ3NzcxMTR9.HoA2KlCWiA2Iwk2pJmERJzyPC7SaTQtX6DLtDjKmzzs"

print(f"JWT_SECRET: {settings.JWT_SECRET}")
print(f"JWT_ALGORITHM: {settings.JWT_ALGORITHM}")
print(f"Token: {token[:50]}...")

try:
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    print(f"Successfully decoded! Payload: {payload}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
