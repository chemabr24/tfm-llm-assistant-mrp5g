from datetime import datetime
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
                    "tasks": [task.content for task in tasks]
                })

    if tasks_by_session:
        await send_reminder_email(tasks_by_session, email)


def should_send_reminder(user: User, current_datetime: datetime) -> bool:
    """
    Determina si corresponde enviar un recordatorio al usuario
    según la periodicidad configurada en sus preferencias.

    - daily: todos los días.
    - weekly: los lunes.
    """
    preferences = user.preferences or {}
    frequency = preferences.get("notification_frequency", "weekly")

    if frequency == "daily":
        return True

    if frequency == "weekly":
        # Monday = 0
        return current_datetime.weekday() == 0

    # Ante una configuración desconocida, no se envía.
    return False


async def run_scheduled_reminders(force: bool = False):
    """
    Recorre los usuarios activos y envía recordatorios únicamente
    cuando corresponde según su preferencia de periodicidad.
    """
    current_datetime = datetime.now()

    async with AsyncSessionLocal() as db:
        users_result = await db.execute(
            select(User).where(User.is_active == True)
        )
        users = users_result.scalars().all()

    for user in users:
        if force or should_send_reminder(user, current_datetime):
            await send_reminders_for_user(user.id, user.email)


def start_scheduler():
    """
    Inicia el planificador de recordatorios.

    El job se ejecuta todos los días a las 08:00.
    La lógica interna determina qué usuarios reciben el recordatorio:
    - frecuencia diaria: todos los días;
    - frecuencia semanal: únicamente los lunes.
    """
    scheduler.add_job(
        run_scheduled_reminders,
        CronTrigger(hour=8, minute=0),
        id="reminders",
        replace_existing=True
    )

    scheduler.start()