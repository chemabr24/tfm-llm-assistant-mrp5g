import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from app.models.database import AsyncSessionLocal, User, MagicLink
from app.services.email_service import send_magic_link_email

router = APIRouter(prefix="/api/auth", tags=["autenticación"])


class MagicLinkRequest(BaseModel):
    """Modelo para solicitar un magic link."""
    email: str


class VerifyTokenRequest(BaseModel):
    """Modelo para verificar un magic link."""
    token: str


@router.post("/magic-link")
async def request_magic_link(request: MagicLinkRequest):
    """
    El médico introduce su email y recibe un enlace único de acceso.
    Si el usuario no existe, se crea automáticamente.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == request.email)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                id=str(uuid.uuid4()),
                email=request.email,
                preferences={"notification_frequency": "weekly"}
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Crear magic link con token único que caduca en 24h
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=24)

        magic_link = MagicLink(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        db.add(magic_link)
        await db.commit()

    await send_magic_link_email(request.email, token)

    return {"mensaje": "Enlace de acceso enviado a tu correo."}


@router.post("/verify")
async def verify_magic_link(request: VerifyTokenRequest):
    """
    Verifica el token del magic link y devuelve los datos del usuario.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(MagicLink).where(
                MagicLink.token == request.token,
                MagicLink.used == False
            )
        )
        magic_link = result.scalar_one_or_none()

        if not magic_link:
            raise HTTPException(status_code=401, detail="Enlace no válido.")

        if magic_link.expires_at < datetime.utcnow():
            raise HTTPException(status_code=401, detail="Enlace caducado.")

        # Marcar el magic link como usado
        magic_link.used = True
        await db.commit()

        # Obtener usuario
        user_result = await db.execute(
            select(User).where(User.id == magic_link.user_id)
        )
        user = user_result.scalar_one()

    return {
        "user_id": user.id,
        "email": user.email,
        "preferences": user.preferences
    }


@router.get("/users/{user_id}/profile")
async def get_profile(user_id: str):
    """Obtiene el perfil del usuario."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    return {
        "user_id": user.id,
        "email": user.email,
        "preferences": user.preferences
    }


@router.patch("/users/{user_id}/profile")
async def update_profile(user_id: str, preferences: dict):
    """Actualiza las preferencias del perfil del usuario."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")

        user.preferences = preferences
        await db.commit()

    return {"mensaje": "Perfil actualizado correctamente."}