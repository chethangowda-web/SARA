"""
Automatic department routing + workload-aware officer assignment service.

Design principles:
- AI classification is ADVISORY: the AI-produced category is validated against a
  whitelist routing table before it can influence protected workflow state.
- transition_grievance() remains the SINGLE authority for changing grievance
  lifecycle state. This service only *computes* the destination and then calls
  the centralized state machine.
- Officer selection is deterministic and workload-aware: the officer with the
  lowest active workload (fewest active assignments) is preferred, with stable
  tie-breaking on pending acknowledgements, overdue cases, then full name.
"""
import uuid
from typing import Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, case

from app.models.user import User, UserRole
from app.models.department import Department
from app.models.grievance import Grievance
from app.models.assignment import Assignment
from app.services.grievance_service import transition_grievance
from app.governance.services import create_in_app_notification, get_department_supervisors

SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")

# Configured routing rules: AI category (upper-case canonical code) -> department code.
# The AI output is advisory; only categories present here are allowed to drive routing.
CATEGORY_TO_DEPARTMENT_CODE: Dict[str, str] = {
    "ELECTRICAL_SAFETY": "ELEC",
    "WATER_SUPPLY": "WATER",
    "ROAD_INFRASTRUCTURE": "ROADS",
    "ROAD_DAMAGE": "ROADS",
    "TRAFFIC": "ROADS",
    "SANITATION": "SANITATION",
    "DRAINAGE": "DRAINAGE",
    "PUBLIC_HEALTH": "PUBLIC_HEALTH",
    "STREET_LIGHTING": "ELEC",
    "WASTE_MANAGEMENT": "WASTE",
    "ENVIRONMENT": "WASTE",
}


