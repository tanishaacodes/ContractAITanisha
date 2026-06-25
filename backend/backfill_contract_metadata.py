"""
Backfill script to extract metadata (value, party, duration) for existing contracts
"""
import os
import sys
import django
import json

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract
from rag import call_llm


def backfill_metadata():
    """Extract and update metadata for all contracts with missing metadata"""

    print("=" * 60)
    print("CONTRACT METADATA BACKFILL SCRIPT")
    print("=" * 60)

    # Get all contracts that need metadata extraction
    contracts = Contract.objects.all()
    total_contracts = contracts.count()

    print(f"\nFound {total_contracts} total contracts")

    # Filter contracts with missing metadata
    contracts_to_update = []
    for contract in contracts:
        needs_update = (
            not contract.contract_value or contract.contract_value == 'Not specified' or
            not contract.party_name or contract.party_name == 'Not specified' or
            not contract.contract_duration or contract.contract_duration == 'Not specified'
        )
        if needs_update and contract.full_text:
            contracts_to_update.append(contract)

    print(f"Found {len(contracts_to_update)} contracts needing metadata extraction\n")

    if not contracts_to_update:
        print("[OK] All contracts already have metadata!")
        return

    updated_count = 0
    failed_count = 0

    for i, contract in enumerate(contracts_to_update, 1):
        print(f"\n[{i}/{len(contracts_to_update)}] Processing: {contract.original_filename}")
        print(f"  Contract ID: {contract.id}")
        print(f"  Current values:")
        print(f"    - Value: {contract.contract_value or 'NULL'}")
        print(f"    - Party: {contract.party_name or 'NULL'}")
        print(f"    - Duration: {contract.contract_duration or 'NULL'}")

        try:
            # Extract metadata using AI
            text_sample = contract.full_text[:3000] if len(contract.full_text) > 3000 else contract.full_text

            prompt = f"""Analyze this contract and extract the following information. Return ONLY a JSON object with these exact keys:

Contract text:
{text_sample}

Extract and return in this exact JSON format:
{{
    "contract_value": "the monetary value/amount mentioned in the contract (e.g., '$50,000', '€25,000', 'Not specified')",
    "party_name": "the name of the other party/vendor/client in the contract (the party that is NOT the agreement holder)",
    "contract_duration": "the duration/term of the contract (e.g., '12 months', '2 years', '3-year term', 'Not specified')"
}}

Rules:
- If any field is not found or unclear, use "Not specified"
- For contract_value: Look for payment amounts, contract value, total cost, fees
- For party_name: Look for "between X and Y", vendor names, client names, "Party B", counterparty
- For contract_duration: Look for term length, duration, validity period, start and end dates
- Return ONLY valid JSON, no other text"""

            response_data = call_llm(prompt, max_tokens=300, temperature=0.0, stream=True)
            response_text = response_data.get('response', '')

            # Parse JSON response
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    metadata = json.loads(json_str)
                else:
                    metadata = {
                        'contract_value': 'Not specified',
                        'party_name': 'Not specified',
                        'contract_duration': 'Not specified'
                    }
            except json.JSONDecodeError:
                metadata = {
                    'contract_value': 'Not specified',
                    'party_name': 'Not specified',
                    'contract_duration': 'Not specified'
                }

            # Update contract (convert empty strings to "Not specified")
            contract.contract_value = metadata.get('contract_value', 'Not specified') or 'Not specified'
            contract.party_name = metadata.get('party_name', 'Not specified') or 'Not specified'
            contract.contract_duration = metadata.get('contract_duration', 'Not specified') or 'Not specified'
            contract.save()

            print(f"  [OK] Updated with:")
            print(f"    - Value: {contract.contract_value}")
            print(f"    - Party: {contract.party_name}")
            print(f"    - Duration: {contract.contract_duration}")

            updated_count += 1

        except Exception as e:
            print(f"  [ERROR] Failed: {str(e)}")
            failed_count += 1

    print("\n" + "=" * 60)
    print("BACKFILL COMPLETE")
    print("=" * 60)
    print(f"[OK] Successfully updated: {updated_count}")
    print(f"[ERROR] Failed: {failed_count}")
    print(f"[INFO] Total processed: {len(contracts_to_update)}")
    print("=" * 60)


if __name__ == '__main__':
    try:
        backfill_metadata()
    except KeyboardInterrupt:
        print("\n\n[WARN] Backfill interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
