"""
Search for the user's actual original 5 contracts
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from django.db import connection


def find_original_contracts():
    """Search for contracts matching the names from the screenshot"""
    print("\n" + "="*60)
    print("SEARCH FOR ORIGINAL CONTRACTS")
    print("="*60)

    # Names from the user's screenshot
    search_patterns = [
        'High_Risk_Construc',
        'High Risk Construc',
        'SOFTWARE DEVELO',
        'MANUFACTURING A',
        'EXCLUSIVE DISTRIBU',
        'COMMERCIAL LEASE'
    ]

    with connection.cursor() as cursor:
        print("\n[INFO] Searching deleted contracts...")

        # Since we deleted them, let's check if we can find them in Alfresco
        # First, let's see what's currently in the database
        cursor.execute("SELECT id, originalFilename, filename, contractType, uploadedAt FROM contracts")
        current_contracts = cursor.fetchall()

        print(f"\n[INFO] Current contracts in database: {len(current_contracts)}")
        for contract in current_contracts:
            print(f"  - {contract[1] or contract[2]}")

        # Check if any match the patterns
        found_matches = []
        for contract in current_contracts:
            filename = contract[1] or contract[2] or ''
            for pattern in search_patterns:
                if pattern.lower() in filename.lower():
                    found_matches.append(contract)
                    break

        if found_matches:
            print(f"\n[FOUND] {len(found_matches)} matching contracts:")
            for contract in found_matches:
                print(f"  - {contract[1] or contract[2]}")
        else:
            print("\n[NOT FOUND] The original contracts were deleted.")
            print("\n[INFO] We need to restore from Alfresco.")
            print("\nThe contracts shown in your screenshot were:")
            print("  1. High_Risk_Construction...")
            print("  2. SOFTWARE DEVELOPMENT...")
            print("  3. MANUFACTURING AGREEMENT")
            print("  4. EXCLUSIVE DISTRIBUTION")
            print("  5. COMMERCIAL LEASE")

            print("\n[SOLUTION] Check if these are available in Alfresco:")
            print("  1. Use the 'Browse Alfresco Contracts' button")
            print("  2. Look for these specific contract names")
            print("  3. We can then selectively sync only these 5")

    print("="*60)


if __name__ == '__main__':
    try:
        find_original_contracts()
    except Exception as e:
        print(f"\n\n[ERROR] Search failed: {e}")
        import traceback
        traceback.print_exc()
