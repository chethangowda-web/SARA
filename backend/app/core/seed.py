import asyncio
import os
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.department import Department
from app.models.user import User, UserRole
from app.services.assignment_service import SYSTEM_USER_ID

# Reference departments: code -> name. Idempotently upserted by code.
DEPARTMENTS: Dict[str, str] = {
    "ELEC": "Electrical Department",
    "WATER": "Water Supply Department",
    "ROADS": "Roads & Infrastructure Department",
    "SANITATION": "Sanitation Department",
    "PUBLIC_HEALTH": "Public Health Department",
    "STREET_LIGHTING": "Street Lighting Department",
    "WASTE": "Waste Management Department",
    "DRAINAGE": "Drainage Department",
}

# Officers per department code. Demo departments (ELEC/WATER/SANITATION) are
# staffed exclusively by the milestone demo accounts; other departments keep
# their legacy seed users.
OFFICERS: Dict[str, List[Dict[str, str]]] = {
    "ELEC": [
        {"email": "officer@sara.gov", "full_name": "Electrical Field Officer 1"},
        {"email": "electrical2@sara.gov", "full_name": "Electrical Field Officer 2"},
        {"email": "officer@sara.com", "full_name": "Electrical Field Officer 1 (Alias)"},
    ],
    "WATER": [
        {"email": "water.officer@sara.gov", "full_name": "Water Field Officer 1"},
        {"email": "water2@sara.gov", "full_name": "Water Field Officer 2"},
        {"email": "water.officer@sara.com", "full_name": "Water Field Officer 1 (Alias)"},
    ],
    "ROADS": [
        {"email": "roads.officer01@sara.gov", "full_name": "Roads Field Officer 01"},
        {"email": "roads.officer02@sara.gov", "full_name": "Roads Field Officer 02"},
    ],
    "SANITATION": [
        {"email": "sanitation.officer@sara.gov", "full_name": "Sanitation Field Officer 1"},
        {"email": "sanitation2@sara.gov", "full_name": "Sanitation Field Officer 2"},
        {"email": "sanitation.officer@sara.com", "full_name": "Sanitation Field Officer 1 (Alias)"},
    ],
    "PUBLIC_HEALTH": [
        {"email": "publichealth.officer01@sara.gov", "full_name": "Public Health Officer 01"},
        {"email": "publichealth.officer02@sara.gov", "full_name": "Public Health Officer 02"},
    ],
    "STREET_LIGHTING": [
        {"email": "streetlighting.officer01@sara.gov", "full_name": "Street Lighting Officer 01"},
        {"email": "streetlighting.officer02@sara.gov", "full_name": "Street Lighting Officer 02"},
    ],
    "WASTE": [
        {"email": "waste.officer01@sara.gov", "full_name": "Waste Management Officer 01"},
        {"email": "waste.officer02@sara.gov", "full_name": "Waste Management Officer 02"},
    ],
    "DRAINAGE": [
        {"email": "drainage.officer01@sara.gov", "full_name": "Drainage Officer 01"},
        {"email": "drainage.officer02@sara.gov", "full_name": "Drainage Officer 02"},
    ],
}

# Supervisors per department code. Demo departments use the milestone demo accounts.
SUPERVISORS: Dict[str, List[Dict[str, str]]] = {
    "ELEC": [
        {"email": "supervisor@sara.gov", "full_name": "Electrical Supervisor"},
        {"email": "supervisor@sara.com", "full_name": "Electrical Supervisor (Alias)"},
    ],
    "WATER": [
        {"email": "water.supervisor@sara.gov", "full_name": "Water Supply Supervisor"},
        {"email": "water.supervisor@sara.com", "full_name": "Water Supply Supervisor (Alias)"},
    ],
    "ROADS": [
        {"email": "roads.supervisor@sara.gov", "full_name": "Roads & Infrastructure Supervisor"},
    ],
    "SANITATION": [
        {"email": "sanitation.supervisor@sara.gov", "full_name": "Sanitation Supervisor"},
        {"email": "sanitation.supervisor@sara.com", "full_name": "Sanitation Supervisor (Alias)"},
    ],
    "PUBLIC_HEALTH": [
        {"email": "publichealth.supervisor@sara.gov", "full_name": "Public Health Supervisor"},
    ],
    "STREET_LIGHTING": [
        {"email": "streetlighting.supervisor@sara.gov", "full_name": "Street Lighting Supervisor"},
    ],
    "WASTE": [
        {"email": "waste.supervisor@sara.gov", "full_name": "Waste Management Supervisor"},
    ],
    "DRAINAGE": [
        {"email": "drainage.supervisor@sara.gov", "full_name": "Drainage Supervisor"},
    ],
}


