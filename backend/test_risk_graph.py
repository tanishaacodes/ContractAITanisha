#!/usr/bin/env python
"""
Test Risk Graph Endpoint
========================
Verify UUID serialization fix works correctly.
"""

import os
import sys
import django
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from ai.graph.risk_graph_schema import get_risk_graph_schema
from core.models import Contract

print("=" * 60)
print("Testing Risk Graph UUID Serialization Fix")
print("=" * 60)

# Get risk graph schema
schema = get_risk_graph_schema()

if not schema.connected:
    print("\n[ERROR] Neo4j is not connected!")
    sys.exit(1)

print("\n[1/3] Connected to Neo4j")

# Get first contract
contract = Contract.objects.first()
if not contract:
    print("\n[ERROR] No contracts found!")
    sys.exit(1)

print(f"\n[2/3] Testing with contract: {contract.original_filename}")
print(f"    Contract ID: {contract.id}")

# Fetch subgraph
try:
    result = schema.get_risk_subgraph(str(contract.id))
    print(f"\n[3/3] Subgraph fetched successfully:")
    print(f"    Nodes: {len(result.get('nodes', []))}")
    print(f"    Edges: {len(result.get('edges', []))}")

    # Test JSON serialization
    json_str = json.dumps(result, indent=2)
    print(f"\n✓ JSON Serialization: SUCCESS")
    print(f"    JSON size: {len(json_str)} bytes")

    # Show sample data
    if result.get('nodes'):
        print(f"\n  Sample Node:")
        sample_node = result['nodes'][0]
        print(f"    ID: {sample_node['id']} (type: {type(sample_node['id']).__name__})")
        print(f"    Type: {sample_node['type']}")
        print(f"    Label: {sample_node['label']}")

    if result.get('edges'):
        print(f"\n  Sample Edge:")
        sample_edge = result['edges'][0]
        print(f"    Source: {sample_edge['source']} (type: {type(sample_edge['source']).__name__})")
        print(f"    Target: {sample_edge['target']} (type: {type(sample_edge['target']).__name__})")
        print(f"    Type: {sample_edge['type']}")

    print("\n" + "=" * 60)
    print("✓ SUCCESS! UUID serialization fix is working!")
    print("=" * 60)

except Exception as e:
    print(f"\n✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
