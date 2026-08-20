import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.department import Department
from app.sangam.models import GovernmentProject, NeedCluster, InvestmentMatch, IntelligenceAlert
from app.sangam.schemas import GovernmentProjectCreate, GovernmentProjectUpdate

class InvestmentService:
    async def seed_demo_projects_if_empty(self, db: AsyncSession) -> List[GovernmentProject]:
        """Seeds realistic demo government investment projects if none exist."""
        result = await db.execute(select(GovernmentProject))
        projects = result.scalars().all()
        if projects:
            return list(projects)

        # Fetch departments
        dept_res = await db.execute(select(Department))
        departments = {d.code: d.id for d in dept_res.scalars().all()}

        demo_projects = [
            GovernmentProject(
                project_code="GOV-PRJ-2025-ELEC-01",
                name="Central Ward Transformer Replacement & Grid Augmentation",
                description="Upgrading 11kV substation infrastructure and replacing overhead cables in Central Ward to reduce power outages.",
                department_id=departments.get("ELEC"),
                category="ELECTRICAL",
                location="Central Ward",
                allocated_amount=4500000.0,
                spent_amount=4200000.0,
                start_date=datetime.now(timezone.utc) - timedelta(days=180),
                expected_end_date=datetime.now(timezone.utc) - timedelta(days=30),
                actual_end_date=datetime.now(timezone.utc) - timedelta(days=15),
                status="COMPLETED",
                source="DEMO_SEEDED"
            ),
            GovernmentProject(
                project_code="GOV-PRJ-2025-WAT-02",
                name="North Zone Main Water Pipeline Renewal Project",
                description="Laying 12km high-density polyethylene distribution pipeline for uninterrupted clean water supply in North Area.",
                department_id=departments.get("WATER"),
                category="WATER_SUPPLY",
                location="North Area",
                allocated_amount=8500000.0,
                spent_amount=3200000.0,
                start_date=datetime.now(timezone.utc) - timedelta(days=90),
                expected_end_date=datetime.now(timezone.utc) + timedelta(days=120),
                status="IN_PROGRESS",
                source="DEMO_SEEDED"
            ),
            GovernmentProject(
                project_code="GOV-PRJ-2025-RDS-03",
                name="South District Stormwater Drain & Pothole Asphalt Overlay",
                description="Comprehensive road resurfacing and concrete stormwater drainage network construction in South Ward.",
                department_id=departments.get("ROADS"),
                category="ROADS",
                location="South Ward",
                allocated_amount=6000000.0,
                spent_amount=5800000.0,
                start_date=datetime.now(timezone.utc) - timedelta(days=210),
                expected_end_date=datetime.now(timezone.utc) - timedelta(days=45),
                actual_end_date=datetime.now(timezone.utc) - timedelta(days=40),
                status="COMPLETED",
                source="DEMO_SEEDED"
            )
        ]

        for p in demo_projects:
            db.add(p)

        await db.commit()
        for p in demo_projects:
            await db.refresh(p)

        return demo_projects

    async def list_projects(self, db: AsyncSession, department_id: Optional[uuid.UUID] = None) -> List[GovernmentProject]:
        query = select(GovernmentProject).options(selectinload(GovernmentProject.department))
        if department_id:
            query = query.where(GovernmentProject.department_id == department_id)
        result = await db.execute(query.order_by(GovernmentProject.created_at.desc()))
        return list(result.scalars().all())

    async def get_project(self, db: AsyncSession, project_id: uuid.UUID) -> Optional[GovernmentProject]:
        result = await db.execute(
            select(GovernmentProject)
            .where(GovernmentProject.id == project_id)
            .options(selectinload(GovernmentProject.department))
        )
        return result.scalars().first()

    async def create_project(self, db: AsyncSession, data: GovernmentProjectCreate) -> GovernmentProject:
        project = GovernmentProject(**data.model_dump())
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project

    async def update_project(self, db: AsyncSession, project_id: uuid.UUID, data: GovernmentProjectUpdate) -> Optional[GovernmentProject]:
        project = await self.get_project(db, project_id)
        if not project:
            return None

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(project, key, value)

        await db.commit()
        await db.refresh(project)
        return project

    async def match_projects_to_clusters(self, db: AsyncSession) -> List[InvestmentMatch]:
        """Matches Government Projects to Need Clusters based on category, location, and department."""
        # Clear old matches
        await db.execute(select(InvestmentMatch))
        
        clusters_res = await db.execute(select(NeedCluster))
        clusters = clusters_res.scalars().all()

        projects_res = await db.execute(select(GovernmentProject))
        projects = projects_res.scalars().all()

        matches: List[InvestmentMatch] = []

        for cluster in clusters:
            for project in projects:
                score = 0.0
                reasons = []

                # Category match
                if cluster.category.upper() == project.category.upper():
                    score += 0.45
                    reasons.append("Exact category alignment")

                # Department match
                if cluster.department_id and project.department_id and cluster.department_id == project.department_id:
                    score += 0.25
                    reasons.append("Same responsible department")

                # Location proximity match
                c_loc = cluster.location_name.strip().lower()
                p_loc = project.location.strip().lower()
                if c_loc in p_loc or p_loc in c_loc:
                    score += 0.30
                    reasons.append("Geographic location overlap")

                if score >= 0.50:
                    # Check existing match
                    existing_res = await db.execute(
                        select(InvestmentMatch).where(
                            InvestmentMatch.need_cluster_id == cluster.id,
                            InvestmentMatch.government_project_id == project.id
                        )
                    )
                    match_rec = existing_res.scalars().first()
                    reason_str = " + ".join(reasons)

                    if match_rec:
                        match_rec.match_score = round(score, 2)
                        match_rec.match_reason = reason_str
                    else:
                        match_rec = InvestmentMatch(
                            need_cluster_id=cluster.id,
                            government_project_id=project.id,
                            match_score=round(score, 2),
                            match_reason=reason_str
                        )
                        db.add(match_rec)

                    matches.append(match_rec)

        await db.commit()
        return matches
