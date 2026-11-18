"""SQLAlchemy ORM models."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    path = Column(String(512), nullable=False)
    rows = Column(Integer, default=0)
    cols = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    jobs = relationship("TrainingJob", back_populates="dataset")


class TrainingJob(Base):
    __tablename__ = "training_jobs"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    task_type = Column(String(32), nullable=False)  # supervised | unsupervised
    problem = Column(String(32), nullable=False)  # classification | regression | clustering | dimensionality
    algorithm = Column(String(64), nullable=False)
    status = Column(String(32), default="pending")  # pending | running | completed | failed
    params_json = Column(JSON, default=dict)
    target_column = Column(String(255), nullable=True)
    test_size = Column(Float, default=0.2)
    metrics_json = Column(JSON, nullable=True)
    model_path = Column(String(512), nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    dataset = relationship("Dataset", back_populates="jobs")


class ModelArtifact(Base):
    __tablename__ = "model_artifacts"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("training_jobs.id"), nullable=False)
    name = Column(String(255), nullable=False)
    path = Column(String(512), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("TrainingJob")
