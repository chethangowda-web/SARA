import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Boolean, DateTime, Float, Integer, Text, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class GovernmentProject(Base):
    __tablename__ = "government_projects"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("departments.id"), nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    allocated_amount: Mapped[float] = mapped_column(Float, default=0.0)
    spent_amount: Mapped[float] = mapped_column(Float, default=0.0)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expected_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PLANNED", index=True)
    source: Mapped[str] = mapped_column(String(50), default="DEMO_SEEDED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    department = relationship("Department", lazy="joined")
    investment_matches = relationship("InvestmentMatch", back_populates="government_project", cascade="all, delete-orphan")


class NeedCluster(Base):
    __tablename__ = "need_clusters"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("departments.id"), nullable=True)
    location_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    complaint_count: Mapped[int] = mapped_column(Integer, default=0)
    unique_citizen_count: Mapped[int] = mapped_column(Integer, default=0)
    severity_score: Mapped[float] = mapped_column(Float, default=0.0)
    persistence_score: Mapped[float] = mapped_column(Float, default=0.0)
    unresolved_count: Mapped[int] = mapped_column(Integer, default=0)
    reopened_count: Mapped[int] = mapped_column(Integer, default=0)
    first_reported_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_reported_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    priority_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    priority_breakdown: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    department = relationship("Department", lazy="joined")
    investment_matches = relationship("InvestmentMatch", back_populates="need_cluster", cascade="all, delete-orphan")
    intelligence_alerts = relationship("IntelligenceAlert", back_populates="need_cluster", cascade="all, delete-orphan")


class InvestmentMatch(Base):
    __tablename__ = "investment_matches"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    need_cluster_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("need_clusters.id", ondelete="CASCADE"), nullable=False, index=True)
    government_project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("government_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    match_score: Mapped[float] = mapped_column(Float, default=0.0)
    match_reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    need_cluster = relationship("NeedCluster", back_populates="investment_matches")
    government_project = relationship("GovernmentProject", back_populates="investment_matches")


class IntelligenceAlert(Base):
    __tablename__ = "intelligence_alerts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(50), default="MEDIUM", index=True)
    need_cluster_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("need_clusters.id", ondelete="CASCADE"), nullable=True, index=True)
    government_project_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("government_projects.id", ondelete="CASCADE"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="OPEN", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    need_cluster = relationship("NeedCluster", back_populates="intelligence_alerts")
    government_project = relationship("GovernmentProject", lazy="joined")
