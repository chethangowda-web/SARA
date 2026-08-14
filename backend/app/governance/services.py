import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.grievance import Grievance
from app.models.assignment import Assignment
from app.models.grievance_event import GrievanceEvent
from app.models.governance import SLAPolicy, AccountabilityDossier, Notification, SystemSetting
from app.services.audit_service import log_security_event

async def get_current_time(db: AsyncSession) -> datetime:
    """
    Returns the current server-side time, potentially modified by an admin-simulated time offset.
    Time offset is disabled in production.
    """
    real_now = datetime.now(timezone.utc)
    if settings.ENVIRONMENT == "production":
        return real_now

    result = await db.execute(select(SystemSetting).where(SystemSetting.key == "time_offset_seconds"))
    setting = result.scalars().first()
    if setting:
        try:
            offset_seconds = int(setting.value)
            return real_now + timedelta(seconds=offset_seconds)
        except ValueError:
            pass
    return real_now

async def get_sla_policy(db: AsyncSession, department_id: Optional[uuid.UUID], priority: Optional[str]) -> SLAPolicy:
    """
    Retrieves the configured SLA policy for a department and priority.
    If no policy is found, returns a default fallback policy object (not persisted) to avoid crashes.
    """
    if department_id and priority:
        result = await db.execute(
            select(SLAPolicy).where(
                SLAPolicy.department_id == department_id,
                SLAPolicy.priority == priority
            )
        )
        policy = result.scalars().first()
        if policy:
            return policy

    # Fallback policies (Do not write inside database business logic, but returned as mock instances for safety)
    # Default SLA durations: CRITICAL=4h, HIGH=24h, MEDIUM=72h, LOW=168h (7 days)
    fallback_hours = 24
    p_upper = (priority or "HIGH").upper()
    if p_upper == "CRITICAL":
        fallback_hours = 4
    elif p_upper == "HIGH":
        fallback_hours = 24
    elif p_upper == "MEDIUM":
        fallback_hours = 72
    elif p_upper == "LOW":
        fallback_hours = 168

    return SLAPolicy(
        department_id=department_id or uuid.uuid4(),
        priority=priority or "HIGH",
        sla_hours=fallback_hours
    )

