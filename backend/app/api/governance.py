import uuid
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from app.core.config import settings
from app.core.rate_limiter import RateLimiter
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.grievance import Grievance
from app.models.assignment import Assignment
from app.models.grievance_event import GrievanceEvent
from app.models.governance import SLAPolicy, AccountabilityDossier, Notification, SystemSetting
from app.services.audit_service import log_security_event
from app.schemas.governance import (
    SLAPolicyCreate,
    SLAPolicyResponse,
    TimeSimulationRequest,
    NotificationResponse,
    AccountabilityDossierResponse,
    GrievanceRiskResponse,
    OfficerBrief,
    SLAPolicyBrief,
    DossierTimelineItem
)
from app.governance.services import get_current_time, get_sla_policy, calculate_risk_score

router = APIRouter(tags=["governance"])

# Common auth validation helper for a grievance (copied from grievances.py to prevent circular import)
async def _verify_access_auth(grievance: Grievance, user: User, db: AsyncSession) -> None:
    if user.role == UserRole.ADMIN:
        return
        
    if user.role == UserRole.CITIZEN:
        if grievance.citizen_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: citizen does not own this resource"
            )
        return
        
    if user.role == UserRole.OFFICER:
        # Check active assignment
        result = await db.execute(
            select(Assignment).where(
                Assignment.grievance_id == grievance.id,
                Assignment.officer_id == user.id,
                Assignment.is_active == True
            )
        )
        if not result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: officer is not currently assigned to this resource"
            )
        return
        
    if user.role == UserRole.SUPERVISOR:
        if grievance.department_id != user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: supervisor department mismatch"
            )
        return
        
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


# ADMIN: GET /api/v1/admin/policies
@router.get("/admin/policies", response_model=List[SLAPolicyResponse])
async def list_sla_policies(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(RoleChecker([UserRole.ADMIN]))
):
    result = await db.execute(select(SLAPolicy))
    return result.scalars().all()


# ADMIN: POST /api/v1/admin/policies (Create or Update)
@router.post("/admin/policies", response_model=SLAPolicyResponse)
async def create_or_update_sla_policy(
    data: SLAPolicyCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(RoleChecker([UserRole.ADMIN]))
):
    # Verify department exists
    res_dept = await db.execute(select(Department).where(Department.id == data.department_id))
    dept = res_dept.scalars().first()
    if not dept:
        raise HTTPException(status_code=400, detail="Invalid department specified")

    # Check if policy already exists
    res_policy = await db.execute(
        select(SLAPolicy).where(
            SLAPolicy.department_id == data.department_id,
            SLAPolicy.priority == data.priority
        )
    )
    policy = res_policy.scalars().first()

    async with db.begin_nested():
        if policy:
            previous_state = {"sla_hours": policy.sla_hours}
            policy.sla_hours = data.sla_hours
            policy.updated_at = datetime.now(timezone.utc)
            new_state = {"sla_hours": policy.sla_hours}
            action = "SLA_POLICY_UPDATED"
        else:
            policy = SLAPolicy(
                department_id=data.department_id,
                priority=data.priority,
                sla_hours=data.sla_hours
            )
            db.add(policy)
            previous_state = {}
            new_state = {"department_id": str(data.department_id), "priority": data.priority, "sla_hours": data.sla_hours}
            action = "SLA_POLICY_CREATED"

        await db.flush()

        await log_security_event(
            db=db,
            action=action,
            actor_id=admin.id,
            actor_role=admin.role.value,
            resource_type="sla_policy",
            resource_id=policy.id,
            previous_state=previous_state,
            new_state=new_state
        )

    await db.commit()
    return policy


