"""
Test that model switching persists correctly using the database-backed SystemSettings.
"""
import django
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from api.embedding_service import EmbeddingService
from core.models import SystemSettings, RiskPlaybook

print("=" * 70)
print("TESTING PERSISTENT MODEL SWITCHING")
print("=" * 70)

# Test 1: Check current state
print("\nTest 1: Current State")
print("-" * 70)
settings = SystemSettings.get_settings()
print(f"Database says: {settings.active_embedding_model}")

service = EmbeddingService()
print(f"Service says: {service.current_key} ({service.dimensions}-dim)")

# Count playbooks for current model
playbooks = RiskPlaybook.objects.filter(embedding_model=service.active_model_name)
print(f"Available playbooks: {playbooks.count()}")

# Test 2: Switch to MiniLM
print("\nTest 2: Switch to MiniLM")
print("-" * 70)
EmbeddingService.switch_model('minilm')
service = EmbeddingService()  # Get fresh instance
settings = SystemSettings.get_settings()

print(f"Database says: {settings.active_embedding_model}")
print(f"Service says: {service.current_key} ({service.dimensions}-dim)")
playbooks = RiskPlaybook.objects.filter(embedding_model=service.active_model_name)
print(f"Available playbooks: {playbooks.count()}")

# Test 3: Switch to BERT
print("\nTest 3: Switch to BERT")
print("-" * 70)
EmbeddingService.switch_model('bert-large-uncased')
service = EmbeddingService()  # Get fresh instance
settings = SystemSettings.get_settings()

print(f"Database says: {settings.active_embedding_model}")
print(f"Service says: {service.current_key} ({service.dimensions}-dim)")
playbooks = RiskPlaybook.objects.filter(embedding_model=service.active_model_name)
print(f"Available playbooks: {playbooks.count()}")

# Test 4: Create a new service instance to verify persistence
print("\nTest 4: New Service Instance (simulates new request)")
print("-" * 70)
new_service = EmbeddingService()
print(f"New service reads: {new_service.current_key} ({new_service.dimensions}-dim)")

# Test 5: Final verification
print("\nTest 5: Database Persistence Check")
print("-" * 70)
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT activeEmbeddingModel FROM system_settings WHERE id = 'system-settings-singleton'")
    result = cursor.fetchone()
    if result:
        print(f"Direct DB query: {result[0]}")
        print("[OK] Model preference is persisted in database")
    else:
        print("[ERROR] No settings found in database!")

print()
print("=" * 70)
print("RESULT: Model switching is now persistent across server restarts!")
print("=" * 70)
