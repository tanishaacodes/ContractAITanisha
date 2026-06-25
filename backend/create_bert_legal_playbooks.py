"""
Create BERT versions of all Legal Playbooks (Playbook Automation)
This is different from RiskPlaybooks (risk scoring)
"""
import django
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from api.embedding_service import EmbeddingService
from core.models import LegalPlaybook

print("=" * 70)
print("CREATING BERT VERSIONS OF LEGAL PLAYBOOKS")
print("=" * 70)

embedding_service = EmbeddingService()

# Get all MiniLM legal playbooks
minilm_playbooks = LegalPlaybook.objects.filter(embedding_model='all-MiniLM-L6-v2')
total = minilm_playbooks.count()

print(f"\nFound {total} MiniLM Legal Playbooks")

if total == 0:
    print("No MiniLM playbooks found")
    sys.exit(0)

# Switch to BERT
print("\nSwitching to BERT...")
EmbeddingService.switch_model('bert-large-uncased')
print(f"Active: {embedding_service.current_key} ({embedding_service.dimensions}-dim)")

created = 0
skipped = 0

print("\nCreating BERT versions...")
print("-" * 70)

for pb in minilm_playbooks:
    # Check if BERT version exists
    exists = LegalPlaybook.objects.filter(
        clause_type=pb.clause_type,
        jurisdiction=pb.jurisdiction,
        embedding_model='bert-large-uncased'
    ).exists()

    if exists:
        print(f"SKIP: {pb.clause_type}/{pb.jurisdiction}")
        skipped += 1
        continue

    # Generate BERT embedding
    bert_emb = embedding_service.embed_text(pb.standard_clause)

    # Create BERT version
    LegalPlaybook.objects.create(
        clause_type=pb.clause_type,
        jurisdiction=pb.jurisdiction,
        standard_clause=pb.standard_clause,
        fallback_clause=pb.fallback_clause,
        embedding=bert_emb,
        embedding_model='bert-large-uncased',
        similarity_threshold=pb.similarity_threshold,
        mandatory=pb.mandatory
    )

    print(f"[OK] {pb.clause_type}/{pb.jurisdiction} ({len(bert_emb)}-dim)")
    created += 1

print()
print("=" * 70)
print(f"Created: {created} | Skipped: {skipped}")
print("[OK] Both models now have Legal Playbooks")
print("=" * 70)
