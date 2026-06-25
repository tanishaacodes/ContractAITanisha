"""
Verify all Risk & Exposure data is ready
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from risk.models import ContractRisk, VendorExposure, CrossContractCorrelation, ClauseRisk
from django.db.models import Count, Avg

print("\n" + "=" * 70)
print("  RISK & EXPOSURE DASHBOARD - DATA VERIFICATION")
print("=" * 70)

# Check 1: Contracts analyzed
contract_count = ContractRisk.objects.count()
print(f"\n[1] Contracts Analyzed: {contract_count}/41")
if contract_count >= 40:
    print("    [PASS] PASS - Sufficient contracts analyzed")
else:
    print("    [FAIL] FAIL - Need more contracts analyzed")

# Check 2: Average risk score
avg_risk = ContractRisk.objects.aggregate(Avg('overall_risk_score'))['overall_risk_score__avg']
print(f"\n[2] Average Risk Score: {avg_risk:.3f}")
if avg_risk > 0:
    print("    [PASS] PASS - Risk scores calculated")
else:
    print("    [FAIL] FAIL - Risk scores missing")

# Check 3: Regional data
regions_with_data = ContractRisk.objects.filter(
    region__isnull=False
).exclude(region='').values('region').distinct().count()
print(f"\n[3] Regions with Data: {regions_with_data}")
if regions_with_data >= 3:
    print("    [PASS] PASS - Regional coverage good")
    regional_breakdown = ContractRisk.objects.filter(
        region__isnull=False
    ).exclude(region='').values('region').annotate(
        count=Count('id'),
        avg_risk=Avg('overall_risk_score')
    ).order_by('-count')[:5]

    for region in regional_breakdown:
        print(f"       - {region['region']}: {region['count']} contracts, avg risk {region['avg_risk']:.2f}")
else:
    print("    [FAIL] FAIL - Need more regional data")

# Check 4: Vendor exposure
vendor_count = VendorExposure.objects.count()
print(f"\n[4] Vendors Tracked: {vendor_count}")
if vendor_count >= 5:
    print("    [PASS] PASS - Vendor exposure calculated")
    top_vendors = VendorExposure.objects.order_by('-total_exposure')[:5]
    for v in top_vendors:
        print(f"       - {v.party.name}: {v.total_exposure:.2f} exposure, {v.contract_count} contracts")
else:
    print("    [FAIL] FAIL - Need vendor exposure data")

# Check 5: Clauses analyzed
clause_count = ClauseRisk.objects.count()
print(f"\n[5] Clauses Analyzed: {clause_count}")
if clause_count > 100:
    print("    [PASS] PASS - Comprehensive clause analysis")
else:
    print("    [WARN]  WARNING - Limited clause analysis")

# Check 6: Correlations
correlation_count = CrossContractCorrelation.objects.count()
print(f"\n[6] Cross-Contract Correlations: {correlation_count}")
if correlation_count > 0:
    print("    [PASS] PASS - Correlations detected")
else:
    print("    [WARN]  WARNING - No correlations found")

# Check 7: High risk contracts
high_risk_count = ContractRisk.objects.filter(overall_risk_score__gte=0.6).count()
critical_risk_count = ContractRisk.objects.filter(overall_risk_score__gte=0.8).count()
print(f"\n[7] Risk Distribution:")
print(f"    - High Risk (>=0.6): {high_risk_count}")
print(f"    - Critical Risk (>=0.8): {critical_risk_count}")
if high_risk_count > 0:
    print("    [PASS] PASS - Risk distribution calculated")

# Final summary
print("\n" + "=" * 70)
print("  SUMMARY")
print("=" * 70)

checks_passed = 0
total_checks = 7

if contract_count >= 40: checks_passed += 1
if avg_risk > 0: checks_passed += 1
if regions_with_data >= 3: checks_passed += 1
if vendor_count >= 5: checks_passed += 1
if clause_count > 100: checks_passed += 1
if correlation_count > 0: checks_passed += 1
if high_risk_count > 0: checks_passed += 1

print(f"\n  Checks Passed: {checks_passed}/{total_checks}")

if checks_passed == total_checks:
    print("\n  [PASS] ALL SYSTEMS GO - Risk & Exposure Dashboard Ready!")
elif checks_passed >= 5:
    print("\n  [WARN]  MOSTLY READY - Some optional features may be limited")
else:
    print("\n  [FAIL] NOT READY - Critical data missing")

print("\n" + "=" * 70)
print()
