import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import SessionLocal
from app.models.department import Department

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
            
    await db.commit()
    print("[SEED] Reference data seeding complete.")

async def main():
    async with SessionLocal() as session:
        await seed_data(session)

if __name__ == "__main__":
    asyncio.run(main())
