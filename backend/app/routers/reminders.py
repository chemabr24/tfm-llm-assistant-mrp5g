from fastapi import APIRouter
from app.services.scheduler_service import run_scheduled_reminders

router = APIRouter(prefix="/api", tags=["recordatorios"])


@router.post("/reminders/send")
async def send_reminders():
    """
    Envía recordatorios de tareas pendientes a todos los usuarios activos.
    Útil para pruebas manuales; en producción se ejecuta automáticamente
    según la periodicidad configurada en el perfil de cada usuario.
    """
    await run_scheduled_reminders()
    return {"mensaje": "Recordatorios enviados correctamente a todos los usuarios con tareas pendientes."}