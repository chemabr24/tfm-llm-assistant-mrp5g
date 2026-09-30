"""
Compara la calidad de recuperación de:

1. BAAI/bge-large-en-v1.5
2. intfloat/multilingual-e5-large

No modifica Qdrant ni la aplicación.
Lee los 286 fragmentos de la sesión de evaluación y realiza
la comparación en memoria.

Ejecutar desde backend:

    python -m tests.compare_embeddings
"""

import os
import re
import statistics
import unicodedata

import numpy as np
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer


load_dotenv()

SESSION_ID = "3a0ece8b-1d95-419a-bac5-bba6d0f51186"
COLLECTION_NAME = "medical_documents"

MODELS = {
    "BGE": "BAAI/bge-large-en-v1.5",
    "E5": "intfloat/multilingual-e5-large",
}

TOP_K_VALUES = [1, 3, 5, 8]


# ============================================================
# PREGUNTAS
# ============================================================

TEST_CASES = [
    {
        "id": "Q01",
        "question": "¿A partir de qué valores de presión arterial en consulta se define hipertensión según la guía ESC 2024?",
        "groups": [
            ["140"],
            ["90"],
            ["hipertension"],
        ],
    },
    {
        "id": "Q02",
        "question": "¿Qué intervalo define la nueva categoría de presión arterial elevada en consulta?",
        "groups": [
            ["120-139", "120 139"],
            ["70-89", "70 89"],
            ["pa elevada", "presion arterial elevada"],
        ],
    },
    {
        "id": "Q03",
        "question": "¿Cuál es el umbral de hipertensión cuando la presión arterial se mide en el domicilio mediante AMPA?",
        "groups": [
            ["135"],
            ["85"],
            ["ampa", "domicilio"],
        ],
    },
    {
        "id": "Q04",
        "question": "¿Qué valores de MAPA de 24 horas confirman hipertensión?",
        "groups": [
            ["130"],
            ["80"],
            ["24 h", "24 horas"],
        ],
    },
    {
        "id": "Q05",
        "question": "¿Cuántas mediciones de presión arterial deben realizarse en consulta y cuál se registra como resultado?",
        "groups": [
            ["tres mediciones", "3 mediciones"],
            ["1-2 minutos", "1 2 minutos"],
            ["media de las dos ultimas", "promedio de las ultimas 2"],
        ],
    },
    {
        "id": "Q06",
        "question": "¿Cómo define la guía la hipotensión ortostática?",
        "groups": [
            ["20/10", "20 10"],
            ["1 y/o 3 minutos", "1 y 3 minutos", "1 o 3 minutos"],
            ["hipotension ortostatica"],
        ],
    },
    {
        "id": "Q07",
        "question": "En un paciente con 145/95 mmHg en consulta, ¿cómo recomienda la guía confirmar el diagnóstico de hipertensión?",
        "groups": [
            ["mapa", "ampa"],
            ["fuera de la consulta", "fuera de consulta"],
            ["140-159", "140 159"],
        ],
    },
    {
        "id": "Q08",
        "question": "¿Con qué frecuencia se debe considerar el cribado de presión arterial en adultos menores de 40 años y en mayores de 40?",
        "groups": [
            ["3 años"],
            ["40 años"],
            ["anual", "una vez al año", "cada año"],
        ],
    },
    {
        "id": "Q09",
        "question": "¿Cuál es el objetivo recomendado de presión arterial sistólica para la mayoría de pacientes tratados, si se tolera bien?",
        "groups": [
            ["120-129", "120 129"],
            ["tolera"],
        ],
    },
    {
        "id": "Q10",
        "question": "¿Qué clases de fármacos se recomiendan como tratamientos antihipertensivos de primera línea?",
        "groups": [
            ["ieca", "inhibidores de la eca"],
            ["ara"],
            ["bcc", "bloqueadores de los canales del calcio"],
            ["diuret"],
        ],
    },
    {
        "id": "Q11",
        "question": "¿Qué cantidad de ejercicio aeróbico semanal recomienda la guía para reducir la presión arterial y el riesgo cardiovascular?",
        "groups": [
            ["150"],
            ["75"],
            ["ejercicio", "actividad fisica"],
        ],
    },
    {
        "id": "Q12",
        "question": "¿Qué recomienda la guía respecto al consumo de alcohol?",
        "groups": [
            ["14"],
            ["8"],
            ["alcohol"],
        ],
    },
    {
        "id": "Q13",
        "question": "Una vez controlada y estable la presión arterial con tratamiento, ¿con qué frecuencia mínima debe considerarse el seguimiento?",
        "groups": [
            ["controlada"],
            ["estable"],
            ["una vez al año", "1 vez al año", "anual"],
        ],
    },
    {
        "id": "Q14",
        "question": "¿Qué umbral de SCORE2 o SCORE2-OP considera la guía como riesgo cardiovascular suficientemente alto en una persona con presión arterial elevada?",
        "groups": [
            ["score2"],
            ["10 %", "10%"],
            ["riesgo"],
        ],
    },
    {
        "id": "Q15",
        "question": "¿Qué tratamiento recomienda la guía añadir en la hipertensión resistente no controlada pese al tratamiento de primera línea?",
        "groups": [
            ["espironolactona"],
            ["resistente"],
        ],
    },
    {
        "id": "Q16",
        "question": "¿Qué cifras de presión arterial pueden indicar una emergencia hipertensiva durante el embarazo?",
        "groups": [
            ["160"],
            ["110"],
            ["embarazo", "embarazada"],
        ],
    },
    {
        "id": "Q17",
        "question": "En pacientes con hipertensión y enfermedad renal crónica con TFGe superior a 20 ml/min/1,73 m2, ¿qué grupo farmacológico recomienda la guía para mejorar resultados?",
        "groups": [
            ["sglt2"],
            ["20"],
            ["tfge"],
        ],
    },
    {
        "id": "Q18",
        "question": "¿Qué diferencia de presión arterial sistólica entre ambos brazos se considera relevante y qué debe hacerse después?",
        "groups": [
            ["10 mmhg"],
            ["ambos brazos", "entre brazos"],
            ["mas elevados", "más elevados", "brazo con"],
        ],
    },
    {
        "id": "Q19",
        "question": "¿Cuánto tiempo debe permanecer el paciente en reposo antes de medir la presión arterial en consulta?",
        "groups": [
            ["5 minutos"],
            ["sentado"],
        ],
    },
    {
        "id": "Q20",
        "question": "¿Durante cuántos días recomienda la guía realizar la automedida de presión arterial en domicilio?",
        "groups": [
            ["3 dias", "3 días"],
            ["7 dias", "7 días"],
            ["ampa", "domicilio"],
        ],
    },
]


