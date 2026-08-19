from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.schemas.grievance import GrievanceResponse

class CitizenDashboardResponse(BaseModel):
    total_grievances: int
    submitted: int
    in_progress: int
    awaiting_verification: int
    closed: int
    reopened: int
    unread_notifications: int
    recent_grievances: List[GrievanceResponse]

class OfficerDashboardResponse(BaseModel):
    assigned_grievances: int
    pending_acknowledgement: int
    in_progress: int
    resolution_pending_verification: int
    overdue_grievances: int
    high_risk_grievances: int
    unread_notifications: int
    department_name: Optional[str] = None

class SupervisorDashboardResponse(BaseModel):
    department_name: Optional[str] = None
    total_grievances: int
    total_active_grievances: int
    assigned_grievances: int
    in_progress_grievances: int
    resolved_grievances: int
    unassigned_routed_grievances: int
    overdue_grievances: int
    high_risk_grievances: int
    escalated_grievances: int
    pending_verification: int
    reopened_grievances: int
    officer_workload: Dict[str, int]

class DepartmentPerformance(BaseModel):
    id: str
    name: str
    total_grievances: int
    active_grievances: int
    overdue_grievances: int
    resolved_grievances: int
    resolution_rate: float

class AdminDashboardResponse(BaseModel):
    total_grievances: int
    grievances_by_department: Dict[str, int]
    grievances_by_state: Dict[str, int]
    sla_breaches: int
    sla_warnings: int
    escalated_grievances: int
    average_resolution_time_hours: float
    reopened_grievances: int
    risk_distribution: Dict[str, int]
    officer_workload: Dict[str, int]
    department_performance: List[DepartmentPerformance]