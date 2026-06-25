"""
Populate negotiation_history table with realistic data for Counterparty Analysis
"""
import os
import django
import random
from datetime import timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from negotiation.models import Counterparty, NegotiationHistory

# Clause types that commonly appear in contracts
CLAUSE_TYPES = [
    'Intellectual Property Rights',
    'Termination',
    'Payment Terms',
    'Indemnification',
    'Confidentiality',
    'Data Protection',
    'Warranty',
    'Limitation of Liability',
    'Force Majeure',
    'Dispute Resolution',
    'Non-Compete',
    'Service Level Agreement',
    'Change Management',
    'Audit Rights',
    'Insurance Requirements'
]

# Sample clause texts for each type
SAMPLE_CLAUSES = {
    'Intellectual Property Rights': [
        "All intellectual property created during the term shall belong to the Client.",
        "Contractor retains ownership of all pre-existing IP and grants a license to Client.",
        "Joint IP shall be owned equally by both parties with mutual licensing rights."
    ],
    'Termination': [
        "Either party may terminate with 90 days written notice.",
        "Termination for convenience requires 30 days notice and payment of early termination fees.",
        "Material breach allows immediate termination without notice."
    ],
    'Payment Terms': [
        "Payment due net 30 days from invoice date.",
        "Milestone-based payments with 15-day review period.",
        "Annual payment in advance with quarterly reconciliation."
    ],
    'Indemnification': [
        "Provider shall indemnify Client for third-party IP claims up to contract value.",
        "Mutual indemnification for negligence and willful misconduct.",
        "Cap on indemnification liability at 2x annual contract value."
    ],
    'Limitation of Liability': [
        "Total liability capped at contract value in preceding 12 months.",
        "No limitation for gross negligence, fraud, or IP infringement.",
        "Consequential damages excluded except for data breaches."
    ]
}

def get_sample_clause_text(clause_type):
    """Get a random sample clause text for the given type"""
    if clause_type in SAMPLE_CLAUSES:
        return random.choice(SAMPLE_CLAUSES[clause_type])
    return f"Standard {clause_type} clause with industry-standard terms."

def generate_history_for_counterparty(counterparty, num_clauses=50):
    """Generate negotiation history for a counterparty"""

    # Define behavior profile
    profiles = {
        'AGGRESSIVE': {'acceptance_rate': 0.3, 'avg_rounds': 5, 'stall_rate': 0.2},
        'FLEXIBLE': {'acceptance_rate': 0.7, 'avg_rounds': 2, 'stall_rate': 0.05},
        'BALANCED': {'acceptance_rate': 0.5, 'avg_rounds': 3, 'stall_rate': 0.1},
    }

    # Randomly assign profile
    profile_type = random.choice(list(profiles.keys()))
    profile = profiles[profile_type]

    print(f"  Profile: {profile_type}")
    print(f"  Target acceptance rate: {profile['acceptance_rate']:.0%}")
    print(f"  Average rounds: {profile['avg_rounds']}")

    created_count = 0

    for _ in range(num_clauses):
        clause_type = random.choice(CLAUSE_TYPES)
        clause_text = get_sample_clause_text(clause_type)

        # Determine acceptance
        accepted = random.random() < profile['acceptance_rate']

        # Determine redline rounds (more if not accepted easily)
        if accepted and random.random() < 0.7:  # Quick acceptance
            redline_rounds = random.randint(0, 1)
        else:
            redline_rounds = random.randint(
                max(1, profile['avg_rounds'] - 2),
                profile['avg_rounds'] + 3
            )

        # Determine if stalled
        stalled = random.random() < profile['stall_rate']

        # Calculate deviation score (higher for rejected/stalled clauses)
        if stalled:
            deviation_score = random.uniform(0.7, 1.0)
        elif not accepted:
            deviation_score = random.uniform(0.5, 0.9)
        else:
            deviation_score = random.uniform(0.0, 0.4)

        # Create history record
        NegotiationHistory.objects.create(
            counterparty=counterparty,
            clause_type=clause_type,
            clause_text=clause_text,
            deviation_score=deviation_score,
            accepted=accepted,
            redline_rounds=redline_rounds,
            stalled=stalled
        )
        created_count += 1

    return created_count, profile_type

def main():
    print("=" * 70)
    print("POPULATING COUNTERPARTY NEGOTIATION HISTORY")
    print("=" * 70)

    # Get all counterparties
    counterparties = list(Counterparty.objects.all())

    if not counterparties:
        print("\nNo counterparties found!")
        print("Creating sample counterparties...")

        # Create sample counterparties
        sample_counterparties = [
            {"name": "TechVendor Solutions", "industry": "Technology"},
            {"name": "GlobalConsulting Inc", "industry": "Consulting"},
            {"name": "DataServices Corp", "industry": "Technology"},
            {"name": "LegalPartners LLP", "industry": "Legal"},
            {"name": "CloudInfra Systems", "industry": "Technology"},
            {"name": "SecurityFirst Ltd", "industry": "Security"},
            {"name": "Analytics Pro", "industry": "Analytics"},
            {"name": "DevOps Masters", "industry": "Technology"},
            {"name": "Compliance Experts", "industry": "Legal"},
            {"name": "Innovation Labs", "industry": "R&D"},
        ]

        for cp_data in sample_counterparties:
            Counterparty.objects.create(**cp_data)

        counterparties = list(Counterparty.objects.all())
        print(f"Created {len(counterparties)} counterparties\n")

    print(f"\nFound {len(counterparties)} counterparties")

    # Clear existing history
    existing_count = NegotiationHistory.objects.count()
    if existing_count > 0:
        print(f"Clearing {existing_count} existing negotiation history records...")
        NegotiationHistory.objects.all().delete()

    total_created = 0
    profile_distribution = {}

    # Generate history for each counterparty
    for i, counterparty in enumerate(counterparties, 1):
        num_clauses = random.randint(30, 80)  # Vary the amount of history

        print(f"\n[{i}/{len(counterparties)}] {counterparty.name}")
        print(f"  Generating {num_clauses} negotiation records...")

        created, profile_type = generate_history_for_counterparty(counterparty, num_clauses)

        total_created += created
        profile_distribution[profile_type] = profile_distribution.get(profile_type, 0) + 1

        print(f"  [OK] Created {created} records")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Counterparties processed: {len(counterparties)}")
    print(f"Total negotiation history records: {total_created}")
    print(f"Average records per counterparty: {total_created / len(counterparties):.1f}")
    print(f"\nProfile distribution:")
    for profile, count in profile_distribution.items():
        print(f"  {profile}: {count} counterparties")
    print("\n[OK] Counterparty Analysis should now show behavioral metrics!")
    print("[OK] Try selecting different counterparties to see varied profiles.")
    print("=" * 70)

if __name__ == '__main__':
    main()
