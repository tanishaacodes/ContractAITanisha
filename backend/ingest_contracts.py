# ingest_contracts.py
import os
from pathlib import Path
from qdrant_client import QdrantClient, models as qmodels
from sentence_transformers import SentenceTransformer
from docx import Document
from PyPDF2 import PdfReader

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.environ.get("QDRANT_COLLECTION", "contracts")
EMBED_MODEL = "all-MiniLM-L6-v2"

embedder = SentenceTransformer(EMBED_MODEL, device='cpu')
VECTOR_DIM = embedder.get_sentence_embedding_dimension()

client = QdrantClient(url=QDRANT_URL)


def read_file_text(path: Path):
    ext = path.suffix.lower()
    if ext == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    elif ext == ".docx":
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    return ""


def chunk_text(text, chunk_size=500):
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]


def ingest_folder(folder_path: str):
    folder = Path(folder_path)

    # ❗ FIX: Remove replication param (YOUR ERROR WAS HERE)
    try:
        client.get_collection(COLLECTION_NAME)
    except:
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=qmodels.VectorParams(
                size=VECTOR_DIM,
                distance=qmodels.Distance.COSINE
            )
        )

    points = []
    point_id = 1

    for file_path in folder.glob("*"):
        text = read_file_text(file_path)
        chunks = chunk_text(text)

        for idx, chunk in enumerate(chunks):
            emb = embedder.encode(chunk).tolist()
            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=emb,
                    payload={
                        "filename": file_path.name,
                        "chunk_index": idx,
                        "text": chunk,
                    }
                )
            )
            point_id += 1

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)
