"""
Benchmark final de evaluación del núcleo RAG del TFM MRP-5G.

Ejecutar desde la carpeta backend:

    python -m tests.evaluate_rag_tfm

Requisitos:
- Backend arrancado en http://localhost:8000
- Qdrant disponible
- VPN conectada para acceder al LLM
- La sesión indicada en SESSION_ID debe contener únicamente
  GPC_ESC_2024_PA_elevada_e_hipertension.pdf
"""

import csv
import json
import math
import re
import statistics
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import httpx

from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService
from app.services.rag_service import RAGService


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_URL = "http://localhost:8000/api"

SESSION_ID = "4fc0b7b8-6693-4d09-bbb4-ab9674e10220"

TOP_K = 5
HTTP_TIMEOUT = 120.0
RUN_END_TO_END = False

OUTPUT_DIR = Path("tests/results_tfm")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# DATASET
# ============================================================

@dataclass
class EvalCase:
    id: str
    category: str
    question: str
    expected_fact: str
    evidence_groups: list[list[str]]


ANSWERABLE_CASES = [
    EvalCase(
        "Q01", "clasificacion",
        "¿A partir de qué valores de presión arterial en consulta se define hipertensión según la guía ESC 2024?",
        "Hipertensión: PAS >=140 mmHg o PAD >=90 mmHg en consulta.",
        [["140"], ["90"], ["hipertension"]],
    ),
    EvalCase(
        "Q02", "clasificacion",
        "¿Qué intervalo define la nueva categoría de presión arterial elevada en consulta?",
        "PA elevada: PAS 120-139 mmHg o PAD 70-89 mmHg.",
        [["120-139", "120 139"], ["70-89", "70 89"], ["pa elevada", "presion arterial elevada"]],
    ),
    EvalCase(
        "Q03", "medicion",
        "¿Cuál es el umbral de hipertensión cuando la presión arterial se mide en el domicilio mediante AMPA?",
        "AMPA media >=135/85 mmHg.",
        [["135"], ["85"], ["ampa", "domicilio"]],
    ),
    EvalCase(
        "Q04", "medicion",
        "¿Qué valores de MAPA de 24 horas confirman hipertensión?",
        "MAPA de 24 h >=130/80 mmHg.",
        [["130"], ["80"], ["24 h", "24 horas"]],
    ),
    EvalCase(
        "Q05", "medicion",
        "¿Cuántas mediciones de presión arterial deben realizarse en consulta y cuál se registra como resultado?",
        "Tres mediciones separadas 1-2 minutos; registrar la media de las dos últimas.",
        [
            ["tres mediciones", "3 mediciones", "tres lecturas", "3 lecturas"],
            ["1-2 minutos", "1 2 minutos"],
            ["media de las dos ultimas", "promedio de las dos ultimas", "media de las ultimas dos"],
        ],
    ),
    EvalCase(
        "Q06", "medicion",
        "¿Cómo define la guía la hipotensión ortostática?",
        "Descenso >=20 mmHg PAS y/o >=10 mmHg PAD tras 1 y/o 3 min de bipedestación.",
        [["20"], ["10"], ["hipotension ortostatica"], ["1", "3"]],
    ),
    EvalCase(
        "Q07", "diagnostico",
        "En un paciente con 145/95 mmHg en consulta, ¿cómo recomienda la guía confirmar el diagnóstico de hipertensión?",
        "Confirmar preferentemente con medición fuera de consulta mediante MAPA o AMPA.",
        [["mapa", "ampa"], ["fuera de la consulta", "fuera de consulta"]],
    ),
    EvalCase(
        "Q08", "cribado",
        "¿Con qué frecuencia se debe considerar el cribado de presión arterial en adultos menores de 40 años y en mayores de 40?",
        "Al menos cada 3 años en <40 y al menos una vez al año en >=40.",
        [["3 años"], ["40 años"], ["anual", "una vez al año", "cada año"]],
    ),
    EvalCase(
        "Q09", "tratamiento",
        "¿Cuál es el objetivo recomendado de presión arterial sistólica para la mayoría de pacientes tratados, si se tolera bien?",
        "PAS objetivo 120-129 mmHg si se tolera.",
        [["120-129", "120 129"], ["tolera"]],
    ),
    EvalCase(
        "Q10", "tratamiento",
        "¿Qué clases de fármacos se recomiendan como tratamientos antihipertensivos de primera línea?",
        "IECA, ARA, BCC dihidropiridínicos y diuréticos tiazídicos o similares.",
        [
            ["ieca", "inhibidores de la eca"],
            ["ara"],
            ["bcc", "bloqueadores de los canales del calcio"],
            ["diuret"],
        ],
    ),
    EvalCase(
        "Q11", "estilo_vida",
        "¿Qué cantidad de ejercicio aeróbico semanal recomienda la guía para reducir la presión arterial y el riesgo cardiovascular?",
        ">=150 min/semana de intensidad moderada o 75 min/semana alta.",
        [["150"], ["75"], ["ejercicio", "actividad fisica"]],
    ),
    EvalCase(
        "Q12", "estilo_vida",
        "¿Qué recomienda la guía respecto al consumo de alcohol?",
        "Menos de 100 g/semana de alcohol puro tanto en hombres como en mujeres; preferiblemente evitar el alcohol.",
        [["100"], ["alcohol"], ["semana"]],
    ),
    EvalCase(
        "Q13", "seguimiento",
        "Una vez controlada y estable la presión arterial con tratamiento, ¿con qué frecuencia mínima debe considerarse el seguimiento?",
        "Seguimiento de PA y factores de riesgo de ECV al menos una vez al año.",
        [["controlada"], ["una vez al año", "1 vez al año", "anual"]],
    ),
    EvalCase(
        "Q14", "riesgo",
        "¿Qué umbral de SCORE2 o SCORE2-OP considera la guía como riesgo cardiovascular suficientemente alto en una persona con presión arterial elevada?",
        "Riesgo de ECV a 10 años >=10%.",
        [["score2"], ["10 %", "10%"], ["riesgo"]],
    ),
    EvalCase(
        "Q15", "resistente",
        "¿Qué tratamiento recomienda la guía añadir en la hipertensión resistente no controlada pese al tratamiento de primera línea?",
        "Añadir espironolactona a dosis baja; existen alternativas si no se tolera.",
        [["espironolactona"], ["resistente"]],
    ),
    EvalCase(
        "Q16", "embarazo",
        "¿Qué cifras de presión arterial pueden indicar una emergencia hipertensiva durante el embarazo?",
        "PAS >=160 mmHg y PAD >=110 mmHg pueden indicar emergencia; >=170/110 se considera emergencia.",
        [["160"], ["110"], ["embarazo", "embarazada"]],
    ),
    EvalCase(
        "Q17", "erc",
        "En pacientes con hipertensión y enfermedad renal crónica con TFGe superior a 20 ml/min/1,73 m2, ¿qué grupo farmacológico recomienda la guía para mejorar resultados?",
        "Inhibidores SGLT2.",
        [["sglt2"], ["20"], ["tfge"]],
    ),
    EvalCase(
        "Q18", "medicion",
        "¿Qué diferencia de presión arterial sistólica entre ambos brazos se considera relevante y qué debe hacerse después?",
        "Diferencia >10 mmHg; repetir/confirmar y usar posteriormente el brazo con lectura más alta.",
        [["10 mmhg"], ["ambos brazos", "entre brazos"], ["mas alta", "más alta", "brazo con"]],
    ),
    EvalCase(
        "Q19", "medicion",
        "¿Cuánto tiempo debe permanecer el paciente en reposo antes de medir la presión arterial en consulta?",
        "5 minutos sentado cómodamente antes de la medición.",
        [["5 minutos"], ["sentado", "reposo"]],
    ),
    EvalCase(
        "Q20", "monitorizacion",
        "¿Durante cuántos días recomienda la guía realizar la automedida de presión arterial en domicilio?",
        "Mínimo 3 días e idealmente 7 días, con dos sesiones diarias.",
        [["3 dias", "3 días", "7 dias", "7 días"], ["ampa", "domicilio", "automedida"]],
    ),
]


