"""
Clause Library Service
======================
Main orchestration service for clause extraction, classification, and library management.

This service integrates all NLP components to provide end-to-end clause processing:
1. Extract clauses from contract text
2. Generate BERT embeddings
3. Cluster similar clauses
4. Generate clause names using Qwen LLM
5. Store in MySQL + Qdrant vector DB
"""

import sys
import os
import logging
from typing import List, Dict, Tuple, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp.clause_extractor import split_into_clauses, extract_clause_with_metadata, identify_clause_type_by_keywords
from nlp.embedding import ClauseEmbedder, get_embedder
from nlp.clustering import ClauseClusterer, cluster_clauses, group_clauses_by_cluster
from llm.qwen import QwenClient, get_qwen_client
from vector.qdrant_store import QdrantStore, get_qdrant_store
from core.models import Contract, Clause

logger = logging.getLogger(__name__)


class ClauseLibraryService:
    """
    Main service for processing contracts and building clause library.
    """

    def __init__(
        self,
        embedder: Optional[ClauseEmbedder] = None,
        llm_client: Optional[QwenClient] = None,
        vector_store: Optional[QdrantStore] = None
    ):
        """
        Initialize the clause library service.

        Args:
            embedder (Optional[ClauseEmbedder]): Custom embedder (uses default if None)
            llm_client (Optional[QwenClient]): Custom LLM client (uses default if None)
            vector_store (Optional[QdrantStore]): Custom vector store (uses default if None)
        """
        self.embedder = embedder or get_embedder()
        self.llm_client = llm_client or get_qwen_client()
        self.vector_store = vector_store or get_qdrant_store()

        logger.info("ClauseLibraryService initialized")

    def process_contract(
        self,
        contract: Contract,
        n_clusters: int = 8,
        save_to_db: bool = True
    ) -> Dict:
        """
        Complete end-to-end processing of a contract.

        Pipeline:
        1. Extract clauses from contract text
        2. Generate BERT embeddings
        3. Cluster clauses by similarity
        4. Generate clause type names using LLM
        5. Store in MySQL and Qdrant

        Args:
            contract (Contract): The contract model instance
            n_clusters (int): Number of clause clusters to create (default: 8)
            save_to_db (bool): Whether to save results to database (default: True)

        Returns:
            Dict: Processing results with statistics and created clauses

        Example:
            >>> service = ClauseLibraryService()
            >>> contract = Contract.objects.get(id='...')
            >>> result = service.process_contract(contract)
            >>> result['total_clauses']
            42
        """
        logger.info(f"Processing contract: {contract.id} - {contract.original_filename}")

        try:
            # Step 1: Extract clauses from contract text
            logger.info("Step 1: Extracting clauses...")
            clauses_text = self._extract_clauses(contract.full_text)
            logger.info(f"Extracted {len(clauses_text)} clauses")

            if not clauses_text:
                logger.warning("No clauses extracted from contract")
                return {
                    'success': False,
                    'message': 'No clauses could be extracted from contract',
                    'total_clauses': 0
                }

            # Step 2: Generate embeddings
            logger.info("Step 2: Generating BERT embeddings...")
            embeddings = self.embedder.embed_clauses(clauses_text, show_progress=True)
            logger.info(f"Generated {len(embeddings)} embeddings")

            # Step 3: Cluster clauses
            logger.info("Step 3: Clustering clauses...")
            actual_clusters = min(n_clusters, len(clauses_text))
            labels = cluster_clauses(embeddings, k=actual_clusters)
            clause_groups = group_clauses_by_cluster(clauses_text, labels)
            logger.info(f"Clustered into {len(clause_groups)} groups")

            # Step 4: Name clause groups using LLM
            logger.info("Step 4: Generating clause names with Qwen LLM...")
            clause_type_names = self._name_clause_groups(clause_groups)
            logger.info(f"Generated names for {len(clause_type_names)} clause types")

            # Step 5: Store in databases
            logger.info("Step 5: Storing clauses...")
            created_clauses = []

            if save_to_db:
                created_clauses = self._store_clauses(
                    contract=contract,
                    clauses_text=clauses_text,
                    embeddings=embeddings,
                    labels=labels,
                    clause_type_names=clause_type_names
                )
                logger.info(f"Stored {len(created_clauses)} clauses in database")

            # Prepare result summary
            result = {
                'success': True,
                'message': 'Contract processed successfully',
                'total_clauses': len(clauses_text),
                'unique_clause_types': len(clause_type_names),
                'clause_types': clause_type_names,
                'clause_distribution': {
                    clause_type_names[label]: len(group)
                    for label, group in clause_groups.items()
                },
                'created_clause_ids': [c.id for c in created_clauses] if save_to_db else []
            }

            logger.info("Contract processing complete")
            return result

        except Exception as e:
            logger.error(f"Error processing contract: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Error processing contract: {str(e)}',
                'total_clauses': 0
            }

    def _extract_clauses(self, contract_text: str) -> List[str]:
        """
        Extract individual clauses from contract text.

        Args:
            contract_text (str): Full contract text

        Returns:
            List[str]: List of extracted clause texts
        """
        try:
            clauses = split_into_clauses(contract_text, min_length=50)
            return clauses
        except Exception as e:
            logger.error(f"Error extracting clauses: {e}")
            return []

    def _name_clause_groups(self, clause_groups: Dict[int, List[str]]) -> Dict[int, str]:
        """
        Generate names for each clause group using LLM.

        Args:
            clause_groups (Dict[int, List[str]]): Map of cluster_id -> clause texts

        Returns:
            Dict[int, str]: Map of cluster_id -> clause type name
        """
        try:
            return self.llm_client.batch_name_clause_groups(clause_groups)
        except Exception as e:
            logger.error(f"Error naming clause groups: {e}")
            # Fallback to generic names
            return {
                cluster_id: f"Clause Group {cluster_id}"
                for cluster_id in clause_groups.keys()
            }

    def _store_clauses(
        self,
        contract: Contract,
        clauses_text: List[str],
        embeddings: List[List[float]],
        labels: List[int],
        clause_type_names: Dict[int, str]
    ) -> List[Clause]:
        """
        Store clauses in MySQL and Qdrant vector database.

        Args:
            contract (Contract): The contract instance
            clauses_text (List[str]): Clause texts
            embeddings (List[List[float]]): BERT embeddings
            labels (List[int]): Cluster labels
            clause_type_names (Dict[int, str]): Clause type names

        Returns:
            List[Clause]: Created Clause model instances
        """
        created_clauses = []

        try:
            # Prepare metadata for Qdrant
            metadata_list = []

            for i, (clause_text, embedding, label) in enumerate(zip(clauses_text, embeddings, labels)):
                clause_type = clause_type_names.get(label, "General")
                clause_label = f"{clause_type}_{label}"

                # Store in Qdrant first to get embedding_id
                metadata = {
                    'contract_id': str(contract.id),
                    'clause_text': clause_text[:1000],  # Truncate for storage
                    'clause_type': clause_type,
                    'clause_label': clause_label,
                    'contract_filename': contract.original_filename,
                    'contract_type': contract.contract_type or 'General'
                }
                metadata_list.append(metadata)

            # Batch store in Qdrant
            logger.info("Storing embeddings in Qdrant...")
            embedding_ids = self.vector_store.store_embeddings(embeddings, metadata_list)

            # Store in MySQL
            logger.info("Storing clauses in MySQL...")
            for i, (clause_text, label, embedding_id) in enumerate(zip(clauses_text, labels, embedding_ids)):
                clause_type = clause_type_names.get(label, "General")
                clause_label = f"{clause_type}_{label}"

                # Create Clause model instance
                clause = Clause.objects.create(
                    contract=contract,
                    clause_name=clause_type,
                    extracted_text=clause_text,
                    found=True,
                    confidence=0.85,  # Placeholder confidence score
                    clause_type=clause_type,
                    clause_label=clause_label,
                    embedding_id=embedding_id
                )

                created_clauses.append(clause)
                logger.debug(f"Created clause {i+1}/{len(clauses_text)}: {clause_type}")

            logger.info(f"Successfully stored {len(created_clauses)} clauses")
            return created_clauses

        except Exception as e:
            logger.error(f"Error storing clauses: {e}", exc_info=True)
            return created_clauses

    def search_similar_clauses(
        self,
        query_text: str,
        limit: int = 10,
        contract_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for clauses similar to query text.

        Args:
            query_text (str): The search query
            limit (int): Maximum number of results (default: 10)
            contract_type (Optional[str]): Filter by contract type

        Returns:
            List[Dict]: Search results with clause data and similarity scores

        Example:
            >>> service = ClauseLibraryService()
            >>> results = service.search_similar_clauses("payment within 30 days", limit=5)
            >>> results[0]['score']
            0.92
        """
        try:
            # Build filters
            filters = {}
            if contract_type:
                filters['contract_type'] = contract_type

            # Perform search
            results = self.vector_store.search_by_text_query(
                query_text=query_text,
                embedder=self.embedder,
                limit=limit,
                filters=filters if filters else None
            )

            logger.info(f"Found {len(results)} similar clauses for query: '{query_text[:50]}...'")
            return results

        except Exception as e:
            logger.error(f"Error searching similar clauses: {e}")
            return []

    def get_clause_statistics(self, contract_id: Optional[str] = None) -> Dict:
        """
        Get statistics about clauses in the library.

        Args:
            contract_id (Optional[str]): Filter by specific contract

        Returns:
            Dict: Statistics including total clauses, clause types distribution, etc.
        """
        try:
            # Query clauses
            if contract_id:
                clauses = Clause.objects.filter(contract_id=contract_id, clause_type__isnull=False)
            else:
                clauses = Clause.objects.filter(clause_type__isnull=False)

            total_clauses = clauses.count()

            # Count by clause type
            clause_type_distribution = {}
            for clause in clauses:
                clause_type = clause.clause_type or 'Unknown'
                clause_type_distribution[clause_type] = clause_type_distribution.get(clause_type, 0) + 1

            # Qdrant statistics
            qdrant_info = self.vector_store.get_collection_info()

            return {
                'total_clauses_in_db': total_clauses,
                'total_vectors_in_qdrant': qdrant_info.get('points_count', 0),
                'unique_clause_types': len(clause_type_distribution),
                'clause_type_distribution': clause_type_distribution,
                'contract_filter': contract_id if contract_id else 'all'
            }

        except Exception as e:
            logger.error(f"Error getting clause statistics: {e}")
            return {
                'error': str(e),
                'total_clauses_in_db': 0
            }


# Convenience functions

def process_contract_with_clause_library(contract: Contract, n_clusters: int = 8) -> Dict:
    """
    Convenience function to process a contract through the clause library pipeline.

    Args:
        contract (Contract): Contract model instance
        n_clusters (int): Number of clause clusters

    Returns:
        Dict: Processing results

    Example:
        >>> from api.clause_library_service import process_contract_with_clause_library
        >>> contract = Contract.objects.get(id='...')
        >>> result = process_contract_with_clause_library(contract)
    """
    service = ClauseLibraryService()
    return service.process_contract(contract, n_clusters=n_clusters)


def search_clause_library(query: str, limit: int = 10) -> List[Dict]:
    """
    Convenience function to search the clause library.

    Args:
        query (str): Search query text
        limit (int): Maximum results

    Returns:
        List[Dict]: Search results
    """
    service = ClauseLibraryService()
    return service.search_similar_clauses(query, limit=limit)
