import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.sangam.models import NeedCluster, GovernmentProject, InvestmentMatch, IntelligenceAlert

class GapDetectionService:
    async def analyze_and_generate_alerts(self, db: AsyncSession) -> List[IntelligenceAlert]:
        """
        Scans all NeedClusters and InvestmentMatches to evaluate:
        1. UNSERVED_GAP: High citizen need (complaints >= 3 or priority >= 40) + NO matching government project (match_score >= 0.5).
        2. POTENTIAL_OUTCOME_MISMATCH: Matching investment project exists and is COMPLETED or IN_PROGRESS, but citizen complaints continue (unresolved_count >= 2 or reopened_count >= 1).
        """
        clusters_res = await db.execute(
            select(NeedCluster).options(
                selectinload(NeedCluster.investment_matches).selectinload(InvestmentMatch.government_project)
            )
        )
        clusters = clusters_res.scalars().all()

        alerts: List[IntelligenceAlert] = []

        for cluster in clusters:
            valid_matches = [m for m in cluster.investment_matches if m.match_score >= 0.50]

            # Case 1: UNSERVED GAP
            if not valid_matches and (cluster.complaint_count >= 2 or cluster.priority_score >= 40.0):
                title = f"Potential Unserved Gap: {cluster.title}"
                desc = (
                    f"High persistent citizen need detected in {cluster.location_name} for category '{cluster.category}' "
                    f"({cluster.complaint_count} complaints, {cluster.unresolved_count} unresolved, priority score {cluster.priority_score}/100), "
                    f"but no matching government project or financial allocation was found. Requires human verification."
                )
                evidence = {
                    "complaint_count": cluster.complaint_count,
                    "unresolved_count": cluster.unresolved_count,
                    "reopened_count": cluster.reopened_count,
                    "location": cluster.location_name,
                    "category": cluster.category,
                    "priority_score": cluster.priority_score,
                    "matching_projects_count": 0,
                    "recommendation": "Evaluate area for potential infrastructure allocation in upcoming planning cycle."
                }

                alert = await self._upsert_alert(
                    db=db,
                    alert_type="UNSERVED_GAP",
                    severity="HIGH" if cluster.priority_score >= 70.0 else "MEDIUM",
                    need_cluster_id=cluster.id,
                    project_id=None,
                    title=title,
                    description=desc,
                    evidence_json=evidence
                )
                alerts.append(alert)

            # Case 2: POTENTIAL OUTCOME MISMATCH
            for match in valid_matches:
                project = match.government_project
                if not project:
                    continue

                # Check if project completed or active but complaints continue
                if project.status in ["COMPLETED", "IN_PROGRESS"] and (cluster.unresolved_count >= 1 or cluster.reopened_count >= 1 or cluster.complaint_count >= 3):
                    title = f"Potential Outcome Mismatch: {project.name}"
                    desc = (
                        f"Government project '{project.name}' (Allocation: ₹{project.allocated_amount:,.2f}, Status: {project.status}) "
                        f"was executed for {project.location}, but {cluster.complaint_count} citizen complaints ({cluster.unresolved_count} unresolved, "
                        f"{cluster.reopened_count} reopened) continue to be reported in the same area. Requires human verification."
                    )
                    evidence = {
                        "project_code": project.project_code,
                        "project_name": project.name,
                        "project_status": project.status,
                        "allocated_amount": project.allocated_amount,
                        "spent_amount": project.spent_amount,
                        "match_score": match.match_score,
                        "match_reason": match.match_reason,
                        "recent_complaints_count": cluster.complaint_count,
                        "unresolved_count": cluster.unresolved_count,
                        "reopened_count": cluster.reopened_count,
                        "recommendation": "Conduct physical inspection or verification to validate outcome quality."
                    }

                    alert = await self._upsert_alert(
                        db=db,
                        alert_type="POTENTIAL_OUTCOME_MISMATCH",
                        severity="HIGH" if project.status == "COMPLETED" else "MEDIUM",
                        need_cluster_id=cluster.id,
                        project_id=project.id,
                        title=title,
                        description=desc,
                        evidence_json=evidence
                    )
                    alerts.append(alert)

        await db.commit()
        return alerts

    async def _upsert_alert(
        self,
        db: AsyncSession,
        alert_type: str,
        severity: str,
        need_cluster_id: uuid.UUID,
        project_id: uuid.UUID,
        title: str,
        description: str,
        evidence_json: dict
    ) -> IntelligenceAlert:
        query = select(IntelligenceAlert).where(
            IntelligenceAlert.type == alert_type,
            IntelligenceAlert.need_cluster_id == need_cluster_id
        )
        if project_id:
            query = query.where(IntelligenceAlert.government_project_id == project_id)

        res = await db.execute(query)
        alert = res.scalars().first()

        if alert:
            alert.severity = severity
            alert.title = title
            alert.description = description
            alert.evidence_json = evidence_json
        else:
            alert = IntelligenceAlert(
                type=alert_type,
                severity=severity,
                need_cluster_id=need_cluster_id,
                government_project_id=project_id,
                title=title,
                description=description,
                evidence_json=evidence_json,
                status="OPEN"
            )
            db.add(alert)

        return alert
