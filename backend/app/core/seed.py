import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.department import Department
from app.models.user import User, UserRole

async def seed_data(db: AsyncSession):
    # Retrieve password from env or default
    default_password = os.getenv("DEMO_PASSWORD", "SARA_demo_pass_2026")
    hashed_pass = hash_password(default_password)

    # 1. Seed Electrical Department (idempotently)
    dept_code = "ELEC"
    result = await db.execute(select(Department).where(Department.code == dept_code))
    elec_dept = result.scalars().first()
    
    if not elec_dept:
        elec_dept = Department(
            name="Electrical Department",
            code=dept_code,
            is_active=True
        )
        db.add(elec_dept)
        await db.flush() # Populate elec_dept.id
        print(f"[SEED] Created Department: {elec_dept.name}")
    else:
        print(f"[SEED] Department {elec_dept.name} already exists.")

    # 2. Seed Users (idempotently)
    users_to_seed = [
        {
            "email": "admin@sara.gov",
            "full_name": "SARA System Administrator",
            "role": UserRole.ADMIN,
            "department_id": None
        },
        {
            "email": "supervisor@sara.gov",
            "full_name": "Electrical Supervisor",
            "role": UserRole.SUPERVISOR,
            "department_id": elec_dept.id
        },
        {
            "email": "officer@sara.gov",
            "full_name": "Electrical Field Officer",
            "role": UserRole.OFFICER,
            "department_id": elec_dept.id
        },
        {
            "email": "citizen@sara.gov",
            "full_name": "Concerned Citizen",
            "role": UserRole.CITIZEN,
            "department_id": None
        }
    ]

    for user_data in users_to_seed:
        result = await db.execute(select(User).where(User.email == user_data["email"]))
        user = result.scalars().first()
        
        if not user:
            user = User(
                email=user_data["email"],
                full_name=user_data["full_name"],
                password_hash=hashed_pass,
                role=user_data["role"],
                department_id=user_data["department_id"],
                is_active=True
            )
            db.add(user)
            print(f"[SEED] Created User: {user.email} ({user.role.value})")
        else:
            # Update fields and password hash to ensure consistency
            user.full_name = user_data["full_name"]
            user.role = user_data["role"]
            user.department_id = user_data["department_id"]
            user.password_hash = hashed_pass
            print(f"[SEED] User {user.email} already exists. Updated password and details.")
            
    await db.commit()
    print("[SEED] Seeding database complete.")

async def main():
    async with SessionLocal() as session:
        await seed_data(session)

if __name__ == "__main__":
    asyncio.run(main())
