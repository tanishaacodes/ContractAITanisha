#!/usr/bin/env python
"""
SAP Integration Test Script

Tests all 5 scenarios of SAP S/4HANA integration with PrimeContractAI.

Usage:
    python test_sap_integration.py
"""
import os
import sys
import django
import asyncio
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from integrations.sap.sap_client import SAPClient, SAPAPIError, SAPAuthError
from integrations.sap.sap_contract_service import SAPContractService
from integrations.sap.risk_engine import RiskEngine
from integrations.sap.intent_engine import IntentEngine
from integrations.sap.clause_engine import ClauseEngine
from integrations.sap.config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(test_name, success, message=""):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {test_name}")
    if message:
        print(f"       {message}")


async def test_authentication():
    """Test 1: SAP Authentication"""
    print_section("TEST 1: SAP Authentication")

    try:
        async with SAPClient() as client:
            await client.ensure_authenticated()

            if client.access_token:
                print_result(
                    "OAuth2 Authentication",
                    True,
                    f"Token obtained: {client.access_token[:20]}..."
                )
                return True
            else:
                print_result("OAuth2 Authentication", False, "No token received")
                return False

    except SAPAuthError as e:
        print_result("OAuth2 Authentication", False, str(e))
        return False
    except Exception as e:
        print_result("OAuth2 Authentication", False, f"Unexpected error: {e}")
        return False


async def test_read_contract(contract_id="4600002345"):
    """Test 2: Read Contract from SAP"""
    print_section(f"TEST 2: Read Contract {contract_id}")

    try:
        async with SAPClient() as client:
            contract = await client.read_contract(contract_id)

            if contract:
                data = contract.get('d', contract)
                print_result(
                    "Read Contract via OData",
                    True,
                    f"Contract: {data.get('PurchaseContract', 'N/A')}, "
                    f"Value: {data.get('NetAmount', 0)}"
                )
                return True
            else:
                print_result("Read Contract via OData", False, "No data returned")
                return False

    except SAPAPIError as e:
        print_result("Read Contract via OData", False, str(e))
        return False
    except Exception as e:
        print_result("Read Contract via OData", False, f"Error: {e}")
        return False


def test_risk_engine():
    """Test 3: Risk Scoring Engine"""
    print_section("TEST 3: Risk Scoring Engine")

    # Mock contract data
    mock_contract = {
        'd': {
            'NetAmount': 5000000,
            'PaymentTerms': 'NET 90',
            'PurchaseContractDesc': 'IT Services Agreement with unlimited indemnity',
            'DocumentCurrency': 'USD'
        }
    }

    try:
        risk_engine = RiskEngine()
        score = risk_engine.score(mock_contract)
        category = risk_engine.category(score)
        details = risk_engine.get_risk_details(mock_contract)

        print_result(
            "Risk Scoring",
            True,
            f"Score: {score}/100, Category: {category}"
        )

        print("\n   Risk Breakdown:")
        for component, value in details['components'].items():
            print(f"     - {component}: {value}")

        return True

    except Exception as e:
        print_result("Risk Scoring", False, f"Error: {e}")
        return False


def test_intent_engine():
    """Test 4: Intent Detection Engine"""
    print_section("TEST 4: Intent Detection Engine")

    mock_contract = {
        'd': {
            'PurchaseContractDesc': 'Master Services Agreement with unlimited indemnity',
            'ContractText': 'Contractor shall indemnify and hold harmless...'
        }
    }

    try:
        intent_engine = IntentEngine()
        intent = intent_engine.detect(mock_contract)
        all_intents = intent_engine.detect_all(mock_contract)
        description = intent_engine.get_intent_description(intent)

        print_result(
            "Intent Detection",
            True,
            f"Primary Intent: {intent}"
        )

        print(f"       All Intents: {', '.join(all_intents)}")
        print(f"       Description: {description}")

        return True

    except Exception as e:
        print_result("Intent Detection", False, f"Error: {e}")
        return False


def test_clause_engine():
    """Test 5: Clause Suggestion Engine"""
    print_section("TEST 5: Clause Suggestion Engine")

    mock_contract = {
        'd': {
            'PurchaseContract': 'TEST001',
            'PurchaseContractDesc': 'High-risk contract with unlimited indemnity',
            'PaymentTerms': 'NET 120',
            'DocumentCurrency': 'EUR'
        }
    }

    try:
        clause_engine = ClauseEngine()
        risk_score = 75

        suggestions = clause_engine.suggest(mock_contract, risk_score)
        summary = clause_engine.generate_redline_summary(mock_contract, suggestions)

        print_result(
            "Clause Suggestions",
            True,
            f"Generated {len(suggestions)} suggestions"
        )

        print("\n   Suggestions:")
        for i, suggestion in enumerate(suggestions[:3], 1):
            print(f"     {i}. {suggestion}")

        return True

    except Exception as e:
        print_result("Clause Suggestions", False, f"Error: {e}")
        return False


