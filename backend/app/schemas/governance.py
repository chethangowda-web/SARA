import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class SLAPolicyCreate(BaseModel):
    department_id: uuid.UUID
    priority: str
    sla_hours: int

class SLAPolicyResponse(BaseModel):
    id: uuid.UUID
    department_id: uuid.UUID
    priority: str
    sla_hours: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TimeSimulationRequest(BaseModel):
    offset_seconds: int

class NotificationResponse(BaseModel):
    id: uuid.UUID
    grievance_id: Optional[uuid.UUID] = None
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class DossierTimelineItem(BaseModel):
    event_type: str
    from_state: Optional[str] = None
    to_state: Optional[str] = None
    actor_role: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime

class SLAPolicyBrief(BaseModel):
    priority: str
    sla_hours: int

class OfficerBrief(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str

class AccountabilityDossierResponse(BaseModel):
    id: uuid.UUID
    grievance_id: uuid.UUID
    risk_score: int
    risk_factors: dict
    created_at: datetime
    updated_at: datetime
    
    # Live Grievance Metadata
    title: str
    description: str
    current_state: str
    escalated: bool
    escalation_level: int
    
    # SLA Info
    sla_policy: Optional[SLAPolicyBrief] = None
    sla_deadline: Optional[datetime] = None
    warning_generated: bool
    breach_generated: bool
    
    # Assignment Info
    assigned_officer: Optional[OfficerBrief] = None
    assigned_at: Optional[datetime] = None
    
    # Activity & Rejections Info
    inactivity_hours: float
    citizen_rejections_count: int
    evidence_status: Optional[str] = None # Resolution notes if RESOLUTION_SUBMITTED or VERIFICATION
    
    # Timeline
    timeline: List[DossierTimelineItem]

    class Config:
        from_attributes = True

class GrievanceRiskResponse(BaseModel):
    grievance_id: uuid.UUID
    risk_score: int
    risk_factors: dict
    calculated_at: Optional[datetime] = None
