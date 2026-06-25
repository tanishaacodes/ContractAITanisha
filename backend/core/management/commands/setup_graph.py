"""
Management command to initialize Neo4j and sync clause data
Usage: python manage.py setup_graph
"""

from django.core.management.base import BaseCommand
from ai.graph_driver import get_neo4j_driver
from ai.graph_sync import get_graph_sync
from core.models import Clause


class Command(BaseCommand):
    help = 'Initialize Neo4j schema and sync clause data to graph database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sync-all',
            action='store_true',
            help='Sync all clauses to Neo4j',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Limit number of clauses to sync (default: 20)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== Neo4j Graph Setup ===\n'))

        # Step 1: Check connection
        driver = get_neo4j_driver()

        if not driver.driver:
            self.stdout.write(self.style.ERROR(
                '[ERROR] Neo4j is not connected!\n\n'
                'Please set the following environment variables:\n'
                '  NEO4J_URI=bolt://localhost:7687\n'
                '  NEO4J_USER=neo4j\n'
                '  NEO4J_PASSWORD=your_password\n\n'
                'Or install and start Neo4j:\n'
                '  1. Download from: https://neo4j.com/download/\n'
                '  2. Start Neo4j Desktop or run: neo4j start\n'
                '  3. Set password and update environment variables\n'
            ))
            return

        self.stdout.write(self.style.SUCCESS(f'[OK] Connected to Neo4j at {driver.uri}\n'))

        # Step 2: Initialize schema
        self.stdout.write('Initializing Neo4j schema...')
        driver.initialize_schema()
        self.stdout.write(self.style.SUCCESS('[OK] Schema initialized\n'))

        # Step 3: Sync clauses (if requested)
        if options['sync_all']:
            limit = options['limit']
            self.stdout.write(f'Syncing up to {limit} clauses to graph...\n')

            graph_sync = get_graph_sync()
            clauses = Clause.objects.all()[:limit]

            if not clauses.exists():
                self.stdout.write(self.style.WARNING(
                    '⚠️  No clauses found in database.\n'
                    'Please upload contracts and run populate_health_from_existing.py first.\n'
                ))
                return

            synced_count = 0
            for clause in clauses:
                try:
                    graph_sync.sync_clause_family(clause)
                    synced_count += 1
                    self.stdout.write(f'  [OK] Synced: {clause.clause_name}')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  [FAIL] Failed: {clause.clause_name} - {e}'))

            self.stdout.write(self.style.SUCCESS(f'\n[OK] Synced {synced_count}/{clauses.count()} clauses\n'))

        # Step 4: Show next steps
        self.stdout.write(self.style.SUCCESS(
            '\n=== Next Steps ===\n'
            '1. Run with --sync-all to sync clause data: python manage.py setup_graph --sync-all\n'
            '2. Access graph API at: http://localhost:8002/api/graph/status/\n'
            '3. View evolution at: http://localhost:8002/api/graph/evolution/{clause_id}/\n'
        ))
