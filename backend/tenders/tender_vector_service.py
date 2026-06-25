"""
Tender Vectorization Service
Uses MiniLM embeddings and Qdrant vector database
"""
import os
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any
import hashlib
import uuid


class TenderVectorService:
    """Vectorization service for tender sections and content"""

    def __init__(self):
        # Lazy load embedding model (don't load at import time)
        self._model = None
        self.vector_size = 384  # MiniLM output dimension

        # Initialize Qdrant client
        try:
            qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
            qdrant_port = int(os.getenv('QDRANT_PORT', 6333))
            self.qdrant = QdrantClient(qdrant_host, port=qdrant_port)
        except:
            # Fallback to in-memory mode if Qdrant server not available
            self.qdrant = QdrantClient(":memory:")

        # Collection name
        self.collection_name = "tender_sections"

        # Ensure collection exists
        self._ensure_collection()

    @property
    def model(self):
        """Lazy load the SentenceTransformer model on first access"""
        if self._model is None:
            self._model = SentenceTransformer("all-MiniLM-L6-v2", device='cpu')
        return self._model

    def _ensure_collection(self):
        """Ensure Qdrant collection exists"""
        try:
            collections = self.qdrant.get_collections().collections
            collection_names = [col.name for col in collections]

            if self.collection_name not in collection_names:
                self.qdrant.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
        except Exception as e:
            print(f"Error ensuring collection: {e}")

    def vectorize_tender(self, tender_id: int, sections: List[Dict]) -> List[str]:
        """
        Vectorize all sections of a tender and store in Qdrant.
        Batches all embeddings + upsert in a single call for speed.
        """
        if not sections:
            return []

        texts = [
            f"{s.get('title', '')} {s.get('content', '')}" for s in sections
        ]

        # Encode all texts in one batch
        embeddings = self.model.encode(texts, batch_size=64, show_progress_bar=False)

        points = []
        vector_ids = []
        for section, embedding in zip(sections, embeddings):
            vector_id = self._generate_vector_id(tender_id, section['number'])
            vector_ids.append(vector_id)
            points.append(PointStruct(
                id=vector_id,
                vector=embedding.tolist(),
                payload={
                    'tender_id': tender_id,
                    'section_number': section['number'],
                    'title': section.get('title', ''),
                    'content': section.get('content', ''),
                    'page': section.get('page', 0),
                    'level': section.get('level', 0),
                }
            ))

        try:
            self.qdrant.upsert(
                collection_name=self.collection_name,
                points=points,
            )
        except Exception as e:
            print(f"Error batch-upserting tender sections: {e}")
            return []

        return vector_ids

    def vectorize_section(self, tender_id: int, section: Dict) -> str:
        """Vectorize a single section (used for incremental updates)."""
        text_to_embed = f"{section.get('title', '')} {section.get('content', '')}"
        embedding = self.model.encode(text_to_embed).tolist()
        vector_id = self._generate_vector_id(tender_id, section['number'])
        payload = {
            'tender_id': tender_id,
            'section_number': section['number'],
            'title': section.get('title', ''),
            'content': section.get('content', ''),
            'page': section.get('page', 0),
            'level': section.get('level', 0),
        }
        try:
            self.qdrant.upsert(
                collection_name=self.collection_name,
                points=[PointStruct(id=vector_id, vector=embedding, payload=payload)],
            )
            return vector_id
        except Exception as e:
            print(f"Error vectorizing section: {e}")
            return None

    def search_similar_sections(
        self,
        query: str,
        tender_id: int = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Search for similar sections using semantic search

        Args:
            query: Search query
            tender_id: Optional tender ID to filter results
            limit: Number of results to return

        Returns:
            List of similar sections with scores
        """
        # Generate query embedding
        query_embedding = self.model.encode(query).tolist()

        # Build filter
        filter_condition = None
        if tender_id:
            filter_condition = {
                "must": [
                    {
                        "key": "tender_id",
                        "match": {"value": tender_id}
                    }
                ]
            }

        try:
            # Search in Qdrant
            results = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=filter_condition
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'section_number': result.payload.get('section_number'),
                    'title': result.payload.get('title'),
                    'content': result.payload.get('content'),
                    'score': result.score,
                    'page': result.payload.get('page'),
                })

            return formatted_results
        except Exception as e:
            print(f"Error searching sections: {e}")
            return []

    def find_related_sections(
        self,
        section_number: str,
        tender_id: int,
        limit: int = 5
    ) -> List[Dict]:
        """
        Find sections related to a given section

        Args:
            section_number: Section number to find related content for
            tender_id: Tender ID
            limit: Number of results

        Returns:
            List of related sections
        """
        # Get the section content
        vector_id = self._generate_vector_id(tender_id, section_number)

        try:
            # Get the vector
            point = self.qdrant.retrieve(
                collection_name=self.collection_name,
                ids=[vector_id]
            )

            if not point:
                return []

            # Search for similar content
            content = point[0].payload.get('content', '')
            return self.search_similar_sections(content, tender_id, limit + 1)[1:]  # Exclude self
        except Exception as e:
            print(f"Error finding related sections: {e}")
            return []

    def delete_tender_vectors(self, tender_id: int):
        """Delete all vectors for a tender"""
        try:
            self.qdrant.delete(
                collection_name=self.collection_name,
                points_selector={
                    "filter": {
                        "must": [
                            {
                                "key": "tender_id",
                                "match": {"value": tender_id}
                            }
                        ]
                    }
                }
            )
        except Exception as e:
            print(f"Error deleting tender vectors: {e}")

    def _generate_vector_id(self, tender_id: int, section_number: str) -> str:
        """Generate unique vector ID"""
        # Create deterministic ID based on tender_id and section_number
        unique_string = f"{tender_id}_{section_number}"
        hash_object = hashlib.md5(unique_string.encode())
        return hash_object.hexdigest()

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks for vectorization

        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)

                if break_point > chunk_size * 0.5:  # At least 50% through chunk
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk.strip())
            start = end - overlap

        return chunks

    def vectorize_chunks(
        self,
        tender_id: int,
        section_number: str,
        chunks: List[str]
    ) -> List[str]:
        """Vectorize text chunks in a single batch upsert."""
        if not chunks:
            return []

        embeddings = self.model.encode(chunks, batch_size=64, show_progress_bar=False)
        base_id = self._generate_vector_id(tender_id, section_number)
        points = []
        vector_ids = []

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector_id = f"{base_id}_chunk_{i}"
            vector_ids.append(vector_id)
            points.append(PointStruct(
                id=vector_id,
                vector=embedding.tolist(),
                payload={
                    'tender_id': tender_id,
                    'section_number': section_number,
                    'chunk_index': i,
                    'content': chunk,
                    'is_chunk': True,
                }
            ))

        try:
            self.qdrant.upsert(collection_name=self.collection_name, points=points)
        except Exception as e:
            print(f"Error batch-vectorizing chunks: {e}")
            return []

        return vector_ids


# Singleton instance
tender_vector_service = TenderVectorService()
