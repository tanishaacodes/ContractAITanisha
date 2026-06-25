"""
ETL (Extract, Transform, Load) functions for Fivetran data.
Transforms raw data from external sources into the canonical UnifiedContract model.
"""
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import logging

from .models import (
    DocuSignEnvelope,
    SalesforceContract,
    SapEKKO,
    SapEKPO,
    SapLFA1,
    UnifiedContract
)

logger = logging.getLogger(__name__)


def transform_docusign_to_unified(envelope: DocuSignEnvelope) -> UnifiedContract:
    """
    Transform a DocuSign envelope into a UnifiedContract.

    Args:
        envelope: DocuSignEnvelope instance

    Returns:
        UnifiedContract instance
    """
    logger.info(f"Transforming DocuSign envelope: {envelope.envelope_id}")

    # Extract counterparty from recipients (first signer)
    counterparty = "Unknown"
    recipients = envelope.recipients.all()
    if recipients:
        # Get first signer
        signer = recipients.filter(role_name__icontains='signer').first()
        if signer:
            counterparty = signer.name

    # Create or update unified contract
    unified, created = UnifiedContract.objects.update_or_create(
        external_id=envelope.envelope_id,
        source_system='DOCUSIGN',
        defaults={
            'contract_name': envelope.email_subject or f"DocuSign Contract {envelope.envelope_id[:8]}",
            'contract_number': envelope.envelope_id,
            'counterparty': counterparty,
            'contract_type': 'DocuSign Agreement',
            'execution_date': envelope.completed_date_time.date() if envelope.completed_date_time else None,
            'lifecycle_status': envelope.status,
            'etl_processed_at': timezone.now(),
        }
    )

    action = "Created" if created else "Updated"
    logger.info(f"{action} UnifiedContract from DocuSign: {unified.external_id}")

    return unified


def transform_salesforce_to_unified(sf_contract: SalesforceContract) -> UnifiedContract:
    """
    Transform a Salesforce contract into a UnifiedContract.

    Args:
        sf_contract: SalesforceContract instance

    Returns:
        UnifiedContract instance
    """
    logger.info(f"Transforming Salesforce contract: {sf_contract.contract_number}")

    # Extract counterparty from account
    counterparty = "Unknown"
    if sf_contract.account:
        counterparty = sf_contract.account.name

    # Calculate contract value from related opportunity if available
    contract_value = None
    if sf_contract.account:
        opportunities = sf_contract.account.opportunities.filter(
            close_date__gte=sf_contract.start_date if sf_contract.start_date else timezone.now().date()
        )
        if opportunities.exists():
            # Sum opportunity amounts
            total_amount = sum(opp.amount or Decimal('0') for opp in opportunities)
            contract_value = total_amount if total_amount > 0 else None

    # Create or update unified contract
    unified, created = UnifiedContract.objects.update_or_create(
        external_id=sf_contract.salesforce_id,
        source_system='SALESFORCE',
        defaults={
            'contract_name': sf_contract.contract_number,
            'contract_number': sf_contract.contract_number,
            'counterparty': counterparty,
            'contract_type': 'Salesforce Contract',
            'contract_value': contract_value,
            'start_date': sf_contract.start_date,
            'end_date': sf_contract.end_date,
            'lifecycle_status': sf_contract.status,
            'etl_processed_at': timezone.now(),
        }
    )

    action = "Created" if created else "Updated"
    logger.info(f"{action} UnifiedContract from Salesforce: {unified.external_id}")

    return unified


