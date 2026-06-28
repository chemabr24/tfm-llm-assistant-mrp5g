from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService
from app.services.rag_service import RAGService
import json

router = APIRouter(prefix="/api", tags=["chat"])

embedding_service = EmbeddingService()
qdrant_service = QdrantService(embedding_dimension=embedding_service.dimension)
rag_service = RAGService(embedding_service, qdrant_service)


class ChatRequest(BaseModel):
    """Modelo de la petición de chat."""
    query: str
    history: list[dict] = []


class ProactiveRequest(BaseModel):
    """Modelo de la petición de introducción proactiva."""
    filename: str


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Recibe una pregunta, recupera chunks relevantes de Qdrant
    y genera una respuesta en streaming usando el LLM.
    """
    chunks = rag_service.retrieve(request.query)
    messages = rag_service.build_prompt(request.query, chunks, request.history)

    def stream_response():
        sources = [
            {"source": c["source"], "page": c["page"], "score": c["score"]}
            for c in chunks
        ]
        for token in rag_service.generate_stream(messages):
            yield token
        yield f"\n\n__SOURCES__{json.dumps(sources)}"

    return StreamingResponse(stream_response(), media_type="text/plain") #Clase FastAPI StreamingResponse para enviar la respuesta token a token al frontend.


@router.post("/chat/proactive")
async def proactive_intro(request: ProactiveRequest):
    """
    Genera automáticamente un resumen y preguntas sugeridas
    tras subir un documento, sin que el médico haya escrito nada.
    """
    intro = rag_service.generate_proactive_intro(request.filename)
    return {"intro": intro}