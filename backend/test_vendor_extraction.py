"""
Test script to re-extract metadata for vendor_agreement.pdf only
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


def test_vendor_extraction():
    print("=" * 60)
    print("TESTING VENDOR_AGREEMENT.PDF EXTRACTION")
    print("=" * 60)

    # Find the vendor_agreement contract
    contract = Contract.objects.filter(original_filename='vendor_agreement.pdf').first()

    if not contract:
        print("[ERROR] vendor_agreement.pdf not found in database!")
        return

    print(f"\nFound contract: {contract.original_filename}")
    print(f"Contract ID: {contract.id}")
    print(f"\nCurrent values:")
    print(f"  Value: {contract.contract_value}")
    print(f"  Party: {contract.party_name}")
    print(f"  Duration: {contract.contract_duration}")

    # Extract with improved prompt
    text_sample = contract.full_text[:5000] if len(contract.full_text) > 5000 else contract.full_text

    prompt = f"""You are a contract analysis expert. Extract EXACTLY the following information from this contract text.

CONTRACT TEXT:
{text_sample}

EXTRACT these 3 fields and return ONLY valid JSON:

1. CONTRACT VALUE - Look for:
   - Total contract value, total amount, contract price
   - Can be in any currency: USD, INR, EUR, GBP, etc.
   - Include currency symbol or code (e.g., "INR 42,00,000", "$50,000", "€25,000")
   - Look for words like "Rupees", "Lakh", "Crore" for Indian currency
   - If not found, use "Not specified"

2. PARTY NAME - The OTHER party (vendor/supplier), NOT Party A or Client:
   - IMPORTANT: Look specifically for "PARTY B" or "Vendor / Supplier" sections
   - Avoid "Party A" or "Client" - we want the COUNTERPARTY
   - Common labels: "Party B (Vendor", "Party B (Supplier", "Vendor:", "Supplier:"
   - Extract the FULL company name (e.g., "PrimePack Industries LLP", "Acme Corp Ltd")
   - If multiple parties, choose the vendor/supplier, not the client
   - If not found, use "Not specified"

3. CONTRACT DURATION - The term/period:
   - Look for "duration", "term", "valid from", "validity period"
   - Can be in months, years, or dates
   - Examples: "12 months", "2 years", "1 year", "24 months"
   - If dates are given (e.g., "10 Feb 2025 to 9 Feb 2026"), calculate duration
   - If not found, use "Not specified"

Return in this EXACT JSON format (no extra text):
{{
    "contract_value": "...",
    "party_name": "...",
    "contract_duration": "..."
}}"""

    print("\n[INFO] Calling AI to extract metadata...")
    response_data = call_llm(prompt, max_tokens=500, temperature=0.0, stream=True)
    response_text = response_data.get('response', '')

    print(f"\n[INFO] Raw AI Response:\n{response_text}\n")

    # Parse JSON response
    try:
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            metadata = json.loads(json_str)

            # Post-process: Fix currency if INR/Rupees/Lakh/Crore is in original text
            contract_value = metadata.get('contract_value', '')
            if contract_value and '$' in contract_value:
                if any(keyword in contract.full_text.lower() for keyword in ['inr', 'rupees', 'rupee', 'lakh', 'crore', '₹']):
                    metadata['contract_value'] = contract_value.replace('$', 'INR ')

            print(f"[OK] Extracted metadata:")
            print(f"  contract_value: {metadata.get('contract_value')}")
            print(f"  party_name: {metadata.get('party_name')}")
            print(f"  contract_duration: {metadata.get('contract_duration')}")

            # Update contract
            contract.contract_value = metadata.get('contract_value', 'Not specified') or 'Not specified'
            contract.party_name = metadata.get('party_name', 'Not specified') or 'Not specified'
            contract.contract_duration = metadata.get('contract_duration', 'Not specified') or 'Not specified'
            contract.save()

            print(f"\n[OK] Contract updated successfully!")
            print(f"  Value: {contract.contract_value}")
            print(f"  Party: {contract.party_name}")
            print(f"  Duration: {contract.contract_duration}")

        else:
            print("[ERROR] No valid JSON found in response")

    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON parse error: {e}")
    except Exception as e:
        print(f"[ERROR] Extraction failed: {e}")


if __name__ == '__main__':
    test_vendor_extraction()
