"""
Test Simulation API
Trigger a negotiation simulation to see if results vary
"""
import requests
import json

API_URL = "http://localhost:8000/api/negotiation/simulate/"

# Get list of contracts first
contracts_url = "http://localhost:8000/api/contracts/list"
print("Fetching contracts...")
contracts_response = requests.get(contracts_url)

if contracts_response.status_code != 200:
    print(f"Error fetching contracts: {contracts_response.status_code}")
    exit(1)

contracts = contracts_response.json()
if not contracts:
    print("No contracts found!")
    exit(1)

# Use first contract
contract_id = contracts[0]['id']
print(f"\nUsing contract: {contracts[0].get('original_filename', contract_id)}")
print(f"Contract ID: {contract_id}")

# Run simulation
print("\nRunning simulation...")
payload = {
    "contract_id": contract_id
}

response = requests.post(API_URL, json=payload)

if response.status_code != 200:
    print(f"Error: {response.status_code}")
    print(response.text)
    exit(1)

result = response.json()

print("\n" + "=" * 60)
print("SIMULATION RESULTS")
print("=" * 60)

# Print overall status
simulation = result.get('simulation', {})
print(f"\nStatus: {simulation.get('final_status', 'UNKNOWN')}")
print(f"Total Rounds: {simulation.get('rounds', 0)}")

# Print clause states by round
clause_states = simulation.get('clause_states', [])
print(f"\nTotal Clause States: {len(clause_states)}")

# Group by round
rounds = {}
for state in clause_states:
    round_num = state.get('round', 1)
    if round_num not in rounds:
        rounds[round_num] = []
    rounds[round_num].append(state)

# Show each round
for round_num in sorted(rounds.keys()):
    print(f"\n--- Round {round_num} ---")
    states = rounds[round_num]

    # Collect unique values
    redlines = set()
    stall_risks = set()

    for state in states:
        redlines.add(state.get('expected_redlines', 0))
        stall_risks.add(state.get('stall_risk', 0))

        print(f"  {state.get('clause_type', 'Unknown')}:")
        print(f"    Redlines: {state.get('expected_redlines')} | " +
              f"Stall Risk: {state.get('stall_risk')*100:.0f}% | " +
              f"Accepted: {state.get('accepted', False)}")

    print(f"\n  Round {round_num} Summary:")
    print(f"    Unique redline counts: {sorted(redlines)}")
    print(f"    Unique stall risks: {sorted([int(r*100) for r in stall_risks])}%")

# Final check
all_redlines = set(state.get('expected_redlines', 0) for state in clause_states)
all_stall_risks = set(state.get('stall_risk', 0) for state in clause_states)

print("\n" + "=" * 60)
print("OVERALL VARIANCE CHECK")
print("=" * 60)
print(f"Unique redline counts across all rounds: {sorted(all_redlines)}")
print(f"Unique stall risks across all rounds: {sorted([int(r*100) for r in all_stall_risks])}%")

if len(all_redlines) > 1 and len(all_stall_risks) > 1:
    print("\n✅ SUCCESS! Simulation shows VARIED values!")
else:
    print("\n⚠️  Values are still uniform")
