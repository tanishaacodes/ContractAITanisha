from django.core.management.base import BaseCommand
from neo4j import GraphDatabase
from django.conf import settings

class Command(BaseCommand):
    help = 'Clear all contract-related data from Neo4j graph database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all graph data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.ERROR(
                'WARNING: This will permanently delete ALL data from Neo4j graph database!\n'
                'To confirm, run: python manage.py clear_neo4j_graph --confirm'
            ))
            return

        try:
            driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            
            with driver.session() as session:
                # Delete all nodes and relationships
                result = session.run("MATCH (n) DETACH DELETE n RETURN count(n) as deleted")
                record = result.single()
                deleted_count = record['deleted'] if record else 0
                
                self.stdout.write(self.style.SUCCESS(
                    f'[SUCCESS] Deleted {deleted_count} nodes and their relationships from Neo4j'
                ))
                
            driver.close()
            self.stdout.write(self.style.SUCCESS('\n[COMPLETE] Neo4j graph database has been cleared!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[ERROR] Failed to clear Neo4j: {str(e)}'))
