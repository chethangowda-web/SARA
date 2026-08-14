from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_

from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from app.models.user import User, UserRole
from app.models.grievance import Grievance
from app.models.assignment import Assignment
from app.models.governance import Notification
from app.schemas.dashboard import (
    CitizenDashboardResponse,
    OfficerDashboardResponse,
    SupervisorDashboardResponse,
    AdminDashboardResponse
)
from app.schemas.grievance import GrievanceResponse

router = APIRouter(prefix="", tags=["dashboards"])

@router.get("/citizen/dashboard", response_model=CitizenDashboardResponse)
async def citizen_dashboard(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RoleChecker([UserRole.CITIZEN]))
):
    # Total grievances
    res_total = await db.execute(select(func.count(Grievance.id)).where(Grievance.citizen_id == user.id))
    total_grievances = res_total.scalar_one()

    # State counts
    res_states = await db.execute(
        select(Grievance.current_state, func.count(Grievance.id))
        .where(Grievance.citizen_id == user.id)
        .group_by(Grievance.current_state)
    )
    state_counts = {row[0]: row[1] for row in res_states.all()}

    # Unread notifications
    res_notif = await db.execute(
        select(func.count(Notification.id))
        .where(Notification.user_id == user.id, Notification.is_read == False)
    )
    unread_notifications = res_notif.scalar_one()

    # Recent grievances
    from sqlalchemy.orm import selectinload
    res_recent = await db.execute(
        select(Grievance)
        .where(Grievance.citizen_id == user.id)
        .order_by(Grievance.updated_at.desc())
        .limit(5)
        .options(selectinload(Grievance.citizen), selectinload(Grievance.department))
    )
    recent_grievances = res_recent.scalars().all()

    return CitizenDashboardResponse(
        total_grievances=total_grievances,
        submitted=state_counts.get("SUBMITTED", 0) + state_counts.get("CLASSIFIED", 0) + state_counts.get("ROUTED", 0),
        in_progress=state_counts.get("ASSIGNED", 0) + state_counts.get("ACKNOWLEDGED", 0) + state_counts.get("IN_PROGRESS", 0),
        awaiting_verification=state_counts.get("VERIFICATION", 0) + state_counts.get("RESOLUTION_SUBMITTED", 0),
        closed=state_counts.get("CLOSED", 0),
        reopened=state_counts.get("REOPENED", 0),
        unread_notifications=unread_notifications,
        recent_grievances=recent_grievances
    )

@router.get("/officer/dashboard", response_model=OfficerDashboardResponse)
async def officer_dashboard(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RoleChecker([UserRole.OFFICER]))
):
    # Subquery for active assignments
    active_assignments_subq = (
        select(Assignment.grievance_id)
        .where(Assignment.officer_id == user.id, Assignment.is_active == True)
        .subquery()
    )

    # Base query for officer's active grievances
    base_query = select(Grievance).where(Grievance.id.in_(select(active_assignments_subq)))

    # Counts
    res_total = await db.execute(select(func.count()).select_from(base_query.subquery()))
    assigned_grievances = res_total.scalar_one()

    res_states = await db.execute(
        select(Grievance.current_state, func.count(Grievance.id))
        .where(Grievance.id.in_(select(active_assignments_subq)))
        .group_by(Grievance.current_state)
    )
    state_counts = {row[0]: row[1] for row in res_states.all()}

    # High risk & overdue
    res_risk = await db.execute(
        select(func.count(Grievance.id))
        .where(
            Grievance.id.in_(select(active_assignments_subq)),
            Grievance.risk_score >= 70
        )
    )
    high_risk_grievances = res_risk.scalar_one()

    res_overdue = await db.execute(
        select(func.count(Grievance.id))
        .where(
            Grievance.id.in_(select(active_assignments_subq)),
            Grievance.escalated == True
        )
    )
    overdue_grievances = res_overdue.scalar_one()

    # Unread notifications
    res_notif = await db.execute(
        select(func.count(Notification.id))
        .where(Notification.user_id == user.id, Notification.is_read == False)
    )
    unread_notifications = res_notif.scalar_one()

    return OfficerDashboardResponse(
        assigned_grievances=assigned_grievances,
        pending_acknowledgement=state_counts.get("ASSIGNED", 0) + state_counts.get("REOPENED", 0),
        in_progress=state_counts.get("ACKNOWLEDGED", 0) + state_counts.get("IN_PROGRESS", 0),
        resolution_pending_verification=state_counts.get("RESOLUTION_SUBMITTED", 0) + state_counts.get("VERIFICATION", 0),
        overdue_grievances=overdue_grievances,
        high_risk_grievances=high_risk_grievances,
        unread_notifications=unread_notifications
    )

