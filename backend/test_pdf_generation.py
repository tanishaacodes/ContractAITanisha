#!/usr/bin/env python
"""
Test script to verify PDF generation works correctly
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, ClauseDeviation
from api.utils import create_modified_pdf

def test_pdf_generation():
    """Test the PDF generation with actual contract data"""

    print("=" * 60)
    print("Testing PDF Generation for Modified Contracts")
    print("=" * 60)

    # Get a contract with accepted clauses
    contract_id = '4372f03a-455c-47da-ba01-b75e3f4c5db9'

    try:
        contract = Contract.objects.get(id=contract_id)
        print(f"\n✓ Contract found: {contract.filename}")
        print(f"  File path: {contract.file_path}")
        print(f"  File exists: {os.path.exists(contract.file_path)}")

        # Get accepted clauses
        accepted_clauses = ClauseDeviation.objects.filter(
            risk_analysis__contract=contract,
            status='ACCEPTED'
        )

        print(f"\n✓ Found {accepted_clauses.count()} accepted clause(s)")

        if not accepted_clauses.exists():
            print("\n⚠ No accepted clauses found. Please accept at least one clause first.")
            return

        # Prepare clause changes
        clause_changes = []
        for clause in accepted_clauses:
            print(f"  - {clause.clause_name} ({clause.severity})")
            clause_changes.append({
                'clause_name': clause.clause_name,
                'original_text': clause.description,
                'accepted_text': clause.accepted_text or clause.suggested_text or 'No suggestion'
            })

        print(f"\n⏳ Generating PDF with {len(clause_changes)} modification(s)...")

        # Generate PDF
        pdf_path = create_modified_pdf(
            original_pdf_path=contract.file_path,
            clause_changes=clause_changes,
            contract_name=contract.original_filename or contract.filename
        )

        print(f"\n✅ SUCCESS! PDF generated:")
        print(f"   Path: {pdf_path}")
        print(f"   Exists: {os.path.exists(pdf_path)}")

        if os.path.exists(pdf_path):
            size_kb = os.path.getsize(pdf_path) / 1024
            print(f"   Size: {size_kb:.2f} KB")

            # Get download URL
            from django.conf import settings
            relative_path = os.path.relpath(pdf_path, settings.MEDIA_ROOT)
            download_url = f'{settings.MEDIA_URL}{relative_path.replace(os.sep, "/")}'
            print(f"   Download URL: http://localhost:8002{download_url}")

        print("\n" + "=" * 60)
        print("PDF generation test PASSED ✓")
        print("=" * 60)

    except Contract.DoesNotExist:
        print(f"\n❌ Contract with ID {contract_id} not found")
        print("   Please update the contract_id in this script")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 60)
        print("PDF generation test FAILED ✗")
        print("=" * 60)

if __name__ == '__main__':
    test_pdf_generation()
