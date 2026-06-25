#!/usr/bin/env python
"""
Test Risk Graph API Endpoint
=============================
Simulate the API view to verify it works end-to-end.
"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
from api.risk_intelligence_views import RiskSubgraphView
from core.models import Contract
import json

print("=" * 60)
print("Testing Risk Graph API Endpoint")
print("=" * 60)

# Get first contract
contract = Contract.objects.first()
if not contract:
    print("\nERROR: No contracts found!")
    sys.exit(1)

print(f"\nTesting with contract: {contract.original_filename}")
print(f"Contract ID: {contract.id}")

# Create a mock request
class MockRequest:
    pass

# Instantiate the view
view = RiskSubgraphView()
request = MockRequest()

print("\nCalling RiskSubgraphView.get()...")

try:
    # Call the view
    response = view.get(request, str(contract.id))

    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Type: {type(response).__name__}")

    # Extract data
    if hasattr(response, 'data'):
        data = response.data
    elif hasattr(response, 'content'):
        data = json.loads(response.content)
    else:
        data = response

    print(f"\nResponse Data:")
    print(f"  Success: {data.get('success')}")
    print(f"  Contract ID: {data.get('contract_id')}")

    subgraph = data.get('subgraph', {})
    print(f"\nSubgraph:")
    print(f"  Nodes: {len(subgraph.get('nodes', []))}")
    print(f"  Edges: {len(subgraph.get('edges', []))}")

    if subgraph.get('nodes'):
        print(f"\n  Sample Node:")
        node = subgraph['nodes'][0]
        print(f"    ID: {node.get('id')} (type: {type(node.get('id')).__name__})")
        print(f"    Type: {node.get('type')}")
        print(f"    Label: {node.get('label')}")

    if subgraph.get('edges'):
        print(f"\n  Sample Edge:")
        edge = subgraph['edges'][0]
        print(f"    Source: {edge.get('source')} (type: {type(edge.get('source')).__name__})")
        print(f"    Target: {edge.get('target')} (type: {type(edge.get('target')).__name__})")
        print(f"    Type: {edge.get('type')}")

    # Test JSON serialization of the response
    try:
        json_str = json.dumps(data)
        print(f"\nJSON Serialization: SUCCESS ({len(json_str)} bytes)")
    except Exception as e:
        print(f"\nJSON Serialization: FAILED - {e}")
        raise

    print("\n" + "=" * 60)
    print("SUCCESS! API endpoint is working correctly!")
    print("=" * 60)
    print("\nRestart Django server to apply the fix:")
    print("  python manage.py runserver 8002")

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
