import uuid
from sqlalchemy import ForeignKey, DateTime, String, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class GrievanceEvent(Base):
    __tablename__ = "grievance_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    grievance_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("grievances.id", ondelete="CASCADE"), nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_role: Mapped[str] = mapped_column(String(50), nullable=True)
    
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    from_state: Mapped[str] = mapped_column(String(50), nullable=True)
    to_state: Mapped[str] = mapped_column(String(50), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    grievance = relationship("Grievance", back_populates="events")
    actor = relationship("User")
