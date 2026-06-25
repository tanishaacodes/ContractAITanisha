import requests
import json

BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "vansh123"

print("=" * 70)
print("TESTING ROLE ASSIGNMENT")
print("=" * 70)

# Step 1: Login
print("\n[1] Testing Admin Login...")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    timeout=5
)

if login_response.status_code == 200:
    token = login_response.json().get('token')
    print(f"[OK] Login successful!")
else:
    print(f"[FAIL] Login failed!")
    exit()

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

# Step 2: Get users list
print("\n[2] Fetching Users List...")
users_response = requests.get(
    f"{BASE_URL}/admin/users",
    headers=headers,
    timeout=5
)

users_data = users_response.json()
users = users_data.get('users', [])
print(f"Found {len(users)} users")

# Find a non-admin user
test_user = None
for user in users:
    if user.get('role', {}).get('name') != 'Admin':
        test_user = user
        break

if not test_user:
    print("[ERROR] No non-admin user available for testing")
    exit()

test_user_id = test_user.get('id')
test_user_email = test_user.get('email')
current_role = test_user.get('role', {}).get('name')
print(f"\n[OK] Found test user: {test_user_email}")
print(f"     Current role: {current_role}")

# Step 3: Get available roles
print("\n[3] Fetching Available Roles...")
roles_response = requests.get(
    f"{BASE_URL}/admin/roles",
    headers=headers,
    timeout=5
)

roles_data = roles_response.json()
roles = roles_data.get('roles', [])
print(f"Found {len(roles)} available roles:")

for role in roles:
    role_name = role.get('name')
    print(f"  - {role_name}")

# Find a different role to assign
new_role = None
for role in roles:
    if role.get('name') != current_role and role.get('name') != 'Admin':
        new_role = role
        break

if not new_role:
    print("[SKIP] No suitable role available for testing")
    exit()

new_role_name = new_role.get('name')
print(f"\n[OK] Will test assigning role: {new_role_name}")

# Step 4: Try to assign the role
print("\n[4] Testing Role Assignment...")
print(f"Attempting to POST /admin/users/{test_user_id}/role")
print(f"With payload: {{'role': '{new_role_name}'}}")

update_response = requests.post(
    f"{BASE_URL}/admin/users/{test_user_id}/role",
    json={"role": new_role_name},
    headers=headers,
    timeout=5
)

print(f"\nStatus: {update_response.status_code}")
response_json = update_response.json()
print(f"Response: {json.dumps(response_json, indent=2)}")

if update_response.status_code == 200:
    print(f"\n[OK] Role assignment successful!")
    updated_user = response_json.get('user', {})
    print(f"Updated user role: {updated_user.get('role', {}).get('name')}")
else:
    print(f"\n[FAIL] Role assignment failed!")
    print(f"Error message: {response_json.get('message')}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
