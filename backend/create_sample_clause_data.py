"""
Create Sample Data for Self-Healing Clause Library
Run this to populate test data for the Clause Health Dashboard
"""

import os
import django
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Clause, ClauseVersion, ClauseEvent, ClauseHealthMetrics, Contract, User
from datetime import datetime
import random


def create_sample_data():
    print("🚀 Creating sample data for Self-Healing Clause Library...")

    # Get or create a test user and contract
    user = User.objects.first()
    if not user:
        print("❌ No users found. Please create a user first.")
        return

    contract = Contract.objects.first()
    if not contract:
        print("❌ No contracts found. Please upload a contract first.")
        return

    print(f"✅ Using user: {user.email}")
    print(f"✅ Using contract: {contract.id}")

    # Sample clause data
    sample_clauses = [
        {
            'name': 'Liability Cap - Standard',
            'text': 'Liability shall be capped at the total contract value.',
            'events': [
                ('EXECUTED', 1.0),
                ('EXECUTED', 1.0),
                ('EXECUTED', 0.9),
                ('RENEWED', 1.0),
            ]
        },
        {
            'name': 'Payment Terms - Net 30',
            'text': 'Payment shall be made within 30 days of invoice.',
            'events': [
                ('EXECUTED', 0.8),
                ('DISPUTED', 0.3),
                ('EXECUTED', 0.7),
            ]
        },
        {
            'name': 'Termination - For Cause',
            'text': 'Either party may terminate for material breach with 30 days notice.',
            'events': [
                ('EXECUTED', 1.0),
                ('EXECUTED', 0.9),
                ('EXECUTED', 1.0),
                ('RENEWED', 1.0),
                ('RENEWED', 0.9),
            ]
        },
        {
            'name': 'Indemnification - Mutual',
            'text': 'Each party shall indemnify the other for third-party claims.',
            'events': [
                ('EXECUTED', 0.5),
                ('DISPUTED', 0.2),
                ('LITIGATED', 0.1),
            ]
        },
        {
            'name': 'Confidentiality - 5 Year',
            'text': 'Confidential information shall remain confidential for 5 years.',
            'events': [
                ('EXECUTED', 1.0),
                ('EXECUTED', 1.0),
                ('RENEWED', 1.0),
            ]
        },
        {
            'name': 'Force Majeure - Extended',
            'text': 'Neither party liable for delays due to force majeure events.',
            'events': [
                ('EXECUTED', 0.9),
                ('EXECUTED', 0.8),
            ]
        },
    ]

    created_count = 0

    for clause_data in sample_clauses:
        # Create Clause
        clause = Clause.objects.create(
            contract=contract,
            clause_name=clause_data['name'],
            extracted_text=clause_data['text'],
            found=True,
            confidence=random.uniform(0.8, 1.0)
        )

        # Create ClauseVersion
        version = ClauseVersion.objects.create(
            clause=clause,
            version_number=1,
            original_text=clause_data['text'],
            modified_text=clause_data['text'],
            modified_by=user
        )

        # Create ClauseEvents
        for event_type, outcome_score in clause_data['events']:
            ClauseEvent.objects.create(
                clause_version=version,
                contract=contract,
                event_type=event_type,
                outcome_score=outcome_score,
                jurisdiction='California' if random.random() > 0.5 else 'Delaware',
                counterparty_type='Enterprise' if random.random() > 0.5 else 'SMB'
            )

        # Calculate and create health metrics
        events = clause_data['events']
        avg_outcome = sum(score for _, score in events) / len(events)

        # Calculate component scores
        success_rate = avg_outcome
        enforceability = min(avg_outcome + 0.1, 1.0)
        negotiation_score = 1.0 - (sum(1 for e, _ in events if e == 'DISPUTED') / len(events))
        usage_count = len(events)

        # Calculate health score
        health_score = (
            0.40 * success_rate +
            0.30 * enforceability +
            0.20 * negotiation_score +
            0.10 * min(usage_count / 10, 1.0)
        )

        # Determine status
        if health_score >= 0.75:
            status = 'ALIVE'
        elif health_score >= 0.45:
            status = 'WEAK'
        else:
            status = 'RETIRED'

        ClauseHealthMetrics.objects.create(
            clause=clause,
            usage_count=usage_count,
            success_rate=success_rate,
            enforceability_score=enforceability,
            negotiation_score=negotiation_score,
            health_score=health_score,
            status=status
        )

        created_count += 1
        print(f"✅ Created: {clause_data['name']} (Health: {health_score:.2f}, Status: {status})")

    print(f"\n🎉 Successfully created {created_count} sample clauses!")
    print("\n📊 Summary:")
    print(f"   Total Clauses: {ClauseHealthMetrics.objects.count()}")
    print(f"   Alive: {ClauseHealthMetrics.objects.filter(status='ALIVE').count()}")
    print(f"   Weak: {ClauseHealthMetrics.objects.filter(status='WEAK').count()}")
    print(f"   Retired: {ClauseHealthMetrics.objects.filter(status='RETIRED').count()}")
    print("\n✨ Refresh your dashboard to see the data!")


if __name__ == '__main__':
    create_sample_data()
