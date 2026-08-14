import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole

class UserCreateAdmin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
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
