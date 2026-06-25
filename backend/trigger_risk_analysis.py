"""
Trigger risk analysis for a contract
"""
import django
import os
import sys
import requests

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract

# Get the construction contract
contract = Contract.objects.filter(filename__icontains='Construction').first()
if not contract:
    contract = Contract.objects.first()

print(f"Triggering analysis for: {contract.filename}")
print(f"Contract ID: {contract.id}")

BASE_URL = "http://localhost:8002/api"

# Trigger deviation analysis
print("\n1. Running deviation analysis...")
try:
    response = requests.post(
        f"{BASE_URL}/embedding/contracts/{contract.id}/analyze-deviations",
        timeout=120
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   [OK] Deviation analysis complete")
    else:
        print(f"   [ERROR] {response.text}")
except Exception as e:
    print(f"   [ERROR] {e}")

# Trigger safeguard detection
print("\n2. Running safeguard detection...")
try:
    response = requests.post(
        f"{BASE_URL}/embedding/contracts/{contract.id}/detect-safeguards",
        timeout=120
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   [OK] Safeguard detection complete")
    else:
        print(f"   [ERROR] {response.text}")
except Exception as e:
    print(f"   [ERROR] {e}")

# Trigger silent risk detection (with our new persistence fix)
print("\n3. Running silent risk detection...")
try:
    response = requests.get(
        f"{BASE_URL}/negotiation/silent-risk/{contract.id}",
        timeout=120
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   [OK] Detected {data['total_risks']} silent risks")
    else:
        print(f"   [ERROR] {response.text}")
except Exception as e:
    print(f"   [ERROR] {e}")

print("\n" + "="*70)
print("ANALYSIS COMPLETE!")
print("="*70)
print("\nRefresh the Risk Heatmap page in your browser to see the results.")