# ADMIN: DELETE /api/v1/admin/policies/{id}
@router.delete("/admin/policies/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sla_policy(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(RoleChecker([UserRole.ADMIN]))
):
    result = await db.execute(select(SLAPolicy).where(SLAPolicy.id == id))
    policy = result.scalars().first()
    if not policy:
        raise HTTPException(status_code=404, detail="SLA Policy not found")

    async with db.begin_nested():
        await db.delete(policy)
        await log_security_event(
            db=db,
            action="SLA_POLICY_DELETED",
            actor_id=admin.id,
            actor_role=admin.role.value,
            resource_type="sla_policy",
            resource_id=id,
            previous_state={"department_id": str(policy.department_id), "priority": policy.priority, "sla_hours": policy.sla_hours}
        )
    await db.commit()


# ADMIN: POST /api/v1/admin/demo/advance-time
@router.post("/admin/demo/advance-time", dependencies=[Depends(RateLimiter(5, 60, "admin"))])
async def advance_time_simulation(
    data: TimeSimulationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(RoleChecker([UserRole.ADMIN]))
):
    """
    Advances simulated time by a specific offset (in seconds).
    Strictly disabled in production environments.
    """
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Time simulation is restricted and disabled in production environments"
        )

    async with db.begin_nested():
        res_setting = await db.execute(select(SystemSetting).where(SystemSetting.key == "time_offset_seconds"))
        setting = res_setting.scalars().first()

        prev_offset = "0"
        if setting:
            prev_offset = setting.value
            try:
                current_offset = int(setting.value)
            except ValueError:
                current_offset = 0
            setting.value = str(current_offset + data.offset_seconds)
        else:
            setting = SystemSetting(key="time_offset_seconds", value=str(data.offset_seconds))
            db.add(setting)

        await db.flush()
        
        sim_now = datetime.now(timezone.utc) + timedelta(seconds=int(setting.value))

        await log_security_event(
            db=db,
            action="DEMO_TIME_TRAVEL_SIMULATED",
            actor_id=admin.id,
            actor_role=admin.role.value,
            resource_type="system_setting",
            resource_id=None,
            previous_state={"offset_seconds": prev_offset},
            new_state={"offset_seconds": setting.value, "simulated_time": sim_now.isoformat()},
            ip_address=request.client.host if request.client else None
        )

    await db.commit()
    return {
        "status": "success",
        "offset_seconds_added": data.offset_seconds,
        "total_offset_seconds": int(setting.value),
        "simulated_time": sim_now.isoformat()
    }


