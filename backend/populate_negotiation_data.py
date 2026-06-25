"""
Populate Negotiation Intelligence Sample Data
Adds counterparties, negotiation history, and initializes Qdrant collections
"""
import os
import django
import random
from datetime import date

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from negotiation.models import (
    Counterparty,
    NegotiationHistory,
    CounterpartyBehaviorSnapshot,
    ClauseInteractionPattern
)
from ai.embedding import embed, embed_clause_pair
from ai.vectorstore import (
    ensure_collections,
    store_negotiation_vectors_batch,
    store_risk_patterns_batch
)

# Sample counterparties with different behaviors
COUNTERPARTIES = [
    {'name': 'Acme Corp', 'industry': 'Technology', 'profile': 'aggressive'},
    {'name': 'Global Solutions Inc', 'industry': 'Consulting', 'profile': 'balanced'},
    {'name': 'Tech Dynamics', 'industry': 'Software', 'profile': 'flexible'},
    {'name': 'Enterprise Systems', 'industry': 'Enterprise', 'profile': 'aggressive'},
    {'name': 'Innovation Labs', 'industry': 'R&D', 'profile': 'flexible'},
]

# Clause types and sample texts
CLAUSE_SAMPLES = {
    'IP Ownership': [
        'All intellectual property created under this agreement shall be owned by the Company.',
        'IP rights shall remain with the Company, including all derivative works.',
        'The Company retains exclusive ownership of all IP developed during this engagement.',
    ],
    'Limitation of Liability': [
        'Total liability is capped at the contract value.',
        'Liability shall not exceed the fees paid in the preceding 12 months.',
        'Maximum liability is limited to 200% of contract value.',
    ],
    'Termination': [
        'Either party may terminate with 90 days written notice.',
        'Contract may be terminated for convenience with 60 days notice.',
        'Termination requires 120 days advance notice.',
    ],
    'Price Escalation': [
        'Prices increase 5% annually.',
        'Annual price adjustment based on CPI, capped at 10%.',
        'Fees escalate 3% per year.',
    ],
    'Auto-Renewal': [
        'Contract automatically renews for 1-year terms unless terminated.',
        'Auto-renewal for successive 12-month periods.',
        'Automatic extension for one year unless either party provides notice.',
    ],
    'Confidentiality': [
        'All information shall remain confidential for 5 years.',
        'Confidential information protected during and for 3 years after termination.',
        'Non-disclosure obligations survive for 7 years.',
    ],
    'Indemnity': [
        'Company indemnifies vendor against all third-party claims.',
        'Mutual indemnification for breaches of this agreement.',
        'Vendor shall indemnify Company for IP infringement claims.',
    ],
    'Payment Terms': [
        'Net 30 payment terms.',
        'Payment due within 45 days of invoice.',
        'Monthly invoicing with 60-day payment terms.',
    ],
}

# Behavior profiles
BEHAVIOR_PROFILES = {
    'aggressive': {
        'acceptance_rate': (0.1, 0.3),
        'redline_range': (4, 7),
        'stall_rate': (0.3, 0.6),
    },
    'balanced': {
        'acceptance_rate': (0.4, 0.6),
        'redline_range': (2, 4),
        'stall_rate': (0.15, 0.35),
    },
    'flexible': {
        'acceptance_rate': (0.7, 0.9),
        'redline_range': (1, 3),
        'stall_rate': (0.05, 0.2),
    },
}

# Known dangerous clause interaction patterns
RISK_PATTERNS = [
    {
        'clauses': ['Auto-Renewal', 'Price Escalation'],
        'risk_type': 'HIDDEN_COST_ESCALATION',
        'description': 'Auto-renewal combined with price escalation creates compounding cost risk',
        'impact_multiplier': 0.6,
    },
    {
        'clauses': ['Termination', 'Payment Terms'],
        'risk_type': 'TERMINATION_PAYMENT_MISMATCH',
        'description': 'Termination rights conflict with payment obligations',
        'impact_multiplier': 0.45,
    },
    {
        'clauses': ['Indemnity', 'Limitation of Liability'],
        'risk_type': 'DELAYED_LIABILITY',
        'description': 'Uncapped indemnity despite liability limitations',
        'impact_multiplier': 0.8,
    },
    {
        'clauses': ['Confidentiality', 'Termination'],
        'risk_type': 'LONG_TAIL_LIABILITY',
        'description': 'Confidentiality obligations extend beyond contract term',
        'impact_multiplier': 0.35,
    },
]


def create_counterparties():
    """Create sample counterparties"""
    print("Creating counterparties...")
    created = []

    for cp_data in COUNTERPARTIES:
        cp, created_flag = Counterparty.objects.get_or_create(
            name=cp_data['name'],
            defaults={
                'industry': cp_data['industry'],
                'risk_profile': 0.5,
            }
        )
        if created_flag:
            print(f"  [OK] Created: {cp.name}")
        else:
            print(f"  - Exists: {cp.name}")
        created.append((cp, cp_data['profile']))

    return created


