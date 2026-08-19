"""
Enriches Grievance ORM objects with computed SLA deadline and active-assignment
officer info before they are serialized by GrievanceResponse.

Values are set directly on the ORM instance so Pydantic's from_attributes mode
picks them up; no schema migration is required.
"""
import uuid
from datetime import timedelta
from typing import Iterable, Optional, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.grievance import Grievance
from app.models.assignment import Assignment
from app.models.department import Department
from app.models.user import User
from app.governance.services import get_sla_policy


async def enrich_grievance(db: AsyncSession, grievance: Grievance) -> Grievance:
    """Attach sla_hours, expected_resolution and active assigned officer to a grievance."""
    if grievance is None:
        return grievance

    # Reload server-computed columns (created_at/updated_at use DB defaults) so
    # response serialization never triggers an async lazy-load outside a greenlet.
    await db.refresh(grievance)

    # SLA policy + deadline
    policy = await get_sla_policy(db, grievance.department_id, grievance.priority)
    grievance.sla_hours = policy.sla_hours
    start = grievance.submitted_at or grievance.created_at
    if start:
        grievance.expected_resolution = start + timedelta(hours=policy.sla_hours)

    # Active assigned officer
    grievance.assigned_officer = None

    # Department name + relationship (populate both so response serialization
    # never triggers an async lazy-load outside a greenlet)
    grievance.department_name = None
    if grievance.department_id:
        res_d = await db.execute(
            select(Department).where(Department.id == grievance.department_id)
        )
        dept = res_d.scalars().first()
        if dept:
            grievance.department_name = dept.name
            grievance.department = dept

    if grievance.assigned_officer_id:
        res_o = await db.execute(
            select(User).where(User.id == grievance.assigned_officer_id)
        )
        officer = res_o.scalars().first()
        if officer:
            grievance.assigned_officer = officer.full_name

    return grievance


async def enrich_grievances(db: AsyncSession, grievances: Iterable[Grievance]) -> list:
    """Enrich a list of grievances (in place on the ORM instances)."""
    result = []
    for g in grievances:
        result.append(await enrich_grievance(db, g))
    return result