# SUPERVISOR: GET /api/v1/supervisor/dossiers
@router.get("/supervisor/dossiers", response_model=List[AccountabilityDossierResponse])
async def list_department_dossiers(
    db: AsyncSession = Depends(get_db),
    supervisor: User = Depends(RoleChecker([UserRole.SUPERVISOR]))
):
    """
    Lists all Accountability Dossiers for grievances in the supervisor's department.
    """
    if not supervisor.department_id:
        raise HTTPException(status_code=400, detail="Supervisor must belong to a department")

    # Fetch dossiers for grievances in supervisor's department
    result = await db.execute(
        select(AccountabilityDossier)
        .join(Grievance, AccountabilityDossier.grievance_id == Grievance.id)
        .where(Grievance.department_id == supervisor.department_id)
        .options(
            selectinload(AccountabilityDossier.grievance)
            .selectinload(Grievance.events),
            selectinload(AccountabilityDossier.grievance)
            .selectinload(Grievance.assignments)
            .selectinload(Assignment.officer)
        )
    )
    dossiers = result.scalars().all()
    
    current_time = await get_current_time(db)
    response_list = []
    
    for dossier in dossiers:
        g = dossier.grievance
        policy = await get_sla_policy(db, g.department_id, g.priority)
        
        # Calculate SLA details
        start_time = g.submitted_at or g.created_at
        sla_deadline = start_time + timedelta(hours=policy.sla_hours) if start_time else None
        warning_generated = any(e.event_type == "SLA_WARNING" for e in g.events)
        breach_generated = any(e.event_type == "SLA_BREACHED" for e in g.events)
        
        # Calculate Assignment details
        active_assign = next((a for a in g.assignments if a.is_active), None)
        assigned_officer = None
        assigned_at = None
        inactivity_hours = 0.0
        
        if active_assign:
            assigned_officer = OfficerBrief(
                id=active_assign.officer.id,
                full_name=active_assign.officer.full_name,
                email=active_assign.officer.email
            )
            assigned_at = active_assign.assigned_at
            # Inactivity calculation
            officer_events = [e for e in g.events if e.actor_id == active_assign.officer_id]
            last_activity = max((e.created_at for e in officer_events), default=active_assign.assigned_at)
            inactivity_hours = (current_time - last_activity).total_seconds() / 3600.0
            
        citizen_rejections_count = sum(1 for e in g.events if e.event_type == "RESOLUTION_REJECTED")
        
        # Evidence notes (if RESOLUTION_SUBMITTED)
        res_submitted_event = next((e for e in reversed(g.events) if e.event_type == "RESOLUTION_SUBMITTED"), None)
        evidence_status = res_submitted_event.reason if res_submitted_event else None
        
        # Compile timeline
        timeline_items = [
            DossierTimelineItem(
                event_type=e.event_type,
                from_state=e.from_state,
                to_state=e.to_state,
                actor_role=e.actor_role,
                reason=e.reason,
                created_at=e.created_at
            ) for e in g.events
        ]
        
        response_list.append(
            AccountabilityDossierResponse(
                id=dossier.id,
                grievance_id=dossier.grievance_id,
                risk_score=dossier.risk_score,
                risk_factors=dossier.risk_factors,
                created_at=dossier.created_at,
                updated_at=dossier.updated_at,
                title=g.title,
                description=g.description,
                current_state=g.current_state,
                escalated=g.escalated,
                escalation_level=g.escalation_level,
                sla_policy=SLAPolicyBrief(priority=policy.priority, sla_hours=policy.sla_hours),
                sla_deadline=sla_deadline,
                warning_generated=warning_generated,
                breach_generated=breach_generated,
                assigned_officer=assigned_officer,
                assigned_at=assigned_at,
                inactivity_hours=max(0.0, inactivity_hours),
                citizen_rejections_count=citizen_rejections_count,
                evidence_status=evidence_status,
                timeline=timeline_items
            )
        )
        
    return response_list


