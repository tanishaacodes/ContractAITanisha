"""
API Views for Alfresco Integration and RAG Operations

Provides endpoints for:
- Syncing contracts from Alfresco
- RAG-based contract intelligence extraction
- Semantic search across contracts
- Q&A using RAG
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.utils import timezone
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.cache import cache
import logging
import os
import threading
import uuid
from typing import Optional
from datetime import datetime

from core.models import Contract, AlfrescoDocument, ContractIntelligence, VectorEmbedding, User
from .alfresco_service import AlfrescoExtractor
from .rag_engine import ContractRAG
from .utils import extract_text_from_file

logger = logging.getLogger(__name__)


def _classify_contract_type(text: str, filename: str) -> str:
    """
    Classify contract type based on filename and content keywords.
    Simple rule-based classification for common contract types.
    """
    text_lower = text.lower() if text else ''
    filename_lower = filename.lower() if filename else ''

    # Check filename first
    if any(keyword in filename_lower for keyword in ['nda', 'confidential', 'non-disclosure']):
        return 'Non-Disclosure Agreement (NDA)'
    elif any(keyword in filename_lower for keyword in ['service', 'msa', 'master']):
        return 'Service Agreement'
    elif any(keyword in filename_lower for keyword in ['employ', 'employment']):
        return 'Employment Agreement'
    elif any(keyword in filename_lower for keyword in ['data', 'datap', 'dpa', 'privacy']):
        return 'Data Processing Agreement'
    elif any(keyword in filename_lower for keyword in ['cyber', 'security']):
        return 'Cybersecurity Agreement'
    elif any(keyword in filename_lower for keyword in ['consult', 'consulting']):
        return 'Consulting Agreement'
    elif any(keyword in filename_lower for keyword in ['loi', 'letter', 'intent']):
        return 'Letter of Intent'

    # Check content if filename doesn't match
    if any(keyword in text_lower for keyword in ['non-disclosure', 'confidential information', 'nda']):
        return 'Non-Disclosure Agreement (NDA)'
    elif any(keyword in text_lower for keyword in ['master service', 'service agreement', 'services agreement']):
        return 'Service Agreement'
    elif any(keyword in text_lower for keyword in ['employment agreement', 'employee', 'employer']):
        return 'Employment Agreement'
    elif any(keyword in text_lower for keyword in ['data processing', 'personal data', 'gdpr']):
        return 'Data Processing Agreement'
    elif any(keyword in text_lower for keyword in ['consulting agreement', 'consultant', 'consulting services']):
        return 'Consulting Agreement'
    elif any(keyword in text_lower for keyword in ['letter of intent', 'loi']):
        return 'Letter of Intent'
    elif any(keyword in text_lower for keyword in ['software license', 'licensing agreement']):
        return 'Software License'
    elif any(keyword in text_lower for keyword in ['purchase agreement', 'sale agreement']):
        return 'Purchase Agreement'

    # Default to generic type
    return 'Contract Agreement'


def _process_contracts_async(task_id: str, raw_contracts: list, user_id: int, extract_intelligence: bool, use_openai: bool):
    """
    Process contracts in a background thread.
    Updates progress in cache as it processes each contract.
    """
    try:
        # Update status
        cache.set(f'sync_task_{task_id}', {
            'status': 'processing',
            'progress': 0,
            'total': len(raw_contracts),
            'synced': 0,
            'failed': 0,
            'current': None,
            'started_at': datetime.now().isoformat()
        }, timeout=3600)

        user = User.objects.get(id=user_id)
        rag = ContractRAG(use_openai=use_openai)

        synced_count = 0
        failed_count = 0
        results = []

        for idx, item in enumerate(raw_contracts):
            try:
                # Update progress
                cache.set(f'sync_task_{task_id}', {
                    'status': 'processing',
                    'progress': idx,
                    'total': len(raw_contracts),
                    'synced': synced_count,
                    'failed': failed_count,
                    'current': item['name'],
                    'started_at': cache.get(f'sync_task_{task_id}')['started_at']
                }, timeout=3600)

                result = _process_alfresco_contract(
                    item=item,
                    user=user,
                    rag=rag,
                    extract_intelligence=extract_intelligence
                )

                results.append(result)

                if result['status'] == 'success':
                    synced_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                logger.error(f"Error processing contract {item['name']}: {e}")
                failed_count += 1
                results.append({
                    'name': item['name'],
                    'status': 'error',
                    'error': str(e)
                })

        # Mark as completed
        cache.set(f'sync_task_{task_id}', {
            'status': 'completed',
            'progress': len(raw_contracts),
            'total': len(raw_contracts),
            'synced': synced_count,
            'failed': failed_count,
            'current': None,
            'started_at': cache.get(f'sync_task_{task_id}')['started_at'],
            'completed_at': datetime.now().isoformat(),
            'results': results
        }, timeout=3600)

    except Exception as e:
        logger.error(f"Async sync error: {e}")
        cache.set(f'sync_task_{task_id}', {
            'status': 'error',
            'error': str(e),
            'progress': 0,
            'total': len(raw_contracts),
            'synced': 0,
            'failed': 0
        }, timeout=3600)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_contracts_from_alfresco(request):
    """
    Sync contracts from Alfresco to the database.

    Workflow:
    1. Fetch documents from Alfresco
    2. Save to Contract model
    3. Extract text
    4. Ingest into vector database
    5. Extract legal intelligence using RAG

    POST /api/alfresco/sync
    Body:
    {
        "folder_id": "alfresco-folder-uuid",  // Optional, defaults to -root-
        "extract_intelligence": true,          // Optional, defaults to true
        "use_openai": false,                   // Optional, use OpenAI or Ollama
        "async": true                          // Optional, process in background
    }

    If async=true, returns immediately with task_id for progress tracking.
    Otherwise processes synchronously (old behavior, may be slow).
    """
    try:
        # Get parameters
        folder_id = request.data.get('folder_id', None)
        extract_intelligence = request.data.get('extract_intelligence', True)
        use_openai = request.data.get('use_openai', False)
        async_mode = request.data.get('async', True)  # Default to async for better UX

        # Initialize services
        extractor = AlfrescoExtractor()
        # Don't initialize RAG yet if async (saves time)

        # If no folder specified, search common locations
        raw_contracts = []
        if folder_id:
            logger.info(f"Fetching contracts from Alfresco folder: {folder_id}")
            raw_contracts = extractor.get_all_contracts(folder_id=folder_id)
        else:
            # Search multiple common folders for contracts
            logger.info("Searching for contracts in common Alfresco folders")
            # Try Shared folder (id: fdedbf0c-69e1-490f-beb1-7dc2a79e955c)
            # Note: This is a hardcoded ID from the current Alfresco instance
            # In production, you'd use the folder path or search API
            shared_folder_id = "fdedbf0c-69e1-490f-beb1-7dc2a79e955c"
            logger.info(f"Searching Shared folder: {shared_folder_id}")
            shared_contracts = extractor.get_all_contracts(folder_id=shared_folder_id)
            logger.info(f"Found {len(shared_contracts)} contracts in Shared folder")
            raw_contracts.extend(shared_contracts)

            # Also try root folder
            logger.info("Searching root folder")
            root_contracts = extractor.get_all_contracts(folder_id="-root-")
            logger.info(f"Found {len(root_contracts)} contracts in root folder")
            raw_contracts.extend(root_contracts)

            logger.info(f"Total contracts found: {len(raw_contracts)}")

        if not raw_contracts:
            return Response({
                "status": "warning",
                "message": "No contracts found in Alfresco folder",
                "count": 0
            }, status=status.HTTP_200_OK)

        # If async mode, start background processing and return immediately
        if async_mode:
            task_id = str(uuid.uuid4())

            # Initialize task status in cache
            cache.set(f'sync_task_{task_id}', {
                'status': 'started',
                'progress': 0,
                'total': len(raw_contracts),
                'synced': 0,
                'failed': 0,
                'current': None
            }, timeout=3600)

            # Start background thread
            thread = threading.Thread(
                target=_process_contracts_async,
                args=(task_id, raw_contracts, request.user.id, extract_intelligence, use_openai),
                daemon=True
            )
            thread.start()

            return Response({
                "status": "started",
                "message": f"Sync started in background. Found {len(raw_contracts)} contracts to process.",
                "task_id": task_id,
                "total_count": len(raw_contracts)
            }, status=status.HTTP_202_ACCEPTED)

        # Synchronous mode (legacy behavior)
        rag = ContractRAG(use_openai=use_openai)
        synced_count = 0
        failed_count = 0
        results = []

        for item in raw_contracts:
            try:
                result = _process_alfresco_contract(
                    item=item,
                    user=request.user,
                    rag=rag,
                    extract_intelligence=extract_intelligence
                )

                results.append(result)

                if result['status'] == 'success':
                    synced_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                logger.error(f"Error processing contract {item['name']}: {e}")
                failed_count += 1
                results.append({
                    'name': item['name'],
                    'status': 'error',
                    'error': str(e)
                })

        return Response({
            "status": "completed",
            "message": f"Sync completed. {synced_count} successful, {failed_count} failed",
            "synced_count": synced_count,
            "failed_count": failed_count,
            "total_count": len(raw_contracts),
            "results": results
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Alfresco sync error: {e}")
        return Response({
            "status": "error",
            "message": "Failed to sync contracts from Alfresco",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sync_status(request, task_id):
    """
    Get the status of an async sync task.

    GET /api/alfresco/sync/status/{task_id}

    Returns:
    {
        "status": "processing|completed|error",
        "progress": 5,
        "total": 10,
        "synced": 4,
        "failed": 1,
        "current": "contract_name.pdf",
        "started_at": "2026-01-05T12:00:00",
        "completed_at": "2026-01-05T12:05:00",  // Only when completed
        "results": [...]  // Only when completed
    }
    """
    task_data = cache.get(f'sync_task_{task_id}')

    if not task_data:
        return Response({
            "status": "not_found",
            "message": "Task not found or expired"
        }, status=status.HTTP_404_NOT_FOUND)

    return Response(task_data, status=status.HTTP_200_OK)


def _process_alfresco_contract(item: dict, user: User, rag: ContractRAG, extract_intelligence: bool = True) -> dict:
    """
    Process a single contract from Alfresco.

    Args:
        item: Alfresco contract data
        user: User who initiated the sync
        rag: RAG engine instance
        extract_intelligence: Whether to extract legal intelligence

    Returns:
        Processing result dict
    """
    try:
        alfresco_id = item['id']
        alfresco_name = item['name']
        content = item['content']
        metadata = item.get('metadata', {})

        # Check if already synced
        existing_doc = AlfrescoDocument.objects.filter(alfresco_node_id=alfresco_id).first()

        if existing_doc:
            logger.info(f"Contract {alfresco_name} already synced, updating...")
            contract = existing_doc.contract
        else:
            contract = None

        # Save file permanently to extract text and for future downloads
        # Get file extension from filename
        file_ext = os.path.splitext(alfresco_name)[1].lower()
        if not file_ext:
            file_ext = '.pdf'  # Default to PDF if no extension

        # Create permanent storage directory
        uploads_dir = os.path.join(settings.BASE_DIR, 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)

        # Generate unique filename to avoid conflicts
        import uuid
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        permanent_path = os.path.join(uploads_dir, unique_filename)

        # Write content to permanent file
        with open(permanent_path, 'wb') as f:
            f.write(content)

        # Extract text with file extension
        text_data = extract_text_from_file(permanent_path, file_ext)
        full_text = text_data.get('text', '')

        # Create or update Contract
        if not contract:
            # Classify contract type based on content
            contract_type = _classify_contract_type(full_text, alfresco_name)

            contract = Contract.objects.create(
                user=user,
                filename=unique_filename,
                original_filename=alfresco_name,
                file_type=metadata.get('content_type', 'application/pdf'),
                file_path=permanent_path,
                full_text=full_text,
                contract_type=contract_type
            )

        # Create or update Alfresco document link
        alfresco_doc, created = AlfrescoDocument.objects.update_or_create(
            alfresco_node_id=alfresco_id,
            defaults={
                'alfresco_folder_id': metadata.get('folder_id', '-root-'),
                'alfresco_name': alfresco_name,
                'alfresco_content_type': metadata.get('content_type', 'application/pdf'),
                'alfresco_properties': metadata.get('properties', {}),
                'alfresco_version': metadata.get('version', '1.0'),
                'contract': contract,
                'last_synced_at': timezone.now(),
                'sync_status': 'SYNCED'
            }
        )

        # Ingest into vector database
        ingest_result = rag.ingest_contract(
            contract_id=str(contract.id),
            text=full_text,
            metadata={
                'alfresco_id': alfresco_id,
                'filename': alfresco_name,
                'user_id': str(user.id)
            }
        )

        # Extract legal intelligence if requested
        intelligence_data = None
        if extract_intelligence and full_text:
            extraction_result = rag.extract_clauses(
                contract_id=str(contract.id),
                contract_text=full_text
            )

            if extraction_result['status'] == 'success':
                extracted = extraction_result['extracted_data']

                # Save to ContractIntelligence model
                intelligence, _ = ContractIntelligence.objects.update_or_create(
                    contract=contract,
                    defaults={
                        'parties': extracted.get('parties', 'Not specified'),
                        'termination_summary': extracted.get('termination', {}).get('summary', 'Not specified'),
                        'termination_notice_period': extracted.get('termination', {}).get('notice_period', 'Not specified'),
                        'liability_summary': extracted.get('liability', 'Not specified'),
                        'jurisdiction': extracted.get('jurisdiction', 'Not specified'),
                        'confidentiality_duration': extracted.get('confidentiality_duration', 'Not specified'),
                        'extraction_confidence': 0.85,  # You can calculate this based on LLM response
                        'vector_db_chunks': ingest_result.get('chunks_created', 0),
                        'relevant_chunks_used': extraction_result.get('chunks_used', 0),
                        'raw_extraction_data': extracted
                    }
                )

                intelligence_data = {
                    'parties': intelligence.parties,
                    'jurisdiction': intelligence.jurisdiction,
                    'termination': intelligence.termination_summary
                }

        # Note: File is now permanently stored in uploads directory for future downloads
        # No cleanup needed

        return {
            'name': alfresco_name,
            'contract_id': str(contract.id),
            'alfresco_id': alfresco_id,
            'status': 'success',
            'chunks_created': ingest_result.get('chunks_created', 0),
            'intelligence_extracted': intelligence_data is not None,
            'intelligence': intelligence_data
        }

    except Exception as e:
        logger.error(f"Error processing Alfresco contract: {e}")
        return {
            'name': item.get('name', 'Unknown'),
            'status': 'error',
            'error': str(e)
        }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def query_contracts(request):
    """
    RAG-based semantic search and Q&A across all contracts.

    GET /api/alfresco/query?q=What+are+the+termination+clauses&use_openai=false

    Query Parameters:
    - q: User's natural language query (required)
    - use_openai: Use OpenAI or Ollama (default: false)
    - k: Number of results (default: 5)
    """
    try:
        query = request.query_params.get('q')
        if not query:
            return Response({
                "status": "error",
                "message": "Query parameter 'q' is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        use_openai = request.query_params.get('use_openai', 'false').lower() == 'true'
        k = int(request.query_params.get('k', 5))

        # Initialize RAG
        rag = ContractRAG(use_openai=use_openai)

        # Perform semantic search
        search_results = rag.semantic_search(query=query, k=k)

        # Generate answer using RAG
        answer = rag.query_contracts(user_query=query)

        return Response({
            "status": "success",
            "query": query,
            "answer": answer,
            "relevant_chunks": [
                {
                    'text': r['text'][:200] + '...',
                    'contract_id': r['metadata'].get('contract_id'),
                    'contract_name': r['metadata'].get('filename', 'Unknown Contract'),
                    'chunk_index': r['metadata'].get('chunk_index'),
                    'relevance_score': 1 - r['distance']
                }
                for r in search_results
            ],
            "total_results": len(search_results)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Query error: {e}")
        return Response({
            "status": "error",
            "message": "Failed to process query",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def contract_intelligence(request, contract_id):
    """
    Get extracted legal intelligence for a specific contract.

    GET /api/alfresco/contracts/{contract_id}/intelligence
    """
    try:
        contract = Contract.objects.get(id=contract_id, user=request.user)

        # Get intelligence if exists
        try:
            intelligence = ContractIntelligence.objects.get(contract=contract)

            return Response({
                "status": "success",
                "contract_id": str(contract.id),
                "contract_name": contract.original_filename,
                "intelligence": {
                    "parties": intelligence.parties,
                    "termination_summary": intelligence.termination_summary,
                    "termination_notice_period": intelligence.termination_notice_period,
                    "liability_summary": intelligence.liability_summary,
                    "jurisdiction": intelligence.jurisdiction,
                    "confidentiality_duration": intelligence.confidentiality_duration,
                    "extraction_confidence": intelligence.extraction_confidence,
                    "extracted_at": intelligence.extracted_at.isoformat(),
                    "raw_data": intelligence.raw_extraction_data
                }
            }, status=status.HTTP_200_OK)

        except ContractIntelligence.DoesNotExist:
            return Response({
                "status": "not_found",
                "message": "Intelligence not extracted for this contract yet"
            }, status=status.HTTP_404_NOT_FOUND)

    except Contract.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Contract not found"
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching intelligence: {e}")
        return Response({
            "status": "error",
            "message": "Failed to fetch contract intelligence",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def extract_contract_intelligence(request, contract_id):
    """
    Manually trigger intelligence extraction for a specific contract.

    POST /api/alfresco/contracts/{contract_id}/extract
    Body:
    {
        "use_openai": false  // Optional
    }
    """
    try:
        contract = Contract.objects.get(id=contract_id, user=request.user)

        if not contract.full_text:
            return Response({
                "status": "error",
                "message": "Contract has no text content"
            }, status=status.HTTP_400_BAD_REQUEST)

        use_openai = request.data.get('use_openai', False)
        rag = ContractRAG(use_openai=use_openai)

        # Check if contract is in vector database, if not, ingest it first
        try:
            from core.models import VectorEmbedding
            embeddings_exist = VectorEmbedding.objects.filter(contract=contract).exists()

            if not embeddings_exist:
                logger.info(f"Contract {contract_id} not in vector DB, ingesting first...")
                ingest_result = rag.ingest_contract(
                    contract_id=str(contract.id),
                    text=contract.full_text,
                    metadata={
                        'filename': contract.original_filename,
                        'user_id': str(contract.user.id)
                    }
                )
                logger.info(f"Ingestion complete: {ingest_result.get('chunks_created', 0)} chunks created")
        except Exception as e:
            logger.warning(f"Could not check/ingest embeddings: {e}")

        # Extract intelligence
        extraction_result = rag.extract_clauses(
            contract_id=str(contract.id),
            contract_text=contract.full_text
        )

        if extraction_result['status'] != 'success':
            return Response({
                "status": "error",
                "message": "Intelligence extraction failed",
                "details": extraction_result
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        extracted = extraction_result['extracted_data']

        # Save to database
        intelligence, created = ContractIntelligence.objects.update_or_create(
            contract=contract,
            defaults={
                'parties': extracted.get('parties', 'Not specified'),
                'termination_summary': extracted.get('termination', {}).get('summary', 'Not specified'),
                'termination_notice_period': extracted.get('termination', {}).get('notice_period', 'Not specified'),
                'liability_summary': extracted.get('liability', 'Not specified'),
                'jurisdiction': extracted.get('jurisdiction', 'Not specified'),
                'confidentiality_duration': extracted.get('confidentiality_duration', 'Not specified'),
                'extraction_confidence': 0.85,
                'relevant_chunks_used': extraction_result.get('chunks_used', 0),
                'raw_extraction_data': extracted
            }
        )

        return Response({
            "status": "success",
            "message": "Intelligence extracted successfully",
            "contract_id": str(contract.id),
            "intelligence": {
                "parties": intelligence.parties,
                "termination_summary": intelligence.termination_summary,
                "jurisdiction": intelligence.jurisdiction,
                "liability_summary": intelligence.liability_summary
            }
        }, status=status.HTTP_200_OK)

    except Contract.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Contract not found"
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error extracting intelligence: {e}\n{error_trace}")
        return Response({
            "status": "error",
            "message": "Failed to extract intelligence",
            "error": str(e),
            "details": error_trace if settings.DEBUG else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def alfresco_health(request):
    """
    Check Alfresco connection health.
    No authentication required for health checks.

    GET /api/alfresco/health
    """
    try:
        extractor = AlfrescoExtractor()
        health = extractor.health_check()

        return Response({
            "status": "success",
            "alfresco": health
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return Response({
            "status": "error",
            "message": "Health check failed",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
