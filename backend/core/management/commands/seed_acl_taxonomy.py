"""
Management command: seed the Advanced Clause Library taxonomy.

    python manage.py seed_acl_taxonomy
    python manage.py seed_acl_taxonomy --force   # re-embed all categories

Loads:
  1. STANDARD_TAXONOMY from advanced_clause_library_service (15 parent + 80+ child nodes)
  2. risk_taxonomy.yaml (8 arbitration risk dimensions + indicators as leaf nodes)
"""
import logging
import os

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Seed the Advanced Clause Library taxonomy from STANDARD_TAXONOMY and risk_taxonomy.yaml'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-embed all categories even if embedding already stored',
        )

    def handle(self, *args, **options):
        from api.advanced_clause_library_service import STANDARD_TAXONOMY, _get_embed_model
        from core.models import ClauseCategory

        force = options['force']

        # ── 1. Standard legal taxonomy ────────────────────────────────────────
        self.stdout.write('Seeding standard legal taxonomy...')
        std_created = 0

        try:
            # Try full engine path (loads MiniLM, builds FAISS index)
            from api.advanced_clause_library_service import get_taxonomy_engine
            engine = get_taxonomy_engine()
            std_created = engine.seed_standard_taxonomy()
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  Engine unavailable ({e}), using DB-only seed'))
            for parent_name, children in STANDARD_TAXONOMY.items():
                parent, is_new = ClauseCategory.objects.get_or_create(
                    name=parent_name,
                    defaults={'is_standard': True, 'embedding_vector': []},
                )
                if is_new:
                    std_created += 1
                for child_name in children:
                    _, child_new = ClauseCategory.objects.get_or_create(
                        name=child_name,
                        defaults={
                            'is_standard': True,
                            'parent_id': parent.id,
                            'embedding_vector': [],
                        },
                    )
                    if child_new:
                        std_created += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ Standard taxonomy: {std_created} new categories'))

        # ── 2. Arbitration risk taxonomy from YAML ────────────────────────────
        yaml_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), '..', '..', '..', 'api', 'risk_taxonomy.yaml')
        )

        if not os.path.exists(yaml_path):
            self.stdout.write(self.style.WARNING(f'  risk_taxonomy.yaml not found at {yaml_path}, skipping'))
            yaml_created = 0
        else:
            self.stdout.write('Seeding arbitration risk taxonomy from YAML...')
            try:
                import yaml
            except ImportError:
                self.stdout.write(self.style.ERROR('  PyYAML not installed. Run: pip install pyyaml'))
                yaml_created = 0
            else:
                with open(yaml_path, 'r') as f:
                    data = yaml.safe_load(f)

                arb_root = data.get('arbitration_risk_taxonomy', {})
                yaml_created = 0

                # Try to load embedding model; gracefully degrade if unavailable
                try:
                    embed_model = _get_embed_model()
                    use_embed = True
                except Exception:
                    embed_model = None
                    use_embed = False

                # Top-level parent: "Arbitration Risk"
                arb_parent, arb_new = ClauseCategory.objects.get_or_create(
                    name='Arbitration Risk',
                    defaults={'is_standard': True, 'embedding_vector': []},
                )
                if arb_new:
                    yaml_created += 1

                for dim_key, dim_data in arb_root.items():
                    readable = dim_key.replace('_', ' ').title()
                    weight = dim_data.get('weight', 0.5)
                    indicators = dim_data.get('indicators', [])
                    description = f'Weight: {weight}. Indicators: {", ".join(indicators[:4])}'

                    emb = embed_model.encode([readable])[0].tolist() if use_embed else []
                    dim_cat, dim_new = ClauseCategory.objects.get_or_create(
                        name=readable,
                        defaults={
                            'is_standard': True,
                            'parent_id': arb_parent.id,
                            'embedding_vector': emb,
                            'description': description,
                        },
                    )
                    if dim_new:
                        yaml_created += 1

                    # Re-embed on --force if needed
                    if force and not dim_new and use_embed:
                        dim_cat.embedding_vector = emb
                        dim_cat.description = description
                        dim_cat.save(update_fields=['embedding_vector', 'description', 'updated_at'])

                    # Leaf nodes: each indicator phrase
                    for indicator in indicators:
                        indicator_name = indicator.strip().title()
                        i_emb = embed_model.encode([indicator_name])[0].tolist() if use_embed else []
                        _, ind_new = ClauseCategory.objects.get_or_create(
                            name=indicator_name,
                            defaults={
                                'is_standard': True,
                                'parent_id': dim_cat.id,
                                'embedding_vector': i_emb,
                            },
                        )
                        if ind_new:
                            yaml_created += 1
                        elif force and use_embed:
                            ClauseCategory.objects.filter(name=indicator_name).update(
                                embedding_vector=i_emb
                            )

                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ Arbitration risk taxonomy: {yaml_created} new categories from {len(arb_root)} dimensions'
                ))

        # ── 3. Summary ────────────────────────────────────────────────────────
        total = ClauseCategory.objects.count()
        standard = ClauseCategory.objects.filter(is_standard=True).count()
        self.stdout.write(self.style.SUCCESS(
            f'\nDone. DB totals: {total} categories ({standard} standard, {total - standard} auto-discovered)'
        ))