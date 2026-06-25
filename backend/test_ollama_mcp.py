"""
Test script to verify Ollama integration with MCP server functions.
"""
import os
import sys
import django
import asyncio

# Setup Django
django_project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, django_project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from agents.mcp_server import call_ollama
from core.models import Contract


async def test_call_ollama():
    """Test direct Ollama call."""
    print("=" * 60)
    print("Testing direct call_ollama() function...")
    print("=" * 60)

    test_prompt = "Hello! Please respond with 'Ollama is working correctly.'"
    result = await call_ollama(test_prompt, max_tokens=50)

    print(f"\nPrompt: {test_prompt}")
    print(f"Response: {result}")

    if "Error" in result:
        print("\n[FAIL] Ollama call returned an error")
        return False
    else:
        print("\n[PASS] Ollama is responding correctly")
        return True


async def test_suggest_improvements():
    """Test the suggest_clause_improvements function."""
    print("\n" + "=" * 60)
    print("Testing suggest_clause_improvements() function...")
    print("=" * 60)

    # Get first contract
    try:
        contract = await Contract.objects.afirst()
        if not contract:
            print("[FAIL] No contracts found in database")
            return False

        print(f"\nTesting with contract: {contract.original_filename} (ID: {contract.id})")

        from agents.mcp_server import suggest_clause_improvements
        import json

        result_json = await suggest_clause_improvements(str(contract.id))
        result = json.loads(result_json)

        print(f"\nResult status: {result.get('status')}")

        if result.get('status') == 'success':
            suggestions = result.get('suggestions', [])
            print(f"Number of suggestions: {len(suggestions)}")

            if suggestions:
                first_suggestion = suggestions[0]
                print(f"\nFirst suggestion:")
                print(f"  Clause: {first_suggestion.get('clause_name')}")
                print(f"  Severity: {first_suggestion.get('severity')}")
                print(f"  Rationale: {first_suggestion.get('rationale')[:100]}...")

                # Check if rationale contains error
                if "Error calling Ollama" in first_suggestion.get('rationale', ''):
                    print("\n[FAIL] FAILED: Rationale contains Ollama error")
                    return False
                else:
                    print("\n[PASS] SUCCESS: Suggestions generated successfully")
                    return True
            else:
                print("\n[FAIL] FAILED: No suggestions returned")
                return False
        else:
            print(f"\n[FAIL] FAILED: {result.get('message')}")
            return False

    except Exception as e:
        print(f"\n[FAIL] EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n[TEST] Starting Ollama + MCP Integration Tests\n")

    # Test 1: Direct Ollama call
    test1_passed = await test_call_ollama()

    # Test 2: Suggest improvements function
    test2_passed = await test_suggest_improvements()

    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"Direct Ollama Call: {'[PASS] PASS' if test1_passed else '[FAIL] FAIL'}")
    print(f"Suggest Improvements: {'[PASS] PASS' if test2_passed else '[FAIL] FAIL'}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
