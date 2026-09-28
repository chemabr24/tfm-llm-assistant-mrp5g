from fastapi import APIRouter
from app.services.scheduler_service import run_scheduled_reminders

router = APIRouter(prefix="/api", tags=["recordatorios"])


@router.post("/reminders/send")
async def send_reminders():
    """
    Fuerza el envío de recordatorios a todos los usuarios activos
    que tengan tareas pendientes, independientemente de su
    periodicidad configurada.

    Endpoint destinado a pruebas manuales.
    """
    await run_scheduled_reminders(force=True)

    return {
        "mensaje": "Recordatorios procesados correctamente."
    }