async def test_scenario_1(contract_id="4600002345"):
    """Test 6: Scenario 1 - Process New Contract"""
    print_section(f"TEST 6: Scenario 1 - Process New Contract {contract_id}")

    try:
        async with SAPContractService() as service:
            result = await service.process_new_contract(contract_id)

            if result and result.get('scenario') == 1:
                print_result(
                    "Process New Contract",
                    True,
                    f"Risk: {result['risk_score']}, Status: {result['status']}"
                )
                print(f"       Intent: {result['intent']}")
                print(f"       Exposure: ₹{result['exposure']:,.0f}")
                return True
            else:
                print_result("Process New Contract", False, "Invalid response")
                return False

    except SAPAPIError as e:
        print_result("Process New Contract", False, str(e))
        return False
    except Exception as e:
        print_result("Process New Contract", False, f"Error: {e}")
        return False


async def test_scenario_2(contract_id="4600002345"):
    """Test 7: Scenario 2 - Block High-Risk Contract"""
    print_section(f"TEST 7: Scenario 2 - Block High-Risk Contract {contract_id}")

    try:
        async with SAPContractService() as service:
            result = await service.block_high_risk_contract(contract_id)

            if result and result.get('scenario') == 2:
                blocked = result.get('blocked', False)
                print_result(
                    "Block High-Risk Contract",
                    True,
                    f"Blocked: {blocked}, Risk: {result['risk_score']}"
                )
                return True
            else:
                print_result("Block High-Risk Contract", False, "Invalid response")
                return False

    except SAPAPIError as e:
        print_result("Block High-Risk Contract", False, str(e))
        return False
    except Exception as e:
        print_result("Block High-Risk Contract", False, f"Error: {e}")
        return False


async def test_scenario_5(contract_id="4600002345"):
    """Test 8: Scenario 5 - AI Clause Suggestions"""
    print_section(f"TEST 8: Scenario 5 - AI Clause Suggestions {contract_id}")

    try:
        async with SAPContractService() as service:
            result = await service.add_clause_suggestions(contract_id)

            if result and result.get('scenario') == 5:
                count = result.get('suggestions_count', 0)
                print_result(
                    "AI Clause Suggestions",
                    True,
                    f"Added {count} suggestions"
                )

                if result.get('suggestions'):
                    print("\n   Sample Suggestions:")
                    for suggestion in result['suggestions'][:3]:
                        print(f"     • {suggestion}")

                return True
            else:
                print_result("AI Clause Suggestions", False, "Invalid response")
                return False

    except SAPAPIError as e:
        print_result("AI Clause Suggestions", False, str(e))
        return False
    except Exception as e:
        print_result("AI Clause Suggestions", False, f"Error: {e}")
        return False


def test_configuration():
    """Test 9: Configuration Validation"""
    print_section("TEST 9: Configuration Validation")

    try:
        # Check if credentials are set
        has_client_id = bool(settings.SAP_CLIENT_ID)
        has_client_secret = bool(settings.SAP_CLIENT_SECRET)
        has_base_url = bool(settings.SAP_BASE_URL)

        config_valid = has_client_id and has_client_secret and has_base_url

        print_result(
            "Configuration Check",
            config_valid,
            f"Client ID: {'✓' if has_client_id else '✗'}, "
            f"Secret: {'✓' if has_client_secret else '✗'}, "
            f"URL: {'✓' if has_base_url else '✗'}"
        )

        if not config_valid:
            print("\n   ⚠️  Configure SAP credentials in backend/.env:")
            print("       SAP_CLIENT_ID=your_client_id")
            print("       SAP_CLIENT_SECRET=your_secret")
            print("       SAP_BASE_URL=https://your-sap-system.com/sap/opu/odata/sap")

        return config_valid

    except Exception as e:
        print_result("Configuration Check", False, f"Error: {e}")
        return False


async def run_all_tests():
    """Run all tests"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "SAP S/4HANA Integration Test Suite" + " " * 13 + "║")
    print("╚" + "═" * 58 + "╝")

    results = []

    # Configuration test (synchronous)
    results.append(test_configuration())

    # Authentication test
    results.append(await test_authentication())

    # Engine tests (synchronous)
    results.append(test_risk_engine())
    results.append(test_intent_engine())
    results.append(test_clause_engine())

    # SAP API tests (async)
    # Note: These will fail if SAP credentials are not configured
    if results[0] and results[1]:  # If config and auth passed
        contract_id = input("\n   Enter SAP Contract ID to test (or press Enter to skip): ").strip()

        if contract_id:
            results.append(await test_read_contract(contract_id))
            results.append(await test_scenario_1(contract_id))
            results.append(await test_scenario_2(contract_id))
            results.append(await test_scenario_5(contract_id))

    # Summary
    print_section("TEST SUMMARY")
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0

    print(f"\n   Tests Passed: {passed}/{total} ({success_rate:.1f}%)")

    if success_rate == 100:
        print("\n   🎉 All tests passed! SAP integration is working correctly.")
    elif success_rate >= 50:
        print("\n   ⚠️  Some tests failed. Check configuration and SAP connectivity.")
    else:
        print("\n   ❌ Most tests failed. Verify SAP credentials and system availability.")

    print("\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n\n   Tests interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n   ❌ Test suite error: {e}")
        sys.exit(1)
