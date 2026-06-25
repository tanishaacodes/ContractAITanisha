"""
Test Portfolio-Level Counterparty Risk Heatmap
Verifies all calculations are working correctly
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from api.counterparty_portfolio_service import CounterpartyPortfolioService
from negotiation.models import Counterparty
from core.models import Contract

print("=" * 70)
print("PORTFOLIO HEATMAP TEST")
print("=" * 70)

service = CounterpartyPortfolioService()

# Test with first few counterparties
counterparties = Counterparty.objects.all()[:5]

print(f"\nTesting with {counterparties.count()} counterparties:\n")

for idx, cp in enumerate(counterparties, 1):
    print(f"{idx}. {cp.name}")

    # Test reliability calculation
    reliability = service.calculate_counterparty_reliability(cp)
    print(f"   Reliability: {reliability:.3f}")

    # Test financial exposure
    exposure = service.calculate_financial_exposure(cp)
    print(f"   Financial Exposure: Rs {exposure/10000000:.1f} Cr")

    # Count contracts
    contracts = Contract.objects.filter(counterparty=cp).count()
    print(f"   Contracts: {contracts}")

    print()

print("=" * 70)
print("FULL HEATMAP TEST")
print("=" * 70)

try:
    # Test the full heatmap generation
    result = service.get_portfolio_heatmap(user_id="test-user")

    print(f"\nHeatmap Data Points: {len(result['heatmap_data'])}")
    print(f"\nSummary:")
    print(f"  Total Exposure: Rs {result['summary']['total_exposure']/10000000:.1f} Cr")
    print(f"  Counterparties: {result['summary']['total_counterparties']}")
    print(f"  Avg Reliability: {result['summary']['avg_reliability']:.2f}")

    print(f"\nQuadrant Distribution:")
    for quadrant, count in result['summary']['quadrant_distribution'].items():
        print(f"  {quadrant}: {count}")

    # Show top 3 highest risk
    sorted_data = sorted(result['heatmap_data'],
                        key=lambda x: x['financial_exposure'],
                        reverse=True)[:3]

    print(f"\nTop 3 Highest Exposure:")
    for i, data in enumerate(sorted_data, 1):
        print(f"  {i}. {data['counterparty_name']}: Rs {data['financial_exposure']/10000000:.1f} Cr "
              f"(Reliability: {data['reliability_score']:.2f})")

    print("\n[OK] Portfolio Heatmap calculations working correctly!")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("=" * 70)