# ============================================================
# UTILIDADES
# ============================================================

def normalize(text: str) -> str:
    text = text.lower()

    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        c for c in text
        if not unicodedata.combining(c)
    )

    text = text.replace("–", "-")
    text = text.replace("—", "-")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def is_relevant(text: str, groups: list[list[str]]) -> bool:
    """
    Cada grupo representa una condición obligatoria.
    Dentro de cada grupo basta con encontrar una alternativa.
    """

    normalized = normalize(text)

    for group in groups:
        alternatives = [
            normalize(value)
            for value in group
        ]

        if not any(
            alternative in normalized
            for alternative in alternatives
        ):
            return False

    return True


def cosine_scores(query_vector, document_matrix):
    return document_matrix @ query_vector


def reciprocal_rank(ranked_indexes, chunks, groups):
    for rank, index in enumerate(ranked_indexes, start=1):
        if is_relevant(
            chunks[index]["text"],
            groups
        ):
            return 1.0 / rank, rank

    return 0.0, None


def hit_at_k(
    ranked_indexes,
    chunks,
    groups,
    k,
):
    for index in ranked_indexes[:k]:
        if is_relevant(
            chunks[index]["text"],
            groups
        ):
            return 1

    return 0


# ============================================================
# QDRANT
# ============================================================

def load_session_chunks():
    qdrant_url = os.getenv(
        "QDRANT_URL",
        "http://localhost:6333"
    )

    client = QdrantClient(
        url=qdrant_url
    )

    session_filter = Filter(
        must=[
            FieldCondition(
                key="session_id",
                match=MatchValue(
                    value=SESSION_ID
                )
            )
        ]
    )

    chunks = []
    offset = None

    while True:
        points, next_offset = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=session_filter,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        for point in points:
            payload = point.payload

            chunks.append(
                {
                    "id": str(point.id),
                    "text": payload["text"],
                    "page": payload["page"],
                    "source": payload["source"],
                }
            )

        if next_offset is None:
            break

        offset = next_offset

    return chunks


# ============================================================
# EVALUACIÓN
# ============================================================