def transform_sap_to_unified(ekko: SapEKKO) -> UnifiedContract:
    """
    Transform a SAP EKKO (purchase order header) into a UnifiedContract.

    Args:
        ekko: SapEKKO instance

    Returns:
        UnifiedContract instance
    """
    logger.info(f"Transforming SAP contract: {ekko.ebeln}")

    # Get vendor information
    counterparty = ekko.lifnr or "Unknown"
    try:
        vendor = SapLFA1.objects.get(lifnr=ekko.lifnr)
        counterparty = vendor.name1 or ekko.lifnr
    except SapLFA1.DoesNotExist:
        logger.warning(f"Vendor {ekko.lifnr} not found in LFA1 table")

    # Calculate total contract value from line items
    line_items = SapEKPO.objects.filter(ebeln=ekko.ebeln)
    contract_value = sum(item.netwr or Decimal('0') for item in line_items)

    # Map SAP document type to contract type
    contract_type_map = {
        'NB': 'Purchase Order',
        'FO': 'Framework Order',
        'KN': 'Contract',
        'LPA': 'Scheduling Agreement',
    }
    contract_type = contract_type_map.get(ekko.bsart, f'SAP {ekko.bsart}')

    # Create or update unified contract
    unified, created = UnifiedContract.objects.update_or_create(
        external_id=ekko.ebeln,
        source_system='SAP',
        defaults={
            'contract_name': f"SAP PO {ekko.ebeln}",
            'contract_number': ekko.ebeln,
            'counterparty': counterparty,
            'contract_type': contract_type,
            'contract_value': contract_value if contract_value > 0 else None,
            'currency': ekko.waers,
            'start_date': ekko.kdatb,
            'end_date': ekko.kdate,
            'execution_date': ekko.bedat,
            'lifecycle_status': 'Active' if ekko.bedat else 'Draft',
            'etl_processed_at': timezone.now(),
        }
    )

    action = "Created" if created else "Updated"
    logger.info(f"{action} UnifiedContract from SAP: {unified.external_id}")

    return unified


def enrich_unified_contract(unified: UnifiedContract) -> UnifiedContract:
    """
    Enrich a unified contract with additional data and business logic.
    This is called after initial transformation.

    Args:
        unified: UnifiedContract instance

    Returns:
        Enriched UnifiedContract instance
    """
    logger.info(f"Enriching UnifiedContract: {unified.external_id}")

    # Calculate contract duration if dates available
    if unified.start_date and unified.end_date:
        duration_days = (unified.end_date - unified.start_date).days
        # You could add a duration field to the model if needed

    # Additional enrichment logic can be added here:
    # - Risk scoring
    # - Category classification
    # - Compliance checks
    # - etc.

    unified.save()
    return unified


def bulk_transform_docusign(limit: int = 100) -> dict:
    """
    Bulk transform multiple DocuSign envelopes.
    Useful for initial data migration.

    Args:
        limit: Maximum number of records to process

    Returns:
        dict with processing stats
    """
    envelopes = DocuSignEnvelope.objects.filter(
        processed=False,
        status='completed'
    )[:limit]

    stats = {
        'total': len(envelopes),
        'success': 0,
        'failed': 0,
        'errors': []
    }

    for envelope in envelopes:
        try:
            with transaction.atomic():
                transform_docusign_to_unified(envelope)
                envelope.processed = True
                envelope.save()
                stats['success'] += 1
        except Exception as e:
            logger.error(f"Failed to transform envelope {envelope.envelope_id}: {str(e)}")
            stats['failed'] += 1
            stats['errors'].append({
                'envelope_id': envelope.envelope_id,
                'error': str(e)
            })

    return stats


def bulk_transform_salesforce(limit: int = 100) -> dict:
    """
    Bulk transform multiple Salesforce contracts.

    Args:
        limit: Maximum number of records to process

    Returns:
        dict with processing stats
    """
    contracts = SalesforceContract.objects.filter(
        processed=False
    ).select_related('account')[:limit]

    stats = {
        'total': len(contracts),
        'success': 0,
        'failed': 0,
        'errors': []
    }

    for contract in contracts:
        try:
            with transaction.atomic():
                transform_salesforce_to_unified(contract)
                contract.processed = True
                contract.save()
                stats['success'] += 1
        except Exception as e:
            logger.error(f"Failed to transform contract {contract.contract_number}: {str(e)}")
            stats['failed'] += 1
            stats['errors'].append({
                'contract_number': contract.contract_number,
                'error': str(e)
            })

    return stats


def bulk_transform_sap(limit: int = 100) -> dict:
    """
    Bulk transform multiple SAP contracts.

    Args:
        limit: Maximum number of records to process

    Returns:
        dict with processing stats
    """
    ekkos = SapEKKO.objects.filter(
        processed=False
    )[:limit]

    stats = {
        'total': len(ekkos),
        'success': 0,
        'failed': 0,
        'errors': []
    }

    for ekko in ekkos:
        try:
            with transaction.atomic():
                transform_sap_to_unified(ekko)
                ekko.processed = True
                ekko.save()
                stats['success'] += 1
        except Exception as e:
            logger.error(f"Failed to transform SAP contract {ekko.ebeln}: {str(e)}")
            stats['failed'] += 1
            stats['errors'].append({
                'ebeln': ekko.ebeln,
                'error': str(e)
            })

    return stats
