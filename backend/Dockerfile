FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir fastapi uvicorn python-multipart python-dotenv openai qdrant-client sentence-transformers pypdf sqlalchemy asyncpg psycopg2-binary alembic fastapi-mail openai-whisper
RUN pip install --no-cache-dir APScheduler==3.11.3 greenlet==3.5.3
COPY . .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]