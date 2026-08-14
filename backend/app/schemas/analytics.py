# Analytics Schemas
import uuid
from datetime import datetime, date
from typing import Optional, List, Dict
from pydantic import BaseModel

class TrendPoint(BaseModel):
    timestamp: str  # Can be date or datetime string depending on granularity
    value: float

class TrendResponse(BaseModel):
    metric: str
    points: List[TrendPoint]

class GlobalMetricsResponse(BaseModel):
    total_grievances: int
    open_grievances: int
    closed_grievances: int
    reopened_grievances: int
    sla_warnings: int
    sla_breaches: int
    escalated_grievances: int
    critical_high_risk: int
    average_resolution_hours: float
    average_acknowledgement_hours: float
    average_assignment_hours: float
    sla_compliance_percent: float

class DepartmentMetricsResponse(BaseModel):
    department_id: uuid.UUID
    department_name: str
    total_grievances: int
    open_grievances: int
    closed_grievances: int
    sla_compliance_percent: float
    average_resolution_hours: float
    average_assignment_hours: float
    average_acknowledgement_hours: float
    escalation_count: int
    risk_distribution: Dict[str, int]
    reopened_grievances: int

class OfficerMetricsResponse(BaseModel):
    officer_id: uuid.UUID
    officer_name: str
    assigned_grievances: int
    active_workload: int
    completed_grievances: int
    average_acknowledgement_hours: float
    average_resolution_hours: float
    sla_breaches: int
    reopened_grievances: int

class AnomalyResponse(BaseModel):
    id: uuid.UUID
    department_id: Optional[uuid.UUID]
    anomaly_type: str
    severity: str
    metric_name: str
    observed_value: float
    expected_value: float
    explanation: str
    detected_at: datetime
    acknowledged_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class AIInsightResponse(BaseModel):
    insights: List[str]
    generated_at: datetime
    provider: str
    is_fallback: bool
