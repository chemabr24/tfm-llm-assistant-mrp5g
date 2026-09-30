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

    def retrieve(self, query: str, top_k: int = 5, session_id: str = None) -> list[dict]:
        """
        Recupera los chunks más relevantes para una consulta.
        
        Calcula el embedding de la consulta y busca en Qdrant
        los fragmentos más similares semánticamente, filtrando
        por sesión si se proporciona session_id.
        """
        query_embedding = self.embedding_service.embed_text(query, is_query=True)
        chunks = self.qdrant_service.search(query_embedding, top_k=top_k, session_id=session_id)
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
- NUNCA diagnostiques ni prescribas de forma autónoma.
- NUNCA incluyas preguntas sugeridas dentro del texto de tu respuesta. Las preguntas sugeridas se gestionan por separado. Limítate a responder la consulta del médico.
- Debes proporcionar siempre una respuesta final visible al usuario.
- No finalices la generación sin escribir una respuesta en el mensaje final.
- Si la documentación recuperada no permite responder con seguridad, responde explícitamente que la información no está disponible en la documentación.

DOCUMENTACIÓN DISPONIBLE:
{context}"""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": query})

        return messages

    def generate_stream(self, messages: list[dict]):
        """
        Genera la respuesta de forma incremental.

        Los fragmentos producidos por el modelo se devuelven progresivamente
        al cliente mediante una respuesta HTTP en streaming.

        Si el primer intento no produce contenido visible suficiente,
        se realiza un único reintento con una instrucción más directa.
        """

        MIN_VISIBLE_CHARS = 15

        def create_stream(current_messages, temperature=0.3):
            return self.llm_client.chat.completions.create(
                model=self.model,
                messages=current_messages,
                stream=True,
                temperature=temperature
            )

        # ---------------------------------------------------------
        # Primer intento
        # ---------------------------------------------------------
        stream = create_stream(messages)

        initial_buffer = ""
        streaming_started = False

        for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            if not delta.content:
                continue

            if not streaming_started:
                initial_buffer += delta.content

                # Esperamos a tener una respuesta mínimamente útil antes
                # de empezar a enviarla al cliente.
                if len(initial_buffer.strip()) >= MIN_VISIBLE_CHARS:
                    streaming_started = True
                    yield initial_buffer
                    initial_buffer = ""
            else:
                yield delta.content

        # Si ya hemos generado una respuesta válida, terminamos.
        if streaming_started:
            return

        # ---------------------------------------------------------
        # Segundo intento
        # ---------------------------------------------------------
        retry_messages = messages + [
            {
                "role": "system",
                "content": (
                    "La generación anterior no produjo una respuesta final "
                    "visible. Responde ahora directamente a la consulta del "
                    "usuario. Utiliza exclusivamente la documentación "
                    "proporcionada. No describas tu razonamiento. "
                    "Si la documentación no contiene información suficiente, "
                    "indícalo explícitamente."
                )
            }
        ]

        retry_stream = create_stream(
            retry_messages,
            temperature=0.1
        )

        retry_buffer = ""
        retry_started = False

        for chunk in retry_stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            if not delta.content:
                continue

            if not retry_started:
                retry_buffer += delta.content

                if len(retry_buffer.strip()) >= MIN_VISIBLE_CHARS:
                    retry_started = True
                    yield retry_buffer
                    retry_buffer = ""
            else:
                yield delta.content

        # ---------------------------------------------------------
        # Si los dos intentos fallan
        # ---------------------------------------------------------
        if not retry_started:
            yield (
                "No ha sido posible generar una respuesta final a partir de "
                "la documentación recuperada. Reformule la consulta o revise "
                "las fuentes asociadas a la sesión."
            )

    def generate_proactive_intro(self, filename: str, session_id: str = None) -> str:
        """
        Genera un resumen proactivo al subir un documento.
        """
        chunks = self.qdrant_service.search(
            self.embedding_service.embed_text("resumen contenido principal"),
            top_k=3,
            session_id=session_id
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