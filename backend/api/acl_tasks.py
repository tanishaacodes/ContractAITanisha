"""
Celery tasks for the Advanced Clause Library.
Auto-triggered via Django post_save signal on Contract creation.
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=90)
def process_contract_acl_task(self, contract_id: str):
    """
    Background task: run the full ACL pipeline (LDA + taxonomy assignment
    + Neo4j ingestion + SIMILAR_TO edges) for one contract.

    Retries up to 3 times (90 s apart) if clauses haven't been extracted yet,
    so the signal's 5-second countdown doesn't race with clause extraction.
    """
    try:
        from core.models import Contract, Clause
        from .advanced_clause_library_service import process_contract_for_library

        contract = Contract.objects.get(id=contract_id)

        clause_count = Clause.objects.filter(
            contract=contract
        ).exclude(extracted_text='').count()

        if clause_count == 0:
            # Clauses not yet extracted — wait and retry
            logger.info(
                f"[ACL] Contract {contract_id}: no clauses yet "
                f"(attempt {self.request.retries + 1}), retrying in 90 s"
            )
            raise self.retry(countdown=90)

        result = process_contract_for_library(contract, use_qwen_naming=True)
        logger.info(
            f"[ACL] Contract {contract_id}: processed={result['processed']}, "
            f"lda_topics={result['lda_topics']}"
        )
        return result
    except Exception as exc:
        if self.request.retries < self.max_retries:
            logger.warning(f"[ACL] Task failed for contract {contract_id}: {exc}, retrying")
            raise self.retry(exc=exc)
        logger.exception(f"[ACL] Task permanently failed for contract {contract_id}: {exc}")
        raise


@shared_task
def clean_taxonomy_task():
    """Periodic task: merge near-duplicate taxonomy categories."""
    from .advanced_clause_library_service import get_taxonomy_engine
    engine = get_taxonomy_engine()
    merged = engine.clean_taxonomy()
    logger.info(f"[ACL] Taxonomy clean: merged {merged} categories")
    return {'merged': merged}
