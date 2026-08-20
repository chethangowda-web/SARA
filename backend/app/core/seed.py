import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import SessionLocal
from app.models.department import Department
from app.models.staff_authorization import StaffAuthorization
from app.models.user import User, UserRole
from app.core.security import hash_password

async def seed_data(db: AsyncSession):
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
        await db.flush()
        print(f"[SEED] Created Department: {elec_dept.name}")
    else:
        print(f"[SEED] Department {elec_dept.name} already exists.")
            
    # 2. Seed Pre-authorized Staff Accounts and Users
    staff_members = [
        ("iamchethen2813@gmail.com", "System Admin", UserRole.ADMIN, None),
        ("prajwals2006ps@gmail.com", "Prajwal PS", UserRole.SUPERVISOR, elec_dept.id),
        ("dmsudeepreddy17@gmail.com", "Sudeep Reddy", UserRole.SUPERVISOR, elec_dept.id),
        ("bhoomija24@gmail.com", "Bhoomija", UserRole.SUPERVISOR, elec_dept.id),
        ("priyankah.4767@gmail.com", "Priyanka H", UserRole.OFFICER, elec_dept.id),
        ("charanavs04@gmail.com", "Charan A", UserRole.OFFICER, elec_dept.id),
    ]

    default_password_hash = hash_password("Password123!")

    for email, full_name, role, dept_id in staff_members:
        # Ensure StaffAuthorization record
        res_auth = await db.execute(select(StaffAuthorization).where(StaffAuthorization.email == email))
        auth_rec = res_auth.scalars().first()
        if not auth_rec:
            auth_rec = StaffAuthorization(
                email=email,
                role=role,
                department_id=dept_id,
                is_active=True
            )
            db.add(auth_rec)
        else:
            auth_rec.role = role
            auth_rec.department_id = dept_id
            auth_rec.is_active = True

        # Ensure User record
        res_user = await db.execute(select(User).where(User.email == email))
        user_rec = res_user.scalars().first()
        if not user_rec:
            user_rec = User(
                email=email,
                full_name=full_name,
                password_hash=default_password_hash,
                role=role,
                department_id=dept_id,
                is_active=True,
                email_verified=True,
                auth_provider="credentials"
            )
            db.add(user_rec)
        else:
            user_rec.role = role
            user_rec.department_id = dept_id
            user_rec.is_active = True
            user_rec.email_verified = True
            if not user_rec.password_hash:
                user_rec.password_hash = default_password_hash

    await db.commit()
    print("[SEED] Reference data & initial staff accounts seeding complete.")

async def main():
    async with SessionLocal() as session:
        await seed_data(session)

if __name__ == "__main__":
    asyncio.run(main())

