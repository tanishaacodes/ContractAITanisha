import requests

BASE_URL = 'http://localhost:8000'
API_URL = f'{BASE_URL}/api'

EMAIL = 'admin@example.com'
PASSWORD = 'admin123'

print("=" * 60)
print("Testing Clause Extraction")
print("=" * 60)

# Step 1: Login
print("\n1. Logging in...")
response = requests.post(
    f'{API_URL}/auth/login',
    json={'email': EMAIL, 'password': PASSWORD}
)

if response.status_code != 200:
    print(f"   [ERROR] Login failed: {response.status_code}")
    print(f"   Response: {response.text}")
    exit(1)

token = response.json().get('token')
print(f"   [OK] Login successful!")

# Step 2: Get list of contracts
print("\n2. Getting contracts...")
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(f'{API_URL}/contracts/list', headers=headers)

if response.status_code != 200:
    print(f"   [ERROR] Failed to get contracts: {response.status_code}")
    exit(1)

contracts = response.json().get('contracts', [])
print(f"   Found {len(contracts)} contracts")

if len(contracts) == 0:
    print("   No contracts found. Please upload a contract first.")
    exit(0)

# Use the first contract
contract = contracts[0]
contract_id = contract['id']
print(f"   Using contract: {contract.get('original_filename', 'Unknown')}")
print(f"   Contract ID: {contract_id}")

# Step 3: Extract clauses
print("\n3. Extracting clauses...")
response = requests.post(
    f'{API_URL}/contracts/{contract_id}/extract-clauses',
    headers=headers
)

print(f"   Status Code: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print(f"   [OK] Clause extraction successful!")
    print(f"\n   Results:")
    print(f"   - Total clauses found: {result.get('found_count', 0)}")
    print(f"   - Total clauses checked: {result.get('total_count', 0)}")

    if result.get('clauses'):
        print(f"\n   Top 5 found clauses:")
        for i, clause in enumerate(result.get('clauses', [])[:5], 1):
            if clause.get('found'):
                print(f"   {i}. {clause.get('clause_name')} - {clause.get('confidence')}% confidence")
else:
    print(f"   [ERROR] Clause extraction failed!")
    print(f"   Response: {response.text}")

# Step 4: Get clauses
print("\n4. Getting extracted clauses...")
response = requests.get(
    f'{API_URL}/contracts/{contract_id}/clauses',
    headers=headers
)

print(f"   Status Code: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    clauses = result.get('clauses', [])
    print(f"   [OK] Got {len(clauses)} clauses from database")

    if clauses:
        print(f"\n   Sample clause:")
        clause = clauses[0]
        print(f"   - Name: {clause.get('clause_name')}")
        print(f"   - Found: {clause.get('found')}")
        print(f"   - Confidence: {clause.get('confidence')}%")
        print(f"   - Match count: {clause.get('match_count')}")
else:
    print(f"   [ERROR] Failed to get clauses!")
    print(f"   Response: {response.text}")

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)
