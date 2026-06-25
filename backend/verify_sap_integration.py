#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick SAP Integration Verification Script

This script verifies that SAP integration is properly set up.
Run this before attempting to connect to real SAP systems.
"""
import os
import sys

print("=" * 70)
print("  SAP Integration Verification")
print("=" * 70)

# Check 1: Python environment
print("\n[CHECK] Checking Python environment...")
print(f"  Python version: {sys.version.split()[0]}")

# Check 2: Django setup
try:
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
    django.setup()
    print("[OK] Django environment: OK")
except Exception as e:
    print(f"[FAIL] Django setup failed: {e}")
    sys.exit(1)

# Check 3: Module imports
print("\n[OK] Checking SAP module imports...")
try:
    from integrations.sap import SAPClient, SAPContractService, RiskEngine
    print("  [OK] SAPClient")
    print("  [OK] SAPContractService")
    print("  [OK] RiskEngine")
except ImportError as e:
    print(f"  [FAIL] Import failed: {e}")
    print("\n  Fix: Ensure integrations/sap/ module is created")
    sys.exit(1)

# Check 4: Configuration
print("\n[OK] Checking SAP configuration...")
try:
    from integrations.sap.config import settings

    config_ok = True

    if settings.SAP_BASE_URL == "https://your-sap-system.com/sap/opu/odata/sap":
        print("  [WARN] SAP_BASE_URL not configured (using default)")
        config_ok = False
    else:
        print(f"  [OK] SAP_BASE_URL: {settings.SAP_BASE_URL}")

    if not settings.SAP_CLIENT_ID:
        print("  [WARN] SAP_CLIENT_ID not configured")
        config_ok = False
    else:
        print(f"  [OK] SAP_CLIENT_ID: {settings.SAP_CLIENT_ID[:10]}...")

    if not settings.SAP_CLIENT_SECRET:
        print("  [WARN] SAP_CLIENT_SECRET not configured")
        config_ok = False
    else:
        print("  [OK] SAP_CLIENT_SECRET: ********")

    print(f"  [OK] SAP_SYSTEM_ID: {settings.SAP_SYSTEM_ID}")
    print(f"  [OK] Risk Thresholds: Low={settings.RISK_THRESHOLD_LOW}, "
          f"Medium={settings.RISK_THRESHOLD_MEDIUM}, High={settings.RISK_THRESHOLD_HIGH}")

    if not config_ok:
        print("\n  [WARN] Configuration incomplete!")
        print("  Action: Update backend/.env with your SAP credentials")
        print("\n  Required:")
        print("    SAP_BASE_URL=https://your-sap.com/sap/opu/odata/sap")
        print("    SAP_TOKEN_URL=https://your-sap.com/sap/bc/sec/oauth2/token")
        print("    SAP_CLIENT_ID=your_client_id")
        print("    SAP_CLIENT_SECRET=your_secret")

except Exception as e:
    print(f"  [FAIL] Configuration error: {e}")
    sys.exit(1)

# Check 5: Dependencies
print("\n[OK] Checking dependencies...")
try:
    import httpx
    print(f"  [OK] httpx: {httpx.__version__}")
except ImportError:
    print("  [FAIL] httpx not installed")
    print("  Fix: pip install httpx")
    sys.exit(1)

try:
    from rest_framework import status
    print("  [OK] djangorestframework: installed")
except ImportError:
    print("  [FAIL] djangorestframework not installed")
    sys.exit(1)

# Check 6: URL registration
print("\n[OK] Checking URL registration...")
try:
    from django.urls import resolve, reverse
    from django.urls.exceptions import NoReverseMatch

    try:
        url = reverse('sap:health')
        print(f"  [OK] SAP URLs registered: {url}")
    except NoReverseMatch:
        print("  [FAIL] SAP URLs not registered")
        print("\n  Fix: Add to backend/contractai/urls.py:")
        print("    path('api/sap/', include('integrations.sap.urls', namespace='sap')),")
        sys.exit(1)

except Exception as e:
    print(f"  [WARN] Could not verify URL registration: {e}")

# Check 7: Test engines (no SAP connection needed)
print("\n[OK] Testing engines...")
try:
    from integrations.sap.risk_engine import RiskEngine
    from integrations.sap.intent_engine import IntentEngine
    from integrations.sap.clause_engine import ClauseEngine

    mock_contract = {
        'd': {
            'NetAmount': 1000000,
            'PaymentTerms': 'NET 30',
            'PurchaseContractDesc': 'Standard IT Services Agreement',
            'DocumentCurrency': 'INR'
        }
    }

    # Test Risk Engine
    risk = RiskEngine()
    score = risk.score(mock_contract)
    category = risk.category(score)
    print(f"  [OK] RiskEngine: score={score}, category={category}")

    # Test Intent Engine
    intent_engine = IntentEngine()
    intent = intent_engine.detect(mock_contract)
    print(f"  [OK] IntentEngine: intent={intent}")

    # Test Clause Engine
    clause = ClauseEngine()
    suggestions = clause.suggest(mock_contract, score)
    print(f"  [OK] ClauseEngine: {len(suggestions)} suggestions generated")

except Exception as e:
    print(f"  [FAIL] Engine test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("\n" + "=" * 70)
print("  VERIFICATION SUMMARY")
print("=" * 70)

if config_ok:
    print("\n[SUCCESS] SAP integration is properly configured!")
    print("\nNext steps:")
    print("  1. Test SAP connectivity:")
    print("     python test_sap_integration.py")
    print("\n  2. Start Django server:")
    print("     python manage.py runserver")
    print("\n  3. Test health endpoint:")
    print("     curl http://localhost:8000/api/sap/health/")
else:
    print("\n[WARN]  SAP integration module is installed but not configured")
    print("\nNext steps:")
    print("  1. Update backend/.env with SAP credentials")
    print("  2. Run this script again to verify")
    print("  3. See: HOW_TO_INTEGRATE_SAP.md for detailed instructions")

print("\n" + "=" * 70)
