import uuid
from datetime import date, datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Date, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("departments.id", ondelete="CASCADE"), nullable=True)
    
    total_grievances: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    open_grievances: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    closed_grievances: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sla_breaches: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    escalated_grievances: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    average_resolution_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    average_assignment_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    average_acknowledgement_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    department = relationship("Department")

class OperationalAnomaly(Base):
    __tablename__ = "operational_anomalies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    department_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("departments.id", ondelete="CASCADE"), nullable=True)
    
    anomaly_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    observed_value: Mapped[float] = mapped_column(Float, nullable=False)
    expected_value: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    department = relationship("Department")