async def calculate_risk_score(db: AsyncSession, grievance: Grievance, current_time: datetime) -> tuple[int, dict]:
    """
    Calculates a deterministic risk score from 0-100 and returns a breakdown of risk factors.
    All factors have capped/maximum contributions.
    """
    factors = {}
    
    # Load all historical events for this grievance to analyze transition history
    res_events = await db.execute(
        select(GrievanceEvent)
        .where(GrievanceEvent.grievance_id == grievance.id)
        .order_by(GrievanceEvent.created_at.asc())
    )
    events = res_events.scalars().all()

    # Retrieve SLA policy
    policy = await get_sla_policy(db, grievance.department_id, grievance.priority)
    
    # 1. SLA Breach / Proximity
    # SLA clock starts at submitted_at or created_at
    start_time = grievance.submitted_at or grievance.created_at
    if start_time:
        sla_duration = timedelta(hours=policy.sla_hours)
        deadline = start_time + sla_duration
        elapsed = current_time - start_time
        
        if current_time >= deadline:
            factors["sla_breach"] = 35  # Max 35
        elif elapsed >= 0.8 * sla_duration:
            factors["sla_proximity"] = 15  # Max 15
            
    # 2. Officer Inactivity
    # Find active assignment
    res_assign = await db.execute(
        select(Assignment).where(
            Assignment.grievance_id == grievance.id,
            Assignment.is_active == True
        )
    )
    active_assign = res_assign.scalars().first()
    if active_assign:
        officer_id = active_assign.officer_id
        # Find latest officer activity
        officer_events = [e for e in events if e.actor_id == officer_id]
        if officer_events:
            last_activity = max(e.created_at for e in officer_events)
        else:
            last_activity = active_assign.assigned_at
            
        if current_time - last_activity > timedelta(hours=48):
            factors["officer_inactivity"] = 20  # Max 20

    # 3. Assignment Delay
    # Time between transition to ROUTED and transition to ASSIGNED
    routed_event = next((e for e in events if e.to_state == "ROUTED"), None)
    if routed_event:
        assigned_event = next((e for e in events if e.to_state == "ASSIGNED" and e.created_at > routed_event.created_at), None)
        if assigned_event:
            delay = assigned_event.created_at - routed_event.created_at
        else:
            delay = current_time - routed_event.created_at
            
        if delay > timedelta(hours=24):
            factors["assignment_delay"] = 15  # Max 15

    # 4. Missed Milestones
    # Capped at max 15 points
    milestone_points = 0
    if grievance.current_state == "ASSIGNED":
        # Find when it entered ASSIGNED state
        assigned_state_event = next((e for e in reversed(events) if e.to_state == "ASSIGNED"), None)
        entry_time = assigned_state_event.created_at if assigned_state_event else (grievance.assigned_at or start_time)
        if entry_time and current_time - entry_time > timedelta(hours=24):
            milestone_points = 15
    elif grievance.current_state == "ACKNOWLEDGED":
        # Find when it entered ACKNOWLEDGED state
        ack_state_event = next((e for e in reversed(events) if e.to_state == "ACKNOWLEDGED"), None)
        entry_time = ack_state_event.created_at if ack_state_event else start_time
        if entry_time and current_time - entry_time > timedelta(hours=24):
            milestone_points = 15
            
    if milestone_points > 0:
        factors["missed_milestone"] = milestone_points

    # 5. Citizen Rejection
    # 20 points per rejection, capped at 40 points total
    rejection_count = sum(1 for e in events if e.event_type == "RESOLUTION_REJECTED")
    if rejection_count > 0:
        factors["citizen_rejection"] = min(40, rejection_count * 20)  # Max 40

    total_score = min(100, sum(factors.values()))
    return total_score, factors

async def create_in_app_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    grievance_id: Optional[uuid.UUID],
    title: str,
    message: str,
    notification_type: str
) -> Notification:
    """
    Creates and records a user notification.
    """
    notif = Notification(
        user_id=user_id,
        grievance_id=grievance_id,
        title=title,
        message=message,
        type=notification_type,
        is_read=False,
        created_at=datetime.now(timezone.utc)
    )
    db.add(notif)
    return notif

async def get_department_supervisors(db: AsyncSession, department_id: uuid.UUID) -> List[User]:
    """
    Retrieves all active supervisors belonging to a department.
    """
    res = await db.execute(
        select(User).where(
            User.department_id == department_id,
            User.role == UserRole.SUPERVISOR,
            User.is_active == True
        )
    )
    return res.scalars().all()

async def trigger_escalation_level1(db: AsyncSession, grievance: Grievance, current_time: datetime) -> None:
    """
    LEVEL 1 Escalation: SLA Warning.
    Creates reminder notification/event for assigned officer.
    """
    # 1. Record event
    event = GrievanceEvent(
        grievance_id=grievance.id,
        actor_id=None,
        actor_role="SYSTEM",
        event_type="SLA_WARNING",
        from_state=grievance.current_state,
        to_state=grievance.current_state,
        reason="SLA warning threshold reached",
        metadata_json={"simulated_time": settings.ENVIRONMENT != "production", "simulated_now": current_time.isoformat()}
    )
    db.add(event)

    # 2. Get assigned officer
    res_assign = await db.execute(
        select(Assignment).where(
            Assignment.grievance_id == grievance.id,
            Assignment.is_active == True
        )
    )
    active_assign = res_assign.scalars().first()
    if active_assign:
        await create_in_app_notification(
            db=db,
            user_id=active_assign.officer_id,
            grievance_id=grievance.id,
            title="SLA Warning: Grievance Resolution SLA is close to expiring",
            message=f"Grievance '{grievance.title}' has elapsed over 80% of its SLA. Please resolve it soon.",
            notification_type="SLA_WARNING"
        )

