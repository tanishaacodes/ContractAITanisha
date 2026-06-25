"""
Set Contract Value for a Contract
==================================
This script helps you set the contract_value field for a specific contract.

Usage:
    python set_contract_value.py <contract_id> <value>

Examples:
    python set_contract_value.py 123e4567-e89b-12d3-a456-426614174000 "50 Crore"
    python set_contract_value.py 123e4567-e89b-12d3-a456-426614174000 "10 Lakhs"
    python set_contract_value.py 123e4567-e89b-12d3-a456-426614174000 "25 Cr"
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')

import django
django.setup()

from core.models import Contract

def set_contract_value(contract_id, value):
    """Set contract value for a specific contract"""
    try:
        contract = Contract.objects.get(id=contract_id)
        old_value = contract.contract_value
        contract.contract_value = value
        contract.save()

        print("\n" + "="*60)
        print("SUCCESS: Contract value updated!")
        print("="*60)
        print(f"Contract ID: {contract_id}")
        print(f"Contract Name: {contract.filename}")
        print(f"Old Value: {old_value}")
        print(f"New Value: {value}")
        print("="*60)
        print("\nNow restart your Django server and run the simulation again.")
        print()

    except Contract.DoesNotExist:
        print(f"\nERROR: Contract with ID '{contract_id}' not found.")
        print("\nTo list all contracts, run:")
        print("    python list_contracts.py")
        print()

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

def list_recent_contracts():
    """List the most recent contracts"""
    print("\n" + "="*60)
    print("RECENT CONTRACTS")
    print("="*60)

    contracts = Contract.objects.all().order_by('-created_at')[:10]

    if not contracts:
        print("No contracts found.")
    else:
        for contract in contracts:
            print(f"\nID: {contract.id}")
            print(f"Name: {contract.filename}")
            print(f"Value: {contract.contract_value or 'Not set'}")
            print(f"Created: {contract.created_at}")
            print("-" * 60)

    print()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(__doc__)
        list_recent_contracts()
        print("\nUsage:")
        print("    python set_contract_value.py <contract_id> <value>")
        print("\nExample:")
        print("    python set_contract_value.py 123e4567-e89b-12d3-a456-426614174000 \"50 Crore\"")
        print()

    elif len(sys.argv) == 3:
        contract_id = sys.argv[1]
        value = sys.argv[2]
        set_contract_value(contract_id, value)

    else:
        print("\nERROR: Invalid number of arguments")
        print("\nUsage:")
        print("    python set_contract_value.py <contract_id> <value>")
        print()
