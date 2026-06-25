"""
Test Risk Analysis Functionality
"""
import requests
import json

BASE_URL = 'http://localhost:8000/api'

def test_risk_analysis():
    """Test risk analysis workflow"""

    print("="*70)
    print("Testing Risk Analysis Feature")
    print("="*70)

    # 1. Login
    print("\n1. Logging in...")
    login_response = requests.post(f'{BASE_URL}/auth/login', json={
        'email': 'admin@test.com',
        'password': 'Admin123!'
    })

    if login_response.status_code != 200:
        print(f"   [ERROR] Login failed: {login_response.text}")
        return

    token = login_response.json().get('token')
    print("   [OK] Login successful!")

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # 2. Get list of contracts
    print("\n2. Getting contracts...")
    contracts_response = requests.get(f'{BASE_URL}/contracts/list', headers=headers)

    if contracts_response.status_code != 200:
        print(f"   [ERROR] Failed to get contracts")
        return

    contracts = contracts_response.json().get('contracts', [])
    print(f"   [OK] Found {len(contracts)} contracts")

    if len(contracts) == 0:
        print("   [INFO] No contracts found. Upload and extract clauses first.")
        return

    # Find a contract with clauses
    contract_with_clauses = None
    for contract in contracts:
        if contract.get('has_analysis'):
            contract_with_clauses = contract
            break

    if not contract_with_clauses:
        print("   [INFO] No contracts with extracted clauses. Extract clauses first.")
        return

    contract_id = contract_with_clauses['id']
    contract_type = contract_with_clauses.get('contract_type', 'Unknown')
    print(f"   [OK] Using contract: {contract_with_clauses['original_filename']}")
    print(f"   [INFO] Contract Type: {contract_type}")

    # 3. Perform risk analysis
    print(f"\n3. Performing risk analysis on contract {contract_id}...")
    analysis_response = requests.post(
        f'{BASE_URL}/contracts/{contract_id}/analyze-risk',
        headers=headers
    )

    if analysis_response.status_code != 200:
        print(f"   [ERROR] Risk analysis failed: {analysis_response.text}")
        return

    result = analysis_response.json()
    print("   [OK] Risk analysis completed!")

    # 4. Display results
    risk_analysis = result.get('riskAnalysis', {})

    print(f"\n{'='*70}")
    print("RISK ANALYSIS RESULTS")
    print(f"{'='*70}")

    risk_level = risk_analysis.get('risk_level', 'N/A')
    risk_score = risk_analysis.get('risk_score', 0)
    total_deviations = risk_analysis.get('total_deviations', 0)
    critical = risk_analysis.get('critical_issues', 0)
    medium = risk_analysis.get('medium_issues', 0)
    low = risk_analysis.get('low_issues', 0)

    # Color codes
    risk_color = {
        'LOW': '[GREEN]',
        'MEDIUM': '[YELLOW]',
        'HIGH': '[RED]'
    }.get(risk_level, '[GRAY]')

    print(f"\nRisk Level:        {risk_color} {risk_level}")
    print(f"Risk Score:        {risk_score}/100")
    print(f"Total Deviations:  {total_deviations}")
    print(f"  - Critical:      {critical}")
    print(f"  - Medium:        {medium}")
    print(f"  - Low:           {low}")

    print(f"\nSummary: {risk_analysis.get('analysis_summary', 'No summary')}")

    # 5. Display deviations
    deviations = risk_analysis.get('deviations', [])

    if deviations:
        print(f"\n{'='*70}")
        print(f"DEVIATIONS FOUND ({len(deviations)})")
        print(f"{'='*70}\n")

        # Group by severity
        high_devs = [d for d in deviations if d['severity'] == 'HIGH']
        medium_devs = [d for d in deviations if d['severity'] == 'MEDIUM']
        low_devs = [d for d in deviations if d['severity'] == 'LOW']

        if high_devs:
            print(f"[HIGH SEVERITY] {len(high_devs)} issues:")
            for i, dev in enumerate(high_devs, 1):
                print(f"  {i}. {dev['clause_name']} - {dev['deviation_type']}")
                print(f"     {dev['description']}")
                print(f"     >> {dev.get('recommendation', 'No recommendation')}\n")

        if medium_devs:
            print(f"\n[MEDIUM SEVERITY] {len(medium_devs)} issues:")
            for i, dev in enumerate(medium_devs, 1):
                print(f"  {i}. {dev['clause_name']} - {dev['deviation_type']}")
                print(f"     {dev['description']}")
                print(f"     >> {dev.get('recommendation', 'No recommendation')}\n")

        if low_devs:
            print(f"\n[LOW SEVERITY] {len(low_devs)} issues:")
            for i, dev in enumerate(low_devs, 1):
                print(f"  {i}. {dev['clause_name']} - {dev['deviation_type']}")
                print(f"     {dev['description']}\n")

    # 6. Test GET endpoint
    print(f"\n{'='*70}")
    print("Testing GET Risk Analysis Endpoint")
    print(f"{'='*70}\n")

    get_response = requests.get(
        f'{BASE_URL}/contracts/{contract_id}/risk-analysis',
        headers=headers
    )

    if get_response.status_code == 200:
        print("[OK] Risk analysis retrieved successfully via GET endpoint")
    else:
        print(f"[ERROR] Failed to get risk analysis: {get_response.text}")

    print(f"\n{'='*70}")
    print("Test Complete!")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    test_risk_analysis()