def generate_negotiation_history(counterparty, profile, count=20):
    """Generate negotiation history for a counterparty"""
    print(f"\nGenerating {count} negotiation records for {counterparty.name}...")

    behavior = BEHAVIOR_PROFILES[profile]
    histories = []
    vectors = []
    payloads = []

    for i in range(count):
        # Random clause type
        clause_type = random.choice(list(CLAUSE_SAMPLES.keys()))
        clause_text = random.choice(CLAUSE_SAMPLES[clause_type])

        # Generate behavior based on profile
        accepted = random.random() < random.uniform(*behavior['acceptance_rate'])
        redline_rounds = random.randint(*behavior['redline_range'])
        stalled = random.random() < random.uniform(*behavior['stall_rate'])

        # Some clause types are harder (lower acceptance)
        if clause_type in ['IP Ownership', 'Termination']:
            accepted = random.random() < (random.uniform(*behavior['acceptance_rate']) * 0.5)
            if not accepted:
                stalled = random.random() < 0.7

        history = NegotiationHistory(
            counterparty=counterparty,
            clause_type=clause_type,
            clause_text=clause_text,
            deviation_score=random.uniform(0.1, 0.9),
            accepted=accepted,
            redline_rounds=redline_rounds,
            stalled=stalled,
        )
        histories.append(history)

        # Generate embedding
        vector = embed(clause_text)
        vectors.append(vector)

        payloads.append({
            'counterparty': counterparty.name,
            'clause_type': clause_type,
            'accepted': accepted,
            'redline_rounds': redline_rounds,
            'stalled': stalled,
        })

    # Bulk create
    NegotiationHistory.objects.bulk_create(histories)
    print(f"  [OK] Created {len(histories)} negotiation records")

    return vectors, payloads


def calculate_behavior_snapshot(counterparty):
    """Calculate and save behavior snapshot"""
    from ai.behavior_metrics import compute_behavior_metrics

    history = NegotiationHistory.objects.filter(counterparty=counterparty)
    if not history.exists():
        return

    metrics = compute_behavior_metrics(history)
    if not metrics:
        return

    CounterpartyBehaviorSnapshot.objects.create(
        counterparty=counterparty,
        avg_acceptance_rate=metrics['acceptance_rate'],
        avg_redline_rounds=metrics['avg_redlines'],
        stall_rate=metrics['stall_rate'],
        aggressiveness_score=metrics['aggressiveness'],
        elasticity_score=metrics['elasticity'],
    )
    print(f"  [OK] Saved behavior snapshot for {counterparty.name}")


def populate_risk_patterns():
    """Populate known risk patterns"""
    print("\nPopulating risk patterns...")

    vectors = []
    payloads = []

    for i, pattern in enumerate(RISK_PATTERNS):
        # Get sample texts for the clause pair
        clause_a_type = pattern['clauses'][0]
        clause_b_type = pattern['clauses'][1]

        clause_a_text = CLAUSE_SAMPLES.get(clause_a_type, [''])[0]
        clause_b_text = CLAUSE_SAMPLES.get(clause_b_type, [''])[0]

        # Generate clause-pair embedding
        vector = embed_clause_pair(clause_a_text, clause_b_text)
        vectors.append(vector)

        payloads.append({
            'clause_types': pattern['clauses'],
            'risk_type': pattern['risk_type'],
            'pattern': pattern['description'],
            'impact_multiplier': pattern['impact_multiplier'],
        })

        # Also save to database
        ClauseInteractionPattern.objects.get_or_create(
            clause_types=pattern['clauses'],
            risk_type=pattern['risk_type'],
            defaults={
                'pattern_description': pattern['description'],
                'impact_multiplier': pattern['impact_multiplier'],
                'vector_embedding': vector,
                'is_active': True,
            }
        )

    print(f"  [OK] Created {len(RISK_PATTERNS)} risk patterns")

    return vectors, payloads


def main():
    """Main execution"""
    print("=" * 60)
    print("NEGOTIATION INTELLIGENCE - SAMPLE DATA POPULATION")
    print("=" * 60)

    # Step 1: Initialize Qdrant collections
    print("\n1. Initializing Qdrant collections...")
    try:
        ensure_collections()
        print("  [OK] Qdrant collections ready")
    except Exception as e:
        print(f"  [ERROR] Error initializing Qdrant: {e}")
        print("  Make sure Qdrant is running on localhost:6333")
        return

    # Step 2: Create counterparties
    print("\n2. Creating counterparties...")
    counterparties = create_counterparties()

    # Step 3: Generate negotiation history
    print("\n3. Generating negotiation history...")
    all_vectors = []
    all_payloads = []
    start_idx = 0

    for counterparty, profile in counterparties:
        vectors, payloads = generate_negotiation_history(counterparty, profile, count=25)
        all_vectors.extend(vectors)
        all_payloads.extend(payloads)

        # Calculate behavior snapshot
        calculate_behavior_snapshot(counterparty)

    # Step 4: Store in Qdrant
    print("\n4. Storing vectors in Qdrant...")
    try:
        store_negotiation_vectors_batch(all_vectors, all_payloads, start_idx=0)
        print(f"  [OK] Stored {len(all_vectors)} negotiation vectors")
    except Exception as e:
        print(f"  [ERROR] Error storing vectors: {e}")

    # Step 5: Populate risk patterns
    print("\n5. Populating risk patterns...")
    risk_vectors, risk_payloads = populate_risk_patterns()

    try:
        store_risk_patterns_batch(risk_vectors, risk_payloads, start_idx=0)
        print(f"  [OK] Stored {len(risk_vectors)} risk pattern vectors")
    except Exception as e:
        print(f"  [ERROR] Error storing risk patterns: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Counterparties created: {len(counterparties)}")
    print(f"Negotiation records: {NegotiationHistory.objects.count()}")
    print(f"Behavior snapshots: {CounterpartyBehaviorSnapshot.objects.count()}")
    print(f"Risk patterns: {ClauseInteractionPattern.objects.count()}")
    print("\n[OK] Sample data population complete!")
    print("\nYou can now:")
    print("  1. View counterparty behavior: /negotiation-intelligence")
    print("  2. Run simulations with sample data")
    print("  3. Detect silent risks in contracts")
    print("=" * 60)


if __name__ == '__main__':
    main()
