import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.grievance import Grievance
from app.models.user import User
from app.sangam.models import NeedCluster, GovernmentProject, InvestmentMatch, IntelligenceAlert

class IntelligenceRepository:
    async def get_overview_metrics(self, db: AsyncSession, department_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        """Calculates high-level metrics for the Sangam Intelligence Dashboard."""
        # Need clusters query
        nc_query = select(NeedCluster)
        if department_id:
            nc_query = nc_query.where(NeedCluster.department_id == department_id)
        nc_res = await db.execute(nc_query)
        clusters = nc_res.scalars().all()

        total_needs = len(clusters)
        active_hotspots = sum(1 for c in clusters if c.priority_score >= 50.0)
        high_priority = sum(1 for c in clusters if c.priority_score >= 70.0)

        # Alerts query
        alert_query = select(IntelligenceAlert).options(
            selectinload(IntelligenceAlert.need_cluster),
            selectinload(IntelligenceAlert.government_project)
        )
        if department_id:
            alert_query = alert_query.join(NeedCluster).where(NeedCluster.department_id == department_id)
        alert_res = await db.execute(alert_query.order_by(IntelligenceAlert.created_at.desc()))
        alerts = alert_res.scalars().all()

        unserved_gaps = sum(1 for a in alerts if a.type == "UNSERVED_GAP" and a.status == "OPEN")
        outcome_mismatches = sum(1 for a in alerts if a.type == "POTENTIAL_OUTCOME_MISMATCH" and a.status == "OPEN")

        # Matched investment calculation
        match_query = select(InvestmentMatch).options(selectinload(InvestmentMatch.government_project))
        match_res = await db.execute(match_query)
        matches = match_res.scalars().all()
        matched_investment = sum(m.government_project.allocated_amount for m in matches if m.government_project and m.match_score >= 0.5)

        # Top priority clusters
        top_clusters = sorted(clusters, key=lambda c: c.priority_score, reverse=True)[:5]

        return {
            "total_active_needs": total_needs,
            "active_hotspots_count": active_hotspots,
            "unserved_gaps_count": unserved_gaps,
            "outcome_mismatches_count": outcome_mismatches,
            "high_priority_count": high_priority,
            "total_matched_investment": matched_investment,
            "recent_alerts": alerts[:10],
            "top_priority_clusters": top_clusters
        }

    async def get_evidence_drawer_data(self, db: AsyncSession, cluster_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Retrieves underlying grievances, matched projects, and intelligence alerts for evidence drawer."""
        cluster_res = await db.execute(
            select(NeedCluster)
            .where(NeedCluster.id == cluster_id)
            .options(
                selectinload(NeedCluster.department),
                selectinload(NeedCluster.investment_matches).selectinload(InvestmentMatch.government_project),
                selectinload(NeedCluster.intelligence_alerts)
            )
        )
        cluster = cluster_res.scalars().first()
        if not cluster:
            return None

        # Fetch underlying grievances matching cluster category & location
        grievances_res = await db.execute(
            select(Grievance)
            .where(
                Grievance.category == cluster.category,
                func.lower(Grievance.location) == cluster.location_name.lower()
            )
            .options(selectinload(Grievance.citizen))
            .order_by(Grievance.created_at.desc())
        )
        grievances = grievances_res.scalars().all()

        detection_reasoning = (
            f"Need Cluster '{cluster.title}' was synthesized by aggregating {cluster.complaint_count} citizen complaints "
            f"in {cluster.location_name}. Priority Score is {cluster.priority_score}/100, driven by volume score "
            f"({cluster.priority_breakdown.get('complaint_volume_score', 0) if cluster.priority_breakdown else 0}), "
            f"severity score ({cluster.priority_breakdown.get('severity_score', 0) if cluster.priority_breakdown else 0}), and "
            f"unresolved cases ({cluster.unresolved_count})."
        )

        return {
            "need_cluster": cluster,
            "contributing_grievances": grievances,
            "matched_projects": cluster.investment_matches,
            "associated_alerts": cluster.intelligence_alerts,
            "detection_reasoning": detection_reasoning
        }
