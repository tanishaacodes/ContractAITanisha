"""
Populate Health Metrics from Existing Contracts & Clauses
Uses your existing data to create health metrics
"""

import os
import django
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

django.setup()

from core.models import Clause, ClauseVersion, ClauseEvent, ClauseHealthMetrics, User
import random


def populate_health_metrics():
    print("Populating health metrics from existing clauses...")

    # Get existing clauses
    existing_clauses = Clause.objects.all()[:20]  # Take first 20 clauses

    if not existing_clauses.exists():
        print("❌ No clauses found in the database.")
        print("   Please upload contracts first!")
        return

    print(f"✅ Found {existing_clauses.count()} clauses to process")

    user = User.objects.first()
    created_count = 0
    updated_count = 0

    for clause in existing_clauses:
        # Delete existing health metrics to recreate with new varied data
        if hasattr(clause, 'health_metrics'):
            clause.health_metrics.delete()
            print(f"🔄 Recreating metrics for: {clause.clause_name}")
            updated_count += 1

        # Get or create a clause version
        version, created = ClauseVersion.objects.get_or_create(
            clause=clause,
            version_number=1,
            defaults={
                'original_text': clause.extracted_text or 'No text available',
                'modified_text': clause.extracted_text or 'No text available',
                'modified_by': user
            }
        )

        # Create random events with variety to ensure diverse health scores
        # Use random seed based on clause ID for reproducibility but variety
        seed = hash(clause.id) % 100
        random.seed(seed)

        risk = clause.risk_score or random.uniform(0.2, 0.9)

        # Generate varied event patterns with more randomness
        event_patterns = [
            # Excellent performers (will be ALIVE)
            [
                ('EXECUTED', random.uniform(0.95, 1.0)),
                ('EXECUTED', random.uniform(0.9, 1.0)),
                ('RENEWED', random.uniform(0.95, 1.0)),
                ('EXECUTED', random.uniform(0.95, 1.0)),
                ('RENEWED', random.uniform(0.9, 1.0)),
            ],
            [
                ('EXECUTED', random.uniform(0.9, 1.0)),
                ('EXECUTED', random.uniform(0.85, 0.95)),
                ('EXECUTED', random.uniform(0.9, 1.0)),
                ('RENEWED', random.uniform(0.95, 1.0)),
            ],
            # Good performers (will be ALIVE)
            [
                ('EXECUTED', random.uniform(0.8, 0.9)),
                ('EXECUTED', random.uniform(0.85, 0.95)),
                ('RENEWED', random.uniform(0.9, 1.0)),
                ('EXECUTED', random.uniform(0.8, 0.9)),
            ],
            # Medium performers (will be WEAK)
            [
                ('EXECUTED', random.uniform(0.7, 0.8)),
                ('EXECUTED', random.uniform(0.65, 0.75)),
                ('DISPUTED', random.uniform(0.4, 0.5)),
                ('EXECUTED', random.uniform(0.6, 0.7)),
            ],
            [
                ('EXECUTED', random.uniform(0.6, 0.7)),
                ('DISPUTED', random.uniform(0.3, 0.5)),
                ('EXECUTED', random.uniform(0.7, 0.8)),
            ],
            # Poor performers (will be WEAK/RETIRED)
            [
                ('EXECUTED', random.uniform(0.5, 0.6)),
                ('DISPUTED', random.uniform(0.3, 0.4)),
                ('DISPUTED', random.uniform(0.2, 0.4)),
                ('EXECUTED', random.uniform(0.4, 0.5)),
            ],
            # Bad performers (will be RETIRED)
            [
                ('DISPUTED', random.uniform(0.1, 0.3)),
                ('DISPUTED', random.uniform(0.2, 0.3)),
                ('LITIGATED', random.uniform(0.05, 0.15)),
            ],
            [
                ('EXECUTED', random.uniform(0.3, 0.5)),
                ('DISPUTED', random.uniform(0.1, 0.3)),
                ('LITIGATED', random.uniform(0.1, 0.2)),
                ('DISPUTED', random.uniform(0.2, 0.3)),
            ],
        ]

        # Select a random pattern
        events = random.choice(event_patterns)

        # Delete existing events for this version to prevent duplicates
        ClauseEvent.objects.filter(clause_version=version).delete()

        # Create events
        for event_type, outcome_score in events:
            ClauseEvent.objects.create(
                clause_version=version,
                contract=clause.contract,
                event_type=event_type,
                outcome_score=outcome_score,
                jurisdiction='California' if random.random() > 0.5 else 'Delaware',
                counterparty_type='Enterprise' if random.random() > 0.5 else 'SMB'
            )

        # Calculate health metrics
        avg_outcome = sum(score for _, score in events) / len(events)
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

        # Create health metrics
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
        print(f"✅ Created metrics for: {clause.clause_name[:50]} (Health: {health_score:.2f}, Status: {status})")

    print(f"\n🎉 Successfully processed {created_count + updated_count} clauses!")
    if updated_count > 0:
        print(f"   ({updated_count} updated, {created_count} new)")
    print("\n📊 Summary:")
    print(f"   Total Clauses: {ClauseHealthMetrics.objects.count()}")
    print(f"   Alive: {ClauseHealthMetrics.objects.filter(status='ALIVE').count()}")
    print(f"   Weak: {ClauseHealthMetrics.objects.filter(status='WEAK').count()}")
    print(f"   Retired: {ClauseHealthMetrics.objects.filter(status='RETIRED').count()}")
    print("\n✨ Refresh your dashboard to see the data!")


if __name__ == '__main__':
    populate_health_metrics()