async def get_system_user(db: AsyncSession) -> User:
    res = await db.execute(select(User).where(User.id == SYSTEM_USER_ID))
    user = res.scalars().first()
    if not user:
        user = User(
            id=SYSTEM_USER_ID,
            email="ai_system@sara.gov",
            full_name="SARA AI Pipeline System",
            password_hash="",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(user)
        await db.flush()
    return user


async def get_department_by_category(db: AsyncSession, category: Optional[str]) -> Optional[Department]:
    """Resolve a (validated) AI category to an active department via the routing rules."""
    if not category:
        return None
    code = CATEGORY_TO_DEPARTMENT_CODE.get(str(category).upper())
    if not code:
        return None
    result = await db.execute(
        select(Department).where(Department.code == code, Department.is_active == True)
    )
    return result.scalars().first()


async def compute_officer_workload(
    db: AsyncSession, officer_ids: List[uuid.UUID]
) -> Dict[uuid.UUID, Tuple[int, int, int]]:
    """
    Compute (active_workload, pending_acknowledgement, overdue) per officer.
    Active workload = active assignments on non-closed grievances.
    Pending acknowledgement = active assignments still in ASSIGNED/REOPENED state.
    Overdue = active assignments on escalated grievances.
    """
    if not officer_ids:
        return {}

    rows = await db.execute(
        select(
            Assignment.officer_id,
            func.sum(case((Grievance.current_state != "CLOSED", 1), else_=0)),
            func.sum(case((Grievance.current_state.in_(["ASSIGNED", "REOPENED"]), 1), else_=0)),
            func.sum(case((Grievance.escalated == True, 1), else_=0)),
        )
        .join(Grievance, Assignment.grievance_id == Grievance.id)
        .where(
            Assignment.is_active == True,
            Assignment.officer_id.in_(officer_ids),
        )
        .group_by(Assignment.officer_id)
    )

    workload: Dict[uuid.UUID, Tuple[int, int, int]] = {}
    for officer_id, active, pending, overdue in rows.all():
        workload[officer_id] = (active or 0, pending or 0, overdue or 0)
    return workload


async def select_best_officer(db: AsyncSession, department_id: uuid.UUID) -> Optional[User]:
    """
    Deterministic workload-aware officer selection for a department.

    Scoring: officers are ranked by (active_workload, pending_acknowledgement,
    overdue_workload, full_name). Lower is better. Full name is the stable
    tie-breaker so selection is reproducible.
    """
    res = await db.execute(
        select(User).where(
            User.department_id == department_id,
            User.role == UserRole.OFFICER,
            User.is_active == True,
        )
    )
    officers = res.scalars().all()
    if not officers:
        return None

    workload = await compute_officer_workload(db, [o.id for o in officers])

    def sort_key(o: User) -> Tuple[int, int, int, str]:
        active, pending, overdue = workload.get(o.id, (0, 0, 0))
        return (active, pending, overdue, (o.full_name or "").lower())

    officers.sort(key=sort_key)
    return officers[0]


async def _notify_supervisors_no_officer(
    db: AsyncSession, department: Department, grievance: Grievance
) -> None:
    """Notify the department's supervisors when a routed grievance has no eligible officer."""
    supervisors = await get_department_supervisors(db, department.id)
    for sup in supervisors:
        await create_in_app_notification(
            db=db,
            user_id=sup.id,
            grievance_id=grievance.id,
            title="Officer Assignment Required",
            message=(
                f"Grievance '{grievance.title}' is routed to {department.name} but no "
                "eligible officer is available. Please assign an officer manually."
            ),
            notification_type="OFFICER_ASSIGNMENT_REQUIRED",
        )


async def _notify_admins_unroutable(db: AsyncSession, grievance: Grievance) -> None:
    """Notify all active admins when a grievance cannot be auto-routed."""
    res = await db.execute(
        select(User).where(User.role == UserRole.ADMIN, User.is_active == True)
    )
    for admin in res.scalars().all():
        await create_in_app_notification(
            db=db,
            user_id=admin.id,
            grievance_id=grievance.id,
            title="Grievance Routing Review Required",
            message=(
                f"Grievance '{grievance.title}' could not be matched to a department "
                f"(AI category: {grievance.category or 'unknown'}). Manual routing required."
            ),
            notification_type="GRIEVANCE_ROUTING_REVIEW",
        )


async def auto_route_and_assign(db: AsyncSession, grievance: Grievance) -> Grievance:
    """
    Automatically route a classified grievance to its department and assign it
    to the best available officer.

    Flow (each step goes through transition_grievance - the single state machine):
      CLASSIFIED -> ROUTED (validated category -> department)
      ROUTED -> ASSIGNED (workload-aware best officer)

    If the category has no routing rule the grievance stays CLASSIFIED and admins
    are notified. If no eligible officer exists it stays ROUTED and the department
    supervisors are notified.
    """
    # 1. Enforce Confidence Threshold (< 0.75 remains in manual review queue under category OTHER)
    if grievance.classification_confidence is not None and grievance.classification_confidence < 0.75:
        grievance.category = "OTHER"
        await _notify_admins_unroutable(db, grievance)
        await db.commit()
        return grievance

    department = await get_department_by_category(db, grievance.category)
    if not department:
        await _notify_admins_unroutable(db, grievance)
        await db.commit()
        return grievance

    system_user = await get_system_user(db)

    # CLASSIFIED -> ROUTED
    grievance = await transition_grievance(
        db=db,
        grievance_id=grievance.id,
        target_state="ROUTED",
        actor=system_user,
        payload={"department_id": str(department.id)},
    )

    # ROUTED -> ASSIGNED
    # Retrieve all active officers in the routed department
    res_officers = await db.execute(
        select(User).where(
            User.department_id == department.id,
            User.role == UserRole.OFFICER,
            User.is_active == True
        )
    )
    officers = res_officers.scalars().all()
    if not officers:
        await _notify_supervisors_no_officer(db, department, grievance)
        await db.commit()
        return grievance

    # Compute workloads for all candidate officers to record workload snapshot
    workloads = await compute_officer_workload(db, [o.id for o in officers])

    workload_snapshot = {}
    for o in officers:
        active, pending, overdue = workloads.get(o.id, (0, 0, 0))
        workload_snapshot[str(o.id)] = {
            "name": o.full_name,
            "active": active,
            "pending": pending,
            "overdue": overdue
        }

    # Deterministically sort officers (active workload, pending, overdue, full name)
    def sort_key(o: User) -> Tuple[int, int, int, str]:
        active, pending, overdue = workloads.get(o.id, (0, 0, 0))
        return (active, pending, overdue, (o.full_name or "").lower())

    officers.sort(key=sort_key)
    best_officer = officers[0]

    payload = {
        "officer_id": str(best_officer.id),
        "reason": "Auto-assigned by SARA Workload Optimizer",
        "workload_snapshot": workload_snapshot
    }

    return await transition_grievance(
        db=db,
        grievance_id=grievance.id,
        target_state="ASSIGNED",
        actor=system_user,
        payload=payload,
    )