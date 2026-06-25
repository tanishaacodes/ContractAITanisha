"""
Test Risk & Exposure endpoints
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from risk.services.risk_engine import get_risk_engine
from risk.models import VendorExposure, ContractRisk
from django.db.models import Count, Avg

print("=" * 60)
print("[*] Testing Risk & Exposure Endpoints")
print("=" * 60)

# Test 1: Regional Heatmap
print("\n[1] Testing Regional Heatmap...")
try:
    engine = get_risk_engine()
    regional_data = engine.get_regional_risk_heatmap()
    print(f"[+] SUCCESS: {len(regional_data)} regions")
    for region in regional_data[:3]:
        print(f"  - {region['region']}: risk={region['risk']}, contracts={region['contract_count']}")
except Exception as e:
    print(f"[!] ERROR: {e}")

# Test 2: Vendor Exposure
print("\n[2] Testing Vendor Exposure...")
try:
    vendors = VendorExposure.objects.order_by('-total_exposure')[:5]
    print(f"[+] SUCCESS: {vendors.count()} vendors")
    for v in vendors:
        print(f"  - {v.party.name}: exposure={v.total_exposure:.2f}, contracts={v.contract_count}")
except Exception as e:
    print(f"[!] ERROR: {e}")

# Test 3: Portfolio Overview
print("\n[3] Testing Portfolio Overview...")
try:
    total = ContractRisk.objects.count()
    avg_risk = ContractRisk.objects.aggregate(Avg('overall_risk_score'))['overall_risk_score__avg']
    high_risk = ContractRisk.objects.filter(overall_risk_score__gte=0.6).count()
    print(f"[+] SUCCESS: {total} contracts, avg risk={avg_risk:.2f}, high risk={high_risk}")
except Exception as e:
    print(f"[!] ERROR: {e}")

print("\n" + "=" * 60)
print("[*] All Tests Complete!")
print("=" * 60)
