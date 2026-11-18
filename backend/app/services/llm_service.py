"""LLM chat service for datasets."""

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

import pandas as pd

from app.config import DATA_DIR  # noqa: F401
from app.database import SessionLocal
from app.models import Dataset
from app.services import cache as cache_service

SYSTEM_PROMPTS = {
    "es": (
        "Eres un asistente analista de datos. Respondes en espanol, de forma concisa y util. "
        "Usa unicamente el contexto del dataset proporcionado. "
        "Si la pregunta no esta relacionada con el dataset (conocimiento general, programacion, "
        "opiniones, tareas, etc.), rechazala amablemente y di que solo puedes responder sobre los datos. "
        "Si no hay suficiente informacion en el contexto, dilo claramente."
    ),
    "en": (
        "You are a data analyst assistant. You respond in English, concisely and helpfully. "
        "Use only the provided dataset context. "
        "If the question is unrelated to the dataset (general knowledge, coding, opinions, tasks, etc.), "
        "politely refuse and say you can only answer questions about the data. "
        "If there is not enough information in the context, say so clearly."
    ),
}

DATA_TERMS = [
    "data", "dataset", "column", "columns", "row", "rows", "value", "values",
    "missing", "null", "nan", "summary", "describe", "statistics", "statistical",
    "mean", "median", "mode", "std", "variance", "min", "max", "count", "unique",
    "correlation", "distribution", "outlier", "outliers", "plot", "chart", "graph",
    "trend", "average", "sum", "total", "filter", "group", "aggregate", "top",
    "bottom", "sample", "head", "tail", "info", "schema", "type", "types",
    "analysis", "analyze", "analyse", "insight", "insights", "record", "records",
    "datos", "conjunto", "columna", "columnas", "fila", "filas", "valor", "valores",
    "faltante", "faltantes", "nulo", "nulos", "resumen", "estadistica", "estadisticas",
    "media", "mediana", "moda", "desviacion", "minimo", "maximo", "conteo",
    "correlacion", "distribucion", "atipico", "atipicos", "grafico", "grafica",
    "tendencia", "promedio", "suma", "total", "filtro", "agrupar", "agregado",
    "muestra", "informacion", "esquema", "tipo", "tipos", "analisis", "analizar",
    "registro", "registros", "tabla",
]

CANNED_MESSAGES = {
    "es": "Solo puedo ayudar con preguntas relacionadas con el dataset proporcionado.",
    "en": "I can only help with questions related to the provided dataset.",
}


def is_data_related(message: Any, df: pd.DataFrame) -> bool:
    if not isinstance(message, str) or not message.strip():
        return False
    text = message.lower()
    try:
        for col in df.columns:
            col_text = str(col).strip().lower()
            if col_text and col_text in text:
                return True
    except Exception:
        pass
    for term in DATA_TERMS:
        if term in text:
            return True
    return False


def _normalize_message(message: Any) -> str:
    return " ".join(str(message).strip().lower().split())


def _system_prompt(lang: str) -> str:
    return SYSTEM_PROMPTS.get((lang or "es").lower(), SYSTEM_PROMPTS["es"])


def _try_import_compute_summary():
    try:
        from app.ml.eda import compute_summary  # type: ignore

        return compute_summary
    except Exception:
        return None


def _build_context(df: pd.DataFrame) -> str:
    lines: List[str] = []
    lines.append(f"Shape: {df.shape[0]} filas x {df.shape[1]} columnas")
    lines.append(f"Columnas: {list(df.columns)}")
    lines.append("Tipos de datos:")
    for col, dtype in df.dtypes.items():
        lines.append(f"  - {col}: {dtype}")
    missing = df.isna().sum()
    lines.append("Valores faltantes:")
    any_missing = False
    for col, val in missing.items():
        if int(val) > 0:
            lines.append(f"  - {col}: {int(val)}")
            any_missing = True
    if not any_missing:
        lines.append("  (ninguno)")
    numeric = df.select_dtypes(include="number")
    lines.append("Resumen numerico (truncado):")
    if numeric.empty:
        lines.append("  (sin columnas numericas)")
    else:
        desc = numeric.describe().round(4)
        lines.append(desc.to_string()[:1500])
    lines.append("Muestra (5 filas):")
    lines.append(df.head(5).to_string()[:1500])

    compute_summary = _try_import_compute_summary()
    if compute_summary is not None:
        try:
            summary = compute_summary(df) or {}
            numeric_summary = summary.get("numeric_summary") or {}
            categorical_summary = summary.get("categorical_summary") or {}
            missing_counts = summary.get("missing") or {}
            correlation = summary.get("correlation") or []
            if numeric_summary:
                lines.append("Resumen numerico:")
                for col, stats in numeric_summary.items():
                    if isinstance(stats, dict):
                        lines.append(f"  - {col}: " + ", ".join(f"{k}={v}" for k, v in stats.items() if v is not None))
            if categorical_summary:
                lines.append("Resumen categorico:")
                for col, stats in categorical_summary.items():
                    if isinstance(stats, dict):
                        lines.append(f"  - {col}: " + ", ".join(f"{k}={v}" for k, v in list(stats.items())[:10]))
            if missing_counts:
                lines.append("Faltantes: " + ", ".join(f"{k}={v}" for k, v in missing_counts.items() if v > 0))
            if correlation:
                lines.append("Correlaciones: " + ", ".join(f"{c.get('a')}-{c.get('b')}={c.get('value')}" for c in correlation[:10]))
        except Exception:
            pass

    return "\n".join(lines)


