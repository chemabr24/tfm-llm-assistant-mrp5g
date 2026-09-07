import os
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService
from app.services.rag_service import RAGService
from app.models.database import AsyncSessionLocal, Session, Document
from sqlalchemy import select

router = APIRouter(prefix="/api", tags=["simulador"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

embedding_service = EmbeddingService()
qdrant_service = QdrantService(embedding_dimension=embedding_service.dimension)
rag_service = RAGService(embedding_service, qdrant_service)


class SimulateRequest(BaseModel):
    """Modelo para la petición de simulación de caso clínico."""
    description: str
    session_id: str


@router.post("/simulate")
async def simulate_case(request: SimulateRequest):
    """
    Genera un caso clínico ficticio completo a partir de una descripción breve
    y lo indexa en Qdrant asociado a la sesión indicada.
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

    prompt = f"""Eres un médico experto en atención primaria. Genera un caso clínico ficticio completo y realista en español basado en la siguiente descripción:

"{request.description}"

El caso clínico debe incluir las siguientes secciones:
1. Datos del paciente (edad, sexo, antecedentes relevantes - todos ficticios)
2. Motivo de consulta
3. Anamnesis
4. Exploración física
5. Pruebas complementarias solicitadas
6. Diagnóstico diferencial
7. Diagnóstico principal
8. Plan terapéutico
9. Seguimiento recomendado

Genera el caso clínico de forma detallada y realista, como si fuera un informe médico real. Todos los datos son completamente ficticios."""
    filename = f"caso_simulado_{uuid.uuid4().hex[:8]}.txt"
    
    try:
        response = rag_service.llm_client.chat.completions.create(
            model=rag_service.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        case_text = response.choices[0].message.content.strip()
        file_path = os.path.join(UPLOAD_DIR, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(case_text)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al generar el caso clínico: {str(e)}")

    
    chunks = []
    words = case_text.split()
    chunk_size = 512
    overlap = 50
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append({
            "id": str(uuid.uuid4()),
            "text": " ".join(chunk_words),
            "page": 1,
            "source": filename,
            "session_id": request.session_id
        })
        if end >= len(words):
            break
        start += chunk_size - overlap

    texts = [c["text"] for c in chunks]
    embeddings = embedding_service.embed_batch(texts)
    qdrant_service.store_chunks(chunks, embeddings)

    async with AsyncSessionLocal() as db:
        document = Document(
            id=str(uuid.uuid4()),
            session_id=request.session_id,
            filename=filename,
            file_path=file_path,
            chunk_count=str(len(chunks))
        )
        db.add(document)
        await db.commit()

    return {
        "filename": filename,
        "session_id": request.session_id,
        "chunks_indexados": len(chunks),
        "caso_clinico": case_text,
        "mensaje": "Caso clínico simulado generado e indexado correctamente."
    }