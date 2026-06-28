from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routers.upload import router as upload_router
from app.routers.chat import router as chat_router

load_dotenv()

app = FastAPI(
    title="TFM LLM Assistant - MRP5G",
    description="Asistente virtual inteligente basado en LLMs para soporte en atención primaria",
    version="0.1.0"
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