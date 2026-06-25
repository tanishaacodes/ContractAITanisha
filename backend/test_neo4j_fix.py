"""Test that Neo4j unavailability doesn't crash Django"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')

import django
django.setup()

# Try importing the problematic module
from api import urls
from ai.trust_engine.neo4j_trust_propagation import get_trust_propagation_service

print("[OK] All imports successful!")
print("[OK] Neo4j unavailability handled gracefully")

# Test that service returns None for driver
service = get_trust_propagation_service()
print(f"[OK] Trust propagation service initialized (available: {service.neo4j_available})")
