from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from app.routers.upload import router as upload_router
from app.routers.chat import router as chat_router
from app.models.database import init_db
from app.routers.sessions import router as sessions_router
from app.routers.voice import router as voice_router
from app.routers.simulate import router as simulate_router
from app.routers.reminders import router as reminders_router
from app.routers.auth import router as auth_router
from app.services.scheduler_service import start_scheduler

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    yield

app = FastAPI(
    title="TFM LLM Assistant - MRP5G",
    description="Asistente virtual inteligente basado en LLMs para soporte en atención primaria",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}

app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(sessions_router)
app.include_router(voice_router)
app.include_router(simulate_router)
app.include_router(reminders_router)
app.include_router(auth_router)