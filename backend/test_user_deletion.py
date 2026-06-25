import requests
import json

BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "vansh123"

print("=" * 70)
print("TESTING USER DELETION ENDPOINT")
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

# Find a non-admin user to delete
test_user = None
for user in users:
    if user.get('role', {}).get('name') != 'Admin':
        test_user = user
        break

if not test_user:
    print("[SKIP] No non-admin user available to test deletion")
    exit()

test_user_id = test_user.get('id')
test_user_email = test_user.get('email')
print(f"\n[OK] Found test user: {test_user_email} (ID: {test_user_id})")

# Step 3: Test user deletion
print("\n[3] Testing User Deletion...")
print(f"Attempting to DELETE /admin/users/{test_user_id}")

delete_response = requests.delete(
    f"{BASE_URL}/admin/users/{test_user_id}",
    headers=headers,
    timeout=5
)

print(f"Status: {delete_response.status_code}")
print(f"Response: {json.dumps(delete_response.json(), indent=2)}")

if delete_response.status_code == 200:
    print(f"\n[OK] User deletion successful!")

    # Step 4: Verify user is deleted
    print("\n[4] Verifying User Deletion...")
    users_response = requests.get(
        f"{BASE_URL}/admin/users",
        headers=headers,
        timeout=5
    )

    users_data = users_response.json()
    users = users_data.get('users', [])

    user_still_exists = any(u.get('id') == test_user_id for u in users)

    if not user_still_exists:
        print(f"[OK] User {test_user_email} has been successfully removed from the system!")
    else:
        print(f"[ERROR] User {test_user_email} still exists in the system!")
else:
    print(f"\n[FAIL] User deletion failed with status {delete_response.status_code}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
