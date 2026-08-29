import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import load_dotenv

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

async def send_reminder_email(tasks_by_session: list[dict]):
    """
    Envía un email resumen con las tareas pendientes agrupadas por sesión.
    
    tasks_by_session es una lista de diccionarios con:
    - session_title: nombre de la sesión
    - patient_identifier: identificador del paciente
    - tasks: lista de tareas pendientes
    """
    if not tasks_by_session:
        return

    recipient = os.getenv("REMINDER_EMAIL")

    # Construir el cuerpo del email en HTML
    html_content = """
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #1976d2;">Asistente Médico MRP-5G — Recordatorio de tareas pendientes</h2>
        <p>Tienes las siguientes tareas pendientes en tus sesiones activas:</p>
        <hr>
    """

    for session in tasks_by_session:
        html_content += f"""
        <div style="margin-bottom: 24px;">
            <h3 style="color: #1976d2; margin-bottom: 4px;">{session['session_title']}</h3>
        """
        if session.get('patient_identifier'):
            html_content += f"<p style='color: #666; margin-top: 0;'>Paciente: {session['patient_identifier']}</p>"

        html_content += "<ul>"
        for task in session['tasks']:
            html_content += f"<li style='margin-bottom: 8px;'>{task}</li>"
        html_content += "</ul></div><hr>"

    html_content += """
        <p style="color: #888; font-size: 12px;">
            Este email ha sido generado automáticamente por el Asistente Médico MRP-5G.
        </p>
    </body>
    </html>
    """

    message = MessageSchema(
        subject="Asistente Médico MRP-5G — Tareas pendientes",
        recipients=[recipient],
        body=html_content,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)