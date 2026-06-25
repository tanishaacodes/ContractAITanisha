#!/usr/bin/env python
"""
Populate Neo4j Concept Graph Schema
====================================
Seeds concept nodes, contract types, and correlations.

Usage:
    python populate_concept_graph.py

Requirements:
    - Neo4j running at NEO4J_URI
    - Environment variables configured (.env)
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from ai.graph.concept_graph_schema import get_concept_graph_schema
from api.services.concept_correlation_service import ConceptCorrelationService

print("=" * 70)
print("  Contract Concept Risk Topology Engine")
print("  Neo4j Graph Population Script")
print("=" * 70)

# Get schema instance
schema = get_concept_graph_schema()

if not schema.connected:
    print("\n[ERROR] Neo4j is not connected!")
    print("\nPlease ensure:")
    print("  1. Neo4j is running")
    print("  2. Environment variables are set:")
    print("     - NEO4J_URI=bolt://localhost:7687")
    print("     - NEO4J_USERNAME=neo4j")
    print("     - NEO4J_PASSWORD=password")
    print("\nTroubleshooting:")
    print("  - Check Neo4j with: docker ps | grep neo4j")
    print("  - Start Neo4j with: docker start neo4j")
    sys.exit(1)

print(f"\n✓ Connected to Neo4j")

# Phase 1: Apply schema
print("\n[1/4] Applying Neo4j schema (constraints + indexes)...")
if schema.apply_schema():
    print("  ✓ Schema applied successfully")
else:
    print("  ✗ Schema application failed")
    sys.exit(1)

# Phase 2: Seed concept nodes
print("\n[2/4] Seeding concept nodes...")
print("  Concepts: Termination, Liability, Indemnification, IP Rights,")
print("           Risk Allocation, Arbitration, Penalty, Obligations,")
print("           Data Protection, Force Majeure")
if schema.seed_concept_nodes():
    print("  ✓ Seeded 10 concept nodes with colors and avg strengths")
else:
    print("  ✗ Concept seeding failed")
    sys.exit(1)

# Phase 3: Seed contract type nodes
print("\n[3/4] Seeding contract type nodes...")
print("  Contract Types: MSA, SaaS, NDA, Employment, EPC")
if schema.seed_contract_type_nodes():
    print("  ✓ Seeded 5 contract type nodes")
    print("  ✓ Created HAS_CONCEPT relationships")
else:
    print("  ✗ Contract type seeding failed")
    sys.exit(1)

# Phase 4: Create concept correlations
print("\n[4/4] Creating concept correlations...")
print("  Computing Pearson correlation matrix...")

service = ConceptCorrelationService()
correlation_count = 0

try:
    # Access private correlation matrix for seeding
    corr_matrix = service._corr_matrix
    if schema.seed_concept_correlations(corr_matrix):
        print("  ✓ Created CORRELATES_WITH relationships")
        print("  ✓ Correlation threshold: 0.50")
    else:
        print("  ✗ Correlation seeding failed")
        sys.exit(1)
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("  ✓ Concept Graph Populated Successfully!")
print("=" * 70)

print("\nNext steps:")
print("  1. Backfill existing contracts:")
print("     python populate_contract_concepts.py")
print("\n  2. Verify in Neo4j Browser:")
print("     http://localhost:7474")
print("\n  3. Test API endpoints:")
print("     GET /api/concept-graph/all/")
print("     GET /api/concept-graph/MSA/")

print("\nVerification queries (run in Neo4j Browser):")
print("  // Check concept nodes")
print("  MATCH (c:Concept) RETURN c ORDER BY c.name;")
print("\n  // Check contract types")
print("  MATCH (ct:ContractType) RETURN ct;")
print("\n  // Check correlations")
print("  MATCH (c1:Concept)-[r:CORRELATES_WITH]-(c2:Concept)")
print("  WHERE r.weight > 0.75")
print("  RETURN c1.name, c2.name, r.weight;")

print("\n" + "=" * 70)
