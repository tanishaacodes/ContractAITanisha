"""
Populate contract_risk_history table with versioned risk data.
This enables the time slider feature to show risk evolution over time.
"""
import os
import django
import random
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, Clause, ContractRiskHistory
from ai.risk_engine import score_clause_risk, calculate_overall_risk
from ai.geography import geography_risk
from ai.ip_risk import ip_risk
from ai.liability import liability_risk


def populate_risk_history():
    """
    Populate risk history for all contracts with multiple versions.
    Creates 3 versions per contract to simulate risk evolution.
    """
    print("=" * 70)
    print("POPULATING CONTRACT RISK HISTORY")
    print("=" * 70)

    # Get all contracts
    contracts = Contract.objects.all()
    print(f"\nFound {contracts.count()} contracts")

    if contracts.count() == 0:
        print("[!] No contracts found. Upload some contracts first!")
        return

    # Clear existing history
    print("\n[1] Clearing existing risk history...")
    deleted_count = ContractRiskHistory.objects.all().delete()[0]
    print(f"    Deleted {deleted_count} old records")

    # Create versioned history for each contract
    print("\n[2] Creating versioned risk history...")
    created = 0

    for contract in contracts:
        # Get clauses for this contract
        clauses = Clause.objects.filter(contract=contract).values('extracted_text')

        # Calculate current risk
        if clauses.exists():
            clauses_data = []
            for clause in clauses:
                risk_score, _ = score_clause_risk(clause['extracted_text'] or '')
                clauses_data.append({'risk_score': risk_score})
            current_overall_risk = calculate_overall_risk(clauses_data)
        else:
            current_overall_risk = random.uniform(20, 60)  # Default for contracts without clauses

        # Calculate dimension-specific risks (functions return tuples)
        current_ip, _ = ip_risk(contract.full_text or '')

        # Get contract value safely
        try:
            contract_val = float(contract.contract_value) if contract.contract_value else 1
        except (ValueError, TypeError):
            contract_val = 1

        current_liability, _ = liability_risk(
            float(contract.total_liability) if contract.total_liability else 0,
            contract_val
        )
        current_geo, _ = geography_risk(contract.full_text or '')

        # Create 3 versions showing risk evolution
        for version_num in range(1, 4):
            # Simulate risk drift over time (getting slightly worse)
            drift_factor = 1.0 + (version_num - 1) * 0.05  # 5% increase per version

            ContractRiskHistory.objects.create(
                contract_id=contract.id,
                version=version_num,
                overall_risk=min(current_overall_risk * drift_factor, 100),
                ip_risk=min(current_ip * drift_factor, 100),
                liability_risk=min(current_liability * drift_factor, 100),
                geography_risk=current_geo  # Geo risk doesn't change
            )
            created += 1

            if created % 50 == 0:
                print(f"    Created {created} risk history records...")

    print(f"\n[OK] Created {created} risk history records!")

    # Show sample
    print("\n[3] Sample risk history:")
    sample = ContractRiskHistory.objects.order_by('contract_id', 'version')[:9]

    for record in sample:
        contract = Contract.objects.get(id=record.contract_id)
        print(f"    {contract.filename[:30]:30} | v{record.version} | "
              f"Overall: {record.overall_risk:5.1f} | "
              f"IP: {record.ip_risk:5.1f} | "
              f"Liability: {record.liability_risk:5.1f}")

    # Show version counts
    print("\n[4] Version summary:")
    from django.db.models import Count
    versions = ContractRiskHistory.objects.values('version').annotate(count=Count('id')).order_by('version')
    for v in versions:
        print(f"    Version {v['version']}: {v['count']} contracts")

    print("\n" + "=" * 70)
    print("✅ RISK HISTORY POPULATED SUCCESSFULLY!")
    print("   Time slider is now ready to use!")
    print("=" * 70)


if __name__ == '__main__':
    populate_risk_history()
