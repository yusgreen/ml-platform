"""Training orchestration service."""

import math
import os
from datetime import datetime

import joblib
import pandas as pd

from app.config import DATA_DIR
from app.database import SessionLocal
from app.ml import supervised, unsupervised
from app.models import Dataset, ModelArtifact, TrainingJob
from app.services.storage import model_path_for_job


def _atomic_dump(model, path) -> None:
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    try:
        joblib.dump(model, tmp)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _sanitize_metrics(value):
    if isinstance(value, dict):
        return {k: _sanitize_metrics(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_metrics(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _load_dataset(db, dataset_id):
    ds = db.get(Dataset, dataset_id)
    if ds is None:
        raise ValueError("Dataset not found")
    return ds, pd.read_csv(ds.path)


def run_training_job(job_id: int) -> None:
    db = SessionLocal()
    try:
        job = db.get(TrainingJob, job_id)
        if job is None:
            return
        job.status = "running"
        db.commit()

        ds, df = _load_dataset(db, job.dataset_id)

        params = job.params_json or {}
        model_path = model_path_for_job(job.id)

        if job.task_type == "supervised":
            if job.problem == "classification":
                model, metrics = supervised.train_classification(
                    df, job.target_column, job.algorithm, job.test_size, params
                )
            elif job.problem == "regression":
                model, metrics = supervised.train_regression(
                    df, job.target_column, job.algorithm, job.test_size, params
                )
            else:
                raise ValueError("Unsupported supervised problem")
            _atomic_dump(model, model_path)
        elif job.task_type == "unsupervised":
            if job.problem in ("clustering",):
                model, labels, metrics = unsupervised.run_clustering(df, job.algorithm, params)
                _atomic_dump(model, model_path)
            elif job.problem in ("dimensionality", "pca"):
                model, transformed, metrics = unsupervised.run_pca(df, params)
                _atomic_dump(model, model_path)
            else:
                raise ValueError("Unsupported unsupervised problem")
        else:
            raise ValueError("Unsupported task_type")

        job.status = "completed"
        job.metrics_json = _sanitize_metrics(metrics)
        job.model_path = str(model_path)
        job.finished_at = datetime.utcnow()

        artifact = ModelArtifact(job_id=job.id, name=model_path.name, path=str(model_path))
        db.add(artifact)
        db.commit()
    except Exception as e:
        db.rollback()
        job = db.get(TrainingJob, job_id)
        if job is not None:
            job.status = "failed"
            job.error = str(e)
            job.finished_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()
