"""Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    rows: int
    cols: int
    created_at: datetime


class DatasetDetail(DatasetOut):
    columns: List[str] = []
    dtypes: Dict[str, str] = {}
    preview: List[Dict[str, Any]] = []


class TrainingStart(BaseModel):
    dataset_id: int
    task_type: Literal["supervised", "unsupervised"]
    problem: Literal["classification", "regression", "clustering", "dimensionality"]
    algorithm: str = Field(min_length=1, max_length=50)
    target_column: Optional[str] = Field(default=None, max_length=200)
    test_size: float = Field(default=0.2, gt=0.05, lt=0.5)
    params: Optional[Dict[str, Any]] = None


class TrainingJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    dataset_id: int
    task_type: str
    problem: str
    algorithm: str
    status: str
    params_json: Optional[Dict[str, Any]] = None
    target_column: Optional[str] = None
    test_size: float
    metrics_json: Optional[Dict[str, Any]] = None
    model_path: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    finished_at: Optional[datetime] = None


class ModelArtifactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    name: str
    path: str
    created_at: datetime


class ModelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    job_id: int
    name: str
    created_at: datetime
    algorithm: Optional[str] = None
    problem: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    dataset_id: int
    message: str = Field(min_length=1, max_length=4000)
    history: Optional[List[Dict[str, Any]]] = Field(default=None, max_length=50)
    lang: Optional[Literal["es", "en"]] = "es"


class ChatResponse(BaseModel):
    reply: str
