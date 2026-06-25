"""
End-to-End System Verification
Tests all major features of the Negotiation Intelligence Platform
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, Clause
from negotiation.models import Counterparty, NegotiationHistory
from api.counterparty_portfolio_service import CounterpartyPortfolioService

print("=" * 70)
print("CONTRACT RISK & FINANCIAL INTELLIGENCE PLATFORM")
print("END-TO-END SYSTEM VERIFICATION")
print("=" * 70)

# Track results
results = {}

# Test 1: Database Integrity
print("\n[1/6] DATABASE INTEGRITY")
print("-" * 70)
try:
    contracts = Contract.objects.count()
    clauses = Clause.objects.count()
    counterparties = Counterparty.objects.count()
    history = NegotiationHistory.objects.count()

    contracts_with_cp = Contract.objects.exclude(counterparty__isnull=True).count()

    print(f"Contracts: {contracts}")
    print(f"Clauses: {clauses}")
    print(f"Counterparties: {counterparties}")
    print(f"Negotiation History: {history}")
    print(f"Contracts with Counterparty: {contracts_with_cp}/{contracts} ({contracts_with_cp/contracts*100:.0f}%)")

    assert contracts > 0, "No contracts found"
    assert clauses > 0, "No clauses found"
    assert counterparties > 0, "No counterparties found"
    assert contracts_with_cp == contracts, "Not all contracts linked to counterparties"

    results['database'] = 'PASS'
    print("[OK] Database integrity verified")
except Exception as e:
    results['database'] = f'FAIL: {e}'
    print(f"[FAIL] {e}")

# Test 2: Counterparty Reliability Scoring
print("\n[2/6] COUNTERPARTY RELIABILITY SCORING")
print("-" * 70)
try:
    service = CounterpartyPortfolioService()
    cp = Counterparty.objects.first()

    reliability = service.calculate_counterparty_reliability(cp)

    print(f"Sample Counterparty: {cp.name}")
    print(f"Reliability Score: {reliability:.3f} (0=unreliable, 1=highly reliable)")

    assert 0 <= reliability <= 1, "Reliability score out of range"

    results['reliability_scoring'] = 'PASS'
    print("[OK] Reliability scoring working")
except Exception as e:
    results['reliability_scoring'] = f'FAIL: {e}'
    print(f"[FAIL] {e}")

# Test 3: Financial Exposure Calculation
print("\n[3/6] FINANCIAL EXPOSURE CALCULATION")
print("-" * 70)
try:
    service = CounterpartyPortfolioService()

    # Get counterparty with most contracts
    from django.db.models import Count
    cp = Counterparty.objects.annotate(
        contract_count=Count('contracts')
    ).order_by('-contract_count').first()

    exposure = service.calculate_financial_exposure(cp)
    contracts_count = Contract.objects.filter(counterparty=cp).count()

    print(f"Counterparty: {cp.name}")
    print(f"Contracts: {contracts_count}")
    print(f"Total Exposure: Rs {exposure/10000000:.1f} Cr")

    assert exposure >= 0, "Negative exposure"

    results['financial_exposure'] = 'PASS'
    print("[OK] Financial exposure calculation working")
except Exception as e:
    results['financial_exposure'] = f'FAIL: {e}'
    print(f"[FAIL] {e}")

# Test 4: Failure Probability (Bayesian)
print("\n[4/6] FAILURE PROBABILITY (BAYESIAN)")
print("-" * 70)
try:
    service = CounterpartyPortfolioService()
    cp = Counterparty.objects.first()

    reliability = service.calculate_counterparty_reliability(cp)
    failure_prob = service.calculate_failure_probability(cp, reliability)

    print(f"Counterparty: {cp.name}")
    print(f"Reliability: {reliability:.3f}")
    print(f"Failure Probability: {failure_prob:.3f}")

    assert 0 <= failure_prob <= 1, "Failure probability out of range"

    results['failure_probability'] = 'PASS'
    print("[OK] Bayesian failure probability working")
except Exception as e:
    results['failure_probability'] = f'FAIL: {e}'
    print(f"[FAIL] {e}")

# Test 5: Portfolio-Level Heatmap
print("\n[5/6] PORTFOLIO-LEVEL RISK HEATMAP")
print("-" * 70)
try:
    service = CounterpartyPortfolioService()

    # Get a user with contracts
    user_id = Contract.objects.first().user_id

    result = service.get_portfolio_heatmap(user_id=user_id)

    print(f"User ID: {user_id}")
    print(f"Data Points: {len(result['heatmap_data'])}")
    print(f"Total Exposure: Rs {result['summary']['total_exposure']/10000000:.1f} Cr")
    print(f"Counterparties: {result['summary']['total_counterparties']}")
    print(f"Avg Reliability: {result['summary']['avg_reliability']:.2f}")

    # Check quadrants
    quadrants = {}
    for point in result['heatmap_data']:
        q = point['quadrant']
        quadrants[q] = quadrants.get(q, 0) + 1

    print(f"\nQuadrant Distribution:")
    for q, count in quadrants.items():
        print(f"  {q}: {count}")

    assert len(result['heatmap_data']) > 0, "No heatmap data"
    assert result['summary']['total_exposure'] > 0, "Zero exposure"

    results['portfolio_heatmap'] = 'PASS'
    print("[OK] Portfolio heatmap generation working")
except Exception as e:
    results['portfolio_heatmap'] = f'FAIL: {e}'
    print(f"[FAIL] {e}")

# Test 6: Negotiation History Analysis
print("\n[6/6] NEGOTIATION HISTORY ANALYSIS")
print("-" * 70)
try:
    # Get behavior metrics for a counterparty
    cp = Counterparty.objects.first()
    history = NegotiationHistory.objects.filter(counterparty=cp)

    if history.count() > 0:
        total = history.count()
        acceptance_rate = history.filter(accepted=True).count() / total
        stall_rate = history.filter(stalled=True).count() / total
        avg_redlines = history.aggregate(
            avg=django.db.models.Avg('redline_rounds')
        )['avg'] or 0

        print(f"Counterparty: {cp.name}")
        print(f"History Records: {total}")
        print(f"Acceptance Rate: {acceptance_rate:.1%}")
        print(f"Stall Rate: {stall_rate:.1%}")
        print(f"Avg Redline Rounds: {avg_redlines:.1f}")

        results['negotiation_history'] = 'PASS'
        print("[OK] Negotiation history analysis working")
    else:
        results['negotiation_history'] = 'SKIP: No history'
        print("[SKIP] No negotiation history available")
except Exception as e:
    results['negotiation_history'] = f'FAIL: {e}'
    print(f"[FAIL] {e}")

# Summary
print("\n" + "=" * 70)
print("VERIFICATION SUMMARY")
print("=" * 70)

passed = sum(1 for r in results.values() if r == 'PASS')
failed = sum(1 for r in results.values() if 'FAIL' in r)
total = len(results)

for test, result in results.items():
    status = "[OK]" if result == 'PASS' else "[FAIL]" if 'FAIL' in result else "[SKIP]"
    print(f"{status} {test.replace('_', ' ').title()}: {result}")

print("\n" + "=" * 70)
print(f"RESULTS: {passed}/{total} tests passed")

if failed == 0:
    print("STATUS: SYSTEM 100% OPERATIONAL")
    print("\nYou have a production-grade Contract Risk & Financial Intelligence Platform.")
else:
    print(f"STATUS: {failed} tests failed - review errors above")

print("=" * 70)
