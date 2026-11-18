"""Models router."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ModelArtifact, TrainingJob
from app.schemas import ModelOut

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=list[ModelOut])
def list_models(db: Session = Depends(get_db)):
    artifacts = db.query(ModelArtifact).order_by(ModelArtifact.id.desc()).all()
    out = []
    for a in artifacts:
        job = db.get(TrainingJob, a.job_id)
        out.append(
            ModelOut(
                id=a.id,
                job_id=a.job_id,
                name=a.name,
                created_at=a.created_at,
                algorithm=job.algorithm if job else None,
                problem=job.problem if job else None,
                metrics=job.metrics_json if job else None,
            )
        )
    return out


@router.get("/{model_id}/download")
def download_model(model_id: int, db: Session = Depends(get_db)):
    artifact = db.get(ModelArtifact, model_id)
    if artifact is None:
        # allow addressing by job id as fallback
        job = db.get(TrainingJob, model_id)
        if job and job.model_path:
            artifact_path = Path(job.model_path)
            if artifact_path.exists():
                return FileResponse(str(artifact_path), filename=artifact_path.name)
        raise HTTPException(status_code=404, detail="Model not found")
    path = Path(artifact.path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Model file missing")
    return FileResponse(str(path), filename=path.name)
