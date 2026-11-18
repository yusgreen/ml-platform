# ML Platform — AI Data Analyst (Free / Self-hosted)

Plataforma web **100% gratuita y auto-hospedada** para subir un dataset CSV y obtener valor analítico automático: **EDA**, **chat con tus datos**, **entrenamiento de modelos** y **reportes PDF**.

---

## ✨ Características

- **📊 Datasets**: subida de CSV (límite 50 MB, máx. 200k filas × 200 columnas), vista previa de columnas y tipos.
- **🔍 EDA**: resumen estadístico, valores faltantes, correlaciones y gráficos automáticos (histogramas, heatmap, missing values, categorías).
- **💬 Chat con datos**: pregunta en lenguaje natural sobre tu dataset (ES/EN). Incluye:
  - Rate limit: **20 preguntas / minuto / IP**.
  - Caché de respuestas: **TTL 10 min**.
  - Historial recortado a **últimos 8 mensajes**.
  - Guardrails: rechaza preguntas off-topic y responde solo con contexto del dataset.
- **🚀 Entrenamiento**: auto-ML con algoritmos permitidos (logistic, random_forest, xgboost, linear, kmeans, dbscan, pca).
- **📄 Reportes PDF**: reporte automático en ES/EN con métricas, resumen y gráficos.
- **🌐 i18n**: interfaz en **español e inglés** con selector en la navbar.

---

## 🧰 Stack

- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS + React
- **Backend**: FastAPI + scikit-learn + pandas + matplotlib/seaborn + ReportLab
- **Base de datos**: SQLite
- **LLM**: Groq (`openai/gpt-oss-20b`, free tier) con fallback a Ollama local
- **Infra**: todo local / filesystem

---

## 📋 Requisitos

- Python 3.11+
- Node.js 18+
- `GROQ_API_KEY` (opcional, gratis) — para el chat. Alternativa: Ollama local.

---

## 🚀 Instalación

### Backend

```bash
cd backend
python -m pip install -r requirements.txt
cp .env.example .env   # y setear GROQ_API_KEY si quieres chat
python run.py
```

API: http://localhost:8000 — Docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

UI: http://localhost:3000

---

## 🔄 Flujo de uso

1. **Datasets** → sube tu CSV.
2. **EDA** → genera resumen, correlaciones y gráficos.
3. **Chat** → pregunta sobre tu data (ej. *"¿cuántas filas tiene?"*).
4. **Train** → elige tarea (clasificación/regresión/clustering/PCA), problema y algoritmo.
5. **Experiments** → ves progreso y métricas del job.
6. **Reports** → genera reporte PDF (ES/EN).
7. **Models** → descarga el modelo entrenado.

---

## 🔌 Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/datasets/upload` | Subir CSV |
| GET | `/api/datasets` | Listar datasets |
| GET | `/api/datasets/{id}` | Detalle (columnas, preview) |
| POST | `/api/eda/{dataset_id}` | Generar EDA + plots |
| POST | `/api/chat` | Chat con dataset |
| POST | `/api/training/start` | Iniciar entrenamiento |
| GET | `/api/training` | Listar jobs |
| GET | `/api/models` | Listar modelos |
| POST | `/api/reports/{dataset_id}` | Generar reporte PDF |

---

## 🤖 Chat (LLM)

Configura Groq (free):

```bash
# backend/.env
GROQ_API_KEY=tu_clave
```

Obtén la clave en: https://console.groq.com

Alternativa: Ollama local en `http://localhost:11434`.

---

## 🧪 Algoritmos soportados

| Tarea | Problema | Algoritmos |
|---|---|---|
| Supervisado | Clasificación | logistic, random_forest, xgboost |
| Supervisado | Regresión | linear, random_forest, xgboost |
| No supervisado | Clustering | kmeans, dbscan |
| No supervisado | Reducción de dimensionalidad | pca |

---

## 🔒 Seguridad

- Storage de uploads con **UUID opaco** + nombre sanitizado.
- Límite de tamaño de upload (`MAX_UPLOAD_MB`) y filas/columnas (`MAX_ROWS`, `MAX_COLS`).
- Sin path traversal en servido de archivos.
- Static serving restringido a `/data/eda` y `/data/reports`.
- Security headers (X-Content-Type-Options, X-Frame-Options, Referrer-Policy).
- Validación estricta en backend (schemas Pydantic).

---

## 📝 Notas

- Sin costos: SQLite, filesystem local, sin servicios externos.
- Para producción: cambiar SQLite por Postgres y definir `NEXT_PUBLIC_API_URL`.
