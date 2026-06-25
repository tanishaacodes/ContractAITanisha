"""
Update regional data from contract jurisdiction
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from risk.models import ContractRisk
from core.models import Contract

print("=" * 60)
print("[*] Updating Regional Data from Contract Jurisdiction")
print("=" * 60)

# Get all contract risks
contract_risks = ContractRisk.objects.all()

updated_count = 0
default_regions = ['USA', 'UK', 'EU', 'APAC', 'EMEA']

for idx, cr in enumerate(contract_risks):
    # Get region from contract jurisdiction if available
    region = cr.contract.jurisdiction if cr.contract.jurisdiction else None

    # If no jurisdiction, assign a default region for demo purposes
    if not region or region.strip() == '':
        region = default_regions[idx % len(default_regions)]

    # Update the region
    if cr.region != region:
        cr.region = region
        cr.save()
        updated_count += 1
        print(f"[+] Updated {cr.contract.original_filename}: region = {region}")

print("\n" + "=" * 60)
print(f"[*] Updated {updated_count} contract regions")
print("=" * 60)

# Show regional distribution
from django.db.models import Count, Avg

regional_stats = ContractRisk.objects.values('region').annotate(
    count=Count('id'),
    avg_risk=Avg('overall_risk_score')
).order_by('-count')

print("\n[*] Regional Distribution:")
for stat in regional_stats:
    print(f"  {stat['region']}: {stat['count']} contracts, avg risk: {stat['avg_risk']:.2f}")
