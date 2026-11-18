"""EDA router."""

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import DATA_DIR
from app.database import get_db
from app.ml.eda import compute_summary, generate_plots
from app.models import Dataset

router = APIRouter(prefix="/api/eda", tags=["eda"])


@router.post("/{dataset_id}")
def run_eda(dataset_id: int, db: Session = Depends(get_db)):
    ds = db.get(Dataset, dataset_id)
    if ds is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    try:
        df = pd.read_csv(ds.path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {e}")

    out_dir = DATA_DIR / "eda" / str(dataset_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        summary = compute_summary(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary failed: {e}")

    try:
        filenames = generate_plots(df, out_dir)
    except Exception:
        filenames = []

    plots = [f"/data/eda/{dataset_id}/{fn}" for fn in filenames]
    return {"dataset_id": dataset_id, "summary": summary, "plots": plots}
