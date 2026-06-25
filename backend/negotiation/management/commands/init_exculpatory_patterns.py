"""
Management command to initialize exculpatory patterns in database and Qdrant
"""

from django.core.management.base import BaseCommand
from negotiation.models import ExculpatoryPattern
from ai.exculpatory_patterns import EXCULPATORY_PATTERNS
from ai.exculpatory_embeddings import generate_embeddings
from ai.exculpatory_qdrant import get_pattern_store
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Initialize exculpatory patterns in database and Qdrant vector store'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-initialization even if patterns exist',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)

        # Check if patterns already exist
        existing_count = ExculpatoryPattern.objects.count()
        if existing_count > 0 and not force:
            self.stdout.write(
                self.style.WARNING(
                    f'{existing_count} patterns already exist. Use --force to re-initialize.'
                )
            )
            return

        if force and existing_count > 0:
            self.stdout.write('Deleting existing patterns...')
            ExculpatoryPattern.objects.all().delete()

        self.stdout.write('Initializing exculpatory patterns...')

        # Extract pattern texts for embedding
        pattern_texts = [p["text"] for p in EXCULPATORY_PATTERNS]

        # Generate embeddings
        self.stdout.write('Generating embeddings...')
        embeddings = generate_embeddings(pattern_texts)

        # Store in database
        self.stdout.write('Storing patterns in database...')
        pattern_objects = []
        for pattern, embedding in zip(EXCULPATORY_PATTERNS, embeddings):
            pattern_obj = ExculpatoryPattern.objects.create(
                pattern_id=pattern["id"],
                label=pattern["label"],
                text=pattern["text"],
                risk_category=pattern["risk_category"],
                controlled_by=pattern["controlled_by"],
                explanation=pattern["explanation"],
                vector_embedding=embedding,
                is_active=True
            )
            pattern_objects.append(pattern_obj)

        self.stdout.write(
            self.style.SUCCESS(f'Created {len(pattern_objects)} patterns in database')
        )

        # Index in Qdrant
        try:
            self.stdout.write('Indexing patterns in Qdrant...')
            pattern_store = get_pattern_store()

            # Prepare data for Qdrant
            patterns_for_qdrant = []
            for pattern_obj in pattern_objects:
                patterns_for_qdrant.append({
                    "id": pattern_obj.id,
                    "pattern_id": pattern_obj.pattern_id,
                    "label": pattern_obj.label,
                    "text": pattern_obj.text,
                    "risk_category": pattern_obj.risk_category,
                    "controlled_by": pattern_obj.controlled_by,
                    "explanation": pattern_obj.explanation,
                    "vector_embedding": pattern_obj.vector_embedding
                })

            pattern_store.index_patterns(patterns_for_qdrant)

            self.stdout.write(
                self.style.SUCCESS(f'Indexed {len(patterns_for_qdrant)} patterns in Qdrant')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to index in Qdrant: {str(e)}')
            )
            self.stdout.write(
                self.style.WARNING('Patterns saved in database but not in Qdrant')
            )

        self.stdout.write(
            self.style.SUCCESS('Exculpatory pattern initialization complete!')
        )
