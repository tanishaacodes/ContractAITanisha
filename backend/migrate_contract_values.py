"""
Migrate contract_value (string) to total_liability (decimal) for enterprise risk calculations
"""
import os
import django
import re
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract


def parse_contract_value(value_string):
    """
    Parse contract value string like "$15,000,000" or "₹45,000,000" to Decimal
    """
    if not value_string:
        return None

    # Remove currency symbols and spaces
    cleaned = re.sub(r'[₹$£€¥,\s]', '', value_string)

    # Remove any non-numeric characters except decimal point
    cleaned = re.sub(r'[^\d.]', '', cleaned)

    if not cleaned:
        return None

    try:
        return Decimal(cleaned)
    except:
        return None


def migrate_contract_values():
    """
    Migrate contract_value to total_liability for all contracts
    """
    print("=" * 70)
    print("  MIGRATING CONTRACT VALUES TO TOTAL LIABILITY")
    print("=" * 70)

    contracts = Contract.objects.all()
    print(f"\nFound {contracts.count()} contracts to process\n")

    updated_count = 0
    skipped_count = 0

    for contract in contracts:
        print(f"Processing: {contract.original_filename}")
        print(f"  Current total_liability: ${contract.total_liability:,.2f}")
        print(f"  Current contract_value: {contract.contract_value}")

        # Parse contract_value
        if contract.contract_value:
            parsed_value = parse_contract_value(contract.contract_value)

            if parsed_value and parsed_value > 0:
                contract.total_liability = parsed_value
                contract.save()
                print(f"  [OK] Updated total_liability to: ${parsed_value:,.2f}")
                updated_count += 1
            else:
                print(f"  [SKIP] Could not parse contract_value")
                skipped_count += 1
        else:
            # Set default value if contract_value is empty
            default_value = Decimal('1000000')  # $1M default
            contract.total_liability = default_value
            contract.save()
            print(f"  [OK] Set default total_liability: ${default_value:,.2f}")
            updated_count += 1

        print()

    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"Total Contracts: {contracts.count()}")
    print(f"Successfully Updated: {updated_count}")
    print(f"Skipped: {skipped_count}")

    # Show final values
    print("\n" + "=" * 70)
    print("  FINAL CONTRACT VALUES")
    print("=" * 70)

    total_exposure = Decimal('0')
    for contract in Contract.objects.all():
        print(f"{contract.original_filename[:50]:50} ${contract.total_liability:>15,.2f}")
        total_exposure += contract.total_liability

    print("-" * 70)
    print(f"{'TOTAL PORTFOLIO EXPOSURE':50} ${total_exposure:>15,.2f}")
    print("=" * 70)

    print("\n[SUCCESS] Contract values migrated!")
    print("Now re-run the extraction script to link suppliers/commodities with correct exposures.")


if __name__ == '__main__':
    migrate_contract_values()
