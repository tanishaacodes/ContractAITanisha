import requests
import json
import time

# Wait for server to start
time.sleep(2)

BASE_URL = "http://localhost:8000/api"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImYzY2NmZmM1LTNhNjAtNGJhMi05MTVkLTQzZjJmMzgyZGU0ZSIsImVtYWlsIjoidGVzdF9hZG1pbkBleGFtcGxlLmNvbSIsImV4cCI6MTc2NDkzMDkyNSwiaWF0IjoxNzY0ODQ0NTI1fQ.CGw4Lc566WOpDhYIKQ0segUcsbfw07PM2rADHAxkoUM"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}"
}

print("=" * 60)
print("TEST 1: Create a new role - Finance Reviewer")
print("=" * 60)
try:
    response = requests.post(
        f"{BASE_URL}/admin/roles",
        json={
            "name": "Finance Reviewer",
            "description": "Can review financial contracts",
            "permissions": {}
        },
        headers=headers,
        timeout=5
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("TEST 2: Create another role - Compliance Officer")
print("=" * 60)
try:
    response = requests.post(
        f"{BASE_URL}/admin/roles",
        json={
            "name": "Compliance Officer",
            "description": "Ensures compliance with regulations",
            "permissions": {}
        },
        headers=headers,
        timeout=5
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("TEST 3: Try to create duplicate role (should fail)")
print("=" * 60)
try:
    response = requests.post(
        f"{BASE_URL}/admin/roles",
        json={
            "name": "Finance Reviewer",
            "description": "Duplicate role",
            "permissions": {}
        },
        headers=headers,
        timeout=5
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("TEST 4: List all roles")
print("=" * 60)
try:
    response = requests.get(
        f"{BASE_URL}/admin/roles",
        headers=headers,
        timeout=5
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("TEST 5: Create role with missing name (should fail)")
print("=" * 60)
try:
    response = requests.post(
        f"{BASE_URL}/admin/roles",
        json={
            "description": "Role without name",
            "permissions": {}
        },
        headers=headers,
        timeout=5
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

print("\nAll tests completed!")
