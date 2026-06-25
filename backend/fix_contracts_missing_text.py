"""
Fix contracts that have missing full_text by re-extracting from their file_path
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract
from api.utils import extract_text_from_file

def fix_contracts_missing_text():
    """Re-extract text for contracts that have empty full_text"""
    print("=" * 80)
    print("Fixing Contracts with Missing Text")
    print("=" * 80)

    # Find contracts with missing or very short text
    contracts = Contract.objects.all()
    missing_text_contracts = [c for c in contracts if not c.full_text or len(c.full_text.strip()) < 100]

    print(f"\nFound {len(missing_text_contracts)} contracts with missing/insufficient text")
    print(f"Total contracts in database: {contracts.count()}\n")

    if not missing_text_contracts:
        print("No contracts need fixing!")
        return

    fixed_count = 0
    failed_count = 0

    for contract in missing_text_contracts:
        print(f"\n{'='*70}")
        print(f"Processing: {contract.original_filename}")
        print(f"ID: {contract.id}")
        print(f"Current text length: {len(contract.full_text or '')} chars")

        # Check if file exists
        if not os.path.exists(contract.file_path):
            print(f"[FAIL] File not found: {contract.file_path}")
            failed_count += 1
            continue

        # Get file extension
        ext = os.path.splitext(contract.file_path)[1].lower()

        try:
            # Re-extract text
            print(f"Extracting text from {ext} file...")
            result = extract_text_from_file(contract.file_path, ext)
            extracted_text = result.get('text', '')
            ocr_performed = result.get('ocr_performed', False)

            if extracted_text and len(extracted_text.strip()) >= 100:
                # Update contract
                contract.full_text = extracted_text
                contract.save()

                print(f"[OK] Successfully extracted {len(extracted_text)} chars")
                if ocr_performed:
                    print(f"     (OCR was used)")
                fixed_count += 1
            else:
                print(f"[FAIL] Insufficient text extracted: {len(extracted_text)} chars")
                failed_count += 1

        except Exception as e:
            print(f"[FAIL] Error: {e}")
            failed_count += 1

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total processed: {len(missing_text_contracts)}")
    print(f"Successfully fixed: {fixed_count}")
    print(f"Failed: {failed_count}")
    print("=" * 80)

if __name__ == '__main__':
    fix_contracts_missing_text()
