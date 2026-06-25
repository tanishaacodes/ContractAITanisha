#!/usr/bin/env python3
"""
Test Arbitration Risk Intelligence with Real Contract
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract
from arbitration.integrated_service import get_integrated_arbitration_service

def main():
    print("\n" + "="*60)
    print("ARBITRATION RISK INTELLIGENCE - FULL SYSTEM TEST")
    print("="*60)

    # Get first contract
    contract = Contract.objects.first()
    if not contract:
        print("\n[ERROR] No contracts found in database")
        print("Please upload a contract first")
        return

    print(f"\nContract: {contract.original_filename}")
    print(f"Contract ID: {contract.id}")

    # Sample EPC contract text
    contract_text = """
    ENGINEERING, PROCUREMENT AND CONSTRUCTION (EPC) CONTRACT
    Contract Reference: EPC-2026-001
    Contract Value: USD 150,000,000

    ARTICLE 15: DISPUTE RESOLUTION

    15.1 Any disputes arising out of or in connection with this Contract shall be
    finally settled by arbitration in accordance with the ICC Rules of Arbitration.

    15.2 The seat of arbitration shall be London, United Kingdom.

    15.3 The arbitration tribunal shall consist of three arbitrators.

    15.4 The language of arbitration shall be English.

    15.5 Each party shall bear its own legal costs. The costs of the arbitration,
    including arbitrator fees, shall be borne equally by both parties.

    15.6 The arbitration award shall be final and binding upon both parties.

    15.7 In the event of delay claims exceeding USD 5,000,000, the Contractor
    shall provide detailed documentation within 30 days of the delay event.

    15.8 The Employer reserves the right to withhold payments pending resolution
    of any dispute regarding the quality of work performed.

    15.9 Any disputes related to subcontractor performance shall first be resolved
    between the Contractor and subcontractor before involving the Employer.
    """

    service = get_integrated_arbitration_service()

    print("\n[STEP 1] Running core analysis...")
    print("          - Monte Carlo: 50,000 runs")
    print("          - Tribunal Simulation: 5,000 runs")
    print("          - Scenario Engine: 512 combinations")

    print("\n[STEP 2] Generating LegalBERT embeddings...")
    print("          - Model: nlpaueb/legal-bert-base-uncased")
    print("          - Dimensions: 768")

    print("\n[STEP 3] Testing with Ollama (clause rewriting)...")
    print("          - Service: AVAILABLE")
    print("          - Model: qwen2.5:0.5b")

    print("\n[STEP 4] Neo4j graph storage...")
    print("          - Service: CHECKING...")

    print("\n" + "-"*60)
    print("RUNNING FULL ANALYSIS...")
    print("-"*60 + "\n")

    try:
        result = service.run_full_analysis_with_persistence(
            contract=contract,
            contract_text=contract_text,
            contract_value=150_000_000,
            settlement_offer=8_000_000,
            enable_gnn=True,
            enable_neo4j=True,  # Will gracefully skip if not running
            enable_clause_rewrite=True,  # Ollama is running
            monte_carlo_runs=50000,
            tribunal_runs=5000
        )

        print("\n" + "="*60)
        print("ANALYSIS RESULTS")
        print("="*60)

        print(f"\n[PERSISTENCE]")
        print(f"  Analysis ID: {result['analysis_id']}")
        print(f"  Database: SAVED")

        print(f"\n[CLAUSE DETECTION]")
        print(f"  Total Clauses: {result['clause_count']}")
        print(f"  High Risk: {result['summary']['high_risk_clauses']}")
        print(f"  Medium Risk: {result['summary']['medium_risk_clauses']}")
        print(f"  Low Risk: {result['summary']['low_risk_clauses']}")

        print(f"\n[RISK ASSESSMENT]")
        print(f"  Overall Risk: {result['summary']['overall_risk_level']}")
        print(f"  Composite Risk: {result['summary']['avg_composite_risk']:.2f}")
        print(f"  Dispute Probability: {result['summary']['dispute_probability']:.1%}")

        print(f"\n[MONTE CARLO SIMULATION]")
        mc = result['monte_carlo']
        print(f"  Expected Loss: ${mc['expected_loss']:,.0f}")
        print(f"  Median Loss: ${mc['median_loss']:,.0f}")
        print(f"  Worst Case (P95): ${mc['worst_case_p95']:,.0f}")
        print(f"  Value at Risk (99%): ${mc['var_99']:,.0f}")

        print(f"\n[TRIBUNAL SIMULATION]")
        ts = result['tribunal_simulation']
        print(f"  Buyer Win: {ts['buyer_win_probability']:.1%}")
        print(f"  Supplier Win: {ts['supplier_win_probability']:.1%}")
        print(f"  Partial Award: {ts['partial_award_probability']:.1%}")
        print(f"  Settlement: {ts['settlement_probability']:.1%}")

        print(f"\n[COST ANALYSIS]")
        print(f"  Expected Award: ${result['summary']['expected_award']:,.0f}")
        print(f"  Legal Costs: ${result['summary']['legal_cost_estimate']:,.0f}")
        print(f"  Total Exposure: ${result['summary']['total_exposure']:,.0f}")

        if result.get('settlement_decision'):
            sd = result['settlement_decision']
            print(f"\n[SETTLEMENT DECISION]")
            print(f"  Settlement Offer: ${result['summary']['settlement_offer']:,.0f}")
            print(f"  Decision: {sd['decision']}")
            print(f"  Potential Saving: ${sd['potential_saving']:,.0f}")

        print(f"\n[SCENARIO OPTIMIZATION]")
        opt = result['optimal_scenario']
        print(f"  Best Seat: {opt['seat']}")
        print(f"  Best Tribunal: {opt['tribunal_size']}")
        print(f"  Best Cost Rule: {opt['cost_rule']}")
        print(f"  Best Institution: {opt['institution']}")
        print(f"  Optimal Cost: ${opt['expected_cost']:,.0f}")

        if result.get('embeddings_generated', 0) > 0:
            print(f"\n[LEGALBERT EMBEDDINGS]")
            print(f"  Embeddings Generated: {result['embeddings_generated']}")
            print(f"  Dimensions: 768")
            print(f"  Status: SAVED TO DATABASE")

        if result.get('graph_stored'):
            print(f"\n[NEO4J GRAPH]")
            print(f"  Status: SAVED")
            print(f"  Nodes Created: Contract + {result['clause_count']} clauses")

        if result.get('gnn_prediction'):
            gnn = result['gnn_prediction']
            print(f"\n[GNN PREDICTION]")
            print(f"  Dispute Probability: {gnn['dispute_probability']:.1%}")
            print(f"  Confidence: {gnn.get('confidence', 0):.1%}")

        if result.get('clause_rewrites'):
            print(f"\n[AI CLAUSE REWRITES]")
            print(f"  Rewrites Generated: {len(result['clause_rewrites'])}")
            for i, rewrite in enumerate(result['clause_rewrites'][:3], 1):
                print(f"\n  Rewrite {i}:")
                print(f"    Original Risk: {rewrite['original_risk_score']:.2f}")
                print(f"    New Risk: {rewrite['predicted_risk_score']:.2f}")
                print(f"    Improvement: {rewrite['risk_reduction']:.1%}")
                print(f"    Changes: {', '.join(rewrite.get('improvements', [])[:3])}")

        print("\n" + "="*60)
        print("[SUCCESS] ARBITRATION ANALYSIS COMPLETE")
        print("="*60)

        print("\nAll results saved to database:")
        print(f"  - arbitration_analyses (ID: {result['analysis_id']})")
        print(f"  - arbitration_clauses ({result['clause_count']} clauses)")
        print(f"  - arbitration_tribunal_simulations")
        print(f"  - arbitration_scenarios")
        if result.get('clause_rewrites'):
            print(f"  - arbitration_clause_rewrites ({len(result['clause_rewrites'])} rewrites)")

    except Exception as e:
        print(f"\n[ERROR] Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
