# ML Training Platform (Free / Self-hosted)

Plataforma web para entrenar modelos de aprendizaje supervisado y no supervisado. Stack 100% gratuito y auto-hospedado.

## Estructura

- `backend/` — FastAPI + scikit-learn (Python)
- `frontend/` — Next.js 14 + TypeScript + Tailwind

## Requisitos

- Python 3.11+
- Node.js 18+

## Backend

```bash
cd backend
python -m pip install -r requirements.txt
python run.py
```

API: http://localhost:8000  (docs: http://localhost:8000/docs)

## Frontend

```bash
cd frontend
npm install
npm run dev
```

UI: http://localhost:3000

## Flujo

1. Sube un CSV en **Datasets**.
2. Ve a **EDA** para obtener resumen estadístico, correlaciones y gráficos.
3. Ve a **Chat** para preguntar en lenguaje natural sobre tus datos (requiere `GROQ_API_KEY` gratis o Ollama local).
4. Ve a **Train Model**, elige dataset, tipo de tarea, problema y algoritmo.
5. Inicia entrenamiento; el progreso y métricas aparecen en **Experiments**.
6. Genera un **Reporte PDF** desde **Reports**.
7. Descarga el modelo desde **Models**.

## Chat con datos (LLM)

Configura una clave gratuita de Groq:
```bash
# Windows PowerShell
$env:GROQ_API_KEY="tu_clave"
# o crea backend/.env con GROQ_API_KEY=...
```
Obtén la clave en https://console.groq.com (free tier). Alternativa: instala Ollama (http://localhost:11434).

## Algoritmos soportados

- Supervisado clasificación: logistic, random_forest, xgboost
- Supervisado regresión: linear, random_forest, xgboost
- No supervisado clustering: kmeans, dbscan
- No supervisado reducción dimensional: pca

## Notas

- Sin costos: SQLite, filesystem local, sin servicios externos.
- Para producción, cambia SQLite por Postgres y define `NEXT_PUBLIC_API_URL`.
