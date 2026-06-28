from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService

router = APIRouter(prefix="/api", tags=["documentos"])

document_service = DocumentService()
embedding_service = EmbeddingService()
qdrant_service = QdrantService(embedding_dimension=embedding_service.dimension)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Recibe un PDF, lo procesa y almacena sus chunks en Qdrant.
    
    Devuelve el número de chunks indexados y el nombre del archivo.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF.")

    file_bytes = await file.read()

    chunks = document_service.process_pdf(file_bytes, filename=file.filename)

    if not chunks:
        raise HTTPException(status_code=422, detail="No se pudo extraer texto del PDF.")

    texts = [chunk["text"] for chunk in chunks]
    embeddings = embedding_service.embed_batch(texts)

    qdrant_service.store_chunks(chunks, embeddings)

    return {
        "filename": file.filename,
        "chunks_indexados": len(chunks),
        "mensaje": f"Documento '{file.filename}' indexado correctamente con {len(chunks)} chunks."
    }