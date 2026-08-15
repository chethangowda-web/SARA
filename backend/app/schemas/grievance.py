import uuid
import enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.auth import UserProfile, DepartmentBase

class VerificationAction(str, enum.Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"

class GrievanceCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=150)
    description: str = Field(..., min_length=10)
    location: str = Field(..., min_length=3, max_length=255)

class GrievanceRoute(BaseModel):
    department_id: uuid.UUID

class GrievanceAssign(BaseModel):
    officer_id: uuid.UUID

class GrievanceResolve(BaseModel):
    resolution_notes: str = Field(..., min_length=5)
    evidence_ids: Optional[List[uuid.UUID]] = None

class GrievanceVerify(BaseModel):
    action: VerificationAction
    reason: Optional[str] = None

class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    grievance_id: uuid.UUID
    officer_id: uuid.UUID
    assigned_by: Optional[uuid.UUID] = None
    assigned_at: datetime
    unassigned_at: Optional[datetime] = None
    is_active: bool

class GrievanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    citizen_id: uuid.UUID
    department_id: Optional[uuid.UUID] = None
    title: str
    description: str
    location: str
    category: Optional[str] = None
    classification_confidence: Optional[float] = None
    priority: Optional[str] = None
    priority_score: Optional[int] = None
    priority_signals: Optional[Dict[str, Any]] = None
    priority_explanation: Optional[str] = None
    summary: Optional[str] = None
    duplicate_info: Optional[Dict[str, Any]] = None
    current_state: str
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # Nested helpers for rich API output
    citizen: Optional[UserProfile] = None
    department: Optional[DepartmentBase] = None

class GrievanceEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    grievance_id: uuid.UUID
    actor_id: Optional[uuid.UUID] = None
    actor_role: Optional[str] = None
    event_type: str
    from_state: Optional[str] = None
    to_state: Optional[str] = None
    reason: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime
