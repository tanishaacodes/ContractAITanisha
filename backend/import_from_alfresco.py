"""
Import Contracts from Alfresco to Database
Fetches contracts from Alfresco and creates new database records
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, User
from django.core.files.base import ContentFile
from api.alfresco_service import AlfrescoExtractor
import requests

ALFRESCO_URL = 'http://localhost:8080/alfresco'
ALFRESCO_USER = 'admin'
ALFRESCO_PASSWORD = 'admin'


def get_contracts_folder_id():
    """Find the Contracts folder ID"""
    print("\n[1/4] Finding Contracts folder...")
    session = requests.Session()
    session.auth = (ALFRESCO_USER, ALFRESCO_PASSWORD)

    try:
        list_url = f"{ALFRESCO_URL}/api/-default-/public/alfresco/versions/1/nodes/-root-/children"
        response = session.get(list_url)

        if response.status_code == 200:
            entries = response.json().get('list', {}).get('entries', [])
            for item in entries:
                entry = item.get('entry', {})
                if entry.get('name') == 'Contracts' and entry.get('isFolder', False):
                    folder_id = entry.get('id')
                    print(f"  [OK] Found Contracts folder: {folder_id}")
                    return folder_id

        print("  [WARN] Contracts folder not found, using root")
        return '-root-'
    except Exception as e:
        print(f"  [ERROR] {e}")
        return '-root-'


def fetch_contracts_from_alfresco(folder_id):
    """Fetch all contracts from Alfresco folder"""
    print(f"\n[2/4] Fetching contracts from Alfresco...")
    session = requests.Session()
    session.auth = (ALFRESCO_USER, ALFRESCO_PASSWORD)

    contracts = []

    try:
        list_url = f"{ALFRESCO_URL}/api/-default-/public/alfresco/versions/1/nodes/{folder_id}/children"
        response = session.get(list_url)

        if response.status_code == 200:
            entries = response.json().get('list', {}).get('entries', [])

            for item in entries:
                entry = item.get('entry', {})

                # Only process files
                if entry.get('isFile', False):
                    node_id = entry.get('id')
                    filename = entry.get('name', 'Unknown')

                    # Download content
                    content_url = f"{ALFRESCO_URL}/api/-default-/public/alfresco/versions/1/nodes/{node_id}/content"
                    content_response = session.get(content_url)

                    if content_response.status_code == 200:
                        contracts.append({
                            'filename': filename,
                            'content': content_response.content,
                            'size': len(content_response.content),
                            'node_id': node_id
                        })

            print(f"  [OK] Found {len(contracts)} contracts in Alfresco")
            return contracts
        else:
            print(f"  [ERROR] Failed to list folder: {response.status_code}")
            return []

    except Exception as e:
        print(f"  [ERROR] {e}")
        return []


def import_to_database(contracts):
    """Import contracts into database"""
    print(f"\n[3/4] Importing {len(contracts)} contracts to database...")

    # Get or create user
    try:
        user = User.objects.first()
        if not user:
            user = User.objects.create(
                email='admin@example.com',
                password='admin',
                role_id=1
            )
            print("  [INFO] Created new user")
        print(f"  [INFO] Using user: {user.email}")
    except Exception as e:
        print(f"  [ERROR] User setup failed: {e}")
        return 0, 0

    success_count = 0
    error_count = 0

    for idx, contract_data in enumerate(contracts, 1):
        filename = contract_data['filename']
        print(f"  [{idx}/{len(contracts)}] {filename}...", end=' ')

        try:
            # Check if already exists
            if Contract.objects.filter(original_filename=filename, user_id=user.id).exists():
                print("[SKIP] Already exists")
                continue

            # Determine file extension
            ext = filename.split('.')[-1].lower() if '.' in filename else 'txt'

            # Create contract
            contract = Contract.objects.create(
                user_id=user.id,
                original_filename=filename,
                filename=filename,
                full_text=contract_data['content'].decode('utf-8', errors='ignore'),
                status='active'
            )

            print(f"[OK] Imported ({str(contract.id)[:8]}...)")
            success_count += 1

        except Exception as e:
            print(f"[FAIL] {str(e)}")
            import traceback
            if idx == 1:  # Print full traceback for first error only
                traceback.print_exc()
            error_count += 1

    return success_count, error_count


def import_from_alfresco():
    """Main import function"""
    print("\n" + "="*60)
    print("IMPORT CONTRACTS FROM ALFRESCO TO DATABASE")
    print("="*60)

    # Find Contracts folder
    folder_id = get_contracts_folder_id()

    # Fetch contracts
    contracts = fetch_contracts_from_alfresco(folder_id)

    if not contracts:
        print("\n[ERROR] No contracts found in Alfresco")
        print("\nMake sure:")
        print("  1. Alfresco is running on port 8080")
        print("  2. Contracts folder exists with documents")
        return

    # Import to database
    success, failed = import_to_database(contracts)

    # Summary
    print("\n[4/4] Summary")
    print("="*60)
    print(f"  Total contracts found: {len(contracts)}")
    print(f"  Successfully imported: {success}")
    print(f"  Failed: {failed}")
    print(f"  Skipped (duplicates): {len(contracts) - success - failed}")
    print()

    if success > 0:
        print(f"[OK] {success} contracts imported!")
        print(f"\n  View them at:")
        print(f"    http://localhost:5173/contracts")
        print(f"\n  Next steps:")
        print(f"    - Contracts will be analyzed automatically")
        print(f"    - Risk scores will be calculated")
        print(f"    - Full text extraction will run in background")

    print("="*60)


if __name__ == '__main__':
    try:
        import_from_alfresco()
    except KeyboardInterrupt:
        print("\n\n[WARN] Import interrupted")
    except Exception as e:
        print(f"\n\n[ERROR] Import failed: {e}")
        import traceback
        traceback.print_exc()