async def trigger_escalation_level2(db: AsyncSession, grievance: Grievance, current_time: datetime) -> None:
    """
    LEVEL 2 Escalation: SLA Breached.
    Marks escalation, notifies supervisor, generates Accountability Dossier.
    """
    # 1. Update grievance governance fields
    grievance.escalated = True
    grievance.escalation_level = 2

    # 2. Record breach event
    event = GrievanceEvent(
        grievance_id=grievance.id,
        actor_id=None,
        actor_role="SYSTEM",
        event_type="SLA_BREACHED",
        from_state=grievance.current_state,
        to_state=grievance.current_state,
        reason="SLA deadline breached",
        metadata_json={"simulated_time": settings.ENVIRONMENT != "production", "simulated_now": current_time.isoformat()}
    )
    db.add(event)

    # 3. Recalculate risk score and factors
    score, factors = await calculate_risk_score(db, grievance, current_time)
    grievance.risk_score = score
    grievance.risk_factors = factors
    grievance.risk_calculated_at = current_time

    # 4. Generate/Insert Accountability Dossier
    res_dossier = await db.execute(
        select(AccountabilityDossier).where(AccountabilityDossier.grievance_id == grievance.id)
    )
    dossier = res_dossier.scalars().first()
    if not dossier:
        dossier = AccountabilityDossier(
            grievance_id=grievance.id,
            risk_score=score,
            risk_factors=factors
        )
        db.add(dossier)
        # Create dossier generation audit event
        dossier_event = GrievanceEvent(
            grievance_id=grievance.id,
            actor_id=None,
            actor_role="SYSTEM",
            event_type="DOSSIER_GENERATED",
            from_state=grievance.current_state,
            to_state=grievance.current_state,
            reason="Accountability dossier generated due to SLA breach",
            metadata_json={"dossier_id": str(dossier.id)}
        )
        db.add(dossier_event)

    # 5. Notify supervisors
    if grievance.department_id:
        supervisors = await get_department_supervisors(db, grievance.department_id)
        for supervisor in supervisors:
            # Notify of SLA Breach
            await create_in_app_notification(
                db=db,
                user_id=supervisor.id,
                grievance_id=grievance.id,
                title="SLA Breach: Grievance SLA has expired",
                message=f"Grievance '{grievance.title}' has breached its SLA. An Accountability Dossier has been generated.",
                notification_type="SLA_BREACH"
            )
            # Notify of Dossier Generation
            await create_in_app_notification(
                db=db,
                user_id=supervisor.id,
                grievance_id=grievance.id,
                title="Accountability Dossier Generated",
                message=f"An Accountability Dossier has been generated for grievance '{grievance.title}'.",
                notification_type="DOSSIER_GENERATION"
            )

