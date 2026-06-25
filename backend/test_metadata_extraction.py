"""
Test script to verify contract metadata extraction.
"""
import os
import sys
import django
import asyncio

# Setup Django
django_project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, django_project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from agents.mcp_server import generate_executive_summary
from core.models import Contract
import json


async def test_metadata_extraction():
    """Test metadata extraction from contract."""
    print("[TEST] Starting Contract Metadata Extraction Test\n")
    print("=" * 70)

    # Get first contract
    try:
        contract = await Contract.objects.afirst()
        if not contract:
            print("[FAIL] No contracts found in database")
            return False

        print(f"\nTesting with contract: {contract.original_filename}")
        print(f"Contract ID: {contract.id}")
        print("-" * 70)

        # Run executive summary generation (which includes metadata extraction)
        result_json = await generate_executive_summary(str(contract.id))
        result = json.loads(result_json)

        if result.get('status') == 'success':
            summary_data = result.get('summary_data', {})

            print("\nEXTRACTED METADATA:")
            print("-" * 70)
            print(f"Contract Type:    {summary_data.get('contract_type', 'N/A')}")
            print(f"Party A:          {summary_data.get('party_a', 'N/A')}")
            print(f"Party B:          {summary_data.get('party_b', 'N/A')}")
            print(f"Contract Value:   {summary_data.get('contract_value', 'N/A')}")
            print(f"Duration:         {summary_data.get('duration', 'N/A')}")
            print(f"Jurisdiction:     {summary_data.get('jurisdiction', 'N/A')}")
            print(f"Payment Terms:    {summary_data.get('payment_terms', 'N/A')}")
            print("-" * 70)

            # Check if metadata was successfully extracted
            success_count = 0
            total_fields = 7

            if summary_data.get('contract_type') not in ['Unknown', 'Not specified']:
                success_count += 1
            if summary_data.get('party_a') not in ['Not specified', None]:
                success_count += 1
            if summary_data.get('party_b') not in ['Not specified', None]:
                success_count += 1
            if summary_data.get('contract_value') not in ['Not specified', None]:
                success_count += 1
            if summary_data.get('duration') not in ['Not specified', None]:
                success_count += 1
            if summary_data.get('jurisdiction') not in ['Not specified', None]:
                success_count += 1
            if summary_data.get('payment_terms') not in ['Not specified', None]:
                success_count += 1

            print(f"\nExtraction Success Rate: {success_count}/{total_fields} fields extracted")
            print("=" * 70)

            if success_count >= 4:
                print("[PASS] Metadata extraction successful!")
                return True
            else:
                print("[FAIL] Too few fields extracted")
                return False
        else:
            print(f"[FAIL] {result.get('message')}")
            return False

    except Exception as e:
        print(f"[FAIL] EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(test_metadata_extraction())
