import os

from dotenv import load_dotenv
from openai import OpenAI

from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService


load_dotenv()


class RAGService:
    """Servicio central de RAG: recuperación y generación de respuestas."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        qdrant_service: QdrantService
    ):
        self.embedding_service = embedding_service
        self.qdrant_service = qdrant_service

        self.llm_client = OpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=f"{os.getenv('LLM_API_URL')}/api"
        )

        self.model = os.getenv("LLM_MODEL", "gpt-oss:20b")

    # ============================================================
    # Recuperación documental
    # ============================================================

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        session_id: str = None
    ) -> list[dict]:
        """
        Recupera los chunks más relevantes para una consulta.

        Calcula el embedding de la consulta y busca en Qdrant
        los fragmentos más similares semánticamente, filtrando
        por sesión si se proporciona session_id.
        """

        query_embedding = self.embedding_service.embed_text(
            query,
            is_query=True
        )

        chunks = self.qdrant_service.search(
            query_embedding,
            top_k=top_k,
            session_id=session_id
        )

        return chunks

    # ============================================================
    # Construcción del prompt
    # ============================================================

    def build_prompt(
        self,
        query: str,
        chunks: list[dict],
        history: list[dict]
    ) -> list[dict]:
        """
        Construye el prompt completo para el LLM.

        Combina:
        - instrucciones de sistema;
        - chunks recuperados mediante RAG;
        - historial completo de la conversación;
        - consulta actual.

        Si la consulta actual ya aparece como último mensaje del historial,
        se elimina esa copia para evitar enviarla dos veces al modelo.
        """

        context = "\n\n".join([
            (
                f"[Fuente: {c['source']}, página {c['page']}]\n"
                f"{c['text']}"
            )
            for c in chunks
        ])

        system_prompt = f"""
    Eres un asistente virtual inteligente especializado en atención primaria,
    integrado en el sistema MRP-5G. Tu rol es ayudar al personal sanitario
    respondiendo consultas basadas en la documentación médica disponible.

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
    {context}
    """.strip()

        # --------------------------------------------------------
        # Mantener el historial completo de la conversación
        # --------------------------------------------------------

        clean_history = list(history or [])

        # El frontend puede incluir ya la consulta actual como último
        # mensaje del historial. En ese caso eliminamos esa copia,
        # ya que se añadirá explícitamente al final del prompt.
        if clean_history:
            last_message = clean_history[-1]

            if (
                last_message.get("role") == "user"
                and last_message.get("content", "").strip() == query.strip()
            ):
                clean_history.pop()

        # --------------------------------------------------------
        # Construcción final
        # --------------------------------------------------------

        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            *clean_history,
            {
                "role": "user",
                "content": query
            }
        ]

        return messages
    # ============================================================
    # Generación en streaming
    # ============================================================

    def generate_stream(self, messages: list[dict]):
        """
        Genera la respuesta de forma incremental.

        Los fragmentos producidos por el modelo se devuelven
        progresivamente al cliente mediante una respuesta HTTP
        en streaming.

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

        # ========================================================
        # DEBUG
        # ========================================================

        print("\n================ LLM REQUEST ================")
        print("Número de mensajes:", len(messages))

        for i, msg in enumerate(messages):
            content = msg.get("content", "")

            print(
                f"MESSAGE {i} | "
                f"role={msg.get('role')} | "
                f"length={len(content) if content else 0}"
            )

        print("=============================================\n")

        # ========================================================
        # Primer intento
        # ========================================================

        stream = create_stream(
            messages,
            temperature=0.3
        )

        initial_buffer = ""
        streaming_started = False

        chunk_count = 0
        content_chunk_count = 0
        total_content = ""

        for chunk in stream:
            chunk_count += 1

            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            if not delta.content:
                continue

            content_chunk_count += 1
            total_content += delta.content

            if not streaming_started:
                initial_buffer += delta.content

                # Esperamos a tener una respuesta mínimamente útil
                # antes de empezar a enviarla al cliente.
                if len(initial_buffer.strip()) >= MIN_VISIBLE_CHARS:
                    streaming_started = True

                    yield initial_buffer

                    initial_buffer = ""

            else:
                yield delta.content

        print(
            f"FIRST ATTEMPT -> "
            f"chunks={chunk_count}, "
            f"content_chunks={content_chunk_count}, "
            f"content_length={len(total_content)}, "
            f"streaming_started={streaming_started}"
        )

        # Si se ha producido contenido válido no es necesario
        # realizar ningún reintento.
        if streaming_started:
            return

        # ========================================================
        # Segundo intento
        # ========================================================

        retry_instruction = {
            "role": "system",
            "content": (
                "La generación anterior no produjo una respuesta final "
                "visible. Responde directamente a la última consulta del "
                "usuario utilizando exclusivamente la documentación "
                "proporcionada. No describas tu razonamiento. "
                "Si la documentación no contiene información suficiente, "
                "indícalo explícitamente."
            )
        }

        # Colocamos la instrucción de reintento junto al system
        # principal y no después del mensaje del usuario.
        retry_messages = [
            messages[0],
            retry_instruction,
            *messages[1:]
        ]

        retry_stream = create_stream(
            retry_messages,
            temperature=0.1
        )

        retry_buffer = ""
        retry_started = False

        retry_chunk_count = 0
        retry_content_chunk_count = 0
        retry_total_content = ""

        for chunk in retry_stream:
            retry_chunk_count += 1

            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            if not delta.content:
                continue

            retry_content_chunk_count += 1
            retry_total_content += delta.content

            if not retry_started:
                retry_buffer += delta.content

                if len(retry_buffer.strip()) >= MIN_VISIBLE_CHARS:
                    retry_started = True

                    yield retry_buffer

                    retry_buffer = ""

            else:
                yield delta.content

        print(
            f"RETRY -> "
            f"chunks={retry_chunk_count}, "
            f"content_chunks={retry_content_chunk_count}, "
            f"content_length={len(retry_total_content)}, "
            f"retry_started={retry_started}"
        )

        # ========================================================
        # Si los dos intentos fallan
        # ========================================================

        if not retry_started:
            yield (
                "No ha sido posible generar una respuesta final a partir de "
                "la documentación recuperada. Reformule la consulta o revise "
                "las fuentes asociadas a la sesión."
            )

    # ============================================================
    # Generación proactiva al subir documentos
    # ============================================================

    def generate_proactive_intro(
        self,
        filename: str,
        session_id: str = None
    ) -> str:
        """
        Genera un resumen proactivo al subir un documento.
        """

        summary_embedding = self.embedding_service.embed_text(
            "resumen contenido principal",
            is_query=True
        )

        chunks = self.qdrant_service.search(
            summary_embedding,
            top_k=3,
            session_id=session_id
        )

        context = "\n\n".join([
            c["text"]
            for c in chunks
        ])

        messages = [
            {
                "role": "system",
                "content": (
                    "Eres un asistente médico. Resume brevemente el documento "
                    "y sugiere 3 preguntas relevantes que el médico podría "
                    "hacerte sobre él. Responde en español."
                )
            },
            {
                "role": "user",
                "content": (
                    f"El documento '{filename}' ha sido cargado. "
                    f"Este es su contenido:\n\n{context}"
                )
            }
        ]

        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3
        )

        return response.choices[0].message.content