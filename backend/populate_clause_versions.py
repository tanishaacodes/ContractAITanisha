"""
Generate ClauseVersion objects for existing Clause objects
This enables evolution tracking in Neo4j
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Clause, ClauseVersion, User
from ai.graph_sync import get_graph_sync

def create_versions_for_clauses(limit=50):
    """Create initial versions for clauses that don't have any"""
    print("=" * 60)
    print("Creating ClauseVersion objects for existing clauses...")
    print("=" * 60)

    # Get a user to assign as modifier (use first admin)
    try:
        admin_user = User.objects.filter(role__name='Admin').first() or User.objects.first()
        if not admin_user:
            print("\nNo users found! Please create a user first.")
            return 0
        print(f"\nUsing user: {admin_user.email} as modifier\n")
    except Exception as e:
        print(f"\nError getting user: {e}")
        return 0

    # Get clauses without versions
    clauses = Clause.objects.filter(versions__isnull=True)[:limit]

    if not clauses.exists():
        print("\nAll clauses already have versions!")
        return

    print(f"\nFound {clauses.count()} clauses without versions")
    print(f"Creating version 1 for each...\n")

    created_count = 0
    for clause in clauses:
        try:
            # Create version 1
            ClauseVersion.objects.create(
                clause=clause,
                version_number=1,
                original_text=clause.extracted_text or "No text available",
                modified_text=clause.extracted_text or "No text available",
                change_description="Initial version from contract extraction",
                new_risk_score=clause.risk_score or 0.5,
                new_risk_level=clause.risk_level or 'MEDIUM',
                modified_by=admin_user,
            )
            created_count += 1
            print(f"  + Created version for: {clause.clause_name[:50]}")
        except Exception as e:
            print(f"  x Failed for {clause.clause_name[:50]}: {e}")

    print(f"\n{'=' * 60}")
    print(f"Created {created_count} versions")
    print(f"{'=' * 60}\n")

    return created_count

def sync_to_neo4j(limit=50):
    """Sync clauses with versions to Neo4j"""
    print("=" * 60)
    print("Syncing clauses to Neo4j...")
    print("=" * 60)

    graph_sync = get_graph_sync()
    clauses = Clause.objects.filter(versions__isnull=False)[:limit]

    if not clauses.exists():
        print("\nNo clauses with versions found!")
        return

    print(f"\nSyncing {clauses.count()} clauses to Neo4j...\n")

    synced_count = 0
    for clause in clauses:
        try:
            graph_sync.sync_clause_family(clause)
            synced_count += 1
            print(f"  + Synced: {clause.clause_name[:50]}")
        except Exception as e:
            print(f"  x Failed: {clause.clause_name[:50]} - {e}")

    print(f"\n{'=' * 60}")
    print(f"Synced {synced_count} clauses to Neo4j")
    print(f"{'=' * 60}\n")

    return synced_count

if __name__ == "__main__":
    # Create versions
    created = create_versions_for_clauses(limit=50)

    if created > 0:
        # Sync to Neo4j
        input("\nPress Enter to sync to Neo4j...")
        sync_to_neo4j(limit=50)

    print("\n[DONE] Done! Your clauses now have evolution data.")
    print("Refresh the AI Clause Library and click the Evolution button!")