ABSENT_CASES = [
    EvalCase(
        "N01", "sin_evidencia",
        "¿Qué pauta antibiótica recomienda esta guía para tratar una otitis media aguda?",
        "La guía no aborda el tratamiento de la otitis media aguda.",
        [],
    ),
    EvalCase(
        "N02", "sin_evidencia",
        "¿Cuál es la dosis de amoxicilina recomendada por esta guía para una neumonía adquirida en la comunidad?",
        "La guía no contiene una pauta de amoxicilina para neumonía.",
        [],
    ),
    EvalCase(
        "N03", "sin_evidencia",
        "¿Qué tratamiento recomienda esta guía para una fractura de fémur?",
        "La guía no aborda el tratamiento de fracturas.",
        [],
    ),
    EvalCase(
        "N04", "sin_evidencia",
        "¿Qué calendario vacunal infantil recomienda esta guía?",
        "La guía no contiene un calendario vacunal infantil.",
        [],
    ),
    EvalCase(
        "N05", "sin_evidencia",
        "¿Qué dosis de insulina rápida recomienda esta guía para una cetoacidosis diabética?",
        "La guía no contiene una pauta terapéutica de insulina para cetoacidosis.",
        [],
    ),
]


# ============================================================
# UTILIDADES
# ============================================================

