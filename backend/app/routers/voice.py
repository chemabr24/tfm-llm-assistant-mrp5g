import tempfile
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
import whisper

router = APIRouter(prefix="/api", tags=["voz"])

# Cargamos el modelo de Whisper una sola vez al arrancar
model = whisper.load_model("base")


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Recibe un archivo de audio y lo transcribe usando Whisper.
    Devuelve el texto transcrito.
    """
    allowed_types = ["audio/webm", "audio/wav", "audio/mp4", "audio/mpeg", "audio/ogg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Formato de audio no soportado.")

    audio_bytes = await file.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        result = model.transcribe(tmp_path, language="es")
        return {"text": result["text"].strip()}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al transcribir: {str(e)}")
    finally:
        os.unlink(tmp_path)