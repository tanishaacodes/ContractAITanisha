#!/usr/bin/env python3
"""Test RAG retrieval with actual user query"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import User
from rag import retrieve_contexts, qa_flow

print("\n" + "="*60)
print("TESTING RAG RETRIEVAL")
print("="*60)

# Get a user
user = User.objects.filter(email='admin@example.com').first()
if not user:
    user = User.objects.first()

if not user:
    print("No users found!")
    sys.exit(1)

user_id = str(user.id)
print(f"Testing with user: {user.email} (ID: {user_id})")

# Test queries
test_queries = [
    "show me uploaded contract",
    "what contracts do I have",
    "list my contracts",
    "show me all contracts"
]

for query in test_queries:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")

    # Test retrieval
    contexts = retrieve_contexts(query, user_id=user_id, top_k=6)

    print(f"\nFound {len(contexts)} context chunks:")
    for i, ctx in enumerate(contexts[:3], 1):
        print(f"\n{i}. Score: {ctx['score']:.3f}")
        print(f"   File: {ctx['filename']}")
        print(f"   Contract ID: {ctx['contract_id']}")
        print(f"   Text preview: {ctx['text'][:100]}...")

    # Test full QA flow
    print(f"\n{'='*60}")
    print(f"TESTING QA FLOW")
    print(f"{'='*60}")

    result = qa_flow(query, user_id=user_id, mode='auto')

    print(f"\nIntent: {result.get('intent')}")
    print(f"Has context: {result.get('has_contract_context')}")
    print(f"Answer preview: {result.get('ollama', {}).get('response', '')[:200]}...")

print("\n" + "="*60 + "\n")
