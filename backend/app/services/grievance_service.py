import uuid
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.user import User, UserRole
from app.models.department import Department
from app.models.grievance import Grievance
from app.models.assignment import Assignment
from app.models.grievance_event import GrievanceEvent
from app.services.audit_service import log_security_event

# Explicitly allowed transitions matrix
VALID_TRANSITIONS: Dict[str, List[str]] = {
    "SUBMITTED": ["CLASSIFIED"],
    "CLASSIFIED": ["ROUTED"],
    "ROUTED": ["ASSIGNED"],
    "ASSIGNED": ["ACKNOWLEDGED", "ON_HOLD", "ABORT_PENDING_REVIEW"],
    "ACKNOWLEDGED": ["IN_PROGRESS", "ON_HOLD", "ABORT_PENDING_REVIEW"],
    "IN_PROGRESS": ["RESOLUTION_SUBMITTED", "ON_HOLD", "ABORT_PENDING_REVIEW"],
    "ON_HOLD": ["IN_PROGRESS"], # and dynamic previous state
    "ABORT_PENDING_REVIEW": ["ABORTED", "IN_PROGRESS"], # or dynamic previous state
    "RESOLUTION_SUBMITTED": ["VERIFICATION", "IN_PROGRESS"],
    "VERIFICATION": ["CLOSED", "REOPENED"],
    "REOPENED": ["ASSIGNED", "ROUTED"]
}

async def create_grievance(
    db: AsyncSession,
    citizen: User,
    title: str,
    description: str,
    location: str,
    ip_address: Optional[str] = None
) -> Grievance:
    """
    Idempotent and atomic creation of a citizen grievance.
    """
    if citizen.role != UserRole.CITIZEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizen role can submit a grievance"
        )

    async with db.begin_nested():
        grievance = Grievance(
            citizen_id=citizen.id,
            title=title,
            description=description,
            location=location,
            current_state="SUBMITTED",
            submitted_at=datetime.now(timezone.utc)
        )
        db.add(grievance)
        await db.flush() # Populate ID
        
        # Log transition event
        event = GrievanceEvent(
            grievance_id=grievance.id,
            actor_id=citizen.id,
            actor_role=citizen.role.value,
            event_type="GRIEVANCE_SUBMITTED",
            to_state="SUBMITTED"
        )
        db.add(event)
        
        await log_security_event(
            db,
            action="GRIEVANCE_CREATED",
            actor_id=citizen.id,
            actor_role=citizen.role.value,
            resource_type="grievance",
            resource_id=grievance.id,
            ip_address=ip_address
        )
        await db.flush()
        
    await db.commit()
    
    # Eager load the final state with nested citizen/department relationships to prevent greenlet lazy-load errors
    res_final = await db.execute(
        select(Grievance)
        .where(Grievance.id == grievance.id)
        .options(selectinload(Grievance.citizen), selectinload(Grievance.department))
    )
    return res_final.scalars().first()

