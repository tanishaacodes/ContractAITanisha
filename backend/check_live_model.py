"""Check which model is active in the RUNNING Django server"""
import requests

# Call the running server (no auth for test)
url = "http://localhost:8002/api/embedding-model/"

print("=" * 60)
print("CHECKING RUNNING SERVER (port 8002)")
print("=" * 60)

# First login to get token
login_response = requests.post(
    "http://localhost:8002/api/auth/login",
    json={"email": "kodandaram@gmail.com", "password": "pass"}
)

if login_response.status_code == 200:
    token = login_response.json()['access']

    # Now check embedding model
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"\nActive Model: {data['current_model']}")
        print(f"Model Name: {data['models'][0]['label'] if data['current_model'] == data['models'][0]['key'] else data['models'][1]['label']}")
        print(f"Dimensions: {data['dimensions']}")
        print()
        print("Available models:")
        for model in data['models']:
            status = "✓ ACTIVE" if model['is_active'] else "  inactive"
            print(f"  [{status}] {model['label']} ({model['dimensions']}-dim)")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
else:
    print(f"Login failed: {login_response.status_code}")
    print(login_response.text)

print("=" * 60)
