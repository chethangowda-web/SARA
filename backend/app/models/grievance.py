import uuid
from sqlalchemy import String, Text, ForeignKey, DateTime, func, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Grievance(Base):
    __tablename__ = "grievances"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    citizen_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    assigned_officer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Multilingual support
    original_language: Mapped[str] = mapped_column(String(10), default="en", server_default="en", nullable=False)
    original_title: Mapped[str] = mapped_column(String(255), nullable=True)
    original_description: Mapped[str] = mapped_column(Text, nullable=True)
    normalized_title: Mapped[str] = mapped_column(String(255), nullable=True)
    normalized_description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # AI Placeholders for Milestone 4
    category: Mapped[str] = mapped_column(String(100), nullable=True)
    classification_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    priority: Mapped[str] = mapped_column(String(50), nullable=True)
    priority_score: Mapped[int] = mapped_column(Float, nullable=True)
    priority_signals: Mapped[dict] = mapped_column(JSON, nullable=True)
    priority_explanation: Mapped[str] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    duplicate_info: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    current_state: Mapped[str] = mapped_column(String(50), default="SUBMITTED", nullable=False)
    
    # Governance Fields
    escalated: Mapped[bool] = mapped_column(default=False, server_default="false", nullable=False)
    escalation_level: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)
    risk_score: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)
    risk_factors: Mapped[dict] = mapped_column(JSON, nullable=True)
    risk_calculated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    submitted_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    citizen = relationship("User", foreign_keys=[citizen_id], back_populates="grievances_submitted")
    department = relationship("Department")
    assigned_officer_rel = relationship("User", foreign_keys=[assigned_officer_id])
    assignments = relationship("Assignment", back_populates="grievance", cascade="all, delete-orphan")
    events = relationship("GrievanceEvent", back_populates="grievance", cascade="all, delete-orphan")
    embedding_record = relationship("GrievanceEmbedding", back_populates="grievance", uselist=False, cascade="all, delete-orphan")
    comments = relationship("GrievanceComment", back_populates="grievance", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="grievance", cascade="all, delete-orphan")
