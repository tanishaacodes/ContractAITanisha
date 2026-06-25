import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, ContractRiskAnalysis

print("=== Syncing Risk Levels ===\n")
contracts = Contract.objects.all()

for contract in contracts:
    liability = contract.liability_level

    # Get or create risk analysis
    risk_analysis, created = ContractRiskAnalysis.objects.get_or_create(contract=contract)

    old_risk = risk_analysis.risk_level
    risk_analysis.risk_level = liability
    risk_analysis.save()

    status = "Created" if created else "Updated"
    print(f"{status}: {contract.filename}")
    print(f"  {old_risk} -> {liability}")
    print()

print("\n=== Sync Complete ===")
print("Grid should now show:")
print("  HIGH: 1 contract")
print("  MEDIUM: 2 contracts")
print("  LOW: 2 contracts")
