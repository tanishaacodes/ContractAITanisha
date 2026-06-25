"""
Qdrant vector database synchronization for Fivetran-synced contracts.
Automatically generates embeddings and stores them in Qdrant.
"""
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import logging
import uuid

from .models import UnifiedContract

logger = logging.getLogger(__name__)

# Initialize Qdrant client
try:
    qdrant_client = QdrantClient(
        url=getattr(settings, 'QDRANT_URL', 'http://localhost:6333'),
        timeout=60
    )
    logger.info("Qdrant client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Qdrant client: {str(e)}")
    qdrant_client = None

# Initialize embedding model
try:
    embedding_model = SentenceTransformer(
        getattr(settings, 'CONTRACTS_BERT_MODEL', 'sentence-transformers/all-MiniLM-L6-v2', device='cpu')
    )
    EMBEDDING_DIM = embedding_model.get_sentence_embedding_dimension()
    logger.info(f"Embedding model loaded. Dimension: {EMBEDDING_DIM}")
except Exception as e:
    logger.error(f"Failed to load embedding model: {str(e)}")
    embedding_model = None
    EMBEDDING_DIM = 384  # Default for all-MiniLM-L6-v2

# Qdrant collection name
COLLECTION_NAME = "unified_contracts"


def ensure_collection_exists():
    """
    Ensure the Qdrant collection for unified contracts exists.
    Creates it if it doesn't exist.
    """
    if not qdrant_client:
        logger.error("Qdrant client not initialized")
        return False

    try:
        collections = qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]

        if COLLECTION_NAME not in collection_names:
            logger.info(f"Creating Qdrant collection: {COLLECTION_NAME}")
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Collection {COLLECTION_NAME} created successfully")
        else:
            logger.info(f"Collection {COLLECTION_NAME} already exists")

        return True

    except Exception as e:
        logger.error(f"Failed to ensure collection exists: {str(e)}")
        return False


def generate_embedding(text: str) -> list:
    """
    Generate embedding vector for given text.

    Args:
        text: Input text to embed

    Returns:
        List of floats representing the embedding vector
    """
    if not embedding_model:
        logger.error("Embedding model not initialized")
        return [0.0] * EMBEDDING_DIM  # Return zero vector

    try:
        embedding = embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Failed to generate embedding: {str(e)}")
        return [0.0] * EMBEDDING_DIM


def build_contract_text(contract: UnifiedContract) -> str:
    """
    Build a comprehensive text representation of the contract for embedding.

    Args:
        contract: UnifiedContract instance

    Returns:
        str: Formatted contract text
    """
    text_parts = []

    # Basic info
    if contract.contract_name:
        text_parts.append(f"Contract: {contract.contract_name}")

    if contract.contract_number:
        text_parts.append(f"Number: {contract.contract_number}")

    # Parties
    text_parts.append(f"Counterparty: {contract.counterparty}")

    # Type and status
    if contract.contract_type:
        text_parts.append(f"Type: {contract.contract_type}")

    text_parts.append(f"Status: {contract.lifecycle_status}")

    # Financial
    if contract.contract_value:
        currency = contract.currency or 'USD'
        text_parts.append(f"Value: {currency} {contract.contract_value:,.2f}")

    # Dates
    if contract.start_date:
        text_parts.append(f"Start Date: {contract.start_date.strftime('%Y-%m-%d')}")

    if contract.end_date:
        text_parts.append(f"End Date: {contract.end_date.strftime('%Y-%m-%d')}")

    if contract.execution_date:
        text_parts.append(f"Execution Date: {contract.execution_date.strftime('%Y-%m-%d')}")

    # Source system
    text_parts.append(f"Source: {contract.source_system}")

    return " | ".join(text_parts)


