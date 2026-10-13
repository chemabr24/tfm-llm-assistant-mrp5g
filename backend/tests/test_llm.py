"""
Script de aislamiento para reproducir el bug de respuestas cortadas/vacías
del LLM sin pasar por el pipeline propio (FastAPI, RAG, etc.).

Llama directamente al cliente OpenAI apuntando al servidor gpt-oss:20b de
la UCLM, en modo streaming, con las mismas preguntas que causaron el corte
en producción. Si el corte se reproduce aquí también, el problema es del
servidor LLM y no del código propio.
"""
import os
import sys
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=f"{os.getenv('LLM_API_URL')}/api"
)
MODEL = os.getenv("LLM_MODEL", "gpt-oss:20b")

# Preguntas de prueba: incluye la que causó el corte original
# ("corresponden a la **" justo antes de cortarse)
QUESTIONS = [
    "y sintomas para valores entre 140 y 159mmHg?",
    "¿Cuál es el tratamiento de primera línea para la hipertensión arterial grado 1?",
    "¿Qué pruebas complementarias se recomiendan en un paciente con HTA de nuevo diagnóstico?",
    "Explica el plan terapéutico completo para hipertensión esencial con obesidad asociada.",
    "¿Cuándo se considera hipertensión resistente y qué se hace en ese caso?",
]

SYSTEM_PROMPT = """Eres un asistente virtual inteligente especializado en atención primaria,
integrado en el sistema MRP-5G. Tu rol es ayudar al personal sanitario respondiendo consultas
basadas en la documentación médica disponible.

INSTRUCCIONES:
- Responde siempre en español.
- Basa tus respuestas ÚNICAMENTE en la documentación proporcionada.
- Cita siempre la fuente indicando el documento y la página.
- Si la información no está en la documentación, indícalo explícitamente.
- Sé proactivo: al final de cada respuesta sugiere una acción siguiente o una pregunta relacionada relevante.
- NUNCA diagnostiques ni prescribas de forma autónoma.
- NUNCA incluyas preguntas sugeridas dentro del texto de tu respuesta.

DOCUMENTACIÓN DISPONIBLE:
(sin contexto RAG en esta prueba de aislamiento — solo se evalúa si el LLM corta la generación)"""


def looks_truncated(text: str) -> bool:
    """Heurística simple: si termina a mitad de una marca de markdown sin cerrar,
    o termina sin puntuación final, probablemente se cortó a media frase."""
    if not text:
        return True
    stripped = text.rstrip()
    if stripped.count("**") % 2 != 0:
        return True
    if stripped and stripped[-1] not in ".!?:\"”)":
        return True
    return False


def run_test(n_repeats: int = 3):
    results = []
    for i, question in enumerate(QUESTIONS, start=1):
        for attempt in range(1, n_repeats + 1):
            print(f"\n[{i}/{len(QUESTIONS)}] Intento {attempt}/{n_repeats}: {question}")
            start = time.time()
            full_text = ""
            error = None
            try:
                stream = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": question},
                    ],
                    stream=True,
                    temperature=0.3,
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        full_text += delta.content
            except Exception as e:
                error = str(e)

            elapsed = time.time() - start
            truncated = looks_truncated(full_text) if not error else None

            results.append({
                "question": question,
                "attempt": attempt,
                "elapsed": round(elapsed, 2),
                "chars": len(full_text),
                "truncated": truncated,
                "error": error,
                "tail": full_text[-80:] if full_text else "",
            })

            if error:
                print(f"  ERROR: {error}")
            else:
                print(f"  {elapsed:.2f}s | {len(full_text)} chars | truncado={truncated}")
                print(f"  Final: ...{full_text[-80:]!r}")

    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    n_ok = sum(1 for r in results if r["error"] is None and not r["truncated"])
    n_truncated = sum(1 for r in results if r["error"] is None and r["truncated"])
    n_error = sum(1 for r in results if r["error"] is not None)
    print(f"Total: {len(results)} | OK: {n_ok} | Truncados: {n_truncated} | Errores: {n_error}")

    for r in results:
        if r["error"] or r["truncated"]:
            print(f"\n- Pregunta: {r['question']} (intento {r['attempt']})")
            print(f"  Error: {r['error']}")
            print(f"  Truncado: {r['truncated']} | Final: {r['tail']!r}")

    return results


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    run_test(n_repeats=n)