"""
Celery tasks for processing Fivetran-synced data.
These tasks are triggered by Fivetran webhooks after successful sync.
"""
from celery import shared_task
from django.utils import timezone
from django.db import transaction
import logging

from .models import (
    DocuSignEnvelope,
    SalesforceContract,
    SalesforceAccount,
    SapEKKO,
    SapEKPO,
    SapLFA1,
    UnifiedContract
)
from .etl import (
    transform_docusign_to_unified,
    transform_salesforce_to_unified,
    transform_sap_to_unified
)
from .qdrant_sync import sync_contract_to_qdrant

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_fivetran_sync(self, schema: str, connector_id: str = None):
    """
    Main task triggered by Fivetran webhook.
    Processes newly synced data based on the schema.

    Args:
        schema: Fivetran schema name (e.g., 'docusign', 'salesforce', 'sap')
        connector_id: Optional Fivetran connector ID
    """
    try:
        logger.info(f"Processing Fivetran sync for schema: {schema}")

        if schema.lower() == 'docusign' or 'docusign' in schema.lower():
            result = process_docusign_contracts.delay()
            logger.info(f"Triggered DocuSign processing task: {result.id}")

        elif schema.lower() == 'salesforce' or 'salesforce' in schema.lower():
            result = process_salesforce_contracts.delay()
            logger.info(f"Triggered Salesforce processing task: {result.id}")

        elif schema.lower() == 'sap' or 'sap' in schema.lower():
            result = process_sap_contracts.delay()
            logger.info(f"Triggered SAP processing task: {result.id}")

        else:
            logger.warning(f"Unknown schema: {schema}. No processing triggered.")
            return {"status": "skipped", "reason": "unknown_schema"}

        return {"status": "success", "schema": schema, "connector_id": connector_id}

    except Exception as e:
        logger.error(f"Error processing Fivetran sync: {str(e)}")
        raise self.retry(exc=e, countdown=60)  # Retry after 60 seconds


@shared_task(bind=True, max_retries=3)
def process_docusign_contracts(self):
    """
    Process unprocessed DocuSign envelopes and create unified contracts.
    """
    try:
        logger.info("Starting DocuSign contract processing...")

        # Get unprocessed DocuSign envelopes with status 'completed'
        unprocessed = DocuSignEnvelope.objects.filter(
            processed=False,
            status='completed'
        ).select_related()

        processed_count = 0
        failed_count = 0

        for envelope in unprocessed:
            try:
                with transaction.atomic():
                    # Transform to unified contract
                    unified_contract = transform_docusign_to_unified(envelope)

                    # Mark as processed
                    envelope.processed = True
                    envelope.save()

                    # Trigger Qdrant sync
                    sync_contract_to_qdrant.delay(str(unified_contract.id))

                    processed_count += 1
                    logger.info(f"Processed DocuSign envelope: {envelope.envelope_id}")

            except Exception as e:
                logger.error(f"Failed to process envelope {envelope.envelope_id}: {str(e)}")
                failed_count += 1
                continue

        logger.info(f"DocuSign processing complete. Processed: {processed_count}, Failed: {failed_count}")

        return {
            "status": "success",
            "processed": processed_count,
            "failed": failed_count
        }

    except Exception as e:
        logger.error(f"Error in DocuSign processing task: {str(e)}")
        raise self.retry(exc=e, countdown=120)