@shared_task(bind=True, max_retries=3)
def sync_contract_to_qdrant(self, contract_id: str):
    """
    Celery task to sync a single contract to Qdrant.

    Args:
        contract_id: UUID of the UnifiedContract
    """
    try:
        logger.info(f"Syncing contract {contract_id} to Qdrant...")

        # Get contract
        contract = UnifiedContract.objects.get(id=contract_id)

        # Check if already synced
        if contract.qdrant_synced:
            logger.info(f"Contract {contract_id} already synced to Qdrant")
            return {"status": "already_synced", "contract_id": contract_id}

        # Ensure collection exists
        if not ensure_collection_exists():
            raise Exception("Failed to ensure Qdrant collection exists")

        # Build contract text
        contract_text = build_contract_text(contract)

        # Generate embedding
        embedding = generate_embedding(contract_text)

        # Prepare metadata
        metadata = {
            "contract_id": str(contract.id),
            "external_id": contract.external_id,
            "source_system": contract.source_system,
            "contract_name": contract.contract_name or "",
            "contract_number": contract.contract_number or "",
            "counterparty": contract.counterparty,
            "contract_type": contract.contract_type or "",
            "contract_value": float(contract.contract_value) if contract.contract_value else None,
            "currency": contract.currency or "",
            "start_date": contract.start_date.isoformat() if contract.start_date else None,
            "end_date": contract.end_date.isoformat() if contract.end_date else None,
            "lifecycle_status": contract.lifecycle_status,
            "synced_at": timezone.now().isoformat(),
        }

        # Upsert to Qdrant
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=str(contract.id),
                    vector=embedding,
                    payload=metadata
                )
            ]
        )

        # Update contract
        contract.qdrant_synced = True
        contract.qdrant_synced_at = timezone.now()
        contract.save()

        logger.info(f"Successfully synced contract {contract_id} to Qdrant")

        return {
            "status": "success",
            "contract_id": contract_id,
            "external_id": contract.external_id,
            "source_system": contract.source_system
        }

    except UnifiedContract.DoesNotExist:
        logger.error(f"Contract {contract_id} not found")
        return {"status": "error", "message": "Contract not found"}

    except Exception as e:
        logger.error(f"Failed to sync contract {contract_id} to Qdrant: {str(e)}")
        raise self.retry(exc=e, countdown=60)


@shared_task
def bulk_sync_to_qdrant(limit: int = 100):
    """
    Bulk sync unsynced contracts to Qdrant.
    Useful for initial migration or catching up.

    Args:
        limit: Maximum number of contracts to sync
    """
    logger.info(f"Starting bulk sync to Qdrant (limit: {limit})...")

    # Get unsynced contracts
    unsynced = UnifiedContract.objects.filter(
        qdrant_synced=False
    ).order_by('created_at')[:limit]

    stats = {
        'total': len(unsynced),
        'success': 0,
        'failed': 0,
        'errors': []
    }

    for contract in unsynced:
        try:
            result = sync_contract_to_qdrant.delay(str(contract.id)).get()
            if result.get('status') == 'success':
                stats['success'] += 1
            else:
                stats['failed'] += 1
                stats['errors'].append({
                    'contract_id': str(contract.id),
                    'error': result.get('message', 'Unknown error')
                })
        except Exception as e:
            logger.error(f"Failed to sync contract {contract.id}: {str(e)}")
            stats['failed'] += 1
            stats['errors'].append({
                'contract_id': str(contract.id),
                'error': str(e)
            })

    logger.info(f"Bulk sync complete. Success: {stats['success']}, Failed: {stats['failed']}")

    return stats


@shared_task
def resync_all_contracts():
    """
    Force resync all contracts to Qdrant.
    This will update embeddings for all contracts regardless of sync status.
    """
    logger.info("Force resyncing all contracts to Qdrant...")

    all_contracts = UnifiedContract.objects.all()

    stats = {
        'total': all_contracts.count(),
        'success': 0,
        'failed': 0
    }

    for contract in all_contracts:
        # Mark as unsynced
        contract.qdrant_synced = False
        contract.save()

        try:
            sync_contract_to_qdrant.delay(str(contract.id)).get()
            stats['success'] += 1
        except Exception as e:
            logger.error(f"Failed to resync contract {contract.id}: {str(e)}")
            stats['failed'] += 1

    logger.info(f"Resync complete. Success: {stats['success']}, Failed: {stats['failed']}")

    return stats


def search_contracts(query: str, limit: int = 10) -> list:
    """
    Search for contracts in Qdrant using semantic similarity.

    Args:
        query: Search query text
        limit: Maximum number of results

    Returns:
        List of search results with contract metadata
    """
    if not qdrant_client or not embedding_model:
        logger.error("Qdrant client or embedding model not initialized")
        return []

    try:
        # Generate query embedding
        query_embedding = generate_embedding(query)

        # Search in Qdrant
        results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=limit,
            with_payload=True
        )

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'contract_id': result.payload.get('contract_id'),
                'external_id': result.payload.get('external_id'),
                'contract_name': result.payload.get('contract_name'),
                'counterparty': result.payload.get('counterparty'),
                'source_system': result.payload.get('source_system'),
                'score': result.score,
                'metadata': result.payload
            })

        return formatted_results

    except Exception as e:
        logger.error(f"Failed to search contracts: {str(e)}")
        return []
