"""
Quick script to analyze all contracts in the database
Run this to populate the Risk & Exposure dashboard with data
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract
from risk.services import get_risk_engine

def analyze_all_contracts():
    """Analyze all contracts that don't have risk data yet"""

    # Get all contracts
    contracts = Contract.objects.all()
    total = contracts.count()

    if total == 0:
        print("[!] No contracts found. Please upload some contracts first.")
        return

    print(f"[*] Found {total} contracts in database")

    # Get contracts without risk analysis
    from risk.models import ContractRisk
    analyzed_ids = ContractRisk.objects.values_list('contract_id', flat=True)
    pending_contracts = contracts.exclude(id__in=analyzed_ids)
    pending_count = pending_contracts.count()

    print(f"[+] Already analyzed: {total - pending_count}")
    print(f"[-] Pending analysis: {pending_count}")

    if pending_count == 0:
        print("\n[*] All contracts already analyzed!")
        return

    # Analyze pending contracts
    risk_engine = get_risk_engine()

    for i, contract in enumerate(pending_contracts, 1):
        print(f"\n[{i}/{pending_count}] Analyzing: {contract.original_filename}")
        try:
            result = risk_engine.analyze_contract(contract.id)
            overall_risk = result.get('overall_risk', {}).get('overall_risk_score', 0)
            print(f"  [+] Risk Score: {overall_risk:.2f}")
            print(f"  [+] Clauses analyzed: {result.get('clauses_analyzed', 0)}")
        except Exception as e:
            print(f"  [!] Error: {str(e)}")

    print("\n" + "="*60)
    print("[*] Analysis Complete!")
    print("="*60)
    print(f"[+] Total contracts analyzed: {pending_count}")
    print(f"[*] Refresh the Risk & Exposure dashboard to see results")

if __name__ == '__main__':
    analyze_all_contracts()
