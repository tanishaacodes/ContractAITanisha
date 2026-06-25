#!/usr/bin/env python
"""
Complete test of Intent Mining system.
This script tests the entire flow from contract upload to intent discovery.
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, Clause
from api.intent_mining_service import IntentMiningService

def test_intent_mining():
    print("=" * 80)
    print("INTENT MINING FULL SYSTEM TEST")
    print("=" * 80)

    # Step 1: Find a contract with clauses
    print("\n[1] Finding contract with clauses...")
    contracts_with_clauses = Contract.objects.filter(clauses__found=True).distinct()

    if not contracts_with_clauses.exists():
        print("ERROR: No contracts with clauses found!")
        print("Please upload a contract and extract clauses first.")
        return False

    contract = contracts_with_clauses.first()
    print(f"✓ Found contract: {contract.original_filename}")
    print(f"  ID: {contract.id}")

    # Step 2: Check clauses
    print("\n[2] Checking clauses...")
    clauses = Clause.objects.filter(contract=contract, found=True)
    print(f"✓ Found {clauses.count()} clauses marked as 'found'")

    for i, clause in enumerate(clauses[:3], 1):
        print(f"\n  Clause {i}: {clause.clause_name}")
        print(f"    extracted_text length: {len(clause.extracted_text or '')}")
        if clause.extracted_text:
            print(f"    Preview: {clause.extracted_text[:100]}...")
        else:
            print(f"    WARNING: No extracted_text!")

    if clauses.count() == 0:
        print("ERROR: No clauses to analyze!")
        return False

    # Step 3: Test Intent Mining Service
    print("\n[3] Testing Intent Mining Service...")
    service = IntentMiningService()
    print(f"✓ Service initialized")
    print(f"  Model: {service.model_name}")
    print(f"  Ollama URL: {service.ollama_url}")

    # Step 4: Test single clause intent discovery
    print("\n[4] Testing intent discovery on first clause...")
    test_clause = clauses.first()
    print(f"  Testing clause: {test_clause.clause_name}")

    try:
        intent_data = service.discover_intent_from_clause(test_clause)

        if intent_data:
            print(f"✓ Intent discovered successfully!")
            print(f"  Intent Name: {intent_data.get('intent_name')}")
            print(f"  Description: {intent_data.get('description')}")
            print(f"  Confidence: {intent_data.get('confidence')}")
        else:
            print(f"✗ Intent discovery returned None")
            print(f"  This means the LLM failed to extract intent")
            return False

    except Exception as e:
        print(f"✗ Intent discovery failed with error:")
        print(f"  {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    # Step 5: Run full contract processing
    print("\n[5] Running full contract intent mining...")
    try:
        result = service.process_contract_clauses(str(contract.id))

        if result.get('success'):
            print(f"✓ Intent mining completed successfully!")
            print(f"\n  Results:")
            print(f"    Clauses processed: {result.get('clauses_processed', 0)}")
            print(f"    Intents discovered: {result.get('intents_discovered', 0)}")
            print(f"    Obligations extracted: {result.get('obligations_extracted', 0)}")
            print(f"    Rights extracted: {result.get('rights_extracted', 0)}")

            if result.get('intents_discovered', 0) > 0:
                print(f"\n✓✓✓ SUCCESS! Intent mining is working!")
                return True
            else:
                print(f"\n✗ WARNING: No intents were discovered")
                print(f"  Check if clauses have extracted_text")
                return False
        else:
            print(f"✗ Intent mining failed")
            print(f"  Error: {result.get('error')}")
            return False

    except Exception as e:
        print(f"✗ Full processing failed with error:")
        print(f"  {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_intent_mining()
    print("\n" + "=" * 80)
    if success:
        print("TEST PASSED ✓✓✓")
        print("Intent mining is working correctly!")
    else:
        print("TEST FAILED ✗✗✗")
        print("Please check the errors above and fix them.")
    print("=" * 80)
