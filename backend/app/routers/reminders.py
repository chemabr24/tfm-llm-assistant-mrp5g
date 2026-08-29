from fastapi import APIRouter
from sqlalchemy import select
from app.models.database import AsyncSessionLocal, Session, Task
from app.services.email_service import send_reminder_email

router = APIRouter(prefix="/api", tags=["recordatorios"])


@router.post("/reminders/send")
async def send_reminders():
    """
    Recorre todas las sesiones activas, recopila las tareas pendientes
    y envía un email resumen al médico.
    """
    async with AsyncSessionLocal() as db:
        sessions_result = await db.execute(
            select(Session).where(Session.is_deleted == False)
        )
        sessions = sessions_result.scalars().all()

        tasks_by_session = []

        for session in sessions:
            tasks_result = await db.execute(
                select(Task).where(
                    Task.session_id == session.id,
                    Task.status == "pending"
                )
            )
            tasks = tasks_result.scalars().all()

            if tasks:
                tasks_by_session.append({
                    "session_title": session.title,
                    "patient_identifier": session.patient_identifier,
                    "tasks": [t.content for t in tasks]
                })

    if not tasks_by_session:
        return {"mensaje": "No hay tareas pendientes. No se ha enviado ningún email."}

    await send_reminder_email(tasks_by_session)
    return {
        "mensaje": f"Email enviado con tareas pendientes de {len(tasks_by_session)} sesiones."
    }