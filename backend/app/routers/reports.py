"""Reports router."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Dataset
from app.services import report_service

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/{dataset_id}")
def generate_report(dataset_id: int, lang: str = Query("es"), db: Session = Depends(get_db)):
    ds = db.get(Dataset, dataset_id)
    if ds is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    try:
        path = report_service.generate_report(dataset_id, db, lang=lang)
    except Exception:
        raise HTTPException(status_code=500, detail="Report generation failed")
    path = Path(path)
    if not path.exists():
        raise HTTPException(status_code=500, detail="Report generation failed")
    return FileResponse(str(path), filename="report.pdf", media_type="application/pdf")


@router.get("/{dataset_id}/download")
def download_report(dataset_id: int, db: Session = Depends(get_db)):
    ds = db.get(Dataset, dataset_id)
    if ds is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    from app.config import DATA_DIR

    path = DATA_DIR / "reports" / str(dataset_id) / "report.pdf"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(str(path), filename="report.pdf", media_type="application/pdf")