def evaluate_model(
    label,
    model_name,
    chunks,
):
    print("\n" + "=" * 80)
    print(f"MODELO: {label}")
    print(model_name)
    print("=" * 80)

    model = SentenceTransformer(
        model_name
    )

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    # --------------------------------------------------------
    # EMBEDDINGS DE DOCUMENTOS
    # --------------------------------------------------------

    if label == "E5":
        document_inputs = [
            f"passage: {text}"
            for text in texts
        ]
    else:
        document_inputs = texts

    print(
        f"\nGenerando embeddings de "
        f"{len(document_inputs)} fragmentos..."
    )

    document_embeddings = model.encode(
        document_inputs,
        normalize_embeddings=True,
        batch_size=16,
        show_progress_bar=True,
    )

    document_embeddings = np.asarray(
        document_embeddings
    )

    metrics = {
        k: []
        for k in TOP_K_VALUES
    }

    reciprocal_ranks = []
    ranks = []

    # --------------------------------------------------------
    # CONSULTAS
    # --------------------------------------------------------

    for case in TEST_CASES:
        question = case["question"]

        if label == "E5":
            query_input = (
                f"query: {question}"
            )
        else:
            query_input = question

        query_embedding = model.encode(
            query_input,
            normalize_embeddings=True,
        )

        query_embedding = np.asarray(
            query_embedding
        )

        scores = cosine_scores(
            query_embedding,
            document_embeddings
        )

        ranked_indexes = np.argsort(
            scores
        )[::-1]

        rr, first_rank = reciprocal_rank(
            ranked_indexes,
            chunks,
            case["groups"],
        )

        reciprocal_ranks.append(rr)

        if first_rank is not None:
            ranks.append(first_rank)

        hits = {}

        for k in TOP_K_VALUES:
            hit = hit_at_k(
                ranked_indexes,
                chunks,
                case["groups"],
                k,
            )

            metrics[k].append(hit)
            hits[k] = hit

        top_pages = [
            chunks[index]["page"]
            for index in ranked_indexes[:8]
        ]

        print(
            f"[{case['id']}] "
            f"rank={first_rank or '-':>2} | "
            f"H@1={hits[1]} "
            f"H@3={hits[3]} "
            f"H@5={hits[5]} "
            f"H@8={hits[8]} | "
            f"pages={top_pages}"
        )

    # --------------------------------------------------------
    # RESUMEN
    # --------------------------------------------------------

    result = {
        "model": label,
        "hit_at_1": statistics.mean(
            metrics[1]
        ),
        "hit_at_3": statistics.mean(
            metrics[3]
        ),
        "hit_at_5": statistics.mean(
            metrics[5]
        ),
        "hit_at_8": statistics.mean(
            metrics[8]
        ),
        "mrr": statistics.mean(
            reciprocal_ranks
        ),
        "mean_first_relevant_rank": (
            statistics.mean(ranks)
            if ranks
            else None
        ),
    }

    print("\n--- RESULTADO ---")

    print(
        f"Hit@1: "
        f"{result['hit_at_1'] * 100:.1f}%"
    )

    print(
        f"Hit@3: "
        f"{result['hit_at_3'] * 100:.1f}%"
    )

    print(
        f"Hit@5: "
        f"{result['hit_at_5'] * 100:.1f}%"
    )

    print(
        f"Hit@8: "
        f"{result['hit_at_8'] * 100:.1f}%"
    )

    print(
        f"MRR: "
        f"{result['mrr']:.3f}"
    )

    if result["mean_first_relevant_rank"]:
        print(
            "Rank medio primera evidencia: "
            f"{result['mean_first_relevant_rank']:.2f}"
        )

    return result


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 80)
    print("COMPARACIÓN DE MODELOS DE EMBEDDINGS")
    print("=" * 80)

    print("\nCargando fragmentos desde Qdrant...")

    chunks = load_session_chunks()

    print(
        f"Fragmentos encontrados: "
        f"{len(chunks)}"
    )

    if not chunks:
        raise RuntimeError(
            "No se encontraron fragmentos para "
            "la sesión indicada."
        )

    results = []

    for label, model_name in MODELS.items():
        result = evaluate_model(
            label,
            model_name,
            chunks,
        )

        results.append(result)

    print("\n" + "=" * 80)
    print("COMPARACIÓN FINAL")
    print("=" * 80)

    print(
        f"{'Modelo':<10} "
        f"{'H@1':>8} "
        f"{'H@3':>8} "
        f"{'H@5':>8} "
        f"{'H@8':>8} "
        f"{'MRR':>8}"
    )

    for result in results:
        print(
            f"{result['model']:<10} "
            f"{result['hit_at_1']*100:>7.1f}% "
            f"{result['hit_at_3']*100:>7.1f}% "
            f"{result['hit_at_5']*100:>7.1f}% "
            f"{result['hit_at_8']*100:>7.1f}% "
            f"{result['mrr']:>8.3f}"
        )

    print("\nFin de la comparación.")


if __name__ == "__main__":
    main()