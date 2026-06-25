#!/usr/bin/env python
"""
Update contract types for existing contracts.
This will reclassify all contracts with 'Unknown' type.

Usage:
    python update_contract_types.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract


def classify_contract_type(text: str, filename: str) -> str:
    """
    Classify contract type based on filename and content keywords.
    """
    text_lower = text.lower() if text else ''
    filename_lower = filename.lower() if filename else ''

    # Check filename first
    if any(keyword in filename_lower for keyword in ['nda', 'confidential', 'non-disclosure']):
        return 'Non-Disclosure Agreement (NDA)'
    elif any(keyword in filename_lower for keyword in ['service', 'msa', 'master']):
        return 'Service Agreement'
    elif any(keyword in filename_lower for keyword in ['employ', 'employment']):
        return 'Employment Agreement'
    elif any(keyword in filename_lower for keyword in ['data', 'datap', 'dpa', 'privacy']):
        return 'Data Processing Agreement'
    elif any(keyword in filename_lower for keyword in ['cyber', 'security']):
        return 'Cybersecurity Agreement'
    elif any(keyword in filename_lower for keyword in ['consult', 'consulting']):
        return 'Consulting Agreement'
    elif any(keyword in filename_lower for keyword in ['loi', 'letter', 'intent']):
        return 'Letter of Intent'

    # Check content if filename doesn't match
    if any(keyword in text_lower for keyword in ['non-disclosure', 'confidential information', 'nda']):
        return 'Non-Disclosure Agreement (NDA)'
    elif any(keyword in text_lower for keyword in ['master service', 'service agreement', 'services agreement']):
        return 'Service Agreement'
    elif any(keyword in text_lower for keyword in ['employment agreement', 'employee', 'employer']):
        return 'Employment Agreement'
    elif any(keyword in text_lower for keyword in ['data processing', 'personal data', 'gdpr']):
        return 'Data Processing Agreement'
    elif any(keyword in text_lower for keyword in ['consulting agreement', 'consultant', 'consulting services']):
        return 'Consulting Agreement'
    elif any(keyword in text_lower for keyword in ['letter of intent', 'loi']):
        return 'Letter of Intent'
    elif any(keyword in text_lower for keyword in ['software license', 'licensing agreement']):
        return 'Software License'
    elif any(keyword in text_lower for keyword in ['purchase agreement', 'sale agreement']):
        return 'Purchase Agreement'

    # Default to generic type
    return 'Contract Agreement'


def update_contract_types():
    """Update contract types for all contracts with Unknown type."""

    print("=" * 60)
    print("UPDATE CONTRACT TYPES")
    print("=" * 60)

    # Find contracts with Unknown type
    unknown_contracts = Contract.objects.filter(contract_type='Unknown')
    total = unknown_contracts.count()

    print(f"\nFound {total} contracts with 'Unknown' type")

    if total == 0:
        print("\n[OK] No contracts to update!")
        return

    print("\nUpdating contract types...\n")

    updated = 0
    for contract in unknown_contracts:
        old_type = contract.contract_type
        new_type = classify_contract_type(contract.full_text or '', contract.original_filename)

        contract.contract_type = new_type
        contract.save()

        updated += 1
        print(f"[{updated}/{total}] {contract.original_filename}")
        print(f"  Old: {old_type}")
        print(f"  New: {new_type}\n")

    print("=" * 60)
    print(f"[DONE] Updated {updated} contracts")
    print("=" * 60)


if __name__ == '__main__':
    update_contract_types()
