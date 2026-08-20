import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

# Government Project Schemas
class GovernmentProjectBase(BaseModel):
    project_code: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    department_id: Optional[uuid.UUID] = None
    category: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    allocated_amount: float = Field(default=0.0, ge=0.0)
    spent_amount: float = Field(default=0.0, ge=0.0)
    start_date: Optional[datetime] = None
    expected_end_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    status: str = Field(default="PLANNED")
    source: str = Field(default="DEMO_SEEDED")

class GovernmentProjectCreate(GovernmentProjectBase):
    pass

class GovernmentProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    allocated_amount: Optional[float] = None
    spent_amount: Optional[float] = None
    status: Optional[str] = None
    actual_end_date: Optional[datetime] = None

class GovernmentProjectResponse(GovernmentProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    department_name: Optional[str] = None


# Need Cluster Schemas
class NeedClusterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    category: str
    department_id: Optional[uuid.UUID] = None
    department_name: Optional[str] = None
    location_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    complaint_count: int
    unique_citizen_count: int
    severity_score: float
    persistence_score: float
    unresolved_count: int
    reopened_count: int
    first_reported_at: Optional[datetime] = None
    last_reported_at: Optional[datetime] = None
    priority_score: float
    priority_breakdown: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: datetime


# Investment Match Schemas
class InvestmentMatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    need_cluster_id: uuid.UUID
    government_project_id: uuid.UUID
    match_score: float
    match_reason: str
    created_at: datetime
    government_project: Optional[GovernmentProjectResponse] = None


# Intelligence Alert Schemas
class IntelligenceAlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    type: str
    severity: str
    need_cluster_id: Optional[uuid.UUID] = None
    government_project_id: Optional[uuid.UUID] = None
    title: str
    description: str
    evidence_json: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: datetime


# Sangam Intelligence Overview Schema
class SangamOverviewResponse(BaseModel):
    total_active_needs: int
    active_hotspots_count: int
    unserved_gaps_count: int
    outcome_mismatches_count: int
    high_priority_count: int
    total_matched_investment: float
    recent_alerts: List[IntelligenceAlertResponse]
    top_priority_clusters: List[NeedClusterResponse]


# Evidence Drawer Response Schema
class EvidenceItemResponse(BaseModel):
    id: uuid.UUID
    tracking_number: str
    title: str
    description: str
    category: str
    current_state: str
    created_at: datetime
    location: str
    citizen_name: Optional[str] = None


class NeedEvidenceDrawerResponse(BaseModel):
    need_cluster: NeedClusterResponse
    contributing_grievances: List[EvidenceItemResponse]
    matched_projects: List[InvestmentMatchResponse]
    associated_alerts: List[IntelligenceAlertResponse]
    detection_reasoning: str
