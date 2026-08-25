import uuid
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from app.models.database import AsyncSessionLocal, Session, Message, Task, Document

router = APIRouter(prefix="/api/sessions", tags=["sesiones"])


class CreateSessionRequest(BaseModel):
    """Modelo para crear una sesión."""
    title: str
    patient_identifier: str | None = None


class UpdateTaskRequest(BaseModel):
    """Modelo para actualizar el estado de una tarea."""
    status: str


# ─── SESIONES ────────────────────────────────────────────────────────────────

@router.post("")
async def create_session(request: CreateSessionRequest):
    """Crea una nueva sesión médica."""
    async with AsyncSessionLocal() as db:
        session = Session(
            id=str(uuid.uuid4()),
            title=request.title,
            patient_identifier=request.patient_identifier
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return {
            "id": session.id,
            "title": session.title,
            "patient_identifier": session.patient_identifier,
            "created_at": session.created_at
        }


@router.get("")
async def list_sessions():
    """Lista todas las sesiones activas ordenadas por fecha de creación."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Session)
            .where(Session.is_deleted == False)
            .order_by(Session.created_at.desc())
        )
        sessions = result.scalars().all()
        return [
            {
                "id": s.id,
                "title": s.title,
                "patient_identifier": s.patient_identifier,
                "created_at": s.created_at,
                "updated_at": s.updated_at
            }
            for s in sessions
        ]


@router.get("/{session_id}")
async def get_session(session_id: str):
    """Obtiene una sesión con sus mensajes, tareas y documentos."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Session).where(
                Session.id == session_id,
                Session.is_deleted == False
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")

        messages_result = await db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.sequence.asc())
        )
        messages = messages_result.scalars().all()

        tasks_result = await db.execute(
            select(Task)
            .where(Task.session_id == session_id, Task.status == "pending")
            .order_by(Task.created_at.asc())
        )
        tasks = tasks_result.scalars().all()

        documents_result = await db.execute(
            select(Document)
            .where(Document.session_id == session_id, Document.is_deleted == False)
            .order_by(Document.created_at.asc())
        )
        documents = documents_result.scalars().all()

        return {
            "id": session.id,
            "title": session.title,
            "patient_identifier": session.patient_identifier,
            "created_at": session.created_at,
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "sources": json.loads(m.sources) if m.sources else [],
                    "created_at": m.created_at
                }
                for m in messages
            ],
            "tasks": [
                {
                    "id": t.id,
                    "content": t.content,
                    "status": t.status,
                    "created_at": t.created_at
                }
                for t in tasks
            ],
            "documents": [
                {
                    "id": d.id,
                    "filename": d.filename,
                    "chunk_count": d.chunk_count,
                    "created_at": d.created_at
                }
                for d in documents
            ]
        }


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Soft delete de una sesión."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Session).where(
                Session.id == session_id,
                Session.is_deleted == False
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")

        session.is_deleted = True
        await db.commit()
        return {"mensaje": "Sesión archivada correctamente"}


# ─── TAREAS ──────────────────────────────────────────────────────────────────

@router.patch("/tasks/{task_id}")
async def update_task(task_id: str, request: UpdateTaskRequest):
    """Actualiza el estado de una tarea (completed o archived)."""
    if request.status not in ["completed", "archived"]:
        raise HTTPException(status_code=400, detail="Estado no válido. Usa 'completed' o 'archived'")

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Task).where(Task.id == task_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        task.status = request.status
        await db.commit()
        return {"mensaje": f"Tarea marcada como {request.status}"}