async def transition_grievance(
    db: AsyncSession,
    grievance_id: uuid.UUID,
    target_state: str,
    actor: User,
    payload: Optional[Dict[str, Any]] = None,
    is_admin_override: bool = False,
    override_reason: Optional[str] = None,
    ip_address: Optional[str] = None
) -> Grievance:
    """
    Deterministic transition service.
    """
    payload = payload or {}
    
    # 1. Fetch grievance
    result = await db.execute(select(Grievance).where(Grievance.id == grievance_id))
    grievance = result.scalars().first()
    if not grievance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grievance not found"
        )
        
    from_state = grievance.current_state
    
    # Check if actor exists in DB to prevent foreign key constraint violations
    actor_id_db = None
    if actor:
        res_actor = await db.execute(select(User.id).where(User.id == actor.id))
        if res_actor.scalars().first():
            actor_id_db = actor.id

    # Handle Admin Override
    if is_admin_override:
        if actor.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Override actions are restricted to system administrator role only"
            )
        if not override_reason or not override_reason.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A valid explanation reason is mandatory for administrative override transitions"
            )
        
        async with db.begin_nested():
            # Apply Override transitions
            grievance.current_state = target_state
            
            # Record events
            event = GrievanceEvent(
                grievance_id=grievance.id,
                actor_id=actor_id_db,
                actor_role=actor.role.value,
                event_type="ADMIN_OVERRIDE",
                from_state=from_state,
                to_state=target_state,
                reason=override_reason,
                metadata_json={"override": True}
            )
            db.add(event)
            
            await log_security_event(
                db,
                action="ADMIN_OVERRIDE_TRANSITION",
                actor_id=actor_id_db,
                actor_role=actor.role.value,
                resource_type="grievance",
                resource_id=grievance.id,
                previous_state={"state": from_state},
                new_state={"state": target_state},
                ip_address=ip_address
            )
            await db.flush()
            
        await db.commit()
        
        # Reload to load updated_at and nested relationships
        res_final = await db.execute(
            select(Grievance)
            .where(Grievance.id == grievance.id)
            .options(selectinload(Grievance.citizen), selectinload(Grievance.department))
        )
        return res_final.scalars().first()

    # Ensure nested transaction/savepoint context for complete rollback
    async with db.begin_nested():

        # Normal Transition Flow Validation
        allowed_targets = VALID_TRANSITIONS.get(from_state, [])
        if target_state not in allowed_targets:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid state transition sequence: cannot transition from {from_state} directly to {target_state}"
            )
            
        # Role/Permission and Predicate Checks
        if target_state == "CLASSIFIED":
            if actor.role not in [UserRole.ADMIN, UserRole.ADMIN.value]: # SYSTEM transitions bypass standard actor roles (System uses ADMIN internally)
                raise HTTPException(status_code=403, detail="Unauthorized transition role")
            # Set category/priority if present in payload
            if "category" in payload:
                grievance.category = payload["category"]
            if "priority" in payload:
                grievance.priority = payload["priority"]
            event_type = "GRIEVANCE_CLASSIFIED"
            
        elif target_state == "ROUTED":
            if actor.role not in [UserRole.ADMIN, UserRole.ADMIN.value]:
                raise HTTPException(status_code=403, detail="Unauthorized transition role")
            dept_id_str = payload.get("department_id")
            if not dept_id_str:
                raise HTTPException(status_code=400, detail="department_id is required for routing")
            dept_id = uuid.UUID(str(dept_id_str))
            
            # Verify department is active
            res_dept = await db.execute(select(Department).where(Department.id == dept_id))
            dept = res_dept.scalars().first()
            if not dept or not dept.is_active:
                raise HTTPException(status_code=400, detail="Invalid department specified")
            
            grievance.department_id = dept_id
            
            # Deactivate any active assignments when re-routing
            res_active = await db.execute(
                select(Assignment).where(Assignment.grievance_id == grievance.id, Assignment.is_active == True)
            )
            for old_assign in res_active.scalars().all():
                old_assign.is_active = False
                old_assign.unassigned_at = datetime.now(timezone.utc)
            grievance.assigned_officer_id = None
            
            event_type = "GRIEVANCE_ROUTED"
            
        elif target_state == "ASSIGNED":
            # Can transition from ROUTED or REOPENED
            if actor.role not in [UserRole.SUPERVISOR, UserRole.ADMIN]:
                raise HTTPException(status_code=403, detail="Unauthorized role permissions")
                
            officer_id_str = payload.get("officer_id")
            if not officer_id_str:
                raise HTTPException(status_code=400, detail="officer_id is required for assignments")
            officer_id = uuid.UUID(str(officer_id_str))
            
            # Verify officer exists, is active, belongs to the supervisor's department (if supervisor is actor)
            res_off = await db.execute(select(User).where(User.id == officer_id))
            officer = res_off.scalars().first()
            if not officer or not officer.is_active or officer.role != UserRole.OFFICER:
                raise HTTPException(status_code=400, detail="Invalid or inactive officer selected")
                
            # Verify department constraints
            if grievance.department_id is None:
                raise HTTPException(status_code=400, detail="Cannot assign officer to unrouted grievance")
                
            if officer.department_id != grievance.department_id:
                raise HTTPException(status_code=400, detail="Officer must belong to the routed department")
                
            if actor.role == UserRole.SUPERVISOR and actor.department_id != grievance.department_id:
                raise HTTPException(status_code=403, detail="Supervisor can only assign within their department")
                
            # Handle assignment records: deactivate active ones
            res_active = await db.execute(
                select(Assignment).where(Assignment.grievance_id == grievance.id, Assignment.is_active == True)
            )
            active_assignments = res_active.scalars().all()
            for old_assign in active_assignments:
                old_assign.is_active = False
                old_assign.unassigned_at = datetime.now(timezone.utc)
                
            # Create new assignment
            new_assignment = Assignment(
                grievance_id=grievance.id,
                officer_id=officer.id,
                assigned_by=actor.id,
                is_active=True,
                reason=payload.get("reason"),
                workload_snapshot=payload.get("workload_snapshot")
            )
            db.add(new_assignment)
            
            # Sync assigned_officer_id directly on the grievance
            grievance.assigned_officer_id = officer.id
            
            # Send notification
            from app.governance.services import create_in_app_notification
            await create_in_app_notification(
                db=db,
                user_id=officer.id,
                grievance_id=grievance.id,
                title="Grievance Assigned",
                message=f"You have been assigned grievance '{grievance.title}'.",
                notification_type="GRIEVANCE_ASSIGNED"
            )
            
            grievance.assigned_at = datetime.now(timezone.utc)
            event_type = "OFFICER_ASSIGNED"
            
        elif target_state == "ACKNOWLEDGED":
            # Fetch active assignment
            res_assign = await db.execute(
                select(Assignment).where(Assignment.grievance_id == grievance.id, Assignment.is_active == True)
            )
            active_assign = res_assign.scalars().first()
            if not active_assign:
                raise HTTPException(status_code=400, detail="No active assignment found for grievance")
                
            if actor.role != UserRole.ADMIN and actor.id != active_assign.officer_id:
                raise HTTPException(status_code=403, detail="Only the assigned officer can acknowledge work")
                
            event_type = "OFFICER_ACKNOWLEDGED"
            
        elif target_state == "IN_PROGRESS":
            # Supervisor action (rejection of resolution or rejection of abort request)
            is_supervisor_action = from_state in ["RESOLUTION_SUBMITTED", "ABORT_PENDING_REVIEW"]
            if is_supervisor_action:
                if actor.role == UserRole.SUPERVISOR:
                    if actor.department_id != grievance.department_id:
                        raise HTTPException(status_code=403, detail="Supervisor can only review within their department")
                elif actor.role != UserRole.ADMIN:
                    raise HTTPException(status_code=403, detail="Only the department supervisor can reject this request")
                rej_reason = payload.get("reason")
                if not rej_reason or not rej_reason.strip():
                    raise HTTPException(status_code=400, detail="Rejection reason explanation is required")
                
                res_assign = await db.execute(
                    select(Assignment).where(Assignment.grievance_id == grievance.id, Assignment.is_active == True)
                )
                active_assign = res_assign.scalars().first()
                
                if from_state == "RESOLUTION_SUBMITTED":
                    event_type = "RESOLUTION_REJECTED"
                    if active_assign:
                        from app.governance.services import create_in_app_notification
                        await create_in_app_notification(
                            db=db,
                            user_id=active_assign.officer_id,
                            grievance_id=grievance.id,
                            title="Resolution Requires Rework",
                            message=f"The resolution for grievance '{grievance.title}' was not approved by the supervisor. Please rework and resubmit.",
                            notification_type="RESOLUTION_REWORK_REQUESTED"
                        )
                else: # ABORT_PENDING_REVIEW
                    event_type = "ABORT_REJECTED"
                    if active_assign:
                        from app.governance.services import create_in_app_notification
                        await create_in_app_notification(
                            db=db,
                            user_id=active_assign.officer_id,
                            grievance_id=grievance.id,
                            title="Abort Request Rejected",
                            message=f"The abort request for grievance '{grievance.title}' was rejected by the supervisor. Please continue work.",
                            notification_type="ABORT_REJECTED"
                        )
            else:
                res_assign = await db.execute(
                    select(Assignment).where(Assignment.grievance_id == grievance.id, Assignment.is_active == True)
                )
                active_assign = res_assign.scalars().first()
                if not active_assign:
                    raise HTTPException(status_code=400, detail="No active assignment found for grievance")
                    
                if actor.role != UserRole.ADMIN and actor.id != active_assign.officer_id:
                    raise HTTPException(status_code=403, detail="Only the assigned officer can start work")
                    
                if from_state == "ON_HOLD":
                    event_type = "WORK_RESUMED"
                else:
                    event_type = "WORK_STARTED"
            
        elif target_state == "RESOLUTION_SUBMITTED":
            res_assign = await db.execute(
                select(Assignment).where(Assignment.grievance_id == grievance.id, Assignment.is_active == True)
            )
            active_assign = res_assign.scalars().first()
            if not active_assign:
                raise HTTPException(status_code=400, detail="No active assignment found for grievance")
                
            if actor.role != UserRole.ADMIN and actor.id != active_assign.officer_id:
                raise HTTPException(status_code=403, detail="Only the assigned officer can submit a resolution")
                
            res_notes = payload.get("resolution_notes")
            if not res_notes or not res_notes.strip():
                raise HTTPException(status_code=400, detail="Resolution notes/evidence is required")
                
            # Notify citizen that resolution has been submitted and awaits department review
            from app.governance.services import create_in_app_notification, get_department_supervisors
            await create_in_app_notification(
                db=db,
                user_id=grievance.citizen_id,
                grievance_id=grievance.id,
                title="Resolution Submitted",
                message=f"A resolution for grievance '{grievance.title}' has been submitted and is awaiting department supervisor review.",
                notification_type="RESOLUTION_SUBMITTED"
            )
            # Notify department supervisors that a resolution awaits their review
            if grievance.department_id:
                for sup in await get_department_supervisors(db, grievance.department_id):
                    await create_in_app_notification(
                        db=db,
                        user_id=sup.id,
                        grievance_id=grievance.id,
                        title="Resolution Pending Review",
                        message=f"A resolution for grievance '{grievance.title}' is awaiting your review.",
                        notification_type="RESOLUTION_PENDING_REVIEW"
                    )
            
            grievance.resolved_at = datetime.now(timezone.utc)
            event_type = "RESOLUTION_SUBMITTED"
            
        elif target_state == "VERIFICATION":
            # Supervisor approval of a submitted resolution:
            # RESOLUTION_SUBMITTED -> VERIFICATION, performed by the department supervisor.
            if from_state == "RESOLUTION_SUBMITTED":
                if actor.role == UserRole.SUPERVISOR:
                    if actor.department_id != grievance.department_id:
                        raise HTTPException(status_code=403, detail="Supervisor can only review within their department")
                    event_type = "RESOLUTION_APPROVED"
                elif actor.role == UserRole.ADMIN:
                    event_type = "RESOLUTION_APPROVED"
                else:
                    raise HTTPException(status_code=403, detail="Only the department supervisor can approve a resolution")
                # Notify citizen that resolution is approved and ready to verify
                from app.governance.services import create_in_app_notification
                await create_in_app_notification(
                    db=db,
                    user_id=grievance.citizen_id,
                    grievance_id=grievance.id,
                    title="Resolution Approved",
                    message=f"The resolution for grievance '{grievance.title}' has been approved. Please verify the resolution.",
                    notification_type="RESOLUTION_APPROVED"
                )
            else:
                if actor.role not in [UserRole.ADMIN, UserRole.ADMIN.value]:
                    raise HTTPException(status_code=403, detail="System action only")
                event_type = "VERIFICATION_STARTED"
            
        elif target_state in ["CLOSED", "REOPENED"]:
            if actor.role != UserRole.ADMIN and actor.id != grievance.citizen_id:
                raise HTTPException(status_code=403, detail="Only the original citizen who submitted the grievance can verify resolution")
                
            if target_state == "CLOSED":
                grievance.closed_at = datetime.now(timezone.utc)
                event_type = "RESOLUTION_ACCEPTED"
            else: # REOPENED
                rej_reason = payload.get("reason")
                if not rej_reason or not rej_reason.strip():
                    raise HTTPException(status_code=400, detail="Rejection reason explanation is required")
                event_type = "RESOLUTION_REJECTED"
                
            # Send notification to assigned officer
            res_assign = await db.execute(
                select(Assignment).where(Assignment.grievance_id == grievance.id, Assignment.is_active == True)
            )
            active_assign = res_assign.scalars().first()
            if active_assign:
                from app.governance.services import create_in_app_notification
                decision = "accepted" if target_state == "CLOSED" else "rejected"
                await create_in_app_notification(
                    db=db,
                    user_id=active_assign.officer_id,
                    grievance_id=grievance.id,
                    title="Citizen Verification",
                    message=f"The citizen has {decision} the resolution for grievance '{grievance.title}'.",
                    notification_type="CITIZEN_VERIFICATION"
                )
                
        elif target_state == "ON_HOLD":
            res_assign = await db.execute(
                select(Assignment).where(Assignment.grievance_id == grievance.id, Assignment.is_active == True)
            )
            active_assign = res_assign.scalars().first()
            if not active_assign:
                raise HTTPException(status_code=400, detail="No active assignment found for grievance")
            if actor.role != UserRole.ADMIN and actor.id != active_assign.officer_id:
                raise HTTPException(status_code=403, detail="Only the assigned officer can put a grievance on hold")
            
            payload["previous_status"] = from_state
            event_type = "GRIEVANCE_HELD"

        elif target_state == "ABORT_PENDING_REVIEW":
            res_assign = await db.execute(
                select(Assignment).where(Assignment.grievance_id == grievance.id, Assignment.is_active == True)
            )
            active_assign = res_assign.scalars().first()
            if not active_assign:
                raise HTTPException(status_code=400, detail="No active assignment found for grievance")
            if actor.role != UserRole.ADMIN and actor.id != active_assign.officer_id:
                raise HTTPException(status_code=403, detail="Only the assigned officer can request an abort")
            
            payload["previous_status"] = from_state
            event_type = "ABORT_REQUESTED"

        elif target_state == "ABORTED":
            if actor.role == UserRole.SUPERVISOR:
                if actor.department_id != grievance.department_id:
                    raise HTTPException(status_code=403, detail="Supervisor can only review within their department")
            elif actor.role != UserRole.ADMIN:
                raise HTTPException(status_code=403, detail="Only the department supervisor can approve an abort")
            
            # Deactivate active assignments
            res_assign = await db.execute(
                select(Assignment).where(Assignment.grievance_id == grievance.id, Assignment.is_active == True)
            )
            active_assign = res_assign.scalars().first()
            if active_assign:
                active_assign.is_active = False
                active_assign.unassigned_at = datetime.now(timezone.utc)
            
            grievance.closed_at = datetime.now(timezone.utc)
            event_type = "ABORT_APPROVED"

        else:
            raise HTTPException(status_code=400, detail="Unsupported state transition destination")

        # Update grievance state
        grievance.current_state = target_state
        
        # Append GrievanceEvent
        event = GrievanceEvent(
            grievance_id=grievance.id,
            actor_id=actor_id_db,
            actor_role=actor.role.value if hasattr(actor.role, "value") else str(actor.role),
            event_type=event_type,
            from_state=from_state,
            to_state=target_state,
            reason=payload.get("reason") or payload.get("resolution_notes") or override_reason,
            metadata_json=payload
        )
        db.add(event)
        
        await log_security_event(
            db,
            action=event_type,
            actor_id=actor_id_db,
            actor_role=actor.role.value if hasattr(actor.role, "value") else str(actor.role),
            resource_type="grievance",
            resource_id=grievance.id,
            previous_state={"state": from_state},
            new_state={"state": target_state},
            ip_address=ip_address
        )
        await db.flush()
        
        # Trigger Level 3 Escalation on Citizen Rejection (Reopen)
        if target_state == "REOPENED":
            from app.governance.services import trigger_escalation_level3, get_current_time
            sim_time = await get_current_time(db)
            await trigger_escalation_level3(db, grievance, sim_time)
            await db.flush()
            
    await db.commit()
    
    # Eager load the final state to prevent lazy-load greenlet errors during serialization
    res_final = await db.execute(
        select(Grievance)
        .where(Grievance.id == grievance.id)
        .options(selectinload(Grievance.citizen), selectinload(Grievance.department))
    )
    return res_final.scalars().first()
