import uuid
from sqlalchemy import String, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    actor_role: Mapped[str] = mapped_column(
        String(20), nullable=True
    )
    action: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    resource_type: Mapped[str] = mapped_column(
        String(50), nullable=True
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        nullable=True
    )
    previous_state: Mapped[dict] = mapped_column(
        JSON, nullable=True
    )
    new_state: Mapped[dict] = mapped_column(
        JSON, nullable=True
    )
    ip_address: Mapped[str] = mapped_column(
        String(45), nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    actor = relationship("User", back_populates="audit_logs")
