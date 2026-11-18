"""PDF report generation service."""

import os
from pathlib import Path
from typing import List
from xml.sax.saxutils import escape

import pandas as pd
from sqlalchemy.orm import Session

from app.config import DATA_DIR
from app.models import Dataset, TrainingJob

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _find_plots(dataset_id: int) -> List[Path]:
    plots: List[Path] = []
    seen = set()

    candidate_dirs = [
        DATA_DIR / "eda" / str(dataset_id),
        DATA_DIR / "plots" / str(dataset_id),
    ]
    for d in candidate_dirs:
        if d.exists() and d.is_dir():
            for p in d.iterdir():
                if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp"}:
                    if p not in seen:
                        seen.add(p)
                        plots.append(p)

    return plots[:20]


TRANSLATIONS = {
    "es": {
        "title": "Reporte del Dataset: {name}",
        "field": "Campo",
        "value": "Valor",
        "id": "ID",
        "name": "Nombre",
        "rows": "Filas",
        "cols": "Columnas",
        "path": "Ruta",
        "created": "Creado",
        "missing": "Valores faltantes",
        "column": "Columna",
        "missing_count": "Faltantes",
        "numeric_summary": "Resumen estadistico (columnas numericas)",
        "no_numeric": "No hay columnas numericas.",
        "shape": "Forma",
        "columns": "Columnas",
        "jobs": "Trabajos de entrenamiento",
        "no_jobs": "No hay trabajos de entrenamiento para este dataset.",
        "metrics": "Metricas",
        "eda_plots": "Graficos EDA",
        "type": "Tipo",
        "problem": "Problema",
        "algorithm": "Algoritmo",
        "status": "Estado",
    },
    "en": {
        "title": "Dataset Report: {name}",
        "field": "Field",
        "value": "Value",
        "id": "ID",
        "name": "Name",
        "rows": "Rows",
        "cols": "Columns",
        "path": "Path",
        "created": "Created",
        "missing": "Missing values",
        "column": "Column",
        "missing_count": "Missing",
        "numeric_summary": "Statistical summary (numeric columns)",
        "no_numeric": "No numeric columns.",
        "shape": "Shape",
        "columns": "Columns",
        "jobs": "Training jobs",
        "no_jobs": "No training jobs for this dataset.",
        "metrics": "Metrics",
        "eda_plots": "EDA plots",
        "type": "Type",
        "problem": "Problem",
        "algorithm": "Algorithm",
        "status": "Status",
    },
}


def _t(lang: str, key: str) -> str:
    lang = (lang or "es").lower()
    if lang not in TRANSLATIONS:
        lang = "es"
    return TRANSLATIONS[lang].get(key, key)


def generate_report(dataset_id: int, db: Session, lang: str = "es") -> Path:
    ds = db.get(Dataset, dataset_id)
    if ds is None:
        raise ValueError("Dataset not found")

    df = pd.read_csv(ds.path)
    jobs = (
        db.query(TrainingJob)
        .filter(TrainingJob.dataset_id == dataset_id)
        .order_by(TrainingJob.id.asc())
        .all()
    )

    out_dir = DATA_DIR / "reports" / str(dataset_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "report.pdf"
    tmp_path = out_dir / f".report.{os.getpid()}.tmp.pdf"

    doc = SimpleDocTemplate(str(tmp_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(_t(lang, "title").format(name=escape(str(ds.name))), styles["Title"]))
    story.append(Spacer(1, 12))

    info_data = [
        [_t(lang, "field"), _t(lang, "value")],
        [_t(lang, "id"), str(ds.id)],
        [_t(lang, "name"), str(ds.name)],
        [_t(lang, "rows"), str(ds.rows)],
        [_t(lang, "cols"), str(ds.cols)],
        [_t(lang, "created"), str(ds.created_at)],
    ]
    info_table = Table(info_data, colWidths=[120, 400])
    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F46E5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
            ]
        )
    )
    story.append(info_table)
    story.append(Spacer(1, 16))

    # Missing values
    story.append(Paragraph(_t(lang, "missing"), styles["Heading2"]))
    missing = df.isna().sum()
    missing_data = [[_t(lang, "column"), _t(lang, "missing_count")]]
    for col, val in missing.items():
        missing_data.append([str(col), str(int(val))])
    missing_table = Table(missing_data, colWidths=[260, 120])
    missing_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F46E5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    story.append(missing_table)
    story.append(Spacer(1, 16))

    # Numeric summary
    story.append(Paragraph(_t(lang, "numeric_summary"), styles["Heading2"]))
    numeric = df.select_dtypes(include="number")
    if numeric.empty:
        story.append(Paragraph(_t(lang, "no_numeric"), styles["Normal"]))
    else:
        desc = numeric.describe().round(4)
        summary_data = [[""] + [str(c) for c in desc.columns]]
        for idx in desc.index:
            summary_data.append([str(idx)] + [str(desc.loc[idx, c]) for c in desc.columns])
        summary_table = Table(summary_data)
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F46E5")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(summary_table)
    story.append(Spacer(1, 16))

    # Training jobs
    story.append(Paragraph(_t(lang, "jobs"), styles["Heading2"]))
    if not jobs:
        story.append(Paragraph(_t(lang, "no_jobs"), styles["Normal"]))
    else:
        jobs_data = [[
            "ID",
            _t(lang, "type"),
            _t(lang, "problem"),
            _t(lang, "algorithm"),
            _t(lang, "status"),
            _t(lang, "metrics"),
        ]]
        for j in jobs:
            metrics = j.metrics_json
            if isinstance(metrics, dict):
                metric_str = ", ".join(f"{k}={v}" for k, v in list(metrics.items())[:6])
            else:
                metric_str = str(metrics) if metrics is not None else ""
            jobs_data.append(
                [
                    str(j.id),
                    str(j.task_type),
                    str(j.problem),
                    str(j.algorithm),
                    str(j.status),
                    metric_str,
                ]
            )
        jobs_table = Table(jobs_data, colWidths=[30, 70, 80, 90, 70, 200])
        jobs_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F46E5")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(jobs_table)
    story.append(Spacer(1, 16))

    # EDA plots
    plots = _find_plots(dataset_id)
    if plots:
        story.append(Paragraph(_t(lang, "eda_plots"), styles["Heading2"]))
        for p in plots:
            try:
                story.append(Paragraph(str(p.name), styles["Normal"]))
                img = Image(str(p), width=420, height=300)
                story.append(img)
                story.append(Spacer(1, 12))
            except Exception:
                continue

    doc.build(story)
    os.replace(tmp_path, pdf_path)
    return pdf_path