@shared_task(bind=True, max_retries=3)
def process_salesforce_contracts(self):
    """
    Process unprocessed Salesforce contracts and create unified contracts.
    """
    try:
        logger.info("Starting Salesforce contract processing...")

        # Get unprocessed Salesforce contracts
        unprocessed = SalesforceContract.objects.filter(
            processed=False
        ).select_related('account')

        processed_count = 0
        failed_count = 0

        for sf_contract in unprocessed:
            try:
                with transaction.atomic():
                    # Transform to unified contract
                    unified_contract = transform_salesforce_to_unified(sf_contract)

                    # Mark as processed
                    sf_contract.processed = True
                    sf_contract.save()

                    # Trigger Qdrant sync
                    sync_contract_to_qdrant.delay(str(unified_contract.id))

                    processed_count += 1
                    logger.info(f"Processed Salesforce contract: {sf_contract.contract_number}")

            except Exception as e:
                logger.error(f"Failed to process contract {sf_contract.contract_number}: {str(e)}")
                failed_count += 1
                continue

        logger.info(f"Salesforce processing complete. Processed: {processed_count}, Failed: {failed_count}")

        return {
            "status": "success",
            "processed": processed_count,
            "failed": failed_count
        }

    except Exception as e:
        logger.error(f"Error in Salesforce processing task: {str(e)}")
        raise self.retry(exc=e, countdown=120)


@shared_task(bind=True, max_retries=3)
def process_sap_contracts(self):
    """
    Process unprocessed SAP contracts (EKKO) and create unified contracts.
    """
    try:
        logger.info("Starting SAP contract processing...")

        # Get unprocessed SAP EKKO records
        unprocessed = SapEKKO.objects.filter(
            processed=False
        ).prefetch_related('sapekpo_set')

        processed_count = 0
        failed_count = 0

        for ekko in unprocessed:
            try:
                with transaction.atomic():
                    # Transform to unified contract
                    unified_contract = transform_sap_to_unified(ekko)

                    # Mark as processed
                    ekko.processed = True
                    ekko.save()

                    # Trigger Qdrant sync
                    sync_contract_to_qdrant.delay(str(unified_contract.id))

                    processed_count += 1
                    logger.info(f"Processed SAP contract: {ekko.ebeln}")

            except Exception as e:
                logger.error(f"Failed to process SAP contract {ekko.ebeln}: {str(e)}")
                failed_count += 1
                continue

        logger.info(f"SAP processing complete. Processed: {processed_count}, Failed: {failed_count}")

        return {
            "status": "success",
            "processed": processed_count,
            "failed": failed_count
        }

    except Exception as e:
        logger.error(f"Error in SAP processing task: {str(e)}")
        raise self.retry(exc=e, countdown=120)


@shared_task
def process_all_unprocessed_contracts():
    """
    Convenience task to process all unprocessed contracts from all sources.
    Can be run manually or scheduled.
    """
    logger.info("Processing all unprocessed contracts from all sources...")

    results = {
        "docusign": process_docusign_contracts.delay().get(),
        "salesforce": process_salesforce_contracts.delay().get(),
        "sap": process_sap_contracts.delay().get(),
    }

    return results


@shared_task
def cleanup_old_raw_data(days: int = 90):
    """
    Cleanup task to archive/delete old processed raw data from Fivetran tables.
    Keeps the system performant by removing stale data.

    Args:
        days: Number of days to keep (default 90 days)
    """
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=days)

    logger.info(f"Cleaning up raw Fivetran data older than {days} days...")

    # Delete old processed DocuSign data
    docusign_deleted = DocuSignEnvelope.objects.filter(
        processed=True,
        last_synced_at__lt=cutoff_date
    ).delete()

    # Delete old processed Salesforce data
    salesforce_deleted = SalesforceContract.objects.filter(
        processed=True,
        last_synced_at__lt=cutoff_date
    ).delete()

    # Delete old processed SAP data
    sap_deleted = SapEKKO.objects.filter(
        processed=True,
        last_synced_at__lt=cutoff_date
    ).delete()

    logger.info(f"Cleanup complete. Deleted: DocuSign={docusign_deleted[0]}, "
                f"Salesforce={salesforce_deleted[0]}, SAP={sap_deleted[0]}")

    return {
        "docusign_deleted": docusign_deleted[0],
        "salesforce_deleted": salesforce_deleted[0],
        "sap_deleted": sap_deleted[0]
    }
