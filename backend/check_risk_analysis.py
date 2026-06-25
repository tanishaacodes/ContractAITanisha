import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, ContractRiskAnalysis

print("=== Contract Risk Levels Comparison ===\n")
contracts = Contract.objects.all()

for contract in contracts:
    liability = contract.liability_level

    # Get risk analysis
    risk_analysis = ContractRiskAnalysis.objects.filter(contract=contract).first()
    risk_level = risk_analysis.risk_level if risk_analysis else "None"

    match = "OK" if liability == risk_level else "MISMATCH"
    print(f"{match} {contract.filename}")
    print(f"  liability_level: {liability}")
    print(f"  risk_level (grid): {risk_level}")
    print()
