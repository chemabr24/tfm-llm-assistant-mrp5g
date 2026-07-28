import uuid
import json
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService
from app.services.rag_service import RAGService
from app.models.database import AsyncSessionLocal, Session, Message, Task

router = APIRouter(prefix="/api", tags=["chat"])

embedding_service = EmbeddingService()
qdrant_service = QdrantService(embedding_dimension=embedding_service.dimension)
rag_service = RAGService(embedding_service, qdrant_service)


class ChatRequest(BaseModel):
    """Modelo de la petición de chat."""
    query: str
    session_id: str
    history: list[dict] = []


class ProactiveRequest(BaseModel):
    """Modelo de la petición de introducción proactiva."""
    filename: str
    session_id: str


@router.post("/chat")
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Recibe una pregunta, recupera chunks relevantes de Qdrant
    filtrados por sesión y genera una respuesta en streaming.
    Persiste el mensaje del usuario y la respuesta en PostgreSQL.
    Extrae tareas automáticamente de la respuesta del agente.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Session).where(
                Session.id == request.session_id,
                Session.is_deleted == False
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Sesión no encontrada.")

    chunks = rag_service.retrieve(request.query, session_id=request.session_id)
    messages = rag_service.build_prompt(request.query, chunks, request.history)

    full_content = []
    sources = [
        {"source": c["source"], "page": c["page"], "score": c["score"]}
        for c in chunks
    ]

    def stream_response():
        for token in rag_service.generate_stream(messages):
            if "__SOURCES__" in token:
                parts = token.split("__SOURCES__")
                full_content.append(parts[0])
                yield parts[0]
            else:
                full_content.append(token)
                yield token
        yield f"\n\n__SOURCES__{json.dumps(sources)}"

    background_tasks.add_task(
        persist_messages,
        request.query,
        full_content,
        sources,
        request.session_id
    )

    return StreamingResponse(stream_response(), media_type="text/plain", background=background_tasks)

async def persist_messages(user_query: str, full_content: list, sources_data: list, session_id: str):
    """Persiste los mensajes y extrae tareas en PostgreSQL."""
    assistant_response = "".join(full_content)

    async with AsyncSessionLocal() as db:
        user_message = Message(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=user_query
        )
        db.add(user_message)

        assistant_message = Message(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="assistant",
            content=assistant_response,
            sources=json.dumps(sources_data)
        )
        db.add(assistant_message)
        await db.commit()

    await extract_and_save_tasks(assistant_response, session_id)


async def extract_and_save_tasks(response_text: str, session_id: str):
    """
    Extrae tareas del texto de respuesta del agente y las guarda en PostgreSQL.
    """
    task_prompt = f"""From the following medical assistant response, extract ONLY the recommended tasks or actions for the healthcare professional.
    Return ONLY a JSON object with this exact format: {{"tasks": ["task1", "task2"]}}
    If there are no clear tasks or next steps, return: {{"tasks": []}}
    Do not include any additional text, explanation or markdown.

    Text:
    {response_text}"""

    try:
        task_response = rag_service.llm_client.chat.completions.create(
            model=rag_service.model,
            messages=[{"role": "user", "content": task_prompt}],
            temperature=0
        )
        task_text = task_response.choices[0].message.content.strip()
        task_data = json.loads(task_text)
        tasks = task_data.get("tasks", [])

        if tasks:
            async with AsyncSessionLocal() as db:
                for task_content in tasks:
                    task = Task(
                        id=str(uuid.uuid4()),
                        session_id=session_id,
                        content=task_content,
                        status="pending"
                    )
                    db.add(task)
                await db.commit()
    except Exception:
        pass


@router.post("/chat/proactive")
async def proactive_intro(request: ProactiveRequest):
    """
    Genera automáticamente un resumen y preguntas sugeridas
    tras subir un documento, sin que el médico haya escrito nada.
    Persiste el mensaje proactivo en PostgreSQL.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Session).where(
                Session.id == request.session_id,
                Session.is_deleted == False
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Sesión no encontrada.")

    intro = rag_service.generate_proactive_intro(request.filename)

    async with AsyncSessionLocal() as db:
        message = Message(
            id=str(uuid.uuid4()),
            session_id=request.session_id,
            role="assistant",
            content=intro
        )
        db.add(message)
        await db.commit()

    return {"intro": intro}