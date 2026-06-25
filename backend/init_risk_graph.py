#!/usr/bin/env python
"""Initialize Risk Intelligence Graph Schema"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from ai.graph.risk_graph_schema import get_risk_graph_schema

print("=" * 60)
print("Risk Intelligence Setup")
print("=" * 60)

schema = get_risk_graph_schema()

print("\n[1/4] Checking Neo4j connection...")
if not schema.connected:
    print("[ERROR] Neo4j is not connected!")
    print("\nCheck:")
    print("  docker ps | grep neo4j")
    print("  NEO4J_URI=bolt://localhost:7687")
    print("  NEO4J_USER=neo4j")
    print("  NEO4J_PASSWORD=password")
    sys.exit(1)

print("[OK] Neo4j connected!")

print("\n[2/4] Applying graph schema...")
schema.apply_schema()
print("[OK] Schema applied!")

print("\n[3/4] Seeding risk categories...")
schema.seed_risk_categories()
print("[OK] 10 risk categories seeded!")

print("\n[4/4] Seeding jurisdictions...")
schema.seed_jurisdictions()
print("[OK] 9 jurisdictions seeded!")

print("\n" + "=" * 60)
print("Setup complete!")
print("=" * 60)
print("\nAPI Endpoints ready:")
print("  POST /api/risk-intelligence/monte-carlo")
print("  POST /api/risk-intelligence/var")
print("  POST /api/risk-intelligence/stress-test")
print("  GET  /api/risk-intelligence/risk-subgraph/<contract-id>")
