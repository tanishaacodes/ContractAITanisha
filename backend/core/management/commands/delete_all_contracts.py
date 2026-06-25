from django.core.management.base import BaseCommand
from django.db import connection
from core.models import Contract
import os
import shutil

class Command(BaseCommand):
    help = 'Permanently delete all contracts and related data from database and filesystem'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all contracts',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.ERROR(
                'WARNING: This will permanently delete ALL contracts and related data!\n'
                'To confirm, run: python manage.py delete_all_contracts --confirm'
            ))
            return

        self.stdout.write(self.style.WARNING('Starting deletion process...'))

        # Get all contracts before deletion for file cleanup
        contracts = Contract.objects.all()
        contract_count = contracts.count()
        
        # Collect file paths
        file_paths = []
        for contract in contracts:
            if contract.file_path and os.path.exists(contract.file_path):
                file_paths.append(contract.file_path)

        # Delete from related tables first (to avoid foreign key constraints)
        with connection.cursor() as cursor:
            tables_to_clear = [
                'clauses',
                'versions',
                'exculpatory_clauses',
                'clause_embeddings',
                'clause_events',
                'clause_health_metrics',
                'clause_playbook_results',
                'playbook_drift_snapshots',
                'playbook_update_suggestions',
                'negotiation_sessions',
                'negotiation_messages',
                'negotiation_clause_suggestions',
                'negotiation_positions',
                'risk_assessments',
                'contract_risks',
                'obligations',
                'intents',
                'jurisdictional_risks',
                'deviation_logs',
                'safeguard_recommendations',
            ]
            
            for table in tables_to_clear:
                try:
                    cursor.execute(f"DELETE FROM {table}")
                    deleted = cursor.rowcount
                    self.stdout.write(f'  [OK] Cleared {deleted} records from {table}')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  [WARN] Could not clear {table}: {str(e)}'))

        # Delete all contracts
        Contract.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'[SUCCESS] Deleted {contract_count} contracts from database'))

        # Delete uploaded files
        deleted_files = 0
        for file_path in file_paths:
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted_files += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  [WARN] Could not delete file {file_path}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'[SUCCESS] Deleted {deleted_files} files from filesystem'))

        # Optional: Clear uploads directory
        uploads_dir = 'uploads/contracts'
        if os.path.exists(uploads_dir):
            try:
                shutil.rmtree(uploads_dir)
                os.makedirs(uploads_dir, exist_ok=True)
                self.stdout.write(self.style.SUCCESS(f'[SUCCESS] Cleared uploads directory: {uploads_dir}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  [WARN] Could not clear uploads directory: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('\n[COMPLETE] All contracts and related data have been permanently deleted!'))
        self.stdout.write(self.style.SUCCESS('You can now start fresh by uploading new contracts.'))
