"""
Script to fix OCR errors in existing clauses
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Clause
from api.ocr_text_cleaner import clean_ocr_text

def fix_existing_clauses():
    """Fix OCR errors in all existing clauses."""
    print("="*60)
    print("FIXING OCR ERRORS IN EXISTING CLAUSES")
    print("="*60)

    clauses = Clause.objects.filter(extracted_text__isnull=False).exclude(extracted_text='')
    total = clauses.count()

    print(f"\nFound {total} clauses with extracted text")
    print("Cleaning OCR errors...\n")

    fixed_count = 0
    for i, clause in enumerate(clauses, 1):
        original_text = clause.extracted_text
        cleaned_text = clean_ocr_text(original_text)

        if cleaned_text != original_text:
            clause.extracted_text = cleaned_text
            clause.save()
            fixed_count += 1

            print(f"{i}/{total} ✓ Fixed: {clause.clause_name[:50]}")
            if 'T10ns' in original_text or '1' in original_text:
                print(f"   Before: {original_text[:80]}...")
                print(f"   After:  {cleaned_text[:80]}...")
        else:
            print(f"{i}/{total} - No changes: {clause.clause_name[:50]}")

    print("\n" + "="*60)
    print(f"✅ COMPLETE: Fixed {fixed_count}/{total} clauses")
    print("="*60)


if __name__ == '__main__':
    try:
        fix_existing_clauses()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
