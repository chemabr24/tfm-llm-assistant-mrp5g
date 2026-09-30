# Asistente Virtual Médico MRP-5G

Trabajo Fin de Máster desarrollado en la Universidad de Castilla-La Mancha en el contexto del proyecto **MRP-5G**.

El proyecto implementa un asistente virtual orientado al apoyo del personal de atención primaria mediante Grandes Modelos de Lenguaje (LLMs), generación aumentada mediante recuperación (RAG), gestión contextual de conversaciones y una interfaz de realidad mixta para Meta Quest 3.

> **Nota:** el sistema desarrollado es un prototipo académico y experimental. No constituye un producto sanitario ni está destinado a realizar diagnósticos o prescripciones de forma autónoma.

---

## Funcionalidades principales

El sistema incorpora, entre otras, las siguientes funcionalidades:

- Autenticación mediante enlaces temporales (*magic links*).
- Gestión de usuarios y sesiones.
- Historial persistente de conversaciones.
- Asociación de documentos a sesiones.
- Procesamiento e indexación de documentos PDF y TXT.
- Recuperación semántica mediante embeddings y Qdrant.
- Generación de respuestas mediante un LLM autoalojado.
- Presentación de las fuentes documentales utilizadas en las respuestas.
- Entrada de consultas mediante texto o voz.
- Transcripción de audio mediante Whisper.
- Generación de preguntas sugeridas.
- Extracción automática de tareas a partir de las conversaciones.
- Gestión de tareas pendientes, completadas y archivadas.
- Recordatorios por correo electrónico con periodicidad configurable.
- Generación y consulta de casos clínicos simulados.
- Aplicación de realidad mixta para Meta Quest 3.
- Navegación mediante un árbol de decisión clínico progresivo.

---

## Arquitectura

La solución se divide en varios componentes principales:

```text
                         ┌──────────────────────┐
                         │      LLM UCLM        │
                         │    gpt-oss:20b       │
                         └──────────▲───────────┘
                                    │
                                    │ API
                                    │
┌────────────────┐          ┌───────┴────────┐          ┌──────────────┐
│ Angular Web    │◄────────►│    FastAPI     │◄────────►│ PostgreSQL   │
│                │   HTTP   │    Backend     │          │              │
└────────────────┘          │                │          └──────────────┘
                            │                │
┌────────────────┐          │                │          ┌──────────────┐
│ Meta Quest 3   │◄────────►│                │◄────────►│   Qdrant     │
│ Unity / MR     │   HTTP   └────────────────┘          │              │
└────────────────┘                                      └──────────────┘