@router.get("/supervisor/dashboard", response_model=SupervisorDashboardResponse)
async def supervisor_dashboard(
    db: AsyncSession = Depends(get_db),
    supervisor: User = Depends(RoleChecker([UserRole.SUPERVISOR]))
):
    if not supervisor.department_id:
        raise HTTPException(status_code=400, detail="Supervisor has no department assigned")

    dept_id = supervisor.department_id

    # Total active grievances (not closed)
    res_active = await db.execute(
        select(func.count(Grievance.id))
        .where(Grievance.department_id == dept_id, Grievance.current_state != "CLOSED")
    )
    total_active_grievances = res_active.scalar_one()

    # States
    res_states = await db.execute(
        select(Grievance.current_state, func.count(Grievance.id))
        .where(Grievance.department_id == dept_id, Grievance.current_state != "CLOSED")
        .group_by(Grievance.current_state)
    )
    state_counts = {row[0]: row[1] for row in res_states.all()}

    # High risk & overdue & escalated
    from sqlalchemy import case
    res_metrics = await db.execute(
        select(
            func.sum(case((Grievance.escalated == True, 1), else_=0)),
            func.sum(case((Grievance.risk_score >= 70, 1), else_=0)),
            func.sum(case((Grievance.escalation_level > 0, 1), else_=0))
        )
        .where(Grievance.department_id == dept_id, Grievance.current_state != "CLOSED")
    )
    metrics = res_metrics.first()
    overdue_grievances = metrics[0] or 0
    high_risk_grievances = metrics[1] or 0
    escalated_grievances = metrics[2] or 0

    # Officer workload
    res_workload = await db.execute(
        select(User.full_name, func.count(Assignment.id))
        .join(Assignment, User.id == Assignment.officer_id)
        .join(Grievance, Assignment.grievance_id == Grievance.id)
        .where(
            User.department_id == dept_id, 
            Assignment.is_active == True,
            Grievance.current_state != "CLOSED"
        )
        .group_by(User.full_name)
    )
    officer_workload = {row[0]: row[1] for row in res_workload.all()}

    return SupervisorDashboardResponse(
        total_active_grievances=total_active_grievances,
        overdue_grievances=overdue_grievances,
        high_risk_grievances=high_risk_grievances,
        escalated_grievances=escalated_grievances,
        unassigned_routed_grievances=state_counts.get("ROUTED", 0),
        pending_verification=state_counts.get("VERIFICATION", 0) + state_counts.get("RESOLUTION_SUBMITTED", 0),
        reopened_grievances=state_counts.get("REOPENED", 0),
        officer_workload=officer_workload
    )

@router.get("/admin/dashboard", response_model=AdminDashboardResponse)
async def admin_dashboard(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(RoleChecker([UserRole.ADMIN]))
):
    # Total grievances
    res_total = await db.execute(select(func.count(Grievance.id)))
    total_grievances = res_total.scalar_one()

    # By Department
    from app.models.department import Department
    res_dept = await db.execute(
        select(Department.name, func.count(Grievance.id))
        .outerjoin(Grievance, Department.id == Grievance.department_id)
        .group_by(Department.name)
    )
    grievances_by_department = {row[0]: row[1] for row in res_dept.all()}

    # By State
    res_state = await db.execute(
        select(Grievance.current_state, func.count(Grievance.id))
        .group_by(Grievance.current_state)
    )
    grievances_by_state = {row[0]: row[1] for row in res_state.all()}

    # Escalations & Risk
    from sqlalchemy import case
    res_metrics = await db.execute(
        select(
            func.sum(case((Grievance.escalation_level == 1, 1), else_=0)),
            func.sum(case((Grievance.escalation_level == 2, 1), else_=0)),
            func.sum(case((Grievance.escalated == True, 1), else_=0))
        )
    )
    metrics = res_metrics.first()
    sla_warnings = metrics[0] or 0
    sla_breaches = metrics[1] or 0
    escalated_grievances = metrics[2] or 0

    # Risk Distribution (Buckets)
    res_risk = await db.execute(select(Grievance.risk_score))
    risk_scores = [r[0] for r in res_risk.all()]
    risk_distribution = {
        "Low (0-30)": sum(1 for s in risk_scores if s <= 30),
        "Medium (31-69)": sum(1 for s in risk_scores if 30 < s < 70),
        "High (70+)": sum(1 for s in risk_scores if s >= 70),
    }

    # Resolution Time
    res_time = await db.execute(
        select(
            func.avg(
                func.extract('epoch', Grievance.closed_at) - func.extract('epoch', Grievance.created_at)
            )
        ).where(Grievance.closed_at.is_not(None))
    )
    avg_seconds = res_time.scalar_one() or 0
    average_resolution_time_hours = round(avg_seconds / 3600.0, 2)

    # Officer workload
    res_workload = await db.execute(
        select(User.full_name, func.count(Assignment.id))
        .join(Assignment, User.id == Assignment.officer_id)
        .join(Grievance, Assignment.grievance_id == Grievance.id)
        .where(Assignment.is_active == True, Grievance.current_state != "CLOSED")
        .group_by(User.full_name)
        .order_by(func.count(Assignment.id).desc())
        .limit(10)
    )
    officer_workload = {row[0]: row[1] for row in res_workload.all()}

    return AdminDashboardResponse(
        total_grievances=total_grievances,
        grievances_by_department=grievances_by_department,
        grievances_by_state=grievances_by_state,
        sla_breaches=sla_breaches,
        sla_warnings=sla_warnings,
        escalated_grievances=escalated_grievances,
        average_resolution_time_hours=average_resolution_time_hours,
        reopened_grievances=grievances_by_state.get("REOPENED", 0),
        risk_distribution=risk_distribution,
        officer_workload=officer_workload
    )
