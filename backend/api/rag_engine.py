"""
Contract RAG (Retrieval-Augmented Generation) Engine

Handles:
- Document chunking and embedding
- Vector database storage (ChromaDB)
- Semantic search and retrieval
- Legal clause extraction using LLMs
"""

import os
import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)


class ContractRAG:
    """
    RAG Engine for contract analysis using:
    - ChromaDB for vector storage
    - Sentence Transformers for embeddings (Contracts-BERT)
    - LangChain for RAG orchestration
    - OpenAI GPT-4 or local LLM (Qwen) for clause extraction
    """

    def __init__(self, use_openai: bool = False):
        """
        Initialize RAG engine.

        Args:
            use_openai: If True, use OpenAI GPT-4, otherwise use local Ollama
        """
        self.use_openai = use_openai
        self._init_embeddings()
        self._init_vector_db()
        self._init_llm()

    def _init_embeddings(self):
        """Initialize embedding model (Contracts-BERT or sentence-transformers)."""
        try:
            from sentence_transformers import SentenceTransformer

            # Use specialized legal embeddings if available
            # nlpaueb/legal-bert-base-uncased is trained on legal documents
            # Alternative: sentence-transformers/all-MiniLM-L6-v2 (general purpose, faster)
            self.embedding_model_name = getattr(
                settings,
                'CONTRACTS_BERT_MODEL',
                'sentence-transformers/all-MiniLM-L6-v2'
            )

            self.embeddings = SentenceTransformer(self.embedding_model_name, device='cpu')
            logger.info(f"✓ Loaded embedding model: {self.embedding_model_name}")

        except Exception as e:
            logger.error(f"Failed to load embeddings: {e}")
            raise

    def _init_vector_db(self):
        """Initialize ChromaDB vector database."""
        try:
            import chromadb

            # Get ChromaDB path from settings
            chroma_path = getattr(settings, 'CHROMADB_PATH', './chroma_db')

            # Ensure directory exists
            os.makedirs(chroma_path, exist_ok=True)

            # Initialize ChromaDB client (v0.5.23+)
            self.chroma_client = chromadb.PersistentClient(path=chroma_path)

            # Get or create collection for contracts
            # Simple approach without metadata for maximum compatibility
            self.collection = self.chroma_client.get_or_create_collection(
                name="contracts"
            )

            logger.info(f"✓ ChromaDB initialized at: {chroma_path}")
            logger.info(f"  Collection size: {self.collection.count()} documents")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def _init_llm(self):
        """Initialize LLM (OpenAI or Ollama)."""
        try:
            if self.use_openai:
                # Use OpenAI GPT-4
                from langchain_openai import ChatOpenAI

                api_key = getattr(settings, 'OPENAI_API_KEY', None)
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not configured in settings")

                self.llm = ChatOpenAI(
                    model_name="gpt-4o",
                    temperature=0,
                    api_key=api_key
                )
                logger.info("✓ Using OpenAI GPT-4 for clause extraction")

            else:
                # Use local Ollama with Qwen
                from langchain_community.llms import Ollama

                ollama_model = getattr(settings, 'OLLAMA_MODEL', 'qwen2.5:0.5b')
                ollama_base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')

                self.llm = Ollama(
                    model=ollama_model,
                    base_url=ollama_base_url,
                    temperature=0
                )
                logger.info(f"✓ Using Ollama ({ollama_model}) for clause extraction")

        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise

    def ingest_contract(
        self,
        contract_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ingest contract text into vector database.

        Args:
            contract_id: Unique contract identifier
            text: Full contract text
            metadata: Additional metadata to store

        Returns:
            Ingestion statistics
        """
        try:
            from langchain_community.document_loaders import TextLoader
            from langchain.text_splitter import RecursiveCharacterTextSplitter

            # Split text into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""]
            )

            chunks = text_splitter.split_text(text)

            # Prepare metadata
            if metadata is None:
                metadata = {}

            metadata['contract_id'] = contract_id
            metadata['total_chunks'] = len(chunks)
            metadata['ingested_at'] = datetime.now().isoformat()

            # Generate embeddings and store in ChromaDB
            chunk_ids = []
            embeddings_list = []
            metadatas = []
            documents = []

            for idx, chunk in enumerate(chunks):
                chunk_id = f"{contract_id}_chunk_{idx}"
                chunk_ids.append(chunk_id)

                # Generate embedding
                embedding = self.embeddings.encode(chunk).tolist()
                embeddings_list.append(embedding)

                # Prepare metadata for this chunk
                chunk_metadata = {
                    **metadata,
                    'chunk_index': idx,
                    'chunk_start': idx * 900,  # Approximate
                    'chunk_end': idx * 900 + len(chunk)
                }
                metadatas.append(chunk_metadata)
                documents.append(chunk)

            # Upsert to ChromaDB (insert new or update existing)
            self.collection.upsert(
                ids=chunk_ids,
                embeddings=embeddings_list,
                metadatas=metadatas,
                documents=documents
            )

            logger.info(f"✓ Ingested contract {contract_id}: {len(chunks)} chunks")

            return {
                'contract_id': contract_id,
                'chunks_created': len(chunks),
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"Error ingesting contract {contract_id}: {e}")
            return {
                'contract_id': contract_id,
                'status': 'error',
                'error': str(e)
            }

    def extract_clauses(self, contract_id: str, contract_text: str) -> Dict[str, Any]:
        """
        Extract legal clauses from contract using LLM.

        Uses RAG to retrieve relevant context before extraction.

        Args:
            contract_id: Contract identifier
            contract_text: Full contract text

        Returns:
            Extracted clauses in structured format
        """
        try:
            # First, retrieve most relevant chunks for clause extraction
            query = "termination clause, liability limitation, payment terms, governing law, confidentiality"
            relevant_chunks = self.semantic_search(
                query=query,
                contract_id=contract_id,
                k=5
            )

            # Combine relevant chunks
            context = "\n\n".join([chunk['text'] for chunk in relevant_chunks])

            # If context is too small, use full text (truncated)
            if len(context) < 500:
                context = contract_text[:4000]

            # Use the legal extraction prompt
            from .legal_extraction_prompt import get_extraction_prompt

            prompt = get_extraction_prompt(context)

            # Invoke LLM
            if self.use_openai:
                from langchain.schema import HumanMessage
                response = self.llm.invoke([HumanMessage(content=prompt)])
                raw_response = response.content
            else:
                raw_response = self.llm.invoke(prompt)

            # Parse JSON response
            clean_json = self._clean_llm_json(raw_response)
            extracted_data = json.loads(clean_json)

            logger.info(f"✓ Extracted clauses from contract {contract_id}")

            return {
                'contract_id': contract_id,
                'extracted_data': extracted_data,
                'chunks_used': len(relevant_chunks),
                'status': 'success'
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.error(f"Raw response: {raw_response[:500]}")
            return {
                'contract_id': contract_id,
                'status': 'error',
                'error': 'JSON parsing failed',
                'raw_response': raw_response[:1000]
            }

        except Exception as e:
            logger.error(f"Error extracting clauses from {contract_id}: {e}")
            return {
                'contract_id': contract_id,
                'status': 'error',
                'error': str(e)
            }

    def _clean_llm_json(self, raw_text: str) -> str:
        """
        Clean LLM response to extract valid JSON.

        Args:
            raw_text: Raw LLM output

        Returns:
            Clean JSON string
        """
        # Remove markdown code blocks
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[-1].split("```")[0]
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1]

        return raw_text.strip()

    def semantic_search(
        self,
        query: str,
        contract_id: Optional[str] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search across contracts.

        Args:
            query: Search query
            contract_id: Optional contract ID to search within
            k: Number of results to return

        Returns:
            List of relevant chunks with metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.embeddings.encode(query).tolist()

            # Build where filter
            where_filter = None
            if contract_id:
                where_filter = {"contract_id": contract_id}

            # Search ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=where_filter
            )

            # Format results
            formatted_results = []
            if results and results['documents']:
                for idx, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'text': doc,
                        'metadata': results['metadatas'][0][idx] if results['metadatas'] else {},
                        'distance': results['distances'][0][idx] if results['distances'] else 0.0,
                        'id': results['ids'][0][idx] if results['ids'] else None
                    })

            return formatted_results

        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []

    def query_contracts(self, user_query: str) -> str:
        """
        RAG-based question answering across all contracts.
        Uses Qdrant semantic search + Ollama LLM directly (no langchain.chains dependency).
        """
        try:
            import requests
            from django.conf import settings

            # Step 1: Embed the query
            query_embedding = self.embeddings.encode(user_query).tolist()

            # Step 2: Search Qdrant for top-5 relevant chunks
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=5,
                include=['documents', 'metadatas', 'distances']
            )

            if not results or not results.get('documents') or not results['documents'][0]:
                return "No relevant contract sections found for your query."

            # Step 3: Build context from retrieved chunks
            docs = results['documents'][0]
            metas = results['metadatas'][0] if results.get('metadatas') else [{}] * len(docs)
            context_parts = []
            for i, (doc, meta) in enumerate(zip(docs, metas)):
                contract_name = meta.get('contract_name', meta.get('filename', f'Contract {i+1}'))
                context_parts.append(f"[{contract_name}]\n{doc}")
            context = "\n\n---\n\n".join(context_parts)

            # Step 4: Call Ollama LLM with context
            prompt = (
                f"You are a legal contract analyst. Answer the following question based only on the contract excerpts provided.\n\n"
                f"CONTRACT EXCERPTS:\n{context}\n\n"
                f"QUESTION: {user_query}\n\n"
                f"ANSWER (be concise and cite the relevant contract where possible):"
            )

            ollama_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
            response = requests.post(
                f"{ollama_url}/api/generate",
                json={"model": "qwen2.5:0.5b", "prompt": prompt, "stream": False},
                timeout=45
            )

            if response.status_code == 200:
                return response.json().get('response', 'No answer generated.')
            else:
                # Fallback: return the most relevant chunk as answer
                return f"Based on your contracts:\n\n{docs[0]}"

        except Exception as e:
            logger.error(f"Query error: {e}")
            return f"Error processing query: {str(e)}"

    def delete_contract(self, contract_id: str) -> bool:
        """
        Delete all chunks for a specific contract from vector DB.

        Args:
            contract_id: Contract identifier

        Returns:
            True if successful
        """
        try:
            # Find all chunk IDs for this contract
            results = self.collection.get(
                where={"contract_id": contract_id}
            )

            if results and results['ids']:
                # Delete chunks
                self.collection.delete(ids=results['ids'])
                logger.info(f"✓ Deleted {len(results['ids'])} chunks for contract {contract_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error deleting contract {contract_id}: {e}")
            return False

    def get_contract_stats(self, contract_id: str) -> Dict[str, Any]:
        """
        Get statistics about a contract's embeddings.

        Args:
            contract_id: Contract identifier

        Returns:
            Statistics dict
        """
        try:
            results = self.collection.get(
                where={"contract_id": contract_id}
            )

            return {
                'contract_id': contract_id,
                'chunk_count': len(results['ids']) if results['ids'] else 0,
                'status': 'found' if results['ids'] else 'not_found'
            }

        except Exception as e:
            logger.error(f"Error getting stats for {contract_id}: {e}")
            return {
                'contract_id': contract_id,
                'status': 'error',
                'error': str(e)
            }
