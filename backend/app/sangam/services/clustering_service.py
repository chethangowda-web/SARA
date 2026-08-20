import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.grievance import Grievance
from app.sangam.models import NeedCluster

class NeedClusteringService:
    async def synchronize_need_clusters(self, db: AsyncSession) -> List[NeedCluster]:
        """
        Aggregates existing SARA grievances into NeedClusters by category and location.
        Does NOT alter, delete, or reclassify existing grievances.
        """
        # Fetch all grievances
        result = await db.execute(select(Grievance))
        grievances = result.scalars().all()

        if not grievances:
            return []

        # Group grievances by (category, normalized location)
        grouped: Dict[tuple, List[Grievance]] = {}
        for g in grievances:
            cat = g.category or "GENERAL"
            loc = (g.location or "LOCATION_UNKNOWN").strip().title()
            key = (cat, loc)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(g)

        clusters: List[NeedCluster] = []

        for (category, loc_name), items in grouped.items():
            dept_id = next((g.department_id for g in items if g.department_id is not None), None)
            complaint_count = len(items)
            unique_citizens = len(set(g.citizen_id for g in items if g.citizen_id))

            # Severity score calculation
            high_count = sum(1 for g in items if (g.priority or "").upper() in ["HIGH", "CRITICAL"])
            med_count = sum(1 for g in items if (g.priority or "").upper() == "MEDIUM")
            severity_score = min(100.0, ((high_count * 2.5 + med_count * 1.5) / max(1, complaint_count)) * 30.0 + min(40, complaint_count * 2))

            # Unresolved & Reopened counts
            unresolved_states = {"SUBMITTED", "CLASSIFIED", "ROUTED", "ASSIGNED", "ACKNOWLEDGED", "IN_PROGRESS", "RESOLUTION_SUBMITTED"}
            unresolved_count = sum(1 for g in items if g.current_state in unresolved_states)
            reopened_count = sum(1 for g in items if g.current_state == "REOPENED")

            # Dates & Persistence
            dates = [g.created_at for g in items if g.created_at]
            first_reported = min(dates) if dates else datetime.now(timezone.utc)
            last_reported = max(dates) if dates else datetime.now(timezone.utc)
            
            # Persistence in days
            days_span = max(1, (last_reported - first_reported).days)
            persistence_score = min(100.0, float(days_span * 4 + unresolved_count * 3))

            # Priority score formula (Transparent & measurable)
            volume_factor = min(30.0, complaint_count * 3.0)
            severity_factor = severity_score * 0.25
            persistence_factor = min(25.0, persistence_score * 0.25)
            unresolved_factor = min(20.0, unresolved_count * 4.0)
            reopened_factor = min(10.0, reopened_count * 5.0)

            priority_score = min(100.0, round(volume_factor + severity_factor + persistence_factor + unresolved_factor + reopened_factor, 1))

            priority_breakdown = {
                "complaint_volume_score": round(volume_factor, 1),
                "severity_score": round(severity_factor, 1),
                "persistence_score": round(persistence_factor, 1),
                "unresolved_score": round(unresolved_factor, 1),
                "reopened_score": round(reopened_factor, 1),
                "raw_complaint_count": complaint_count
            }

            title = f"{category.replace('_', ' ').title()} Issue in {loc_name}"

            # Check if cluster exists
            existing_res = await db.execute(
                select(NeedCluster).where(
                    NeedCluster.category == category,
                    NeedCluster.location_name == loc_name
                )
            )
            cluster = existing_res.scalars().first()

            if cluster:
                cluster.title = title
                cluster.department_id = dept_id
                cluster.complaint_count = complaint_count
                cluster.unique_citizen_count = unique_citizens
                cluster.severity_score = round(severity_score, 1)
                cluster.persistence_score = round(persistence_score, 1)
                cluster.unresolved_count = unresolved_count
                cluster.reopened_count = reopened_count
                cluster.first_reported_at = first_reported
                cluster.last_reported_at = last_reported
                cluster.priority_score = priority_score
                cluster.priority_breakdown = priority_breakdown
            else:
                cluster = NeedCluster(
                    title=title,
                    category=category,
                    department_id=dept_id,
                    location_name=loc_name,
                    complaint_count=complaint_count,
                    unique_citizen_count=unique_citizens,
                    severity_score=round(severity_score, 1),
                    persistence_score=round(persistence_score, 1),
                    unresolved_count=unresolved_count,
                    reopened_count=reopened_count,
                    first_reported_at=first_reported,
                    last_reported_at=last_reported,
                    priority_score=priority_score,
                    priority_breakdown=priority_breakdown,
                    status="ACTIVE"
                )
                db.add(cluster)

            clusters.append(cluster)

        await db.commit()
        for c in clusters:
            await db.refresh(c)

        return clusters