async def trigger_escalation_level3(db: AsyncSession, grievance: Grievance, current_time: datetime) -> None:
    """
    LEVEL 3 Escalation: Citizen Rejected.
    Triggered when a grievance enters/remains in REOPENED due to citizen rejection.
    Updates the supervisor dossier and notifies supervisor.
    """
    grievance.escalated = True
    grievance.escalation_level = 3

    # Recalculate risk score and factors
    score, factors = await calculate_risk_score(db, grievance, current_time)
    grievance.risk_score = score
    grievance.risk_factors = factors
    grievance.risk_calculated_at = current_time

    # Update or Generate Accountability Dossier
    res_dossier = await db.execute(
        select(AccountabilityDossier).where(AccountabilityDossier.grievance_id == grievance.id)
    )
    dossier = res_dossier.scalars().first()
    if dossier:
        dossier.risk_score = score
        dossier.risk_factors = factors
        dossier.updated_at = current_time
    else:
        dossier = AccountabilityDossier(
            grievance_id=grievance.id,
            risk_score=score,
            risk_factors=factors
        )
        db.add(dossier)
        # Create dossier generation event
        dossier_event = GrievanceEvent(
            grievance_id=grievance.id,
            actor_id=None,
            actor_role="SYSTEM",
            event_type="DOSSIER_GENERATED",
            from_state=grievance.current_state,
            to_state=grievance.current_state,
            reason="Accountability dossier generated due to Level 3 escalation",
            metadata_json={"dossier_id": str(dossier.id)}
        )
        db.add(dossier_event)

    # Notify supervisors
    if grievance.department_id:
        supervisors = await get_department_supervisors(db, grievance.department_id)
        for supervisor in supervisors:
            # Notify of Citizen Rejection
            await create_in_app_notification(
                db=db,
                user_id=supervisor.id,
                grievance_id=grievance.id,
                title="Citizen Rejection: Resolution Rejected",
                message=f"The citizen has rejected the resolution for grievance '{grievance.title}'.",
                notification_type="CITIZEN_REJECTION"
            )
            # Notify of Escalation level change
            await create_in_app_notification(
                db=db,
                user_id=supervisor.id,
                grievance_id=grievance.id,
                title="Supervisor Escalation: Level 3 Escalation Active",
                message=f"Grievance '{grievance.title}' has escalated to Level 3. The Accountability Dossier has been updated.",
                notification_type="SUPERVISOR_ESCALATION"
            )

async def evaluate_grievance_slas(db: AsyncSession) -> None:
    """
    Main background job runner. Evaluates all active grievances against SLA policies.
    Identifies warnings and breaches, preventing duplicate events/notifications.
    """
    current_time = await get_current_time(db)
    
    # Active states
    active_states = ["SUBMITTED", "CLASSIFIED", "ROUTED", "ASSIGNED", "ACKNOWLEDGED", "IN_PROGRESS", "REOPENED"]
    
    # Query all active grievances
    result = await db.execute(
        select(Grievance)
        .where(Grievance.current_state.in_(active_states))
    )
    grievances = result.scalars().all()
    
    for grievance in grievances:
        # Check if department and priority are set
        if not grievance.department_id:
            # Can't evaluate SLA without a routed department
            continue
            
        policy = await get_sla_policy(db, grievance.department_id, grievance.priority)
        
        # Calculate start time
        start_time = grievance.submitted_at or grievance.created_at
        if not start_time:
            continue
            
        sla_duration = timedelta(hours=policy.sla_hours)
        deadline = start_time + sla_duration
        warning_threshold = start_time + 0.8 * sla_duration
        
        # 1. Fetch events since start_time to prevent duplicates
        res_events = await db.execute(
            select(GrievanceEvent).where(
                GrievanceEvent.grievance_id == grievance.id,
                GrievanceEvent.created_at >= start_time
            )
        )
        events = res_events.scalars().all()
        
        has_warning_event = any(e.event_type == "SLA_WARNING" for e in events)
        has_breach_event = any(e.event_type == "SLA_BREACHED" for e in events)
        
        # Evaluate SLA breaches and warnings
        if current_time >= deadline:
            if not has_breach_event:
                # Trigger Level 2 Escalation (SLA Breached)
                await trigger_escalation_level2(db, grievance, current_time)
                await db.flush()
        elif current_time >= warning_threshold:
            if not has_warning_event:
                # Trigger Level 1 Escalation (SLA Warning)
                await trigger_escalation_level1(db, grievance, current_time)
                await db.flush()
                
        # Periodically update the risk score of all active grievances
        score, factors = await calculate_risk_score(db, grievance, current_time)
        grievance.risk_score = score
        grievance.risk_factors = factors
        grievance.risk_calculated_at = current_time
        
        # If dossier exists, keep it updated with the live risk score
        res_dossier = await db.execute(
            select(AccountabilityDossier).where(AccountabilityDossier.grievance_id == grievance.id)
        )
        dossier = res_dossier.scalars().first()
        if dossier:
            dossier.risk_score = score
            dossier.risk_factors = factors
            dossier.updated_at = current_time
            
        await db.flush()
        
    await db.commit()
