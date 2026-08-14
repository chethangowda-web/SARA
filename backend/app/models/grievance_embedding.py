import uuid
from sqlalchemy import ForeignKey, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.core.database import Base

class GrievanceEmbedding(Base):
    __tablename__ = "grievance_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    grievance_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("grievances.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    embedding: Mapped[Vector] = mapped_column(Vector(384), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), default="all-MiniLM-L6-v2", nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    grievance = relationship("Grievance", back_populates="embedding_record")
