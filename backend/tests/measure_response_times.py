"""
Script para medir el tiempo de respuesta del endpoint /api/chat
sobre un conjunto de preguntas reales relacionadas con el documento
de hipertensión arterial indexado.

Requiere que el backend esté corriendo, la VPN conectada, y que
exista una sesión con el documento hta.pdf ya indexado (usar el
session_id de esa sesión en SESSION_ID).
"""
import httpx
import time

BASE_URL = "http://localhost:8000/api"
SESSION_ID = "1ba98b01-a7ad-47f6-8903-91916f6627b4"  # sesión con hta.pdf indexado

PREGUNTAS = [
    "¿Cuáles son los valores que definen la hipertensión grado 1?",
    "¿Qué tratamiento se recomienda para la hipertensión grado 2?",
    "¿Cuándo se considera una emergencia hipertensiva?",
    "¿Qué cambios en el estilo de vida se recomiendan para la hipertensión normal-alta?",
    "¿Con qué frecuencia hay que revisar a un paciente con hipertensión grado 1?",
]

resultados = []

with httpx.Client(timeout=60.0) as client:
    for pregunta in PREGUNTAS:
        inicio = time.perf_counter()
        response = client.post(f"{BASE_URL}/chat", json={
            "query": pregunta,
            "session_id": SESSION_ID,
            "history": []
        })
        fin = time.perf_counter()

        duracion = fin - inicio
        exito = response.status_code == 200 and len(response.text.strip()) > 0
        resultados.append((pregunta, duracion, exito))

        print(f"[{'OK' if exito else 'FALLO'}] {duracion:.2f}s — {pregunta}")

tiempos = [r[1] for r in resultados if r[2]]
fallos = sum(1 for r in resultados if not r[2])

print("\n--- Resumen ---")
print(f"Preguntas totales: {len(resultados)}")
print(f"Fallos: {fallos}")
if tiempos:
    print(f"Tiempo medio: {sum(tiempos)/len(tiempos):.2f}s")
    print(f"Tiempo mínimo: {min(tiempos):.2f}s")
    print(f"Tiempo máximo: {max(tiempos):.2f}s")