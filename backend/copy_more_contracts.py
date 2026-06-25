import os
import sys
import django
import shutil
from pathlib import Path

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, User
from django.utils import timezone
from api.risk_analyzer import analyze_contract_risk

# Get the target user
target_user = User.objects.get(email='vanshshriwastava821@gmail.com')

# Get sample contracts from other users
sample_contracts = Contract.objects.filter(user__email='admin@example.com')[:5]

print(f"Copying {sample_contracts.count()} contracts to {target_user.email}...")

for sample in sample_contracts:
    source_file = Path(sample.file_path)
    if not source_file.exists():
        print(f"[SKIP] File not found: {source_file}")
        continue

    # Create new filename
    new_filename = f"{int(timezone.now().timestamp() * 1000)}-{sample.original_filename}"
    target_file = Path(sample.file_path).parent / new_filename

    # Copy file
    shutil.copy2(source_file, target_file)

    # Create new contract record
    new_contract = Contract.objects.create(
        user=target_user,
        original_filename=sample.original_filename,
        file_path=str(target_file),
        full_text=sample.full_text,
        contract_type=sample.contract_type or 'General Contract',
        confidence_score=sample.confidence_score or 50.0,
        party_a=sample.party_a,
        party_b=sample.party_b,
        contract_value=sample.contract_value,
        start_date=sample.start_date,
        end_date=sample.end_date,
        status='DRAFT'
    )

    print(f"[SUCCESS] Copied: {new_contract.original_filename} (ID: {new_contract.id})")

    # Run risk analysis
    try:
        risk = analyze_contract_risk(new_contract.id)
        print(f"   Risk: {risk.risk_level} (Score: {risk.risk_score})")
    except Exception as e:
        print(f"   Risk analysis failed: {e}")

print(f"\n[DONE] Total contracts for {target_user.email}: {Contract.objects.filter(user=target_user).count()}")
