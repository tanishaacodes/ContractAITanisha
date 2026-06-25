"""
Calculate vendor exposure from existing ContractRisk data
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from risk.models import VendorExposure, Party, ContractRisk
from django.db.models import Avg, Count, Sum

print("=" * 60)
print("[*] Calculating Vendor Exposure")
print("=" * 60)

# Get all parties with contracts
parties = Party.objects.all()

for party in parties:
    # Get all contract risks for this party
    contract_risks = ContractRisk.objects.filter(party=party)

    if contract_risks.exists():
        contract_count = contract_risks.count()
        avg_risk = contract_risks.aggregate(Avg('overall_risk_score'))['overall_risk_score__avg']
        total_exposure = avg_risk * contract_count  # Simple exposure calculation

        # Update or create vendor exposure
        vendor_exposure, created = VendorExposure.objects.update_or_create(
            party=party,
            defaults={
                'total_exposure': total_exposure,
                'contract_count': contract_count,
                'average_risk': avg_risk,
                'exposure_by_region': {}
            }
        )

        action = "Created" if created else "Updated"
        print(f"[+] {action} exposure for {party.name}: {total_exposure:.2f} ({contract_count} contracts)")

print("\n" + "=" * 60)
print("[*] Vendor Exposure Calculation Complete!")
print(f"[*] Total vendors with exposure: {VendorExposure.objects.count()}")
print("=" * 60)
