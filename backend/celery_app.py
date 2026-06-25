"""
Celery configuration for ContractAI

This module configures Celery for async task processing, which is essential
for handling long-running operations like:
- Document OCR processing
- Clause extraction
- RAG indexing
- Risk analysis
- Compliance checking

Usage:
    # Start worker:
    celery -A celery_app worker -l info

    # Start worker for slow tasks:
    celery -A celery_app worker -Q slow_tasks -l info --concurrency=1

    # In views:
    from celery_app import process_contract_task
    result = process_contract_task.delay(contract_id)
"""

import os
from celery import Celery
from decouple import config

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

# Create Celery app
app = Celery('contractai')

# Configure Celery using Django settings with 'CELERY' namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load tasks from all registered Django apps
app.autodiscover_tasks()

# Celery configuration
app.conf.update(
    # Redis as broker and result backend
    broker_url=config('CELERY_BROKER_URL', default='redis://localhost:6379/0'),
    result_backend=config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0'),

    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Task execution
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,  # Don't prefetch tasks
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks

    # Result backend
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,

    # Task routing
    task_routes={
        'api.tasks.process_contract': {'queue': 'slow_tasks'},
        'api.tasks.extract_clauses': {'queue': 'slow_tasks'},
        'api.tasks.generate_embeddings': {'queue': 'slow_tasks'},
        'api.tasks.analyze_risk': {'queue': 'default'},
    },

    # Task priorities
    task_default_priority=5,
    task_queue_max_priority=10,

    # Beat schedule (for periodic tasks)
    beat_schedule={
        'cleanup-old-results': {
            'task': 'api.tasks.cleanup_old_results',
            'schedule': 3600.0,  # hourly
        },
        'acl-clean-taxonomy': {
            'task': 'api.acl_tasks.clean_taxonomy_task',
            'schedule': 86400.0,  # daily — merges near-duplicate taxonomy nodes
        },
    },
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to test Celery setup"""
    print(f'Request: {self.request!r}')


# Example task definitions (you can move these to api/tasks.py)
@app.task(bind=True, name='api.tasks.process_contract')
def process_contract_task(self, contract_id: int):
    """
    Process contract asynchronously

    Args:
        contract_id: ID of the contract to process

    Returns:
        dict: Processing results
    """
    from api.models import Contract
    from api.contract_operations import ContractProcessor
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Processing contract {contract_id}")

        contract = Contract.objects.get(id=contract_id)
        processor = ContractProcessor()

        # Update status
        contract.processing_status = 'processing'
        contract.save()

        # Process contract
        result = processor.process_full_contract(contract)

        # Update status
        contract.processing_status = 'completed'
        contract.save()

        logger.info(f"✅ Contract {contract_id} processed successfully")

        return {
            'status': 'success',
            'contract_id': contract_id,
            'result': result
        }

    except Exception as e:
        logger.error(f"❌ Error processing contract {contract_id}: {str(e)}")

        # Update status
        try:
            contract = Contract.objects.get(id=contract_id)
            contract.processing_status = 'failed'
            contract.processing_error = str(e)
            contract.save()
        except:
            pass

        return {
            'status': 'error',
            'contract_id': contract_id,
            'error': str(e)
        }


@app.task(bind=True, name='api.tasks.extract_clauses')
def extract_clauses_task(self, contract_id: int):
    """
    Extract clauses from contract asynchronously

    Args:
        contract_id: ID of the contract

    Returns:
        dict: Extraction results
    """
    from api.models import Contract
    from api.clause_edit_service import ClauseEditService
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Extracting clauses for contract {contract_id}")

        contract = Contract.objects.get(id=contract_id)
        service = ClauseEditService()

        # Extract clauses
        clauses = service.extract_clauses(contract.full_text)

        # Save clauses to database
        from api.models import Clause
        created_clauses = []

        for clause_data in clauses:
            clause = Clause.objects.create(
                contract=contract,
                name=clause_data.get('name', 'Untitled'),
                original_text=clause_data.get('text', ''),
                clause_type=clause_data.get('type', 'general'),
            )
            created_clauses.append(clause.id)

        logger.info(f"✅ Extracted {len(created_clauses)} clauses for contract {contract_id}")

        return {
            'status': 'success',
            'contract_id': contract_id,
            'clauses_count': len(created_clauses),
            'clause_ids': created_clauses
        }

    except Exception as e:
        logger.error(f"❌ Error extracting clauses for contract {contract_id}: {str(e)}")

        return {
            'status': 'error',
            'contract_id': contract_id,
            'error': str(e)
        }


@app.task(bind=True, name='api.tasks.cleanup_old_results')
def cleanup_old_results(self):
    """
    Periodic task to cleanup old task results

    This runs automatically based on beat_schedule
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info("🧹 Running cleanup of old task results")

    # Cleanup logic here
    # For example, delete old processed files, clear caches, etc.

    return {'status': 'cleaned'}


if __name__ == '__main__':
    app.start()