# SUPERVISOR: GET /api/v1/supervisor/dossiers/{id}
@router.get("/supervisor/dossiers/{id}", response_model=AccountabilityDossierResponse)
async def get_accountability_dossier(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    supervisor: User = Depends(RoleChecker([UserRole.SUPERVISOR]))
):
    """
    Retrieves a detailed Accountability Dossier by dossier ID or grievance ID.
    Enforces supervisor department boundary check.
    """
    if not supervisor.department_id:
        raise HTTPException(status_code=400, detail="Supervisor must belong to a department")

    # Attempt to fetch by dossier ID or grievance ID
    result = await db.execute(
        select(AccountabilityDossier)
        .where(
            (AccountabilityDossier.id == id) | 
            (AccountabilityDossier.grievance_id == id)
        )
        .options(
            selectinload(AccountabilityDossier.grievance)
            .selectinload(Grievance.events),
            selectinload(AccountabilityDossier.grievance)
            .selectinload(Grievance.assignments)
            .selectinload(Assignment.officer)
        )
    )
    dossier = result.scalars().first()
    if not dossier:
        raise HTTPException(status_code=404, detail="Accountability Dossier not found")

    g = dossier.grievance
    
    # Enforce department boundary check
    if g.department_id != supervisor.department_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: dossier belongs to a different department"
        )

    current_time = await get_current_time(db)
    policy = await get_sla_policy(db, g.department_id, g.priority)
    
    # Calculate SLA details
    start_time = g.submitted_at or g.created_at
    sla_deadline = start_time + timedelta(hours=policy.sla_hours) if start_time else None
    warning_generated = any(e.event_type == "SLA_WARNING" for e in g.events)
    breach_generated = any(e.event_type == "SLA_BREACHED" for e in g.events)
    
    # Calculate Assignment details
    active_assign = next((a for a in g.assignments if a.is_active), None)
    assigned_officer = None
    assigned_at = None
    inactivity_hours = 0.0
    
    if active_assign:
        assigned_officer = OfficerBrief(
            id=active_assign.officer.id,
            full_name=active_assign.officer.full_name,
            email=active_assign.officer.email
        )
        assigned_at = active_assign.assigned_at
        # Inactivity calculation
        officer_events = [e for e in g.events if e.actor_id == active_assign.officer_id]
        last_activity = max((e.created_at for e in officer_events), default=active_assign.assigned_at)
        inactivity_hours = (current_time - last_activity).total_seconds() / 3600.0
        
    citizen_rejections_count = sum(1 for e in g.events if e.event_type == "RESOLUTION_REJECTED")
    
    # Evidence notes (if RESOLUTION_SUBMITTED)
    res_submitted_event = next((e for e in reversed(g.events) if e.event_type == "RESOLUTION_SUBMITTED"), None)
    evidence_status = res_submitted_event.reason if res_submitted_event else None
    
    # Compile timeline
    timeline_items = [
        DossierTimelineItem(
            event_type=e.event_type,
            from_state=e.from_state,
            to_state=e.to_state,
            actor_role=e.actor_role,
            reason=e.reason,
            created_at=e.created_at
        ) for e in g.events
    ]
    
    return AccountabilityDossierResponse(
        id=dossier.id,
        grievance_id=dossier.grievance_id,
        risk_score=dossier.risk_score,
        risk_factors=dossier.risk_factors,
        created_at=dossier.created_at,
        updated_at=dossier.updated_at,
        title=g.title,
        description=g.description,
        current_state=g.current_state,
        escalated=g.escalated,
        escalation_level=g.escalation_level,
        sla_policy=SLAPolicyBrief(priority=policy.priority, sla_hours=policy.sla_hours),
        sla_deadline=sla_deadline,
        warning_generated=warning_generated,
        breach_generated=breach_generated,
        assigned_officer=assigned_officer,
        assigned_at=assigned_at,
        inactivity_hours=max(0.0, inactivity_hours),
        citizen_rejections_count=citizen_rejections_count,
        evidence_status=evidence_status,
        timeline=timeline_items
    )


# SHARED/ROLE-SCOPED: GET /api/v1/grievances/{id}/risk
@router.get("/grievances/{id}/risk", response_model=GrievanceRiskResponse)
async def get_grievance_risk(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Retrieves the calculated risk score and factor breakdown for a grievance.
    """
    # Fetch grievance
    result = await db.execute(select(Grievance).where(Grievance.id == id))
    grievance = result.scalars().first()
    if not grievance:
        raise HTTPException(status_code=404, detail="Grievance not found")

    # Verify authorization
    await _verify_access_auth(grievance, user, db)

    return GrievanceRiskResponse(
        grievance_id=grievance.id,
        risk_score=grievance.risk_score,
        risk_factors=grievance.risk_factors or {},
        calculated_at=grievance.risk_calculated_at
    )


# SHARED/ROLE-SCOPED: GET /api/v1/grievances/{id}/notifications
@router.get("/grievances/{id}/notifications", response_model=List[NotificationResponse])
async def list_grievance_notifications(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Retrieves notifications related to a grievance specifically addressed to the calling user.
    """
    # Fetch grievance
    result = await db.execute(select(Grievance).where(Grievance.id == id))
    grievance = result.scalars().first()
    if not grievance:
        raise HTTPException(status_code=404, detail="Grievance not found")

    # Verify authorization to view grievance
    await _verify_access_auth(grievance, user, db)

    # Fetch notifications for this user and grievance
    res_notif = await db.execute(
        select(Notification).where(
            Notification.grievance_id == id,
            Notification.user_id == user.id
        ).order_by(Notification.created_at.desc())
    )
    return res_notif.scalars().all()
