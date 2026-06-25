"""
Create BERT versions of all existing MiniLM risk playbooks.

This script:
1. Temporarily switches to BERT model
2. Reads all MiniLM playbooks (384-dim)
3. Creates BERT versions (1024-dim) with identical content
4. Switches back to original model
"""
import django
import os
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from api.embedding_service import EmbeddingService
from core.models import RiskPlaybook

print("=" * 70)
print("CREATING BERT VERSIONS OF ALL RISK PLAYBOOKS")
print("=" * 70)

# Get embedding service
embedding_service = EmbeddingService()

# Save current model
original_model = embedding_service.current_key
print(f"\nOriginal model: {original_model}")

# Get all MiniLM playbooks (384-dim)
minilm_playbooks = RiskPlaybook.objects.filter(embedding_model='all-MiniLM-L6-v2')
total_minilm = minilm_playbooks.count()

print(f"Found {total_minilm} MiniLM playbooks to duplicate")

if total_minilm == 0:
    print("No MiniLM playbooks found. Nothing to do.")
    sys.exit(0)

# Switch to BERT
print("\nSwitching to BERT model...")
EmbeddingService.switch_model('bert-large-uncased')
print(f"Active model: {embedding_service.current_key} ({embedding_service.dimensions}-dim)")

# Check if BERT playbooks already exist
existing_bert = RiskPlaybook.objects.filter(embedding_model='bert-large-uncased').count()
print(f"Existing BERT playbooks: {existing_bert}")

created_count = 0
skipped_count = 0

print("\nCreating BERT versions...")
print("-" * 70)

for playbook in minilm_playbooks:
    # Check if BERT version already exists with same risk_name
    bert_exists = RiskPlaybook.objects.filter(
        risk_name=playbook.risk_name,
        embedding_model='bert-large-uncased'
    ).exists()

    if bert_exists:
        print(f"SKIP  SKIP: {playbook.risk_name} (BERT version already exists)")
        skipped_count += 1
        continue

    # Generate BERT embedding for the example clause text
    bert_embedding = embedding_service.embed_text(playbook.example_clause_text)

    # Create BERT version
    bert_playbook = RiskPlaybook.objects.create(
        risk_name=playbook.risk_name,
        risk_type=playbook.risk_type,
        risk_description=playbook.risk_description,
        example_clause_text=playbook.example_clause_text,
        severity_weight=playbook.severity_weight,
        similarity_threshold=playbook.similarity_threshold,
        embedding=bert_embedding,
        embedding_model='bert-large-uncased',
        jurisdiction=playbook.jurisdiction,
        court_treatment=playbook.court_treatment,
        is_active=playbook.is_active
    )

    print(f"[OK] Created: {playbook.risk_name} ({len(bert_embedding)}-dim)")
    created_count += 1

print()
print("=" * 70)
print(f"SUMMARY")
print("=" * 70)
print(f"Total MiniLM playbooks: {total_minilm}")
print(f"Created BERT versions: {created_count}")
print(f"Skipped (already exist): {skipped_count}")
print()

# Switch back to original model
if original_model != 'bert-large-uncased':
    print(f"Switching back to {original_model}...")
    EmbeddingService.switch_model(original_model)
    print(f"Active model: {embedding_service.current_key}")

print()
print("[OK] Done! Both models now have complete knowledge bases.")
print("=" * 70)
