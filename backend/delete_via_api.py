import requests

# API configuration
API_URL = "http://localhost:8002/api/contracts/bulk-delete"
TOKEN = None

# Get token from storage if needed
try:
    with open('../frontend/token.txt', 'r') as f:
        TOKEN = f.read().strip()
except:
    pass

# Contract IDs to delete
contract_ids = [
    '907d5284-5aaa-4573-b19a-6557377dbc0d',
    '8004e173-68cc-45ad-b55b-89416c0b26d7',
    '16ee2025-0bc6-428e-84e5-492b5bb37ac9',
    '206dc5f3-da37-4944-afb4-358947cbadce',
    '8b92b0b4-3671-4dc8-8208-3d4ed708c0b4',
    'ccd031e5-19bb-404e-b178-b63b041495c5'
]

print(f"Deleting {len(contract_ids)} contracts...")

# Try without authentication first (if API allows)
try:
    response = requests.post(
        API_URL,
        json={"contract_ids": contract_ids}
    )
    if response.status_code in [200, 204]:
        print(f"Successfully deleted {len(contract_ids)} contracts!")
        print(response.json() if response.text else "Deletion complete")
    else:
        print(f"Failed: {response.status_code} - {response.text}")
except Exception as e:
    print(f"Error: {e}")
