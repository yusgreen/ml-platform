"""FastAPI application entrypoint."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import DATA_DIR, ensure_dirs
from app.database import Base, engine
from app.models import Dataset, ModelArtifact, TrainingJob  # noqa: F401
from app.routers import chat, datasets, eda, health, models, reports, training

ensure_dirs()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_dirs()
    # Reconcile jobs left "running" by a previous crash/restart.
    try:
        from datetime import datetime, timezone
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            stale = db.query(TrainingJob).filter(TrainingJob.status.in_(["pending", "running"])).all()
            for job in stale:
                job.status = "failed"
                job.error = "Interrupted by server restart"
                job.finished_at = datetime.now(timezone.utc)
            db.commit()
        finally:
            db.close()
    except Exception:
        pass
    yield


app = FastAPI(title="ML Training Platform", version="0.1.0", lifespan=lifespan)

_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins.split(",") if o.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    return response


app.include_router(health.router)
app.include_router(datasets.router)
app.include_router(training.router)
app.include_router(models.router)
app.include_router(eda.router)
app.include_router(chat.router)
app.include_router(reports.router)

# Serve only derived artifacts (plots/reports), never raw datasets.
for _sub in ("eda", "reports"):
    _path = DATA_DIR / _sub
    _path.mkdir(parents=True, exist_ok=True)
    app.mount(f"/data/{_sub}", StaticFiles(directory=str(_path), html=False), name=f"static-{_sub}")
