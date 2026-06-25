"""
Populate negotiation history with sample data for demonstration
"""
import os
import django
import random
from datetime import timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, Clause
from negotiation.models import NegotiationHistory, Counterparty

# Event types for negotiation
EVENT_TYPES = [
    'CLAUSE_PROPOSED',
    'CLAUSE_MODIFIED',
    'COUNTER_OFFER',
    'ACCEPTED',
    'REJECTED',
    'REVISED',
    'STALLED'
]

# Negotiation patterns for different counterparty behaviors
AGGRESSIVE_PATTERN = {
    'clause_changes_per_round': (3, 6),
    'rejection_rate': 0.6,
    'stall_probability': 0.1,
    'response_delay_hours': (2, 12)
}

FLEXIBLE_PATTERN = {
    'clause_changes_per_round': (1, 3),
    'rejection_rate': 0.2,
    'stall_probability': 0.05,
    'response_delay_hours': (1, 6)
}

BALANCED_PATTERN = {
    'clause_changes_per_round': (2, 4),
    'rejection_rate': 0.4,
    'stall_probability': 0.15,
    'response_delay_hours': (4, 24)
}

def generate_negotiation_rounds(contract, counterparty, num_rounds=5, pattern='BALANCED'):
    """Generate realistic negotiation history for a contract"""

    patterns = {
        'AGGRESSIVE': AGGRESSIVE_PATTERN,
        'FLEXIBLE': FLEXIBLE_PATTERN,
        'BALANCED': BALANCED_PATTERN
    }

    config = patterns.get(pattern, BALANCED_PATTERN)
    clauses = list(contract.clauses.all()[:10])  # Use first 10 clauses

    if not clauses:
        print(f"  No clauses found for contract {contract.id}")
        return 0

    created_count = 0
    current_time = timezone.now() - timedelta(days=90)  # Start 90 days ago

    for round_num in range(1, num_rounds + 1):
        # Determine events for this round
        num_changes = random.randint(*config['clause_changes_per_round'])

        for _ in range(num_changes):
            clause = random.choice(clauses)

            # Determine event type based on pattern
            if random.random() < config['rejection_rate']:
                event_type = 'REJECTED'
            elif random.random() < 0.3:
                event_type = 'COUNTER_OFFER'
            elif random.random() < 0.5:
                event_type = 'CLAUSE_MODIFIED'
            else:
                event_type = 'CLAUSE_PROPOSED'

            # Check for stall
            if random.random() < config['stall_probability']:
                event_type = 'STALLED'
                current_time += timedelta(hours=random.randint(48, 168))  # 2-7 days delay

            # Create negotiation event
            NegotiationHistory.objects.create(
                contract=contract,
                counterparty=counterparty,
                clause=clause,
                round_number=round_num,
                event_type=event_type,
                proposed_text=f"Modified clause text for {clause.clause_type} (Round {round_num})",
                justification=f"Counterparty {counterparty.name} {event_type.lower()} this clause",
                timestamp=current_time
            )
            created_count += 1

            # Add response delay
            delay_hours = random.randint(*config['response_delay_hours'])
            current_time += timedelta(hours=delay_hours)

        # Final acceptance in last round (70% chance)
        if round_num == num_rounds and random.random() < 0.7:
            NegotiationHistory.objects.create(
                contract=contract,
                counterparty=counterparty,
                clause=random.choice(clauses),
                round_number=round_num,
                event_type='ACCEPTED',
                proposed_text="Final agreement reached",
                justification="Both parties agreed to terms",
                timestamp=current_time
            )
            created_count += 1

    return created_count

def main():
    print("=" * 60)
    print("POPULATING NEGOTIATION HISTORY")
    print("=" * 60)

    # Get all contracts with counterparties
    contracts = Contract.objects.select_related('counterparty').all()[:30]  # First 30 contracts

    if not contracts:
        print("No contracts found!")
        return

    print(f"\nFound {contracts.count()} contracts")

    # Clear existing negotiation history
    existing_count = NegotiationHistory.objects.count()
    print(f"Clearing {existing_count} existing negotiation records...")
    NegotiationHistory.objects.all().delete()

    total_created = 0
    contracts_processed = 0

    # Assign negotiation patterns to counterparties
    patterns = ['AGGRESSIVE', 'FLEXIBLE', 'BALANCED']

    for contract in contracts:
        if not contract.counterparty:
            print(f"Skipping contract {contract.id} - no counterparty")
            continue

        # Randomly assign pattern (or use counterparty-specific logic)
        pattern = random.choice(patterns)
        num_rounds = random.randint(3, 7)

        print(f"\nContract: {contract.title[:50]}...")
        print(f"  Counterparty: {contract.counterparty.name}")
        print(f"  Pattern: {pattern}, Rounds: {num_rounds}")

        created = generate_negotiation_rounds(
            contract,
            contract.counterparty,
            num_rounds=num_rounds,
            pattern=pattern
        )

        total_created += created
        contracts_processed += 1
        print(f"  Created {created} negotiation events")

    print("\n" + "=" * 60)
    print(f"SUMMARY")
    print("=" * 60)
    print(f"Contracts processed: {contracts_processed}")
    print(f"Total negotiation events created: {total_created}")
    print(f"Average events per contract: {total_created / contracts_processed if contracts_processed > 0 else 0:.1f}")
    print("\nCounterparty Analysis should now show behavioral metrics!")
    print("=" * 60)

if __name__ == '__main__':
    main()
