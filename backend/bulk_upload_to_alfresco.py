"""
Bulk Upload Contracts to Alfresco
Uploads contracts from Django database to Alfresco CMS
"""
import os
import sys
import django
import requests
from pathlib import Path

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract
from django.conf import settings

# Alfresco Configuration
ALFRESCO_URL = getattr(settings, 'ALFRESCO_URL', 'http://localhost:8080/alfresco')
ALFRESCO_USER = getattr(settings, 'ALFRESCO_USER', 'admin')
ALFRESCO_PASSWORD = getattr(settings, 'ALFRESCO_PASSWORD', 'admin')
ALFRESCO_FOLDER_ID = getattr(settings, 'ALFRESCO_CONTRACTS_FOLDER', '-root-')


def authenticate_alfresco():
    """Authenticate with Alfresco and get session"""
    print("\n[1/4] Authenticating with Alfresco...")
    session = requests.Session()
    session.auth = (ALFRESCO_USER, ALFRESCO_PASSWORD)

    # Test connection
    try:
        test_url = f"{ALFRESCO_URL}/api/-default-/public/alfresco/versions/1/nodes/-root-"
        response = session.get(test_url, timeout=10)

        if response.status_code == 200:
            print(f"  [OK] Connected to Alfresco at {ALFRESCO_URL}")
            return session
        else:
            print(f"  [ERROR] Alfresco returned status {response.status_code}")
            print(f"  Response: {response.text}")
            return None
    except Exception as e:
        print(f"  [ERROR] Cannot connect to Alfresco: {e}")
        print("\n  Make sure Alfresco is running:")
        print("    docker run -p 8080:8080 alfresco/alfresco-content-repository-community")
        return None


def create_contracts_folder(session):
    """Create a dedicated folder for contracts if it doesn't exist"""
    print("\n[2/4] Setting up contracts folder...")

    try:
        # Create folder in root
        create_url = f"{ALFRESCO_URL}/api/-default-/public/alfresco/versions/1/nodes/-root-/children"

        folder_data = {
            "name": "Contracts",
            "nodeType": "cm:folder",
            "properties": {
                "cm:title": "Contract Documents",
                "cm:description": "AI-analyzed contract repository"
            }
        }

        response = session.post(
            create_url,
            json=folder_data,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code in [201, 409]:  # 201 Created, 409 Already Exists
            if response.status_code == 201:
                folder_id = response.json()['entry']['id']
                print(f"  [OK] Created Contracts folder: {folder_id}")
            else:
                # Folder already exists, get its ID
                list_url = f"{ALFRESCO_URL}/api/-default-/public/alfresco/versions/1/nodes/-root-/children"
                list_response = session.get(list_url)

                if list_response.status_code == 200:
                    entries = list_response.json().get('list', {}).get('entries', [])
                    contracts_folder = next(
                        (e for e in entries if e['entry']['name'] == 'Contracts'),
                        None
                    )

                    if contracts_folder:
                        folder_id = contracts_folder['entry']['id']
                        print(f"  [OK] Using existing Contracts folder: {folder_id}")
                    else:
                        print("  [WARN] Using root folder")
                        folder_id = '-root-'
                else:
                    folder_id = '-root-'

            return folder_id
        else:
            print(f"  [WARN] Could not create folder, using root. Status: {response.status_code}")
            return '-root-'

    except Exception as e:
        print(f"  [WARN] Error creating folder: {e}, using root")
        return '-root-'


def upload_contract_to_alfresco(session, contract, folder_id):
    """Upload a single contract to Alfresco"""
    try:
        # Get contract file path
        if not contract.file or not os.path.exists(contract.file.path):
            return {'status': 'error', 'error': 'File not found'}

        file_path = contract.file.path
        filename = contract.original_filename or os.path.basename(file_path)

        # Upload file
        upload_url = f"{ALFRESCO_URL}/api/-default-/public/alfresco/versions/1/nodes/{folder_id}/children"

        with open(file_path, 'rb') as f:
            files = {
                'filedata': (filename, f, 'application/octet-stream')
            }

            # Add metadata
            data = {
                'name': filename,
                'nodeType': 'cm:content',
                'properties': {
                    'cm:title': filename,
                    'cm:description': f'Risk Level: {contract.risk_level} | Contract ID: {contract.id}'
                }
            }

            # Use multipart/form-data for file upload
            response = session.post(
                upload_url,
                files=files,
                data={'properties': str(data)},
                timeout=30
            )

            if response.status_code == 201:
                node_id = response.json()['entry']['id']
                return {
                    'status': 'success',
                    'node_id': node_id,
                    'filename': filename
                }
            else:
                return {
                    'status': 'error',
                    'error': f'Upload failed: {response.status_code}'
                }

    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def bulk_upload(limit=100):
    """Upload contracts to Alfresco in bulk"""
    print("\n" + "="*60)
    print("BULK UPLOAD CONTRACTS TO ALFRESCO")
    print("="*60)

    # Authenticate
    session = authenticate_alfresco()
    if not session:
        print("\n[ERROR] Cannot proceed without Alfresco connection")
        return

    # Create/get contracts folder
    folder_id = create_contracts_folder(session)

    # Get contracts from database
    print(f"\n[3/4] Fetching {limit} contracts from database...")
    contracts = Contract.objects.filter(
        file__isnull=False
    ).exclude(
        file=''
    ).order_by('-created_at')[:limit]

    total_contracts = contracts.count()

    if total_contracts == 0:
        print("  [WARN] No contracts with files found in database")
        print("\n  Upload some contracts first:")
        print("    1. Go to http://localhost:5173/upload")
        print("    2. Upload contract PDFs/DOCX files")
        print("    3. Run this script again")
        return

    print(f"  [OK] Found {total_contracts} contracts to upload")

    # Upload contracts
    print(f"\n[4/4] Uploading contracts to Alfresco...")
    print(f"  Target folder: {folder_id}")
    print()

    success_count = 0
    error_count = 0

    for idx, contract in enumerate(contracts, 1):
        print(f"  [{idx}/{total_contracts}] {contract.original_filename or 'Unnamed'}...", end=' ')

        result = upload_contract_to_alfresco(session, contract, folder_id)

        if result['status'] == 'success':
            print(f"✓ OK (Node: {result['node_id'][:8]}...)")
            success_count += 1
        else:
            print(f"✗ FAILED: {result['error']}")
            error_count += 1

    # Summary
    print("\n" + "="*60)
    print("[COMPLETE] Upload Summary")
    print("="*60)
    print(f"  Total attempted: {total_contracts}")
    print(f"  Successful:      {success_count}")
    print(f"  Failed:          {error_count}")
    print()

    if success_count > 0:
        print(f"✓ {success_count} contracts uploaded to Alfresco!")
        print(f"\n  Access them at:")
        print(f"    {ALFRESCO_URL}/share/page/repository#filter=path|/Contracts")
        print(f"\n  Or sync them to your app:")
        print(f"    http://localhost:5173/alfresco-sync")

    print("="*60)


if __name__ == '__main__':
    import sys

    # Get limit from command line or use default
    limit = 100
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            print(f"Invalid limit: {sys.argv[1]}, using default 100")

    try:
        bulk_upload(limit)
    except KeyboardInterrupt:
        print("\n\n[WARN] Upload interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Upload failed: {e}")
        import traceback
        traceback.print_exc()
