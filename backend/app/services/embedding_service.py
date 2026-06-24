import os
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

class EmbeddingService:
    """Servicio para calcular embeddings de texto usando bge-large-en-v1.5."""
    
    def __init__(self):
        model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
        print(f"Cargando modelo de embeddings: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"Modelo cargado. Dimensión de embeddings: {self.dimension}")

    def embed_text(self, text: str) -> list[float]:
        """Calcula el embedding de un texto."""
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Calcula embeddings de una lista de textos en batch."""
        embeddings = self.model.encode(texts, normalize_embeddings=True, batch_size=32)
        return embeddings.tolist()