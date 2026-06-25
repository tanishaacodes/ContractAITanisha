"""
Test script to verify LLM-based redline suggestions work correctly.
According to ContractAI spec from the PDF.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
import django
django.setup()

from api.redline_engine import analyze_clause, get_ollama_response

def test_ollama_connection():
    """Test if Ollama is running and responsive"""
    print("\n" + "="*80)
    print("TEST 1: Ollama Connection")
    print("="*80)

    response = get_ollama_response("Say 'Hello from Ollama!'", temperature=0.1)

    if response:
        print("[OK] Ollama is running and responsive")
        print(f"Response: {response[:100]}...")
        return True
    else:
        print("[FAIL] Ollama is NOT responding")
        print("Make sure Ollama is running: http://localhost:11434")
        return False


def test_clause_analysis_with_llm():
    """Test clause analysis with LLM-based suggestions"""
    print("\n" + "="*80)
    print("TEST 2: Clause Analysis with LLM")
    print("="*80)

    # Test clause from the PDF spec example
    test_clause = "The supplier shall be liable for any and all damages arising from this agreement."

    print(f"\nOriginal Clause:\n{test_clause}\n")

    result = analyze_clause(test_clause, jurisdiction="Common Law")

    print(f"Risk Type: {result['risk_type']}")
    print(f"Risk Score: {result['risk_score']}/100")
    print(f"Risk Explanation: {result['risk_explanation']}")
    print(f"\nSuggested Clause:\n{result['suggested_clause']}\n")
    print(f"Improvement Summary: {result['improvement_summary']}")

    # Check if suggestion is different from original
    if result['suggested_clause'] != test_clause:
        print("\n[OK] LLM generated a DIFFERENT suggestion (GOOD!)")
        return True
    else:
        print("\n[WARN] LLM returned same text (may be using fallback)")
        return False


def test_multiple_perspectives():
    """Test regenerating suggestions with different perspectives"""
    print("\n" + "="*80)
    print("TEST 3: Multiple Perspectives (Balanced/Buyer/Seller)")
    print("="*80)

    from api.redline_engine import regenerate_clause_suggestion

    test_clause = "Either party may terminate this agreement at will without notice."

    print(f"\nOriginal Clause:\n{test_clause}\n")

    perspectives = ['balanced', 'buyer_favorable', 'seller_favorable']

    for perspective in perspectives:
        print(f"\n{'='*60}")
        print(f"Perspective: {perspective.upper()}")
        print('='*60)

        result = regenerate_clause_suggestion(
            test_clause,
            perspective=perspective,
            jurisdiction="Common Law"
        )

        print(f"Suggested: {result['suggested_clause']}")
        print(f"Changes: {result['changes_made']}")
        print(f"Risk Reduction: {result['risk_reduction']}")


if __name__ == "__main__":
    print("\n" + "#"*80)
    print("# ContractAI Redline Engine - LLM Integration Test")
    print("# According to PDF spec: LLM-powered suggestions for ALL clauses")
    print("#"*80)

    # Test 1: Ollama connection
    ollama_ok = test_ollama_connection()

    if not ollama_ok:
        print("\n[WARN] Ollama is not running. Tests will use fallback mode.")
        print("To start Ollama: ollama serve")
        print("To pull model: ollama pull qwen2.5:0.5b")

    # Test 2: Clause analysis
    test_clause_analysis_with_llm()

    # Test 3: Multiple perspectives
    if ollama_ok:
        test_multiple_perspectives()

    print("\n" + "#"*80)
    print("# Test Complete")
    print("#"*80 + "\n")
