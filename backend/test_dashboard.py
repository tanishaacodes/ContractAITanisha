import requests

BASE_URL = 'http://localhost:8000'
API_URL = f'{BASE_URL}/api'

EMAIL = 'admin@example.com'
PASSWORD = 'admin123'

print("=" * 60)
print("Testing Dashboard Stats")
print("=" * 60)

# Step 1: Login
print("\n1. Logging in...")
response = requests.post(
    f'{API_URL}/auth/login',
    json={'email': EMAIL, 'password': PASSWORD}
)

if response.status_code != 200:
    print(f"   [ERROR] Login failed: {response.status_code}")
    exit(1)

token = response.json().get('token')
print(f"   [OK] Login successful!")

# Step 2: Get dashboard stats
print("\n2. Getting dashboard stats...")
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(f'{API_URL}/dashboard/stats', headers=headers)

print(f"   Status Code: {response.status_code}")

if response.status_code == 200:
    stats = response.json()
    print(f"   [OK] Dashboard stats retrieved!")
    print(f"\n   Dashboard Statistics:")
    print(f"   ---------------------")
    print(f"   Total Contracts:     {stats.get('totalContracts', 0)}")
    print(f"   Analysis Complete:   {stats.get('analysisComplete', 0)}")
    print(f"   Pending Review:      {stats.get('pendingReview', 0)}")
    print(f"   Risk Score Average:  {stats.get('riskScoreAvg', 0)}")
else:
    print(f"   [ERROR] Failed to get dashboard stats!")
    print(f"   Response: {response.text}")

# Step 3: Get contracts list for verification
print("\n3. Getting contracts list for verification...")
response = requests.get(f'{API_URL}/contracts/list', headers=headers)

if response.status_code == 200:
    result = response.json()
    contracts = result.get('contracts', [])
    print(f"   [OK] Found {len(contracts)} contracts in database")

    if contracts:
        print(f"\n   Sample contracts:")
        for i, contract in enumerate(contracts[:3], 1):
            print(f"   {i}. {contract.get('original_filename')} - Type: {contract.get('contract_type')}, Score: {contract.get('confidence_score')}")

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)
