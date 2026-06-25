import requests
import json
import time

BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "vansh123"

print("=" * 70)
print("DIAGNOSING CONTRACTAI ISSUES")
print("=" * 70)

# Step 1: Login
print("\n[1] Testing Admin Login...")
try:
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=5
    )
    print(f"Status: {login_response.status_code}")
    print(f"Response: {json.dumps(login_response.json(), indent=2)}")

    if login_response.status_code == 200:
        token = login_response.json().get('token')
        print(f"\n[OK] Login successful! Token: {token[:50]}...")
    else:
        print(f"[FAIL] Login failed!")
        token = None
except Exception as e:
    print(f"[ERROR] Error: {e}")
    token = None

if not token:
    print("\nCannot continue without token. Exiting...")
    exit()

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

# Step 2: Get Users List
print("\n" + "=" * 70)
print("[2] Fetching Users List...")
print("=" * 70)
try:
    users_response = requests.get(
        f"{BASE_URL}/admin/users",
        headers=headers,
        timeout=5
    )
    print(f"Status: {users_response.status_code}")
    users_data = users_response.json()
    print(f"Response: {json.dumps(users_data, indent=2)}")

    users = users_data.get('users', [])
    print(f"\nFound {len(users)} users")
    for i, user in enumerate(users[:3], 1):
        print(f"\n  User {i}:")
        print(f"    - Email: {user.get('email')}")
        print(f"    - Role: {user.get('role', {}).get('name') if isinstance(user.get('role'), dict) else user.get('role')}")
        print(f"    - Is Active: {user.get('is_active')}")
        print(f"    - Last Login: {user.get('last_login')}")
        print(f"    - First Name: {user.get('first_name')}")
        print(f"    - Last Name: {user.get('last_name')}")

except Exception as e:
    print(f"[ERROR] Error fetching users: {e}")

# Step 3: Get Roles List
print("\n" + "=" * 70)
print("[3] Fetching Roles List...")
print("=" * 70)
try:
    roles_response = requests.get(
        f"{BASE_URL}/admin/roles",
        headers=headers,
        timeout=5
    )
    print(f"Status: {roles_response.status_code}")
    roles_data = roles_response.json()
    roles = roles_data.get('roles', [])
    print(f"Found {len(roles)} roles:")
    for role in roles:
        print(f"\n  - {role['name']}")
        print(f"    ID: {role['id']}")
        print(f"    Description: {role.get('description', 'N/A')}")

except Exception as e:
    print(f"[ERROR] Error fetching roles: {e}")

# Step 4: Test Creating a Custom Role
print("\n" + "=" * 70)
print("[4] Testing Custom Role Creation...")
print("=" * 70)
try:
    custom_role = {
        "name": "Test Delete Role",
        "description": "This role should be deletable",
        "permissions": {}
    }
    create_response = requests.post(
        f"{BASE_URL}/admin/roles",
        json=custom_role,
        headers=headers,
        timeout=5
    )
    print(f"Status: {create_response.status_code}")
    print(f"Response: {json.dumps(create_response.json(), indent=2)}")

    if create_response.status_code == 201:
        created_role = create_response.json().get('role')
        role_id = created_role.get('id')
        print(f"\n[OK] Role created with ID: {role_id}")

        # Step 5: Test Deleting the Role
        print("\n" + "=" * 70)
        print("[5] Testing Role Deletion...")
        print("=" * 70)
        time.sleep(1)

        delete_response = requests.delete(
            f"{BASE_URL}/admin/roles/{role_id}",
            headers=headers,
            timeout=5
        )
        print(f"Status: {delete_response.status_code}")
        print(f"Response: {json.dumps(delete_response.json(), indent=2)}")

except Exception as e:
    print(f"[ERROR] {e}")

print("\n" + "=" * 70)
print("DIAGNOSIS COMPLETE")
print("=" * 70)
