"""
Utility to link contracts to counterparties.
Extracts counterparty names from contracts and creates/links them.
"""
import os
import django
import re
from difflib import SequenceMatcher

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract
from negotiation.models import Counterparty


def clean_party_name(name):
    """Clean and normalize party names"""
    if not name:
        return None

    # Remove common artifacts
    name = name.strip()
    name = re.sub(r'\s+', ' ', name)  # Normalize whitespace
    name = re.sub(r'(vs|&)\s*(the|THE)$', '', name).strip()  # Remove "vs the"
    name = re.sub(r'^(the|THE)\s+', '', name).strip()  # Remove leading "the"

    # If too short or generic, skip
    if len(name) < 3 or name.lower() in ['the', 'client', 'owner', 'contractor']:
        return None

    return name


def find_or_create_counterparty(party_name):
    """Find existing counterparty or create new one"""
    party_name = clean_party_name(party_name)
    if not party_name:
        return None

    # Try exact match first
    try:
        return Counterparty.objects.get(name__iexact=party_name)
    except Counterparty.DoesNotExist:
        pass

    # Try fuzzy match (>= 85% similarity)
    all_counterparties = Counterparty.objects.all()
    for cp in all_counterparties:
        similarity = SequenceMatcher(None, party_name.lower(), cp.name.lower()).ratio()
        if similarity >= 0.85:
            print(f"  Fuzzy match: '{party_name}' -> '{cp.name}' (similarity: {similarity:.2f})")
            return cp

    # Create new counterparty
    print(f"  Creating new counterparty: '{party_name}'")
    return Counterparty.objects.create(name=party_name)


def link_contracts_to_counterparties():
    """Link all contracts to counterparties based on party_b field"""
    print("=" * 70)
    print("LINKING CONTRACTS TO COUNTERPARTIES")
    print("=" * 70)

    contracts = Contract.objects.all()
    total = contracts.count()

    print(f"\nTotal contracts: {total}")
    print(f"Contracts already linked: {contracts.exclude(counterparty__isnull=True).count()}")
    print(f"Contracts to process: {contracts.filter(counterparty__isnull=True).count()}\n")

    linked_count = 0
    created_count = 0
    skipped_count = 0

    for i, contract in enumerate(contracts.filter(counterparty__isnull=True), 1):
        # Try party_b first, then party_name, then filename
        party_name = contract.party_b or contract.party_name or contract.original_filename

        print(f"[{i}/{total}] Contract: {contract.original_filename[:50]}")
        print(f"  Raw party name: {party_name[:80] if party_name else 'None'}")

        counterparty = find_or_create_counterparty(party_name)

        if counterparty:
            contract.counterparty = counterparty
            contract.save(update_fields=['counterparty'])
            linked_count += 1
            print(f"  [OK] Linked to: {counterparty.name}")

            if counterparty.created_at == counterparty.updated_at:
                created_count += 1
        else:
            skipped_count += 1
            print(f"  [SKIP] Skipped (invalid party name)")

        print()

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total contracts processed: {contracts.filter(counterparty__isnull=True).count() + linked_count}")
    print(f"Successfully linked: {linked_count}")
    print(f"New counterparties created: {created_count}")
    print(f"Skipped (invalid names): {skipped_count}")
    print(f"\nTotal counterparties in system: {Counterparty.objects.count()}")
    print(f"Contracts with counterparty link: {Contract.objects.exclude(counterparty__isnull=True).count()}")
    print("=" * 70)


if __name__ == '__main__':
    link_contracts_to_counterparties()
