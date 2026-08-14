from datetime import datetime, timezone, date
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.models.analytics import AnalyticsSnapshot
from app.models.department import Department
from app.analytics.metrics import get_global_metrics, get_department_metrics
from app.analytics.anomalies import detect_anomalies

async def create_analytics_snapshots(db: AsyncSession) -> None:
    today = datetime.now(timezone.utc).date()
    
    # Global Snapshot
    global_metrics = await get_global_metrics(db)
    
    global_snap_res = await db.execute(
        select(AnalyticsSnapshot).where(
            AnalyticsSnapshot.snapshot_date == today,
            AnalyticsSnapshot.department_id.is_(None)
        )
    )
    global_snap = global_snap_res.scalars().first()
    
    if global_snap:
        global_snap.total_grievances = global_metrics.total_grievances
        global_snap.open_grievances = global_metrics.open_grievances
        global_snap.closed_grievances = global_metrics.closed_grievances
        global_snap.sla_breaches = global_metrics.sla_breaches
        global_snap.escalated_grievances = global_metrics.escalated_grievances
        global_snap.average_resolution_hours = global_metrics.average_resolution_hours
        global_snap.average_assignment_hours = global_metrics.average_assignment_hours
        global_snap.average_acknowledgement_hours = global_metrics.average_acknowledgement_hours
    else:
        new_global_snap = AnalyticsSnapshot(
            snapshot_date=today,
            department_id=None,
            total_grievances=global_metrics.total_grievances,
            open_grievances=global_metrics.open_grievances,
            closed_grievances=global_metrics.closed_grievances,
            sla_breaches=global_metrics.sla_breaches,
            escalated_grievances=global_metrics.escalated_grievances,
            average_resolution_hours=global_metrics.average_resolution_hours,
            average_assignment_hours=global_metrics.average_assignment_hours,
            average_acknowledgement_hours=global_metrics.average_acknowledgement_hours
        )
        db.add(new_global_snap)

    # Department Snapshots
    dept_res = await db.execute(select(Department.id).where(Department.is_active == True))
    departments = dept_res.scalars().all()
    
    for dept_id in departments:
        dept_metrics = await get_department_metrics(db, dept_id)
        
        dept_snap_res = await db.execute(
            select(AnalyticsSnapshot).where(
                AnalyticsSnapshot.snapshot_date == today,
                AnalyticsSnapshot.department_id == dept_id
            )
        )
        dept_snap = dept_snap_res.scalars().first()
        
        if dept_snap:
            dept_snap.total_grievances = dept_metrics.total_grievances
            dept_snap.open_grievances = dept_metrics.open_grievances
            dept_snap.closed_grievances = dept_metrics.closed_grievances
            dept_snap.sla_breaches = dept_metrics.sla_breaches
            dept_snap.escalated_grievances = dept_metrics.escalation_count
            dept_snap.average_resolution_hours = dept_metrics.average_resolution_hours
            dept_snap.average_assignment_hours = dept_metrics.average_assignment_hours
            dept_snap.average_acknowledgement_hours = dept_metrics.average_acknowledgement_hours
        else:
            new_dept_snap = AnalyticsSnapshot(
                snapshot_date=today,
                department_id=dept_id,
                total_grievances=dept_metrics.total_grievances,
                open_grievances=dept_metrics.open_grievances,
                closed_grievances=dept_metrics.closed_grievances,
                sla_breaches=dept_metrics.sla_breaches,
                escalated_grievances=dept_metrics.escalation_count,
                average_resolution_hours=dept_metrics.average_resolution_hours,
                average_assignment_hours=dept_metrics.average_assignment_hours,
                average_acknowledgement_hours=dept_metrics.average_acknowledgement_hours
            )
            db.add(new_dept_snap)
    
    # Run Anomaly Detection
    await detect_anomalies(db)
    
    await db.commit()
