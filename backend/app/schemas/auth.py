import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from app.models.user import UserRole

# Safe Department schema for nested user profiles
class DepartmentBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    code: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        # Simple validation: enforce non-blank
        if not v.strip():
            raise ValueError("Password cannot be empty or whitespace only")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenIn(BaseModel):
    refresh_token: Optional[str] = None

class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    department_id: Optional[uuid.UUID] = None
    department_name: Optional[str] = None
    is_active: bool
    preferred_language: str = "en"
    created_at: datetime
    updated_at: datetime

class UserSignupResponse(BaseModel):
    message: str
    user: UserProfile

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: UserProfile
