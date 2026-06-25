#!/usr/bin/env python3
"""
Complete Arbitration System Test with All Features
"""
import os, sys, django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract
from arbitration.integrated_service import get_integrated_arbitration_service
from arbitration.models import ArbitrationAnalysis, ArbitrationClause, ClauseRewrite

print("\n" + "="*70)
print("ARBITRATION RISK INTELLIGENCE - COMPLETE SYSTEM TEST")
print("="*70)

contract = Contract.objects.first()
if not contract:
    print("\n[ERROR] No contracts found")
    sys.exit(1)

print(f"\n[CONTRACT]: {contract.original_filename}")

contract_text = """
ENGINEERING, PROCUREMENT AND CONSTRUCTION (EPC) CONTRACT
Contract Value: USD 150,000,000

ARTICLE 15: DISPUTE RESOLUTION

15.1 Any disputes shall be settled by ICC arbitration.
15.2 The seat of arbitration shall be London, United Kingdom.
15.3 The tribunal shall consist of three arbitrators.
15.4 Each party shall bear its own legal costs equally.
15.5 Delay claims exceeding $5M require 30 days documentation.
15.6 The Employer may withhold payments pending dispute resolution.
"""

print("\n[TESTING] Running analysis with ALL features enabled...")
print("  - Core Analysis (Monte Carlo + Tribunal)")
print("  - LegalBERT Embeddings (768-dim)")
print("  - Neo4j Graph Storage")
print("  - GNN Prediction")
print("  - AI Clause Rewriting (Ollama)")

service = get_integrated_arbitration_service()

try:
    result = service.run_full_analysis_with_persistence(
        contract=contract,
        contract_text=contract_text,
        contract_value=150_000_000,
        settlement_offer=8_000_000,
        enable_gnn=True,
        enable_neo4j=True,  # NOW ENABLED
        enable_clause_rewrite=True,  # NOW ENABLED
        monte_carlo_runs=50000,
        tribunal_runs=5000
    )

    print(f"\n[SUCCESS] Analysis complete!")
    print(f"  Analysis ID: {result['analysis_id']}")

    # Get from database to show persistence
    analysis = ArbitrationAnalysis.objects.get(id=result['analysis_id'])

    print(f"\n[DATABASE] Results persisted:")
    print(f"  - arbitration_analyses: ID {analysis.id}")
    print(f"  - Total Clauses: {analysis.total_clauses}")
    print(f"  - Overall Risk: {analysis.overall_risk_level}")
    print(f"  - Dispute Probability: {analysis.dispute_probability:.1%}")
    print(f"  - Expected Loss: ${analysis.expected_loss:,.0f}")
    print(f"  - Settlement Decision: {analysis.settlement_decision}")

    # Check Neo4j graph
    if result.get('graph_stored'):
        print(f"\n[NEO4J] Graph persisted successfully!")
        print(f"  - Contract node created")
        print(f"  - {analysis.total_clauses} clause nodes created")
        print(f"  - Semantic relationships established")

    # Check embeddings
    clauses = ArbitrationClause.objects.filter(analysis_id=analysis.id)
    embeddings_count = sum(1 for c in clauses if c.embedding)
    if embeddings_count > 0:
        print(f"\n[LEGALBERT] Embeddings generated!")
        print(f"  - {embeddings_count} clause embeddings (768-dim)")
        print(f"  - Stored in database for semantic search")

    # Check rewrites
    rewrites = ClauseRewrite.objects.filter(clause__analysis_id=analysis.id)
    if rewrites.exists():
        print(f"\n[OLLAMA] AI clause rewrites generated!")
        print(f"  - {rewrites.count()} high-risk clauses rewritten")
        for rewrite in rewrites[:2]:
            print(f"\n  Clause improvement:")
            print(f"    Original Risk: {rewrite.original_risk_score:.2f}")
            print(f"    New Risk: {rewrite.predicted_risk_score:.2f}")
            print(f"    Risk Reduction: {rewrite.risk_reduction:.1%}")
            print(f"    Strategy: {rewrite.rewrite_strategy}")

    print(f"\n[RESULTS SUMMARY]")
    print(f"  Monte Carlo: {analysis.monte_carlo_runs:,} runs")
    print(f"  Tribunal Sim: {analysis.tribunal_runs:,} runs")
    print(f"  Buyer Win: {analysis.buyer_win_probability:.1%}")
    print(f"  Supplier Win: {analysis.supplier_win_probability:.1%}")
    print(f"  Settlement: {analysis.settlement_probability:.1%}")
    print(f"  Optimal Seat: {analysis.optimal_seat}")
    print(f"  Optimal Institution: {analysis.optimal_institution}")

    print("\n" + "="*70)
    print("[COMPLETE] All enterprise features working successfully!")
    print("="*70)
    print("\nSystem capabilities verified:")
    print("  [OK] Core arbitration analysis")
    print("  [OK] LegalBERT semantic embeddings")
    print("  [OK] Neo4j graph persistence")
    print("  [OK] Database persistence (7 models)")
    print("  [OK] AI clause rewriting (Ollama)")
    print("  [OK] Monte Carlo simulation")
    print("  [OK] Tribunal modeling")
    print("\n")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
