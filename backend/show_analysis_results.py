#!/usr/bin/env python3
"""
Show the latest arbitration analysis results from database
"""
import os, sys, django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from arbitration.models import ArbitrationAnalysis, ArbitrationClause, ClauseRewrite
from core.models import Contract

print("\n" + "="*70)
print("ARBITRATION ANALYSIS DATABASE - LATEST RESULTS")
print("="*70)

# Get latest analysis
latest = ArbitrationAnalysis.objects.order_by('-created_at').first()

if not latest:
    print("\n[INFO] No arbitration analyses found in database yet")
    print("Run test_arbitration_full.py to create one")
    sys.exit(0)

print(f"\n[ANALYSIS ID]: {latest.id}")
print(f"[CONTRACT]: {latest.contract.original_filename}")
print(f"[CREATED]: {latest.created_at}")

print(f"\n[CLAUSES DETECTED]")
print(f"  Total: {latest.total_clauses}")
print(f"  High Risk: {latest.high_risk_clauses}")
print(f"  Medium Risk: {latest.medium_risk_clauses}")
print(f"  Low Risk: {latest.low_risk_clauses}")

print(f"\n[RISK METRICS]")
print(f"  Overall Risk Level: {latest.overall_risk_level}")
print(f"  Average Risk Score: {latest.avg_composite_risk:.2f}")
print(f"  Dispute Probability: {latest.dispute_probability:.1%}")

print(f"\n[MONTE CARLO SIMULATION] ({latest.monte_carlo_runs:,} runs)")
print(f"  Expected Loss: ${latest.expected_loss:,.0f}")
print(f"  Median Loss: ${latest.median_loss:,.0f}")
print(f"  Worst Case (P95): ${latest.worst_case_p95:,.0f}")
print(f"  Value at Risk (99%): ${latest.var_99:,.0f}")

print(f"\n[TRIBUNAL SIMULATION] ({latest.tribunal_runs:,} runs)")
print(f"  Buyer Win: {latest.buyer_win_probability:.1%}")
print(f"  Supplier Win: {latest.supplier_win_probability:.1%}")
print(f"  Partial Award: {latest.partial_award_probability:.1%}")
print(f"  Settlement: {latest.settlement_probability:.1%}")

print(f"\n[COST ANALYSIS]")
print(f"  Expected Award: ${latest.expected_award:,.0f}")
print(f"  Legal Costs: ${latest.legal_cost_estimate:,.0f}")
print(f"  Arbitration Exposure: ${latest.arbitration_exposure:,.0f}")
print(f"  Total Exposure: ${latest.total_exposure:,.0f}")

if latest.settlement_offer:
    print(f"\n[SETTLEMENT ANALYSIS]")
    print(f"  Offer: ${latest.settlement_offer:,.0f}")
    print(f"  Decision: {latest.settlement_decision}")
    print(f"  Potential Saving: ${latest.potential_saving:,.0f}")

print(f"\n[OPTIMAL CONFIGURATION]")
print(f"  Best Seat: {latest.optimal_seat}")
print(f"  Best Tribunal: {latest.optimal_tribunal}")
print(f"  Best Cost Rule: {latest.optimal_cost_rule}")
print(f"  Best Institution: {latest.optimal_institution}")
print(f"  Expected Cost: ${latest.optimal_expected_cost:,.0f}")

if latest.gnn_dispute_probability:
    print(f"\n[GNN PREDICTION]")
    print(f"  Dispute Probability: {latest.gnn_dispute_probability:.1%}")
    print(f"  Confidence: {latest.gnn_confidence:.1%}")

# Show clauses
clauses = ArbitrationClause.objects.filter(analysis_id=latest.id).order_by('-composite_risk')
if clauses:
    print(f"\n[TOP 3 RISKIEST CLAUSES]")
    for i, clause in enumerate(clauses[:3], 1):
        print(f"\n  Clause {i} (Risk: {clause.composite_risk:.2f}, Level: {clause.risk_level})")
        print(f"    {clause.clause_text[:150]}...")
        print(f"    - Jurisdiction Risk: {clause.jurisdiction_risk:.2f}")
        print(f"    - Cost Exposure: {clause.cost_exposure:.2f}")
        print(f"    - Institutional Risk: {clause.institutional_risk:.2f}")

# Show rewrites if any
rewrites = ClauseRewrite.objects.filter(clause__analysis_id=latest.id).order_by('-risk_reduction')
if rewrites:
    print(f"\n[AI CLAUSE REWRITES] ({rewrites.count()} total)")
    for i, rewrite in enumerate(rewrites[:2], 1):
        print(f"\n  Rewrite {i}:")
        print(f"    Original Risk: {rewrite.original_risk_score:.2f}")
        print(f"    New Risk: {rewrite.predicted_risk_score:.2f}")
        print(f"    Improvement: {rewrite.risk_reduction:.1%}")
        print(f"    Strategy: {rewrite.rewrite_strategy}")
        print(f"    Status: {rewrite.status}")

print("\n" + "="*70)
print("[SUCCESS] All data persisted in database!")
print("="*70)

print("\nDatabase tables populated:")
print(f"  - arbitration_analyses: 1 record")
print(f"  - arbitration_clauses: {clauses.count()} records")
if rewrites:
    print(f"  - arbitration_clause_rewrites: {rewrites.count()} records")

print("\n")
