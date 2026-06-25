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

# Get the target user (vanshshriwastava821@gmail.com)
target_user = User.objects.get(email='vanshshriwastava821@gmail.com')

# Get a sample contract from another user
sample_contract = Contract.objects.filter(user__email='admin@example.com').first()

if not sample_contract:
    print("No sample contract found")
    sys.exit(1)

# Copy the contract file
source_file = Path(sample_contract.file_path)
if source_file.exists():
    # Create new filename
    new_filename = f"{int(timezone.now().timestamp() * 1000)}-{sample_contract.original_filename}"
    target_file = Path(sample_contract.file_path).parent / new_filename

    # Copy file
    shutil.copy2(source_file, target_file)

    # Create new contract record
    new_contract = Contract.objects.create(
        user=target_user,
        original_filename=sample_contract.original_filename,
        file_path=str(target_file),
        full_text=sample_contract.full_text,
        contract_type=sample_contract.contract_type,
        confidence_score=sample_contract.confidence_score,
        party_a=sample_contract.party_a,
        party_b=sample_contract.party_b,
        contract_value=sample_contract.contract_value,
        start_date=sample_contract.start_date,
        end_date=sample_contract.end_date,
        status='DRAFT'
    )

    print(f"[SUCCESS] Contract copied to {target_user.email}")
    print(f"   Contract: {new_contract.original_filename}")
    print(f"   ID: {new_contract.id}")
    print(f"   Type: {new_contract.contract_type}")
else:
    print(f"[ERROR] Source file not found: {source_file}")
