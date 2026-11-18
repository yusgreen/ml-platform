"""Datasets router."""

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import MAX_COLS, MAX_PREVIEW_ROWS, MAX_ROWS
from app.database import get_db
from app.models import Dataset
from app.schemas import DatasetDetail, DatasetOut
from app.services.storage import display_name_for_upload, save_uploaded_csv

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.post("/upload", response_model=DatasetOut)
async def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    try:
        path = save_uploaded_csv(file.file, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not store uploaded file")

    try:
        df = pd.read_csv(path, nrows=MAX_ROWS + 1)
    except Exception:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Invalid CSV file")

    if df.empty or df.shape[1] == 0:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="CSV has no data")
    if len(df) > MAX_ROWS:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=413, detail=f"CSV exceeds the row limit ({MAX_ROWS})")
    if df.shape[1] > MAX_COLS:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=413, detail=f"CSV exceeds the column limit ({MAX_COLS})")

    ds = Dataset(
        name=display_name_for_upload(file.filename),
        path=str(path),
        rows=int(df.shape[0]),
        cols=int(df.shape[1]),
    )
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return ds


@router.get("", response_model=list[DatasetOut])
def list_datasets(db: Session = Depends(get_db)):
    return db.query(Dataset).order_by(Dataset.id.desc()).all()


@router.get("/{dataset_id}", response_model=DatasetDetail)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    ds = db.get(Dataset, dataset_id)
    if ds is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    try:
        df = pd.read_csv(ds.path, nrows=MAX_PREVIEW_ROWS)
    except FileNotFoundError:
        raise HTTPException(status_code=410, detail="Dataset file no longer exists")
    except Exception:
        raise HTTPException(status_code=422, detail="Dataset file is unreadable")
    preview = df.replace([float("inf"), float("-inf")], None).fillna("").to_dict(orient="records")
    dtypes = {c: str(t) for c, t in df.dtypes.items()}
    return DatasetDetail(
        id=ds.id,
        name=ds.name,
        rows=ds.rows,
        cols=ds.cols,
        created_at=ds.created_at,
        columns=list(df.columns),
        dtypes=dtypes,
        preview=preview,
    )
