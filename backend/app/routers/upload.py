import mimetypes
import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService
from app.models.database import AsyncSessionLocal, Session, Document

router = APIRouter(prefix="/api", tags=["documentos"])

document_service = DocumentService()
embedding_service = EmbeddingService()
qdrant_service = QdrantService(embedding_dimension=embedding_service.dimension)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Query(..., description="ID de la sesión a la que asociar el documento")
):
    """
    Recibe un PDF, lo procesa y almacena sus chunks en Qdrant.
    Asocia el documento a la sesión indicada en PostgreSQL.
    
    Devuelve el número de chunks indexados y el nombre del archivo.
    """
    if not file.filename.endswith(".pdf") and not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF o TXT.")

    # Verificar que la sesión existe y no está eliminada
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Session).where(
                Session.id == session_id,
                Session.is_deleted == False
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Sesión no encontrada.")

    file_bytes = await file.read()

    # Guardar archivo en disco
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    chunks = document_service.process_pdf(file_bytes, filename=file.filename)

    if not chunks:
        raise HTTPException(status_code=422, detail="No se pudo extraer texto del PDF.")

    # Añadir session_id a cada chunk para filtrar por sesión en el retrieval
    for chunk in chunks:
        chunk["session_id"] = session_id

    texts = [chunk["text"] for chunk in chunks]
    embeddings = embedding_service.embed_batch(texts)
    qdrant_service.store_chunks(chunks, embeddings)

    # Guardar el documento en PostgreSQL asociado a la sesión
    async with AsyncSessionLocal() as db:
        document = Document(
            id=str(uuid.uuid4()),
            session_id=session_id,
            filename=file.filename,
            file_path=file_path,
            chunk_count=str(len(chunks))
        )
        db.add(document)
        await db.commit()

    return {
        "filename": file.filename,
        "session_id": session_id,
        "chunks_indexados": len(chunks),
        "mensaje": f"Documento '{file.filename}' indexado correctamente con {len(chunks)} chunks."
    }

@router.get("/documents/{document_id}/file")
async def get_document_file(document_id: str):
    """
    Sirve el archivo de un documento para que pueda abrirse en el navegador.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.is_deleted == False
            )
        )
        document = result.scalar_one_or_none()
        if not document:
            raise HTTPException(status_code=404, detail="Documento no encontrado.")
        if not document.file_path or not os.path.exists(document.file_path):
            raise HTTPException(status_code=404, detail="Archivo no encontrado en el servidor.")

    media_type, _ = mimetypes.guess_type(document.filename)
    media_type = media_type or "application/octet-stream"

    return FileResponse(
        path=document.file_path,
        filename=document.filename,
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename={document.filename}"}
    )