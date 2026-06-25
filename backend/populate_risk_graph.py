#!/usr/bin/env python
"""
Populate Neo4j Risk Graph with Contract Data
=============================================
This script populates the Neo4j graph with contracts and clauses from MySQL.
"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, Clause
from ai.graph.risk_graph_schema import get_risk_graph_schema

print("=" * 60)
print("Populating Neo4j Risk Graph")
print("=" * 60)

schema = get_risk_graph_schema()

if not schema.connected:
    print("\n[ERROR] Neo4j is not connected!")
    sys.exit(1)

print("\n[1/3] Connected to Neo4j")

# Get all contracts with clauses
print("\n[2/3] Fetching contracts from MySQL...")
contracts = Contract.objects.all()
populated_count = 0

for contract in contracts:
    clauses = list(Clause.objects.filter(contract=contract))

    if not clauses:
        print(f"  Skipping {contract.original_filename} (no clauses)")
        continue

    print(f"\n  Processing: {contract.original_filename}")
    print(f"    - Contract ID: {contract.id}")
    print(f"    - Clauses: {len(clauses)}")

    # Get jurisdiction
    jurisdiction = contract.jurisdiction or 'IN'

    try:
        # Convert Clause objects to dicts
        clause_dicts = []
        for clause in clauses:
            # Use clause_name as fallback for clause_type if type is generic
            clause_type = clause.clause_type or 'general'
            if clause_type == 'general' and clause.clause_name:
                clause_type = clause.clause_name  # Use name for better risk mapping

            clause_dicts.append({
                'id': str(clause.id),
                'clause_name': clause.clause_name or '',
                'clause_type': clause_type,
                'risk_score': float(clause.risk_score or 0.5),
                'breach_probability': float(clause.risk_score or 0.5) * 0.1,
                'loss_mean': 0.0,
                'loss_std': 0.0
            })

        # Create contract with risks in Neo4j
        schema.create_contract_with_risks(
            contract_id=str(contract.id),
            clauses=clause_dicts,
            jurisdiction=jurisdiction
        )
        populated_count += 1
        print(f"    [OK] Populated in Neo4j!")
    except Exception as e:
        print(f"    [FAILED] {e}")

print("\n" + "=" * 60)
print(f"Populated {populated_count} contracts in Neo4j!")
print("=" * 60)

# Verify
print("\nVerifying first contract...")
first_contract = Contract.objects.first()
if first_contract:
    result = schema.get_risk_subgraph(str(first_contract.id))
    print(f"  Contract: {first_contract.original_filename}")
    print(f"  Nodes in graph: {len(result.get('nodes', []))}")
    print(f"  Edges in graph: {len(result.get('edges', []))}")

    if len(result.get('nodes', [])) > 0:
        print("\n✓ SUCCESS! Graph is populated!")
    else:
        print("\n✗ Graph still empty - check errors above")

print("\nDone! Refresh your browser to see the Risk Graph.")
