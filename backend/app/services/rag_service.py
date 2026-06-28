import os
from dotenv import load_dotenv
from openai import OpenAI
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService

load_dotenv()

class RAGService:
    """Servicio central de RAG: recuperación y generación de respuestas."""

    def __init__(self, embedding_service: EmbeddingService, qdrant_service: QdrantService):
        self.embedding_service = embedding_service
        self.qdrant_service = qdrant_service
        self.llm_client = OpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=f"{os.getenv('LLM_API_URL')}/api"
        )
        self.model = os.getenv("LLM_MODEL", "gpt-oss:20b")

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Recupera los chunks más relevantes para una consulta.
        
        Calcula el embedding de la consulta y busca en Qdrant
        los fragmentos más similares semánticamente.
        """
        query_embedding = self.embedding_service.embed_text(query)
        chunks = self.qdrant_service.search(query_embedding, top_k=top_k)
        return chunks

    def build_prompt(self, query: str, chunks: list[dict], history: list[dict]) -> list[dict]:
        """
        Construye el prompt completo para el LLM.
        
        Combina: instrucción de sistema + chunks recuperados + 
        historial de conversación + pregunta actual.
        """
        context = "\n\n".join([
            f"[Fuente: {c['source']}, página {c['page']}]\n{c['text']}"
            for c in chunks
        ])

        system_prompt = f"""Eres un asistente virtual inteligente especializado en atención primaria, 
        integrado en el sistema MRP-5G. Tu rol es ayudar al personal sanitario respondiendo consultas 
        basadas en la documentación médica disponible.

INSTRUCCIONES:
- Responde siempre en español.
- Basa tus respuestas ÚNICAMENTE en la documentación proporcionada.
- Cita siempre la fuente indicando el documento y la página.
- Si la información no está en la documentación, indícalo explícitamente.
- Sé proactivo: al final de cada respuesta sugiere una acción siguiente o una pregunta relacionada relevante.
- Nunca diagnostiques ni prescribas de forma autónoma.

DOCUMENTACIÓN DISPONIBLE:
{context}"""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": query})

        return messages

    def generate_stream(self, messages: list[dict]):
        """
        Genera la respuesta en streaming token a token.
        
        Usa Server-Sent Events (SSE) para enviar cada token
        al frontend conforme se genera.
        """
        stream = self.llm_client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            temperature=0.3  #para respuestas precisas y consistentes
        )

        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    def generate_proactive_intro(self, filename: str) -> str:
        """
        Genera un resumen proactivo al subir un documento.
        
        El asistente presenta el documento y sugiere preguntas
        sin que el médico haya escrito nada.
        """
        chunks = self.qdrant_service.search(
            self.embedding_service.embed_text("resumen contenido principal"),
            top_k=3
        )

        context = "\n\n".join([c['text'] for c in chunks])

        messages = [
            {
                "role": "system",
                "content": "Eres un asistente médico. Resume brevemente el documento y sugiere 3 preguntas relevantes que el médico podría hacerte sobre él. Responde en español."
            },
            {
                "role": "user",
                "content": f"El documento '{filename}' ha sido cargado. Este es su contenido:\n\n{context}"
            }
        ]

        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3
        )

        return response.choices[0].message.content