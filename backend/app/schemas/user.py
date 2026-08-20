import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.user import UserRole

class UserCreateAdmin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)
    role: UserRole
    department_id: Optional[uuid.UUID] = None

class UserUpdateAdmin(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    department_id: Optional[uuid.UUID] = None

class RoleUpdate(BaseModel):
    role: UserRole

class StatusUpdate(BaseModel):
    is_active: bool

class StaffAuthorizationCreate(BaseModel):
    email: EmailStr
    role: UserRole
    department_id: Optional[uuid.UUID] = None

class StaffAuthorizationUpdate(BaseModel):
    role: Optional[UserRole] = None
    department_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None

class StaffAuthorizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: EmailStr
    role: UserRole
    department_id: Optional[uuid.UUID] = None
    is_active: bool
    created_at: datetime
    revoked_at: Optional[datetime] = None
