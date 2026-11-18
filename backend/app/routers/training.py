"""Training router."""

import numpy as np
import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Dataset, TrainingJob
from app.schemas import TrainingJobOut, TrainingStart
from app.services.ml_service import run_training_job

router = APIRouter(prefix="/api/training", tags=["training"])

ALLOWED_ALGORITHMS = {
    ("supervised", "classification"): {"logistic", "random_forest", "xgboost"},
    ("supervised", "regression"): {"linear", "random_forest", "xgboost"},
    ("unsupervised", "clustering"): {"kmeans", "dbscan"},
    ("unsupervised", "dimensionality"): {"pca"},
}


@router.post("/start", response_model=TrainingJobOut)
def start_training(req: TrainingStart, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    ds = db.get(Dataset, req.dataset_id)
    if ds is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    allowed = ALLOWED_ALGORITHMS.get((req.task_type, req.problem))
    if allowed is None:
        raise HTTPException(status_code=400, detail="Unsupported task/problem combination")
    if req.algorithm not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported algorithm. Allowed: {', '.join(sorted(allowed))}",
        )

    if req.task_type == "supervised" and not req.target_column:
        raise HTTPException(status_code=400, detail="target_column required for supervised tasks")

    try:
        sample = pd.read_csv(ds.path, nrows=5)
    except Exception:
        raise HTTPException(status_code=422, detail="Dataset file is unreadable")

    if len(sample) < 2:
        raise HTTPException(status_code=422, detail="Dataset needs at least 2 rows")

    if req.target_column:
        if req.target_column not in sample.columns:
            raise HTTPException(status_code=422, detail="Target column not found in dataset")
        if req.problem == "regression" and not np.issubdtype(sample[req.target_column].dtype, np.number):
            raise HTTPException(status_code=422, detail="Regression target must be numeric")

    job = TrainingJob(
        dataset_id=req.dataset_id,
        task_type=req.task_type,
        problem=req.problem,
        algorithm=req.algorithm,
        params_json=req.params or {},
        target_column=req.target_column,
        test_size=req.test_size,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(run_training_job, job.id)
    return job


@router.get("", response_model=list[TrainingJobOut])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(TrainingJob).order_by(TrainingJob.id.desc()).all()


@router.get("/{job_id}", response_model=TrainingJobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(TrainingJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
