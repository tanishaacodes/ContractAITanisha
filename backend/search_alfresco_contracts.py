"""
Search for specific contracts in Alfresco and restore them
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from api.alfresco_service import AlfrescoExtractor


def search_alfresco_contracts():
    """Search Alfresco for the user's original contracts"""
    print("\n" + "="*60)
    print("SEARCH ALFRESCO FOR ORIGINAL CONTRACTS")
    print("="*60)

    # Initialize Alfresco extractor
    extractor = AlfrescoExtractor()

    # Get all contracts from Alfresco
    print("\n[INFO] Fetching contracts from Alfresco...")

    raw_contracts = []

    # Search Contracts folder
    try:
        list_url = f"{extractor.base_url}/api/-default-/public/alfresco/versions/1/nodes/-root-/children"
        response = extractor.session.get(list_url)
        if response.status_code == 200:
            entries = response.json().get('list', {}).get('entries', [])
            for item in entries:
                entry = item.get('entry', {})
                if entry.get('name') == 'Contracts' and entry.get('isFolder', False):
                    contracts_folder_id = entry.get('id')
                    print(f"[INFO] Found Contracts folder: {contracts_folder_id}")
                    contracts_folder_docs = extractor.get_all_contracts(folder_id=contracts_folder_id)
                    raw_contracts.extend(contracts_folder_docs)
                    print(f"[INFO] Found {len(contracts_folder_docs)} contracts in Contracts folder")
                    break
    except Exception as e:
        print(f"[ERROR] Failed to fetch from Contracts folder: {e}")

    # Also search Shared folder
    try:
        shared_folder_id = "fdedbf0c-69e1-490f-beb1-7dc2a79e955c"
        shared_contracts = extractor.get_all_contracts(folder_id=shared_folder_id)
        raw_contracts.extend(shared_contracts)
        print(f"[INFO] Found {len(shared_contracts)} contracts in Shared folder")
    except Exception as e:
        print(f"[ERROR] Failed to fetch from Shared folder: {e}")

    print(f"\n[INFO] Total contracts found in Alfresco: {len(raw_contracts)}")

    # Search for the specific contracts
    search_patterns = [
        ('High_Risk', 'High Risk Construction'),
        ('SOFTWARE', 'Software Development'),
        ('MANUFACTURING', 'Manufacturing Agreement'),
        ('EXCLUSIVE', 'Exclusive Distribution'),
        ('COMMERCIAL', 'Commercial Lease')
    ]

    found_contracts = []
    print("\n[INFO] Searching for your original contracts:")

    for pattern, display_name in search_patterns:
        matches = [c for c in raw_contracts if pattern.lower() in c['name'].lower()]
        if matches:
            print(f"  + Found {len(matches)} match(es) for '{display_name}':")
            for match in matches[:3]:  # Show first 3 matches
                print(f"    - {match['name']}")
                found_contracts.append(match)
        else:
            print(f"  - No matches for '{display_name}'")

    if found_contracts:
        print(f"\n[SUCCESS] Found {len(found_contracts)} matching contracts in Alfresco!")
        print("\n[NEXT STEP] Would you like to sync these specific contracts?")
        print("They will be imported with full analysis (text extraction, intelligence, etc.)")
    else:
        print("\n[WARNING] Could not find your original contracts in Alfresco.")
        print("\nPossible reasons:")
        print("  1. They were uploaded directly (not from Alfresco)")
        print("  2. They have different names in Alfresco")
        print("  3. They're in a different folder")

        print("\n[INFO] Showing all available contracts in Alfresco:")
        print("="*60)
        for idx, contract in enumerate(raw_contracts[:30], 1):
            print(f"{idx}. {contract['name']}")

        if len(raw_contracts) > 30:
            print(f"... and {len(raw_contracts) - 30} more")

    print("="*60)
    return found_contracts


if __name__ == '__main__':
    try:
        search_alfresco_contracts()
    except Exception as e:
        print(f"\n\n[ERROR] Search failed: {e}")
        import traceback
        traceback.print_exc()
