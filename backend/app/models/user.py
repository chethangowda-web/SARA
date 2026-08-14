import uuid
import enum
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.session import RefreshToken
from app.models.audit import AuditLog
from app.models.grievance import Grievance

class UserRole(str, enum.Enum):
    CITIZEN = "CITIZEN"
    OFFICER = "OFFICER"
    SUPERVISOR = "SUPERVISOR"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    full_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_roles_enum"), nullable=False
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    department = relationship("Department", back_populates="users")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="actor")
    grievances_submitted = relationship("Grievance", back_populates="citizen", foreign_keys="[Grievance.citizen_id]")
