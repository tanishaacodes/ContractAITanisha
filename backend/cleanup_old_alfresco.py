#!/usr/bin/env python
"""
Cleanup script for old Alfresco contracts with missing files.
Run this to remove contracts synced before the permanent file storage fix.
Users can then re-sync to get downloadable copies.

Usage:
    python cleanup_old_alfresco.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, AlfrescoDocument, VectorEmbedding, ContractIntelligence


def cleanup_old_alfresco_contracts():
    """Remove Alfresco contracts with missing files."""

    print("=" * 60)
    print("CLEANUP OLD ALFRESCO CONTRACTS WITH MISSING FILES")
    print("=" * 60)

    # Find all Alfresco contracts
    alfresco_contracts = Contract.objects.filter(alfresco_doc__isnull=False)
    total_count = alfresco_contracts.count()

    print(f"\nTotal Alfresco contracts in database: {total_count}")

    # Find contracts with missing files
    missing_files = []
    valid_files = []

    for contract in alfresco_contracts:
        if not contract.file_path or not os.path.exists(contract.file_path):
            missing_files.append(contract)
        else:
            valid_files.append(contract)

    print(f"Contracts with valid files: {len(valid_files)}")
    print(f"Contracts with missing files: {len(missing_files)}")

    if not missing_files:
        print("\n[OK] No cleanup needed! All contracts have valid files.")
        return

    print("\nContracts to be deleted:")
    for contract in missing_files[:20]:  # Show first 20
        print(f"  - {contract.original_filename} (ID: {contract.id})")

    if len(missing_files) > 20:
        print(f"  ... and {len(missing_files) - 20} more")

    # Ask for confirmation
    print("\n" + "=" * 60)
    response = input(f"\nDelete {len(missing_files)} contracts? (yes/no): ").strip().lower()

    if response != 'yes':
        print("[CANCEL] Cleanup cancelled.")
        return

    # Delete contracts and related data
    deleted_count = 0
    for contract in missing_files:
        try:
            contract_id = contract.id
            filename = contract.original_filename

            # Delete will cascade to:
            # - AlfrescoDocument (OneToOne)
            # - ContractIntelligence (OneToOne)
            # - VectorEmbedding (ForeignKey)
            # - Clauses, RiskAnalysis, etc.
            contract.delete()

            deleted_count += 1
            print(f"[OK] Deleted: {filename}")

        except Exception as e:
            print(f"[ERROR] Error deleting {contract.original_filename}: {e}")

    print("\n" + "=" * 60)
    print(f"[DONE] CLEANUP COMPLETE")
    print(f"Deleted {deleted_count} contracts with missing files")
    print(f"Remaining contracts: {Contract.objects.filter(alfresco_doc__isnull=False).count()}")
    print("\nYou can now re-sync from Alfresco to get fresh copies with downloadable files.")
    print("=" * 60)


if __name__ == '__main__':
    cleanup_old_alfresco_contracts()
