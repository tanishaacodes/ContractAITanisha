"""Quick test to check which embedding model is active"""
import django
import os
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from api.embedding_service import embedding_service

print("=" * 60)
print("EMBEDDING MODEL STATUS")
print("=" * 60)

# Get current model info
print(f"Active key: {embedding_service.current_key}")
print(f"Model name (DB label): {embedding_service.active_model_name}")
print(f"Dimensions: {embedding_service.dimensions}")
print()

# Test embedding generation
test_text = "This is a test clause for payment obligations."
embedding = embedding_service.embed_text(test_text)

print(f"Test embedding generated:")
print(f"  - Length: {len(embedding)} dimensions")
print(f"  - First 5 values: {embedding[:5]}")
print()

# Check DB state
from core.models import ClauseEmbedding
from django.db.models import Count, Q
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT
            embeddingModel,
            JSON_LENGTH(embedding) as dims,
            COUNT(*) as count
        FROM clause_embeddings
        GROUP BY embeddingModel, dims
    """)

    print("Database state (clause_embeddings):")
    print("-" * 60)
    for row in cursor.fetchall():
        print(f"  Model: {row[0]:30} | Dims: {row[1]:4} | Count: {row[2]}")

print()
print("=" * 60)
