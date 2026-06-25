"""
Test Portfolio Risk Detail API Endpoint
"""
import os
import sys
import django

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from core.models import Contract
from api.counterparty_portfolio_service import counterparty_portfolio_service

print("=" * 70)
print("PORTFOLIO RISK DETAIL API TEST")
print("=" * 70)

# Get a contract with counterparty
contracts_with_cp = Contract.objects.filter(counterparty__isnull=False).first()

if not contracts_with_cp:
    print("[ERROR] No contracts with counterparty found")
    exit(1)

contract = contracts_with_cp
print(f"\n[TEST] Testing with Contract: {contract.original_filename or contract.filename}")
print(f"Contract ID: {contract.id}")
print(f"Counterparty: {contract.counterparty.name}")

try:
    result = counterparty_portfolio_service.get_contract_risk_detail(str(contract.id))

    print("\n[SUCCESS] API endpoint returned data successfully")
    print("\n" + "=" * 70)
    print("RESPONSE STRUCTURE")
    print("=" * 70)

    # Contract Info
    print("\n[1] Contract Information:")
    print(f"  Name: {result['contract']['name']}")
    print(f"  Value: {result['contract']['value']}")
    print(f"  Has Counterparty: {result['contract']['has_counterparty']}")

    # Counterparty Profile
    print("\n[2] Counterparty Profile:")
    print(f"  Name: {result['counterparty_profile']['name']}")
    print(f"  Industry: {result['counterparty_profile']['industry']}")
    print(f"  Reliability: {result['counterparty_profile']['reliability_score']:.3f}")
    print(f"  Total Contracts: {result['counterparty_profile']['total_contracts']}")

    # Reliability Breakdown
    print("\n[3] Reliability Breakdown:")
    rb = result['reliability_breakdown']
    print(f"  Overall Score: {rb['overall_score']:.3f}")
    print(f"  Acceptance Rate: {rb['acceptance_rate']:.1%} (40% weight)")
    print(f"  Stall Rate: {rb['stall_rate']:.1%} (30% weight)")
    print(f"  Avg Redline Rounds: {rb['avg_redline_rounds']:.1f}")
    print(f"  Deviation Score: {rb['deviation_score']:.3f}")
    print(f"  History Records: {rb['history_records']}")

    # Financial Exposure
    print("\n[4] Financial Exposure:")
    fe = result['financial_exposure']
    print(f"  Total: Rs {fe['total']/10000000:.2f} Cr")
    print(f"  Contract Value: Rs {fe['contract_value']/10000000:.2f} Cr")
    print(f"  Total Liability: Rs {fe['total_liability']/10000000:.2f} Cr")
    print(f"  Silent Risk: Rs {fe['silent_risk_exposure']/10000000:.2f} Cr")

    # Failure Analysis
    print("\n[5] Bayesian Failure Analysis:")
    fa = result['failure_analysis']
    print(f"  Probability: {fa['probability']:.1%}")
    print(f"  Risk Level: {fa['risk_level']}")
    print(f"  Explanation: {fa['explanation']}")

    # Portfolio Context
    print("\n[6] Portfolio Context:")
    pc = result['portfolio_context']
    print(f"  Counterparty Total Exposure: Rs {pc['counterparty_total_exposure']/10000000:.2f} Cr")
    print(f"  Related Contracts: {pc['related_contracts_count']}")
    print(f"  Portfolio Percentage: {pc['portfolio_percentage']:.2f}%")
    print(f"  Total Portfolio Exposure: Rs {pc['user_total_exposure']/10000000:.2f} Cr")

    # Risk Quadrant
    print("\n[7] Risk Quadrant & Actions:")
    print(f"  Quadrant: {result['risk_quadrant']}")
    print(f"  Recommended Actions: {len(result['recommended_actions'])} actions")

    for i, action in enumerate(result['recommended_actions'], 1):
        print(f"\n  Action {i} [{action['priority']}]:")
        print(f"    - {action['action']}")
        print(f"    - Rationale: {action['rationale']}")

    print("\n" + "=" * 70)
    print("[OK] Portfolio Risk Detail API Test PASSED")
    print("=" * 70)

except Exception as e:
    print(f"\n[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
