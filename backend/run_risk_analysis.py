import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, User, Clause, TemplateClause
from api.risk_analyzer import analyze_contract_risk

# Get the user's contract
user = User.objects.get(email='vanshshriwastava821@gmail.com')
contract = Contract.objects.filter(user=user).first()

if not contract:
    print("[ERROR] No contract found for user")
    sys.exit(1)

print(f"[INFO] Analyzing contract: {contract.original_filename}")
print(f"[INFO] Contract ID: {contract.id}")

# First, create some template clauses if they don't exist
if not TemplateClause.objects.filter(contract_type='General Contract').exists():
    print("[INFO] Creating template clauses...")
    TemplateClause.objects.create(
        contract_type='General Contract',
        clause_name='Termination Clause',
        importance='CRITICAL',
        risk_keywords=['immediate termination', 'no notice', 'penalty']
    )
    TemplateClause.objects.create(
        contract_type='General Contract',
        clause_name='Payment Terms',
        importance='CRITICAL',
        risk_keywords=['late payment', 'penalty', 'interest']
    )
    TemplateClause.objects.create(
        contract_type='General Contract',
        clause_name='Liability Clause',
        importance='IMPORTANT',
        risk_keywords=['unlimited liability', 'no cap']
    )

# Create some dummy clauses for the contract
if not Clause.objects.filter(contract=contract).exists():
    print("[INFO] Creating clauses for contract...")
    Clause.objects.create(
        contract=contract,
        clause_name='Termination Clause',
        found=True,
        confidence=85.5,
        match_count=1,
        extracted_text='Either party may terminate this agreement with 30 days notice.'
    )
    Clause.objects.create(
        contract=contract,
        clause_name='Payment Terms',
        found=True,
        confidence=90.0,
        match_count=1,
        extracted_text='Payment shall be made within 30 days of invoice date.'
    )

# Run risk analysis
print("[INFO] Running risk analysis...")
try:
    risk_analysis = analyze_contract_risk(contract.id)
    print(f"[SUCCESS] Risk analysis completed!")
    print(f"   Risk Level: {risk_analysis.risk_level}")
    print(f"   Risk Score: {risk_analysis.risk_score}/100")
    print(f"   Critical Issues: {risk_analysis.critical_issues}")
    print(f"   Medium Issues: {risk_analysis.medium_issues}")
    print(f"   Low Issues: {risk_analysis.low_issues}")
    print(f"   Total Deviations: {risk_analysis.total_deviations}")
except Exception as e:
    print(f"[ERROR] Risk analysis failed: {e}")
    import traceback
    traceback.print_exc()
