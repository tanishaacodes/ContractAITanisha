"""
Test silent risk detection directly
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, Clause
from ai.silent_risk_engine import detect_silent_risks, generate_silent_risk_heatmap

# Get first tesy.pdf contract
contract = Contract.objects.filter(filename__icontains='tesy').first()
print(f"Testing contract: {contract.id}")
print(f"Contract value: {contract.contract_value}")

# Get clauses
clauses = Clause.objects.filter(contract=contract).order_by('-id')[:15]
print(f"Clauses to analyze: {clauses.count()}")

clauses_with_text = [c for c in clauses if c.extracted_text]
print(f"Clauses with text: {len(clauses_with_text)}")

if len(clauses_with_text) > 0:
    print("\nClause types:")
    for c in clauses_with_text:
        print(f"  - {c.clause_type}")

print("\n" + "="*60)
print("DETECTING SILENT RISKS")
print("="*60)

try:
    silent_risks = detect_silent_risks(contract, clauses)
    print(f"\nFound {len(silent_risks)} risks")

    for i, risk in enumerate(silent_risks[:5], 1):
        print(f"\n{i}. {risk['risk_type']}")
        print(f"   Exposure: ₹{risk['financial_exposure']/10000000:.1f} Cr")
        print(f"   Confidence: {risk['confidence']:.0%}")
        print(f"   Clauses: {risk['clause_pair']}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("GENERATING HEATMAP")
print("="*60)

try:
    heatmap = generate_silent_risk_heatmap(contract, clauses)
    print(f"\nClauses: {len(heatmap.get('clauses', []))}")
    print(f"Matrix entries: {len(heatmap.get('matrix', {}))}")

    if heatmap.get('matrix'):
        print("\nSample matrix entries:")
        for key, value in list(heatmap['matrix'].items())[:3]:
            print(f"  {key}: exposure={value.get('financial_exposure', 0)}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