def percentile(values, p):
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return xs[int(k)]
    return xs[f] * (c - k) + xs[c] * (k - f)


def summary_stats(values):
    if not values:
        return {}
    result = {
        "n": len(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
        "p95": percentile(values, 95),
    }
    result["stdev"] = statistics.stdev(values) if len(values) > 1 else 0.0
    return result


def normalize(text):
    text = (text or "").lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_is_relevant(text, evidence_groups):
    """
    Cada grupo es obligatorio.
    Dentro de un grupo basta con que aparezca una de las alternativas.
    """
    normalized = normalize(text)

    for group in evidence_groups:
        alternatives = [normalize(value) for value in group]
        if not any(value in normalized for value in alternatives):
            return False

    return True


def reciprocal_rank(chunks, evidence_groups):
    for rank, chunk in enumerate(chunks, start=1):
        if chunk_is_relevant(chunk.get("text", ""), evidence_groups):
            return 1.0 / rank
    return 0.0


def hit_at_k(chunks, evidence_groups, k):
    return int(
        any(
            chunk_is_relevant(chunk.get("text", ""), evidence_groups)
            for chunk in chunks[:k]
        )
    )


def precision_at_k(chunks, evidence_groups, k):
    top = chunks[:k]
    if not top:
        return 0.0

    relevant = sum(
        chunk_is_relevant(chunk.get("text", ""), evidence_groups)
        for chunk in top
    )
    return relevant / len(top)


def relevant_pages(chunks, evidence_groups):
    return sorted({
        int(chunk["page"])
        for chunk in chunks
        if "page" in chunk
        and chunk_is_relevant(chunk.get("text", ""), evidence_groups)
    })


def parse_chat_response(text):
    marker = "__SOURCES__"

    if marker not in text:
        return text.strip(), []

    answer, raw_sources = text.rsplit(marker, 1)

    try:
        sources = json.loads(raw_sources.strip())
    except json.JSONDecodeError:
        sources = []

    return answer.strip(), sources


FALLBACK_TEXT = (
    "no ha sido posible generar una respuesta final "
    "a partir de la documentacion recuperada"
)


def is_generation_failure(answer):
    normalized = normalize(answer)

    if not normalized:
        return True

    return FALLBACK_TEXT in normalized


ABSTENTION_PATTERNS = [
    r"no (?:se )?encuentra",
    r"no aparece",
    r"no (?:está|esta) (?:incluid[ao]|disponible|recogid[ao])",
    r"no se menciona",
    r"no se incluye",
    r"no (?:se )?aborda",
    r"no contiene",
    r"no proporciona",
    r"no especifica",
    r"la documentación (?:proporcionada )?no",
    r"el documento no",
    r"la guía no",
    r"no dispongo de información",
    r"no hay información",
    r"información insuficiente",
    r"fuera del alcance",
]


def detects_abstention(answer):
    normalized = (answer or "").lower()
    return any(re.search(pattern, normalized) for pattern in ABSTENTION_PATTERNS)


# ============================================================
# BENCHMARK
# ============================================================

def main():
    print("\n=== Inicializando RAG real ===")

    embedding_service = EmbeddingService()

    qdrant_service = QdrantService(
        embedding_dimension=embedding_service.dimension
    )

    rag_service = RAGService(
        embedding_service,
        qdrant_service
    )

    detailed_rows = []

    # --------------------------------------------------------
    # 1. RETRIEVAL
    # --------------------------------------------------------

    print("\n=== 1/3 Benchmark de retrieval ===")

    retrieval_times = []
    hit1_values = []
    hit3_values = []
    hit5_values = []
    rr_values = []
    p5_values = []

    retrieval_cache = {}

    for case in ANSWERABLE_CASES:
        t0 = time.perf_counter()

        chunks = rag_service.retrieve(
            case.question,
            top_k=TOP_K,
            session_id=SESSION_ID,
        )

        elapsed = time.perf_counter() - t0

        pages = [int(c["page"]) for c in chunks]
        scores = [float(c["score"]) for c in chunks]
        rel_pages = relevant_pages(chunks, case.evidence_groups)

        h1 = hit_at_k(chunks, case.evidence_groups, 1)
        h3 = hit_at_k(chunks, case.evidence_groups, 3)
        h5 = hit_at_k(chunks, case.evidence_groups, 5)
        rr = reciprocal_rank(chunks, case.evidence_groups)
        p5 = precision_at_k(chunks, case.evidence_groups, 5)

        retrieval_times.append(elapsed)
        hit1_values.append(h1)
        hit3_values.append(h3)
        hit5_values.append(h5)
        rr_values.append(rr)
        p5_values.append(p5)

        retrieval_cache[case.id] = {
            "pages": pages,
            "scores": scores,
            "chunks": chunks,
            "relevant_pages": rel_pages,
            "latency": elapsed,
            "hit_at_1": h1,
            "hit_at_3": h3,
            "hit_at_5": h5,
            "rr": rr,
            "p5": p5,
        }

        print(
            f"[{case.id}] "
            f"Hit@1={h1} Hit@3={h3} Hit@5={h5} "
            f"RR={rr:.3f} | páginas={pages} | "
            f"evidencia={rel_pages or '-'} | {elapsed:.3f}s"
        )

    retrieval_metrics = {
        "questions": len(ANSWERABLE_CASES),
        "hit_at_1": statistics.mean(hit1_values),
        "hit_at_3": statistics.mean(hit3_values),
        "hit_at_5": statistics.mean(hit5_values),
        "mrr": statistics.mean(rr_values),
        "precision_at_5": statistics.mean(p5_values),
        "latency_seconds": summary_stats(retrieval_times),
        "relevance_method": (
            "Detección por contenido del chunk mediante grupos de "
            "evidencia predefinidos; revisar manualmente los fallos."
        ),
    }

    # --------------------------------------------------------
    # 2. END-TO-END
    # --------------------------------------------------------

    e2e_metrics = {}

    if RUN_END_TO_END:
        print("\n=== 2/3 Benchmark end-to-end ===")

        total_times = []
        answer_failures = 0
        source_hits = []
        answer_lengths = []

        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            for case in ANSWERABLE_CASES:
                t0 = time.perf_counter()

                try:
                    response = client.post(
                        f"{BASE_URL}/chat",
                        json={
                            "query": case.question,
                            "session_id": SESSION_ID,
                            "history": [],
                        },
                    )

                    elapsed = time.perf_counter() - t0

                    if response.status_code != 200:
                        answer_failures += 1

                        print(
                            f"[{case.id}] FALLO HTTP "
                            f"{response.status_code} ({elapsed:.2f}s)"
                        )

                        detailed_rows.append({
                            "id": case.id,
                            "category": case.category,
                            "question": case.question,
                            "expected_fact": case.expected_fact,
                            "retrieved_pages": "|".join(
                                map(str, retrieval_cache[case.id]["pages"])
                            ),
                            "relevant_retrieved_pages": "|".join(
                                map(str, retrieval_cache[case.id]["relevant_pages"])
                            ),
                            "retrieval_scores": "|".join(
                                f"{s:.5f}"
                                for s in retrieval_cache[case.id]["scores"]
                            ),
                            "hit_at_1": retrieval_cache[case.id]["hit_at_1"],
                            "hit_at_3": retrieval_cache[case.id]["hit_at_3"],
                            "hit_at_5": retrieval_cache[case.id]["hit_at_5"],
                            "reciprocal_rank": retrieval_cache[case.id]["rr"],
                            "precision_at_5": retrieval_cache[case.id]["p5"],
                            "retrieval_latency_s": retrieval_cache[case.id]["latency"],
                            "total_latency_s": elapsed,
                            "source_pages_response": "",
                            "relevant_source_hit": 0,
                            "generation_failure": 1,
                            "answer": f"<HTTP {response.status_code}>",
                            "manual_grounded_0_2": "",
                            "manual_relevance_0_2": "",
                            "manual_notes": "",
                        })

                        continue

                    answer, sources = parse_chat_response(response.text)

                    source_pages = [
                        int(s["page"])
                        for s in sources
                        if "page" in s and str(s["page"]).isdigit()
                    ]

                    rel_pages = set(
                        retrieval_cache[case.id]["relevant_pages"]
                    )

                    source_hit = int(
                        bool(rel_pages.intersection(source_pages))
                    )

                    generation_failure = is_generation_failure(answer)

                    if generation_failure:
                        answer_failures += 1

                    total_times.append(elapsed)
                    source_hits.append(source_hit)
                    answer_lengths.append(len(answer))

                    detailed_rows.append({
                        "id": case.id,
                        "category": case.category,
                        "question": case.question,
                        "expected_fact": case.expected_fact,
                        "retrieved_pages": "|".join(
                            map(str, retrieval_cache[case.id]["pages"])
                        ),
                        "relevant_retrieved_pages": "|".join(
                            map(str, retrieval_cache[case.id]["relevant_pages"])
                        ),
                        "retrieval_scores": "|".join(
                            f"{s:.5f}"
                            for s in retrieval_cache[case.id]["scores"]
                        ),
                        "hit_at_1": retrieval_cache[case.id]["hit_at_1"],
                        "hit_at_3": retrieval_cache[case.id]["hit_at_3"],
                        "hit_at_5": retrieval_cache[case.id]["hit_at_5"],
                        "reciprocal_rank": retrieval_cache[case.id]["rr"],
                        "precision_at_5": retrieval_cache[case.id]["p5"],
                        "retrieval_latency_s": retrieval_cache[case.id]["latency"],
                        "total_latency_s": elapsed,
                        "source_pages_response": "|".join(map(str, source_pages)),
                        "relevant_source_hit": source_hit,
                        "generation_failure": int(generation_failure),
                        "answer": answer,
                        "manual_grounded_0_2": "",
                        "manual_relevance_0_2": "",
                        "manual_notes": "",
                    })

                    status = "FALLO" if generation_failure else "OK"

                    print(
                        f"[{case.id}] {status} | "
                        f"{elapsed:.2f}s | "
                        f"source_hit={source_hit} | "
                        f"{len(answer)} caracteres"
                    )

                except Exception as exc:
                    answer_failures += 1
                    print(f"[{case.id}] EXCEPCIÓN: {exc}")

        completed = len(ANSWERABLE_CASES) - answer_failures

        e2e_metrics = {
            "questions": len(ANSWERABLE_CASES),
            "failures": answer_failures,
            "completion_rate": completed / len(ANSWERABLE_CASES),
            "relevant_source_hit_rate": (
                statistics.mean(source_hits) if source_hits else 0.0
            ),
            "answer_length_chars": summary_stats(answer_lengths),
            "total_latency_seconds": summary_stats(total_times),
            "failure_definition": (
                "Respuesta vacía, error HTTP/excepción o activación "
                "del mensaje controlado de fallback tras dos generaciones fallidas."
            ),
        }

    # --------------------------------------------------------
    # 3. PREGUNTAS SIN EVIDENCIA
    # --------------------------------------------------------

    no_evidence_metrics = {}

    if RUN_END_TO_END:
        print("\n=== 3/3 Prueba de abstención sin evidencia ===")

        abstentions = []
        absent_latencies = []
        absent_rows = []

        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            for case in ABSENT_CASES:
                t0 = time.perf_counter()

                try:
                    response = client.post(
                        f"{BASE_URL}/chat",
                        json={
                            "query": case.question,
                            "session_id": SESSION_ID,
                            "history": [],
                        },
                    )

                    elapsed = time.perf_counter() - t0

                    answer, sources = parse_chat_response(response.text)

                    abstained = detects_abstention(answer)

                    abstentions.append(int(abstained))
                    absent_latencies.append(elapsed)

                    absent_rows.append({
                        "id": case.id,
                        "category": case.category,
                        "question": case.question,
                        "expected_fact": case.expected_fact,
                        "retrieved_pages": "",
                        "relevant_retrieved_pages": "",
                        "retrieval_scores": "",
                        "hit_at_1": "",
                        "hit_at_3": "",
                        "hit_at_5": "",
                        "reciprocal_rank": "",
                        "precision_at_5": "",
                        "retrieval_latency_s": "",
                        "total_latency_s": elapsed,
                        "source_pages_response": "|".join(
                            str(s.get("page", ""))
                            for s in sources
                        ),
                        "relevant_source_hit": "",
                        "generation_failure": int(is_generation_failure(answer)),
                        "answer": answer,
                        "manual_grounded_0_2": "",
                        "manual_relevance_0_2": "",
                        "manual_notes": "",
                    })

                    print(
                        f"[{case.id}] "
                        f"abstención={'SÍ' if abstained else 'NO'} "
                        f"| {elapsed:.2f}s"
                    )

                except Exception as exc:
                    print(f"[{case.id}] EXCEPCIÓN: {exc}")
                    abstentions.append(0)

        detailed_rows.extend(absent_rows)

        no_evidence_metrics = {
            "questions": len(ABSENT_CASES),
            "abstention_rate_heuristic": (
                statistics.mean(abstentions)
                if abstentions
                else 0.0
            ),
            "latency_seconds": summary_stats(absent_latencies),
            "warning": (
                "La abstención se detecta mediante patrones textuales. "
                "Las cinco respuestas deben revisarse manualmente antes "
                "de fijar el resultado definitivo."
            ),
        }

    # --------------------------------------------------------
    # EXPORTACIÓN
    # --------------------------------------------------------

    all_metrics = {
        "session_id": SESSION_ID,
        "embedding_model": "intfloat/multilingual-e5-large",
        "top_k": TOP_K,
        "retrieval": retrieval_metrics,
        "end_to_end": e2e_metrics,
        "no_evidence": no_evidence_metrics,
    }

    json_path = OUTPUT_DIR / "metrics.json"
    csv_path = OUTPUT_DIR / "results.csv"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(
            all_metrics,
            f,
            indent=2,
            ensure_ascii=False
        )

    if detailed_rows:
        fieldnames = list(detailed_rows[0].keys())

        with csv_path.open(
            "w",
            encoding="utf-8-sig",
            newline=""
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames
            )
            writer.writeheader()
            writer.writerows(detailed_rows)

    # --------------------------------------------------------
    # RESUMEN
    # --------------------------------------------------------

    print("\n" + "=" * 64)
    print("RESULTADOS DEL BENCHMARK")
    print("=" * 64)

    print("\n[RETRIEVAL]")
    print(
        f"Preguntas evaluadas: "
        f"{retrieval_metrics['questions']}"
    )
    print(
        f"Hit@1: "
        f"{retrieval_metrics['hit_at_1'] * 100:.1f}%"
    )
    print(
        f"Hit@3: "
        f"{retrieval_metrics['hit_at_3'] * 100:.1f}%"
    )
    print(
        f"Hit@5: "
        f"{retrieval_metrics['hit_at_5'] * 100:.1f}%"
    )
    print(
        f"MRR: "
        f"{retrieval_metrics['mrr']:.3f}"
    )
    print(
        f"Precision@5 media: "
        f"{retrieval_metrics['precision_at_5'] * 100:.1f}%"
    )

    rt = retrieval_metrics["latency_seconds"]

    print(
        f"Latencia retrieval: "
        f"media={rt['mean']:.3f}s, "
        f"mediana={rt['median']:.3f}s, "
        f"p95={rt['p95']:.3f}s"
    )

    if RUN_END_TO_END:
        print("\n[END-TO-END]")
        print(
            f"Tasa de finalización: "
            f"{e2e_metrics['completion_rate'] * 100:.1f}%"
        )
        print(
            f"Fuente relevante presente: "
            f"{e2e_metrics['relevant_source_hit_rate'] * 100:.1f}%"
        )

        et = e2e_metrics["total_latency_seconds"]

        if et:
            print(
                f"Latencia total: "
                f"media={et['mean']:.2f}s, "
                f"mediana={et['median']:.2f}s, "
                f"min={et['min']:.2f}s, "
                f"max={et['max']:.2f}s, "
                f"p95={et['p95']:.2f}s"
            )

        print("\n[SIN EVIDENCIA]")
        print(
            f"Tasa de abstención (heurística): "
            f"{no_evidence_metrics['abstention_rate_heuristic'] * 100:.1f}%"
        )

    print(f"\nMétricas JSON: {json_path}")

    if detailed_rows:
        print(f"Resultados CSV: {csv_path}")

    print(
        "\nIMPORTANTE: abre results.csv y revisa manualmente "
        "las 20 respuestas. Las columnas "
        "manual_grounded_0_2 y manual_relevance_0_2 "
        "se completarán después."
    )


if __name__ == "__main__":
    main()