async def _upsert_department(db: AsyncSession, code: str, name: str) -> Department:
    result = await db.execute(select(Department).where(Department.code == code))
    dept = result.scalars().first()
    if dept:
        dept.name = name
        dept.is_active = True
        return dept
    dept = Department(name=name, code=code, is_active=True)
    db.add(dept)
    await db.flush()
    print(f"[SEED] Created Department: {dept.name}")
    return dept


async def _upsert_user(
    db: AsyncSession,
    email: str,
    full_name: str,
    role: UserRole,
    department_id: Optional[str],
    hashed_pass: str,
) -> None:
    result = await db.execute(
        select(User).where(User.email == email).options(selectinload(User.department))
    )
    user = result.scalars().first()
    if not user:
        user = User(
            email=email,
            full_name=full_name,
            password_hash=hashed_pass,
            role=role,
            department_id=department_id,
            is_active=True,
        )
        db.add(user)
        print(f"[SEED] Created User: {email} ({role.value})")
    else:
        user.full_name = full_name
        user.role = role
        user.department_id = department_id
        user.password_hash = hashed_pass
        user.is_active = True


async def seed_data(db: AsyncSession):
    default_password = os.getenv("DEMO_PASSWORD", "SARA_demo_pass_2026")
    hashed_pass = hash_password(default_password)

    # 1. Departments (idempotent by code)
    dept_ids: Dict[str, str] = {}
    for code, name in DEPARTMENTS.items():
        dept = await _upsert_department(db, code, name)
        dept_ids[code] = str(dept.id)

    # 2. Officers & Supervisors per department
    for code, officers in OFFICERS.items():
        for o in officers:
            await _upsert_user(db, o["email"], o["full_name"], UserRole.OFFICER, dept_ids[code], hashed_pass)

    for code, supervisors in SUPERVISORS.items():
        for s in supervisors:
            await _upsert_user(db, s["email"], s["full_name"], UserRole.SUPERVISOR, dept_ids[code], hashed_pass)

    # Deactivate legacy staff in the demo departments so assignment is deterministic.
    # Scoped to ELEC/WATER/SANITATION only; other departments are untouched.
    demo_codes = {"ELEC", "WATER", "SANITATION"}
    active_emails = set()
    demo_dept_ids = []
    for code in demo_codes:
        demo_dept_ids.append(dept_ids[code])
        for o in OFFICERS.get(code, []):
            active_emails.add(o["email"])
        for s in SUPERVISORS.get(code, []):
            active_emails.add(s["email"])
    if active_emails:
        legacy = await db.execute(
            select(User).where(
                User.role.in_([UserRole.OFFICER, UserRole.SUPERVISOR]),
                User.department_id.in_(demo_dept_ids),
                User.email.notin_(active_emails),
                User.is_active == True,
            )
        )
        for u in legacy.scalars().all():
            u.is_active = False
            print(f"[SEED] Deactivated legacy staff: {u.email}")

    # 3. Platform users (admin + citizen)
    await _upsert_user(
        db, "admin@sara.gov", "SARA System Administrator", UserRole.ADMIN, None, hashed_pass
    )
    await _upsert_user(
        db, "citizen@sara.gov", "Concerned Citizen", UserRole.CITIZEN, None, hashed_pass
    )
    await _upsert_user(
        db, "admin@sara.com", "SARA System Administrator", UserRole.ADMIN, None, hashed_pass
    )
    await _upsert_user(
        db, "citizen@sara.com", "Concerned Citizen", UserRole.CITIZEN, None, hashed_pass
    )

    # 4. System actor row (zero UUID) so automated assignment transitions satisfy
    #    the assignments.assigned_by foreign key to users.
    sys_result = await db.execute(select(User).where(User.id == SYSTEM_USER_ID))
    sys_user = sys_result.scalars().first()
    if not sys_user:
        db.add(User(
            id=SYSTEM_USER_ID,
            email="ai_system@sara.gov",
            full_name="SARA AI Pipeline System",
            password_hash=hashed_pass,
            role=UserRole.ADMIN,
            is_active=True,
        ))
        print("[SEED] Created System Actor (ai_system@sara.gov)")

    await db.commit()
    print("[SEED] Seeding database complete.")


async def main():
    async with SessionLocal() as session:
        await seed_data(session)


if __name__ == "__main__":
    asyncio.run(main())
