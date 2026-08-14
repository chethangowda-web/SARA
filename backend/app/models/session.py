import uuid
from sqlalchemy import String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_jti: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    expires_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ip_address: Mapped[str] = mapped_column(
        String(45), nullable=True
    )
    user_agent: Mapped[str] = mapped_column(
        Text, nullable=True
    )

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")
