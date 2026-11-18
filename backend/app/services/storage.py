"""File storage helpers."""

import shutil
import uuid
from pathlib import Path

from app.config import DATA_DIR, MAX_UPLOAD_MB, MODELS_DIR


def _safe_display_name(original_name: str) -> str:
    name = Path(original_name or "dataset.csv").name
    cleaned = "".join(c for c in name if c.isalnum() or c in "._- ")
    cleaned = cleaned.strip().replace(" ", "_")
    return (cleaned or "dataset.csv")[:120]


def save_uploaded_csv(file_obj, original_name: str) -> Path:
    dest_dir = DATA_DIR / "datasets"
    dest_dir.mkdir(parents=True, exist_ok=True)
    # Store with an opaque name; the original name is kept only in the DB.
    dest = dest_dir / f"{uuid.uuid4().hex}.csv"
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    written = 0
    try:
        with open(dest, "wb") as f:
            while True:
                chunk = file_obj.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > max_bytes:
                    raise ValueError(f"File too large (max {MAX_UPLOAD_MB} MB)")
                f.write(chunk)
    except Exception:
        dest.unlink(missing_ok=True)
        raise
    return dest


def model_path_for_job(job_id: int) -> Path:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    return MODELS_DIR / f"job_{job_id}.joblib"


def display_name_for_upload(original_name: str) -> str:
    return _safe_display_name(original_name)
