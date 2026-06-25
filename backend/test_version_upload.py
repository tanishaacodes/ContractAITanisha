"""
Test script for uploading contract versions

This demonstrates how to upload a new version of an existing contract
"""

import requests

# Configuration
BASE_URL = "http://localhost:8002/api"
CONTRACT_ID = "your-contract-id-here"  # Replace with actual contract ID
TOKEN = "your-jwt-token-here"  # Replace with actual JWT token

def upload_new_version(contract_id, file_path, change_description="Version 2"):
    """
    Upload a new version of an existing contract

    Args:
        contract_id: UUID of the existing contract
        file_path: Path to the new version file (PDF, DOCX, etc.)
        change_description: Optional description of what changed
    """

    url = f"{BASE_URL}/contracts/{contract_id}/versions/upload"

    headers = {
        'Authorization': f'Bearer {TOKEN}'
    }

    # Prepare file and data
    with open(file_path, 'rb') as f:
        files = {
            'file': f
        }
        data = {
            'changeDescription': change_description
        }

        print(f"Uploading new version for contract {contract_id}...")
        print(f"File: {file_path}")
        print(f"Change description: {change_description}")

        response = requests.post(url, headers=headers, files=files, data=data)

    if response.status_code == 201:
        result = response.json()
        print("\n✅ SUCCESS! New version uploaded")
        print(f"\nVersion Info:")
        print(f"  Version Number: {result['version']['versionNumber']}")
        print(f"  Total Versions: {result['versionHistory']['totalVersions']}")
        print(f"  Processing Time: {result['processingTime']}s")
        print(f"\nContract Info:")
        print(f"  ID: {result['contract']['id']}")
        print(f"  Filename: {result['contract']['originalFilename']}")
        print(f"  Type: {result['contract']['contractType']}")

        print(f"\n✨ Intent drift detection has been automatically triggered!")
        print(f"   Check the Intent Drift tab to see changes between versions")

        return result
    else:
        print(f"\n❌ ERROR: {response.status_code}")
        print(response.json())
        return None


def get_version_history(contract_id):
    """Get all versions of a contract"""

    url = f"{BASE_URL}/contracts/{contract_id}/versions"

    headers = {
        'Authorization': f'Bearer {TOKEN}'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        result = response.json()
        print(f"\n📋 Version History for Contract {contract_id}")
        print(f"Total Versions: {result['totalVersions']}")
        print(f"Current Version: {result['currentVersion']}")
        print("\nVersions:")
        for version in result['versions']:
            print(f"  v{version['versionNumber']} - {version['changeDescription']}")
            print(f"    Created: {version['createdAt']}")
            print(f"    By: {version.get('createdBy', 'Unknown')}")
        return result
    else:
        print(f"❌ ERROR: {response.status_code}")
        print(response.json())
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("CONTRACT VERSION UPLOAD TEST")
    print("=" * 60)

    # Example usage:
    # 1. First, get your contract ID and JWT token
    # 2. Update the CONTRACT_ID and TOKEN variables above
    # 3. Prepare a modified version of your contract file
    # 4. Run this script

    print("\n⚠️  Before running this test:")
    print("1. Update CONTRACT_ID with your actual contract UUID")
    print("2. Update TOKEN with your JWT token from login")
    print("3. Update the file_path in the upload_new_version() call")
    print("\nExample:")
    print('  CONTRACT_ID = "123e4567-e89b-12d3-a456-426614174000"')
    print('  TOKEN = "eyJhbGci..."')
    print('  upload_new_version(CONTRACT_ID, "path/to/modified_contract.pdf", "Updated payment terms")')
    print("\n" + "=" * 60)

    # Uncomment and modify these lines to test:
    # upload_new_version(CONTRACT_ID, "modified_contract.pdf", "Updated payment terms")
    # get_version_history(CONTRACT_ID)
