"""
Create BERT versions of ALL knowledge base items
Ensures both MiniLM and BERT have complete, identical knowledge bases
"""
import django
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from api.embedding_service import EmbeddingService
from core.models import IntentTemplate, ApprovedClause, GoldStandardTemplate, ExpectedObligation

print("=" * 80)
print("CREATING BERT VERSIONS OF ALL KNOWLEDGE BASE ITEMS")
print("=" * 80)

embedding_service = EmbeddingService()

# Switch to BERT
print("\nSwitching to BERT...")
EmbeddingService.switch_model('bert-large-uncased')
print(f"Active: {embedding_service.current_key} ({embedding_service.dimensions}-dim)\n")

total_created = 0

# 1. Intent Templates
print("1. Intent Templates")
print("-" * 80)
minilm_templates = IntentTemplate.objects.filter(embedding_model='all-MiniLM-L6-v2')
created = 0
for item in minilm_templates:
    exists = IntentTemplate.objects.filter(
        intent_name=item.intent_name,
        embedding_model='bert-large-uncased'
    ).exists()
    if exists:
        continue

    bert_emb = embedding_service.embed_text(item.example_clause_text)
    IntentTemplate.objects.create(
        intent_name=item.intent_name,
        intent_category=item.intent_category,
        intent_description=item.intent_description,
        example_clause_text=item.example_clause_text,
        party_impact=item.party_impact,
        risk_level=item.risk_level,
        embedding=bert_emb,
        embedding_model='bert-large-uncased',
        similarity_threshold=item.similarity_threshold,
        is_active=item.is_active
    )
    created += 1
print(f"Created: {created}/{minilm_templates.count()}")
total_created += created

# 2. Approved Clauses
print("\n2. Approved Clauses")
print("-" * 80)
minilm_approved = ApprovedClause.objects.filter(embedding_model='all-MiniLM-L6-v2')
created = 0
for item in minilm_approved:
    exists = ApprovedClause.objects.filter(
        clause_name=item.clause_name,
        clause_type=item.clause_type,
        embedding_model='bert-large-uncased'
    ).exists()
    if exists:
        continue

    bert_emb = embedding_service.embed_text(item.clause_text)
    ApprovedClause.objects.create(
        clause_name=item.clause_name,
        clause_type=item.clause_type,
        clause_text=item.clause_text,
        intent_name=item.intent_name,
        protection_level=item.protection_level,
        jurisdiction=item.jurisdiction,
        embedding=bert_emb,
        embedding_model='bert-large-uncased',
        is_active=item.is_active
    )
    created += 1
print(f"Created: {created}/{minilm_approved.count()}")
total_created += created

# 3. Gold Standard Templates
print("\n3. Gold Standard Templates")
print("-" * 80)
minilm_gold = GoldStandardTemplate.objects.filter(embedding_model='all-MiniLM-L6-v2')
created = 0
for item in minilm_gold:
    exists = GoldStandardTemplate.objects.filter(
        template_name=item.template_name,
        embedding_model='bert-large-uncased'
    ).exists()
    if exists:
        continue

    bert_emb = embedding_service.embed_text(item.approved_clause_text)
    GoldStandardTemplate.objects.create(
        template_name=item.template_name,
        clause_category=item.clause_category,
        approved_clause_text=item.approved_clause_text,
        embedding=bert_emb,
        embedding_model='bert-large-uncased',
        jurisdiction=item.jurisdiction,
        safe_threshold=item.safe_threshold,
        review_threshold=item.review_threshold,
        legal_notes=item.legal_notes,
        is_active=item.is_active
    )
    created += 1
print(f"Created: {created}/{minilm_gold.count()}")
total_created += created

# 4. Expected Obligations
print("\n4. Expected Obligations")
print("-" * 80)
minilm_obligations = ExpectedObligation.objects.filter(embedding_model='all-MiniLM-L6-v2')
created = 0
for item in minilm_obligations:
    exists = ExpectedObligation.objects.filter(
        obligation_name=item.obligation_name,
        embedding_model='bert-large-uncased'
    ).exists()
    if exists:
        continue

    bert_emb = embedding_service.embed_text(item.expected_clause_text)
    ExpectedObligation.objects.create(
        obligation_name=item.obligation_name,
        obligation_category=item.obligation_category,
        criticality=item.criticality,
        expected_clause_text=item.expected_clause_text,
        embedding=bert_emb,
        embedding_model='bert-large-uncased',
        presence_threshold=item.presence_threshold,
        absence_risk_description=item.absence_risk_description,
        absence_risk_example=item.absence_risk_example,
        suggested_clause_text=item.suggested_clause_text,
        contract_type=item.contract_type,
        party_protected=item.party_protected,
        jurisdiction=item.jurisdiction,
        is_active=item.is_active
    )
    created += 1
print(f"Created: {created}/{minilm_obligations.count()}")
total_created += created

print()
print("=" * 80)
print(f"TOTAL CREATED: {total_created} BERT knowledge base items")
print("[OK] Both models now have complete knowledge bases")
print("=" * 80)
