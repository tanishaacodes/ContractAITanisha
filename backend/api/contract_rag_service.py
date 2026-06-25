"""
Contract RAG (Retrieval-Augmented Generation) Service
Handles contract generation using uploaded sample contracts as context
"""
import os
import uuid
from typing import List, Dict
from django.conf import settings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Import embedding service singleton
from api.embedding_service import embedding_service


class ContractRAGService:
    """Service for contract generation using RAG"""

    def __init__(self):
        # Initialize Qdrant client
        qdrant_url = getattr(settings, 'QDRANT_URL', 'http://localhost:6333')
        self.qdrant_client = QdrantClient(url=qdrant_url)

        # Initialize embedding service
        self.embedding_service = embedding_service

        # Collection name for contract samples
        self.collection_name = "contract_samples"

        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        # Ensure collection exists
        self._ensure_collection()

    def _ensure_collection(self):
        """Create Qdrant collection if it doesn't exist"""
        try:
            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                # Create collection with vector size matching active embedding model
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_service.dimensions,
                        distance=Distance.COSINE
                    )
                )
                print(f"[RAG] Created Qdrant collection: {self.collection_name}")
            else:
                print(f"[RAG] Using existing Qdrant collection: {self.collection_name}")
        except Exception as e:
            print(f"[RAG] Error ensuring collection: {e}")
            # If Qdrant is not available, we'll handle it gracefully later

    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from a contract file (PDF, DOCX, TXT)"""
        from api.utils import extract_text_from_file as extract_util

        # Get file extension
        file_ext = os.path.splitext(file_path)[1].lower()

        # Extract text using existing utility
        result = extract_util(file_path, file_ext)

        return result.get('text', '')

    def index_contracts(self, file_paths: List[str], user_id: str = None) -> Dict:
        """
        Index multiple contract files into Qdrant vector database

        Args:
            file_paths: List of file paths to index
            user_id: Optional user ID for filtering

        Returns:
            Dictionary with indexing results
        """
        try:
            all_chunks = []
            all_metadata = []

            # Extract and chunk text from each file
            for file_path in file_paths:
                # Extract text
                text = self.extract_text_from_file(file_path)

                if not text.strip():
                    print(f"[RAG] Warning: No text extracted from {file_path}")
                    continue

                # Split into chunks
                chunks = self.text_splitter.split_text(text)

                # Add chunks and metadata
                filename = os.path.basename(file_path)
                for i, chunk in enumerate(chunks):
                    all_chunks.append(chunk)
                    all_metadata.append({
                        'filename': filename,
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'user_id': user_id or 'public'
                    })

            if not all_chunks:
                return {
                    'success': False,
                    'error': 'No text could be extracted from the provided files'
                }

            # Generate embeddings
            print(f"[RAG] Generating embeddings for {len(all_chunks)} chunks...")
            vectors = self.embedding_service.embed_batch(all_chunks)

            # Upload to Qdrant
            points = [
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector if isinstance(vector, list) else vector.tolist(),
                    payload={
                        'text': chunk,
                        **metadata
                    }
                )
                for vector, chunk, metadata in zip(vectors, all_chunks, all_metadata)
            ]

            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )

            print(f"[RAG] Successfully indexed {len(points)} chunks from {len(file_paths)} files")

            return {
                'success': True,
                'files_indexed': len(file_paths),
                'chunks_created': len(points),
                'filenames': [os.path.basename(fp) for fp in file_paths]
            }

        except Exception as e:
            print(f"[RAG] Error indexing contracts: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def retrieve_similar_chunks(self, query: str, top_k: int = 5, user_id: str = None) -> List[str]:
        """
        Retrieve similar contract chunks based on query

        Args:
            query: Search query
            top_k: Number of chunks to retrieve
            user_id: Optional user ID for filtering

        Returns:
            List of similar text chunks
        """
        try:
            # Generate query embedding
            query_vector = self.embedding_service.embed_text(query)

            # Search Qdrant
            search_filter = None
            if user_id:
                search_filter = {
                    'must': [
                        {'key': 'user_id', 'match': {'value': user_id}}
                    ]
                }

            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector if isinstance(query_vector, list) else query_vector.tolist(),
                limit=top_k,
                query_filter=search_filter
            )

            # Extract text from results
            chunks = [result.payload['text'] for result in results]

            return chunks

        except Exception as e:
            print(f"[RAG] Error retrieving chunks: {e}")
            return []

    def generate_contract(self, prompt: str, title: str = None, user_id: str = None) -> Dict:
        """
        Generate a new contract based on prompt using RAG

        Args:
            prompt: User's description of the contract to generate
            title: Optional contract title
            user_id: Optional user ID for context filtering

        Returns:
            Dictionary with generated contract and metadata
        """
        import requests

        try:
            # Retrieve similar contract chunks
            context_chunks = self.retrieve_similar_chunks(prompt, top_k=5, user_id=user_id)

            # Build context from retrieved chunks
            context = "\n\n".join([
                f"--- Example {i+1} ---\n{chunk}"
                for i, chunk in enumerate(context_chunks)
            ])

            # Get Ollama configuration
            ollama_base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
            ollama_model = getattr(settings, 'OLLAMA_MODEL', 'qwen2.5:0.5b')

            # Build prompt for LLM
            system_prompt = """You are a legal contract generation assistant.
Your task is to generate a professional contract based on the user's requirements and the example contracts provided.

Use the example contracts as reference for:
- Structure and formatting
- Legal language and terminology
- Standard clauses and provisions

Generate a complete, well-structured contract that addresses all the user's requirements."""

            user_prompt = f"""Based on these example contracts:

{context}

Generate a new contract with the following requirements:
{prompt}

Contract Title: {title or 'Untitled Contract'}

Please generate a complete, professional contract."""

            # Call Ollama API
            response = requests.post(
                f"{ollama_base_url}/api/chat",
                json={
                    'model': ollama_model,
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_prompt}
                    ],
                    'stream': False
                },
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                generated_contract = result.get('message', {}).get('content', '')

                return {
                    'success': True,
                    'contract': generated_contract,
                    'title': title or 'Generated Contract',
                    'model_used': ollama_model,
                    'context_chunks_used': len(context_chunks),
                    'has_context': len(context_chunks) > 0
                }
            else:
                return {
                    'success': False,
                    'error': f'LLM API returned status {response.status_code}'
                }

        except Exception as e:
            print(f"[RAG] Error generating contract: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def clear_user_contracts(self, user_id: str) -> bool:
        """Clear all indexed contracts for a specific user"""
        try:
            # Delete points with matching user_id
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector={
                    'filter': {
                        'must': [
                            {'key': 'user_id', 'match': {'value': user_id}}
                        ]
                    }
                }
            )
            return True
        except Exception as e:
            print(f"[RAG] Error clearing user contracts: {e}")
            return False

    def get_collection_stats(self) -> Dict:
        """Get statistics about the indexed contracts"""
        try:
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            return {
                'total_vectors': collection_info.points_count,
                'collection_name': self.collection_name
            }
        except Exception as e:
            return {
                'error': str(e)
            }
