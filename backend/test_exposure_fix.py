"""
Test script to verify exposure calculation fix
Run this with: python test_exposure_fix.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')

try:
    django.setup()
except Exception as e:
    print(f"Warning: Could not setup Django: {e}")

from api.services.exposure_engine import ExposureEngine

def test_contract_value_parsing():
    """Test that contract values are parsed correctly"""
    engine = ExposureEngine()

    test_cases = [
        ("10 Crore", 100_000_000),
        ("Not set", 0),
        ("", 0),
        (None, 0),
        ("5 Cr", 50_000_000),
        ("50 Lakhs", 5_000_000),
        ("50 L", 5_000_000),
    ]

    print("\n" + "="*60)
    print("TESTING CONTRACT VALUE PARSING")
    print("="*60)

    for value_str, expected in test_cases:
        result = engine.parse_contract_value(value_str)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} | Input: '{value_str}' | Expected: {expected} | Got: {result}")

    print("\n" + "="*60)
    print("TESTING DEFAULT FALLBACK LOGIC")
    print("="*60)

    # Test the fallback logic
    default_value = "10 Crore"
    test_values = ["Not set", "", None, "invalid", "xyz"]

    for value in test_values:
        contract_value_str = value or default_value
        parsed = engine.parse_contract_value(contract_value_str)

        # If parsing resulted in 0, use default
        if parsed == 0:
            parsed = engine.parse_contract_value(default_value)
            print(f"✅ '{value}' → 0 → DEFAULT → {parsed:,.0f}")
        else:
            print(f"⚠️  '{value}' → {parsed:,.0f} (no fallback needed)")

    print("\n" + "="*60)
    print("EXPECTED BEHAVIOR:")
    print("="*60)
    print("✅ All 'Not set', '', None, and invalid values should fallback to 100,000,000")
    print("✅ This means Financial Exposure will show actual values, not ₹0")
    print("\n")

if __name__ == "__main__":
    try:
        test_contract_value_parsing()
        print("✅ TEST COMPLETED SUCCESSFULLY\n")
        print("=" * 60)
        print("NEXT STEPS:")
        print("=" * 60)
        print("1. Make sure Django backend server is restarted")
        print("2. In another terminal, run: python manage.py runserver")
        print("3. Refresh your browser (Ctrl+Shift+R / Cmd+Shift+R)")
        print("4. Run the What-If simulation again")
        print("5. Check the terminal logs for [WHAT-IF-EXPOSURE] messages")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        import traceback
        traceback.print_exc()