def _ollama_status() -> (bool, Optional[Dict[str, Any]]):  # type: ignore
    try:
        req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        if req.status != 200:
            return False, None
        data = json.loads(req.read().decode("utf-8"))
        return True, data
    except Exception:
        return False, None


def _call_groq(messages: List[Dict[str, str]]) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    url = "https://api.groq.com/openai/v1/chat/completions"
    body = {
        "model": "openai/gpt-oss-20b",
        "messages": messages,
        "temperature": 0.2,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ml-platform/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            out = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        raise ValueError(f"Groq error {e.code}: {detail}") from e
    return out["choices"][0]["message"]["content"]


def _call_ollama(messages: List[Dict[str, str]]) -> str:
    ok, tags = _ollama_status()
    models: List[str] = []
    if isinstance(tags, dict):
        for m in tags.get("models", []) or []:
            name = m.get("name") if isinstance(m, dict) else None
            if name:
                models.append(name)

    model = "llama3.2"
    if models:
        preferred = [m for m in models if m.startswith("llama3.2")]
        model = preferred[0] if preferred else models[0]

    url = "http://localhost:11434/api/chat"
    body = {"model": model, "messages": messages, "stream": False}
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            out = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        raise ValueError(f"Ollama error {e.code}: {detail}") from e
    if isinstance(out, dict) and "message" in out:
        return out["message"].get("content", "")
    return str(out)


def chat(dataset_id: Any, message: str, history: Optional[List[Dict[str, str]]] = None, lang: str = "es") -> str:
    if history is None:
        history = []

    lang = (lang or "es").lower()
    if lang not in ("es", "en"):
        lang = "es"

    db = SessionLocal()
    try:
        ds = db.get(Dataset, dataset_id)
        if ds is None:
            raise ValueError("Dataset not found" if lang == "en" else "Dataset no encontrado")
        df = pd.read_csv(ds.path)
    finally:
        db.close()

    if not is_data_related(message, df):
        return CANNED_MESSAGES.get(lang, CANNED_MESSAGES["es"])

    normalized = _normalize_message(message)
    cache_key = (dataset_id, lang, normalized)
    cached = cache_service.get(cache_key)
    if cached is not None:
        return cached

    context = _build_context(df)
    label = "DATASET CONTEXT:" if lang == "en" else "CONTEXTO DEL DATASET:"
    system_content = _system_prompt(lang) + "\n\n" + label + "\n" + context
    messages: List[Dict[str, str]] = [{"role": "system", "content": system_content}]
    from app.config import CHAT_HISTORY_LIMIT

    for item in history[-CHAT_HISTORY_LIMIT:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "")).lower()
        content = str(item.get("content", ""))[:4000]
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": message})

    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        reply = _call_groq(messages)
    elif _ollama_status()[0]:
        reply = _call_ollama(messages)
    else:
        if lang == "en":
            raise ValueError(
                "No LLM provider configured. Set GROQ_API_KEY (free at https://console.groq.com) "
                "or install and run Ollama (http://localhost:11434)."
            )
        else:
            raise ValueError(
                "No hay proveedor LLM configurado. Configura GROQ_API_KEY (gratis en https://console.groq.com) "
                "o instala y ejecuta Ollama (http://localhost:11434)."
            )

    try:
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": reply})
    except Exception:
        pass

    try:
        from app.config import CHAT_CACHE_TTL

        cache_service.set(cache_key, reply, ttl_seconds=CHAT_CACHE_TTL)
    except Exception:
        pass

    return reply