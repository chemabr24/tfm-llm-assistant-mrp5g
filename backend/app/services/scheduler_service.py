import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from app.models.database import AsyncSessionLocal, User, Session, Task
from app.services.email_service import send_reminder_email

scheduler = AsyncIOScheduler()


async def send_reminders_for_user(user_id: str, email: str):
    """
    Revisa las tareas pendientes del usuario y envía un email recordatorio.
    """
    async with AsyncSessionLocal() as db:
        sessions_result = await db.execute(
            select(Session).where(
                Session.user_id == user_id,
                Session.is_deleted == False
            )
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

    if tasks_by_session:
        await send_reminder_email(tasks_by_session, email)


async def run_scheduled_reminders():
    """
    Recorre todos los usuarios activos y envía recordatorios
    según su preferencia de periodicidad.
    """
    async with AsyncSessionLocal() as db:
        users_result = await db.execute(
            select(User).where(User.is_active == True)
        )
        users = users_result.scalars().all()

    for user in users:
        await send_reminders_for_user(user.id, user.email)


def start_scheduler():
    """
    Inicia el scheduler con dos jobs:
    - Diario: se ejecuta a las 8:00 AM para usuarios con frecuencia diaria
    - Semanal: se ejecuta los lunes a las 8:00 AM para usuarios con frecuencia semanal
    """
    scheduler.add_job(
        run_scheduled_reminders,
        CronTrigger(hour=8, minute=0),
        id="daily_reminders",
        replace_existing=True
    )

    scheduler.start()