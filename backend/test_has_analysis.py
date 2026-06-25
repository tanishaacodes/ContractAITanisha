import requests
import json

BASE_URL = 'http://localhost:8000'
API_URL = f'{BASE_URL}/api'

EMAIL = 'admin@example.com'
PASSWORD = 'admin123'

print("=" * 70)
print("Testing has_analysis Field in Contracts")
print("=" * 70)

# Login
print("\n1. Logging in...")
response = requests.post(f'{API_URL}/auth/login', json={'email': EMAIL, 'password': PASSWORD})
token = response.json().get('token')
print(f"   [OK] Login successful!")

# Get contracts
print("\n2. Getting contracts list...")
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(f'{API_URL}/contracts/list', headers=headers)

if response.status_code == 200:
    result = response.json()
    contracts = result.get('contracts', [])
    print(f"   [OK] Found {len(contracts)} contracts")

    # Analyze contracts
    analyzed_count = sum(1 for c in contracts if c.get('has_analysis') == True)
    pending_count = sum(1 for c in contracts if c.get('has_analysis') == False)

    print(f"\n   Breakdown:")
    print(f"   - Analyzed (has_analysis=True):  {analyzed_count}")
    print(f"   - Pending (has_analysis=False):  {pending_count}")

    print(f"\n3. Sample contracts with has_analysis field:")
    for i, contract in enumerate(contracts[:3], 1):
        has_analysis = contract.get('has_analysis')
        status = "ANALYZED" if has_analysis == True else "PENDING" if has_analysis == False else "UNKNOWN"
        print(f"   {i}. {contract.get('original_filename')[:40]:<40} | {status:>10} | has_analysis={has_analysis}")

else:
    print(f"   [ERROR] Failed: {response.status_code}")
    print(f"   Response: {response.text}")

print("\n" + "=" * 70)
print("Test complete!")
print("=" * 70)
