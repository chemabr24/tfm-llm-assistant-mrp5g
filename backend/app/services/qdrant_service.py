import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv

load_dotenv()

COLLECTION_NAME = "medical_documents"

class QdrantService:
    """Servicio para gestionar la base de datos vectorial Qdrant."""

    def __init__(self, embedding_dimension: int):
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.client = QdrantClient(url=qdrant_url)
        self.embedding_dimension = embedding_dimension
        self._ensure_collection()

    def _ensure_collection(self):
        """Crea la colección en Qdrant si no existe."""
        collections = self.client.get_collections().collections
        names = [c.name for c in collections]

        if COLLECTION_NAME not in names:
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.embedding_dimension,
                    distance=Distance.COSINE
                )
            )
            print(f"Colección '{COLLECTION_NAME}' creada en Qdrant.")
        else:
            print(f"Colección '{COLLECTION_NAME}' ya existe en Qdrant.")

    def store_chunks(self, chunks: list[dict], embeddings: list[list[float]]):
        """
        Almacena chunks y sus embeddings en Qdrant.
        
        Cada chunk debe tener: text, page, source (nombre del archivo).
        """
        points = [
            PointStruct(
                id=chunk["id"],
                vector=embedding,
                payload={
                    "text": chunk["text"],
                    "page": chunk["page"],
                    "source": chunk["source"]
                }
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]

        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """
        Busca los chunks más similares a un embedding de consulta.
        
        Devuelve los top_k chunks más relevantes con su texto y metadatos.
        """
        results = self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=top_k,
            with_payload=True
        )

        return [
            {
                "text": r.payload["text"],
                "page": r.payload["page"],
                "source": r.payload["source"],
                "score": r.score
            }
            for r in results
        ]