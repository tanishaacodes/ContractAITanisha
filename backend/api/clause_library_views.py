"""
Clause Library API Views
Provides endpoints for clause clustering, naming, and library management
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
import logging
import time

from core.models import Contract, Clause
from .clause_clustering import get_clusterer
from .clause_naming import get_clause_namer
from .qdrant_service import get_qdrant_service
from .clause_audit_storage import get_audit_storage
from .hybrid_clause_search import get_hybrid_searcher

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_contract_clause_library(request, contract_id):
    """
    Process contract to build clause library with clustering and LLM naming

    Flow:
    1. Extract all clauses from contract
    2. Generate BERT embeddings
    3. Cluster clauses using KMeans
    4. Generate semantic names for clusters using LLM
    5. Store embeddings in Qdrant
    6. Save audit trail to text files
    7. Update database with cluster information
    """
    start_time = time.time()

    try:
        # Get contract
        try:
            contract = Contract.objects.get(id=contract_id, user=request.user)
        except Contract.DoesNotExist:
            return Response(
                {'error': 'Contract not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get all clauses for this contract
        clauses = Clause.objects.filter(contract=contract)

        if not clauses.exists():
            return Response(
                {'error': 'No clauses found. Please extract clauses first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(f"Processing {clauses.count()} clauses for contract {contract_id}")

        # Prepare clause texts
        clause_texts = []
        clause_objs = []

        for clause in clauses:
            # Use extracted text or context sentences
            text = clause.extracted_text or clause.context_sentences or clause.clause_name
            if text and len(text.strip()) > 10:  # Minimum text length
                clause_texts.append(text)
                clause_objs.append(clause)

        if len(clause_texts) < 2:
            return Response(
                {'error': 'Not enough valid clause texts for clustering'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Step 1: Cluster clauses
        logger.info("Step 1: Clustering clauses...")
        clusterer = get_clusterer()
        cluster_method = request.data.get('cluster_method', 'kmeans')  # 'kmeans' or 'lda'

        if cluster_method == 'lda':
            lda_result = clusterer.cluster_clauses_lda(
                clause_texts,
                n_topics=request.data.get('n_clusters'),
            )
            labels = lda_result['labels']
            n_clusters = lda_result['n_clusters']
            # Build clause_groups from LDA labels
            clause_groups_raw = {}
            for idx, label in enumerate(labels):
                label = int(label)
                clause_groups_raw.setdefault(label, []).append(clause_texts[idx])
            # Auto-name clusters using top LDA words
            cluster_names = {}
            for label, words in lda_result['topic_words'].items():
                cluster_names[label] = ' / '.join(words[:3]).title()
            # Generate embeddings for downstream Qdrant storage
            embeddings = clusterer.embed_clauses(clause_texts)
            clustering_result = {
                'embeddings': embeddings,
                'labels': labels,
                'n_clusters': n_clusters,
            }
        else:
            clustering_result = clusterer.cluster_clauses(
                clause_texts,
                n_clusters=request.data.get('n_clusters')
            )
            embeddings = clustering_result['embeddings']
            labels = clustering_result['labels']
            n_clusters = clustering_result['n_clusters']

        # Step 2: Group clauses by cluster
        clause_groups = {}
        for idx, label in enumerate(labels):
            lbl = int(label)
            if lbl not in clause_groups:
                clause_groups[lbl] = []
            clause_groups[lbl].append(clause_texts[idx])

        # Step 3: Generate semantic names for clusters using LLM (skip if LDA already named)
        if cluster_method != 'lda':
            logger.info("Step 2: Generating semantic names for clusters...")
            namer = get_clause_namer()
            cluster_names = namer.batch_name_clause_groups(clause_groups)

        # Step 4: Store embeddings in Qdrant
        logger.info("Step 3: Storing embeddings in Qdrant...")
        qdrant = get_qdrant_service()

        if qdrant.client:
            # Prepare batch data for Qdrant
            qdrant_data = []
            for idx, clause_obj in enumerate(clause_objs):
                label = int(labels[idx])

                qdrant_data.append({
                    'clause_id': clause_obj.id,
                    'contract_id': contract_id,
                    'clause_text': clause_texts[idx],
                    'clause_name': clause_obj.clause_name,
                    'embedding': embeddings[idx],
                    'metadata': {
                        'cluster_label': label,
                        'cluster_name': cluster_names.get(label),
                        'confidence': float(clause_obj.confidence) if clause_obj.confidence else 0.0,
                    }
                })

            # Store in batch
            point_ids = qdrant.store_clause_embeddings_batch(qdrant_data)
        else:
            point_ids = [None] * len(clause_objs)
            logger.warning("Qdrant not available, skipping vector storage")

        # Step 5: Update database with clustering results
        logger.info("Step 4: Updating database...")

        with transaction.atomic():
            for idx, clause_obj in enumerate(clause_objs):
                label = int(labels[idx])

                # Clause library fields (clustering only)
                clause_obj.clause_type = cluster_names.get(label, f"Category {label}")
                clause_obj.clause_label = f"{cluster_names.get(label, 'Category')}_{label}"
                clause_obj.cluster_id = label

                if point_ids[idx]:
                    clause_obj.embedding_id = point_ids[idx]

                clause_obj.save()

        # Step 8: Save audit trail to text files
        logger.info("Step 7: Saving audit trail...")
        audit_storage = get_audit_storage()

        # Prepare clauses for audit file
        audit_clauses = []
        for idx, clause_obj in enumerate(clause_objs):
            label = int(labels[idx])

            audit_clauses.append({
                'name': clause_obj.clause_name,
                'type': cluster_names.get(label, f"Category {label}"),
                'cluster_label': label,
                'confidence': float(clause_obj.confidence) if clause_obj.confidence else 0.0,
                'text': clause_texts[idx]
            })

        # Save clauses file
        clauses_file = audit_storage.save_clauses_to_file(
            contract_id,
            audit_clauses,
            metadata={
                'contract_name': contract.original_filename,
                'total_clauses': len(audit_clauses),
                'clusters': n_clusters,
                'processing_time': f"{time.time() - start_time:.2f}s"
            }
        )

        # Save organized library file
        library_file = audit_storage.save_clause_library(
            contract_id,
            clause_groups,
            cluster_names
        )

        # Save JSON backup
        json_file = audit_storage.save_json_backup(
            contract_id,
            {
                'contract_id': str(contract_id),
                'contract_name': contract.original_filename,
                'clusters': n_clusters,
                'cluster_names': cluster_names,
                'clause_groups': {str(k): v for k, v in clause_groups.items()},
                'total_clauses': len(clause_texts),
                'processing_timestamp': time.time(),
            }
        )

        # Calculate processing time
        processing_time = time.time() - start_time

        logger.info(f"Clause library processing completed in {processing_time:.2f}s")

        return Response({
            'message': 'Clause library processed successfully',
            'data': {
                'contract_id': str(contract_id),
                'total_clauses': len(clause_texts),
                'clusters': n_clusters,
                'cluster_names': cluster_names,
                'cluster_method': cluster_method,
                'processing_time': processing_time,
                'audit_files': {
                    'clauses_file': clauses_file,
                    'library_file': library_file,
                    'json_backup': json_file,
                },
                'qdrant_storage': qdrant.client is not None,
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Failed to process clause library: {e}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_clause_library(request, contract_id):
    """
    Get organized clause library for a contract
    """
    try:
        # Get contract
        try:
            contract = Contract.objects.get(id=contract_id, user=request.user)
        except Contract.DoesNotExist:
            return Response(
                {'error': 'Contract not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get all clauses with cluster information
        clauses = Clause.objects.filter(contract=contract).order_by('clause_label', '-confidence')

        if not clauses.exists():
            return Response(
                {'error': 'No clauses found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Organize by clause type
        library = {}

        for clause in clauses:
            clause_type = clause.clause_type or "Uncategorized"

            if clause_type not in library:
                library[clause_type] = []

            library[clause_type].append({
                'id': str(clause.id),
                'clause_name': clause.clause_name,
                'clause_type': clause.clause_type,
                'clause_label': clause.clause_label,
                'found': clause.found,
                'confidence': float(clause.confidence) if clause.confidence else 0.0,
                'match_count': clause.match_count,
                'extracted_text': clause.extracted_text[:200] + '...' if clause.extracted_text and len(clause.extracted_text) > 200 else clause.extracted_text,
                'has_embedding': bool(clause.embedding_id),
                # Enhanced fields from PDF requirements
                'sentence_type': clause.sentence_type,
                'party': clause.party,
                'cluster_id': clause.cluster_id,
                'risk_score': float(clause.risk_score) if clause.risk_score else 0.0,
                'risk_level': clause.risk_level,
                'financial_impact': float(clause.financial_impact) if clause.financial_impact else 0.0,
                'keywords': clause.keywords if clause.keywords else {},
            })

        return Response({
            'contract_id': str(contract_id),
            'contract_name': contract.original_filename,
            'library': library,
            'categories': list(library.keys()),
            'total_clauses': clauses.count(),
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Failed to get clause library: {e}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_full_clause_text(request, clause_id):
    """
    Get full text of a specific clause (not truncated)
    """
    import json as _json

    try:
        # Get clause with ownership check
        try:
            clause = Clause.objects.get(id=clause_id, contract__user=request.user)
        except Clause.DoesNotExist:
            return Response(
                {'error': 'Clause not found or you do not have permission to access it'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Find the section in the contract whose heading contains the clause name.
        # Approach:
        #   1. Find all lines that look like section headings (ARTICLE X, "9. TERMINATION", etc.)
        #   2. Pick the heading line whose text contains the clause name
        #   3. Extract from that heading to the next heading
        import re as _re
        extracted_text = clause.extracted_text or ''
        try:
            full_text = clause.contract.full_text or ''
            clause_name = (clause.clause_name or '').strip()
            if full_text and clause_name:
                clause_lower = clause_name.lower()

                # Find every line that is a top-level section heading.
                # We match:
                #   "ARTICLE 11 - TERMINATION"   (keyword + number)
                #   "11. TERMINATION"             (number + ALL CAPS title, no lowercase)
                # We deliberately exclude sub-clauses like "11.1 The party shall..."
                # by requiring the title part to be ALL CAPS (no lowercase letters).
                heading_pat = _re.compile(
                    r'^[ \t]*(?:'
                    r'(?:ARTICLE|Section|Clause|SECTION|CLAUSE)\s+\d+\b'     # ARTICLE 11
                    r'|\d+\.\s+[A-Z][A-Z0-9 &/()\-]{2,}(?:\n|$)'            # 11. TERMINATION (all caps)
                    r')',
                    _re.MULTILINE
                )

                # Get all heading positions
                headings = [(m.start(), m.end()) for m in heading_pat.finditer(full_text)]

                # Find the heading whose full line contains the clause name
                best_start = None
                for (hstart, hend) in headings:
                    line_end = full_text.find('\n', hstart)
                    line_end = line_end if line_end != -1 else len(full_text)
                    line = full_text[hstart:line_end].lower()
                    if clause_lower in line:
                        best_start = hstart
                        break  # take the first match

                if best_start is not None:
                    # Find the next heading after best_start
                    section_end = len(full_text)
                    for (hstart, hend) in headings:
                        if hstart > best_start + 5:
                            section_end = hstart
                            break
                    extracted_text = full_text[best_start:section_end].strip()
        except Exception as e:
            logger.warning(f"Could not extract clause text: {e}")

        return Response({
            'id': str(clause.id),
            'clause_name': clause.clause_name,
            'clause_type': clause.clause_type,
            'extracted_text': extracted_text,
            'sentence_type': clause.sentence_type,
            'party': clause.party,
            'cluster_id': clause.cluster_id,
            'risk_score': float(clause.risk_score) if clause.risk_score else 0.0,
            'risk_level': clause.risk_level,
            'financial_impact': float(clause.financial_impact) if clause.financial_impact else 0.0,
            'keywords': clause.keywords if clause.keywords else {},
            'confidence': float(clause.confidence) if clause.confidence else 0.0,
            'match_count': clause.match_count,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Failed to get full clause text: {e}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_similar_clauses(request):
    """
    Search for similar clauses using semantic search (optimized)
    """
    start_time = time.time()

    try:
        query_text = request.data.get('query')
        contract_id = request.data.get('contract_id')
        clause_type = request.data.get('clause_type')
        limit = request.data.get('limit', 10)

        if not query_text:
            return Response(
                {'error': 'Query text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check Qdrant availability first (fast check)
        qdrant = get_qdrant_service()
        if not qdrant.client:
            return Response(
                {
                    'error': 'Qdrant vector database is not running',
                    'message': 'Semantic search requires Qdrant. Start it with: docker run -p 6333:6333 qdrant/qdrant',
                    'fallback': 'You can still use the clause library without semantic search',
                    'results': []
                },
                status=status.HTTP_200_OK
            )

        # Generate embedding for query (optimized for single query)
        embed_start = time.time()
        clusterer = get_clusterer()
        query_embedding = clusterer.embed_clauses([query_text], batch_size=1)[0]
        embed_time = time.time() - embed_start
        logger.info(f"Query embedding generated in {embed_time:.3f}s")

        # Search in Qdrant (fast vector search)
        search_start = time.time()
        results = qdrant.search_similar_clauses(
            query_embedding=query_embedding,
            limit=limit,
            contract_id=contract_id,
            clause_type=clause_type
        )
        search_time = time.time() - search_start
        logger.info(f"Vector search completed in {search_time:.3f}s")

        total_time = time.time() - start_time
        logger.info(f"Total search time: {total_time:.3f}s")

        return Response({
            'query': query_text,
            'results': results,
            'total_results': len(results),
            'timing': {
                'embedding_ms': round(embed_time * 1000, 2),
                'search_ms': round(search_time * 1000, 2),
                'total_ms': round(total_time * 1000, 2),
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Failed to search similar clauses: {e}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def hybrid_search_clauses(request):
    """
    Hybrid search combining BM25 + BERT + GraphRAG + LLM re-ranking.

    Request body:
        - query (str): Search query
        - limit (int, optional): Max results (default: 10)
        - mode (str, optional): 'bm25', 'bert', or 'hybrid' (default: 'hybrid')
        - contract_id (str, optional): Filter by contract
    """
    start_time = time.time()

    try:
        query_text = request.data.get('query')
        limit = request.data.get('limit', 10)
        mode = request.data.get('mode', 'hybrid')
        contract_id = request.data.get('contract_id')

        if not query_text:
            return Response(
                {'error': 'Query text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if mode not in ['bm25', 'bert', 'hybrid']:
            return Response(
                {'error': 'Invalid mode. Must be one of: bm25, bert, hybrid'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get hybrid searcher
        searcher = get_hybrid_searcher()

        # Perform search
        results = searcher.search(
            query=query_text,
            limit=limit,
            mode=mode,
            contract_id=contract_id
        )

        # Enrich results with database info
        enriched_results = []
        for result in results:
            try:
                clause = Clause.objects.get(id=result['clause_id'])
                enriched_results.append({
                    'clause_id': result['clause_id'],
                    'clause_name': clause.clause_name,
                    'clause_type': clause.clause_type,
                    'clause_text': result.get('text', clause.extracted_text)[:200],
                    'contract_id': str(clause.contract_id),
                    'contract_name': clause.contract.original_filename if clause.contract else None,
                    # Scores
                    'bm25_score': result.get('bm25_score', 0),
                    'bert_score': result.get('bert_score', 0),
                    'final_score': result.get('final_score', 0),
                    # Enhanced fields
                    'sentence_type': clause.sentence_type,
                    'party': clause.party,
                    'risk_level': clause.risk_level,
                    'financial_impact': float(clause.financial_impact) if clause.financial_impact else 0,
                    # Source
                    'source': result.get('source', mode.upper()),
                })
            except Clause.DoesNotExist:
                continue

        total_time = time.time() - start_time

        return Response({
            'query': query_text,
            'mode': mode,
            'results': enriched_results,
            'total_results': len(enriched_results),
            'timing': {
                'total_ms': round(total_time * 1000, 2),
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Hybrid search failed: {e}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_qdrant_stats(request):
    """
    Get Qdrant collection statistics
    """
    try:
        qdrant = get_qdrant_service()

        if not qdrant.client:
            return Response(
                {'error': 'Qdrant not available'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        stats = qdrant.get_collection_stats()

        return Response(stats, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Failed to get Qdrant stats: {e}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
