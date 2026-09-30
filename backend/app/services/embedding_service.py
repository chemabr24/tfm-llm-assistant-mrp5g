import os
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()


class EmbeddingService:
    """Servicio para calcular embeddings de texto."""

    def __init__(self):
        model_name = os.getenv(
            "EMBEDDING_MODEL",
            "intfloat/multilingual-e5-large"
        )

        print(f"Cargando modelo de embeddings: {model_name}")

        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.dimension = self.model.get_embedding_dimension()

        print(
            f"Modelo cargado. "
            f"Dimensión de embeddings: {self.dimension}"
        )

    def embed_text(
        self,
        text: str,
        is_query: bool = False
    ) -> list[float]:
        """
        Calcula el embedding de un texto.

        Para modelos E5:
        - query: para consultas
        - passage: para fragmentos de documentos
        """

        if "e5" in self.model_name.lower():
            prefix = "query: " if is_query else "passage: "
            text = prefix + text

        embedding = self.model.encode(
            text,
            normalize_embeddings=True
        )

        return embedding.tolist()

    def embed_batch(
        self,
        texts: list[str]
    ) -> list[list[float]]:
        """
        Calcula embeddings de fragmentos de documentos en batch.
        """

        if "e5" in self.model_name.lower():
            texts = [
                f"passage: {text}"
                for text in texts
            ]

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=32
        )

        return embeddings.tolist()