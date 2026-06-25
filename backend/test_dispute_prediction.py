"""
Test script to verify the dispute prediction pipeline works end-to-end.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from dispute_predictor.dispute_service import predict_dispute

def test_prediction():
    print("=" * 80)
    print("TESTING DISPUTE PREDICTION PIPELINE")
    print("=" * 80)

    # Sample contract text
    contract_text = """
    This Software Development and Licensing Agreement ("Agreement") is entered into between
    TechCorp Solutions Inc. ("Supplier") and GlobalBank Financial Services Ltd. ("Buyer") for the
    development, delivery, and licensing of a core banking platform valued at $8,500,000.

    DELIVERY AND PERFORMANCE OBLIGATIONS
    The Supplier shall use best efforts to deliver the software modules in accordance with the project
    milestones. In the event of supplier delay exceeding 45 days, liquidated damages shall apply at
    the reasonable discretion of the Buyer. The Supplier bears full responsibility for any delivery failure
    or service failure caused by inadequate resource allocation.

    PAYMENT TERMS
    Payment shall be made within 30 days of invoice submission. The Buyer reserves the right to
    withhold payment in case of service quality issues or SLA violations.

    LIABILITY AND INDEMNIFICATION
    The parties agree that liability shall be limited to the contract value, except in cases of gross
    negligence or willful misconduct. The Supplier shall indemnify the Buyer against all third-party
    claims arising from the software.

    TERMINATION
    Either party may terminate this Agreement with 60 days written notice. Upon termination, all
    outstanding payments become immediately due and payable.
    """

    contract_value = 8500000

    print("\n Contract Preview:")
    print(contract_text[:300] + "...")
    print(f"\n Contract Value: ${contract_value:,}")

    print("\n Running prediction...")

    try:
        result = predict_dispute(
            contract_text=contract_text,
            contract_value=contract_value
        )

        print("\n[OK] PREDICTION SUCCESSFUL!\n")
        print("=" * 80)
        print("RESULTS")
        print("=" * 80)

        print(f"\n* Overall Dispute Probability: {result['dispute_probability']:.1%}")
        print(f"*  Arbitration Probability: {result['arbitration_probability']:.1%}")
        print(f"* Contract Risk Score: {result['contract_risk_score']:.1%}")
        print(f"* Legal Cost Exposure: ${result['legal_cost_exposure']:,.0f}")

        print("\n RISK BREAKDOWN:")
        print("-" * 80)
        for category, score in result['risk_breakdown'].items():
            bar = "█" * int(score * 50)
            print(f"{category:.<30} {score:.1%} {bar}")

        print("\n TOP RISK DRIVERS:")
        print("-" * 80)
        for i, driver in enumerate(result['top_risk_drivers'][:5], 1):
            print(f"{i}. {driver['node']:.<40} {driver['risk']:.1%}")

        print("\n EXPLANATION:")
        print("-" * 80)
        print(result['explanation'])

        print("\n DETECTED RISKY CLAUSES:")
        print("-" * 80)
        for i, clause in enumerate(result['risky_clauses'][:3], 1):
            print(f"\n{i}. {clause['type'].upper()} (Risk: {clause['risk_score']:.1%})")
            print(f"   \"{clause['text'][:100]}...\"")

        print("\n" + "=" * 80)
        print("[OK] TEST COMPLETED SUCCESSFULLY!")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_prediction()
    exit(0 if success else 1)
