import uuid
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.models.grievance import Grievance
from app.models.department import Department
from app.models.analytics import OperationalAnomaly

async def detect_anomalies(db: AsyncSession) -> None:
    """
    Deterministically scan for anomalies.
    Runs globally and per-department. Writes anomalies to DB.
    """
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    fourteen_days_ago = now - timedelta(days=14)

    # Fetch departments
    dept_res = await db.execute(select(Department.id, Department.name).where(Department.is_active == True))
    departments = dept_res.all()

    for dept_id, dept_name in departments:
        # 1. Volume spike: Last 7 days vs Previous 7 days
        recent_vol_res = await db.execute(
            select(func.count(Grievance.id)).where(Grievance.department_id == dept_id, Grievance.created_at >= seven_days_ago)
        )
        recent_vol = recent_vol_res.scalar_one_or_none() or 0
        
        prev_vol_res = await db.execute(
            select(func.count(Grievance.id)).where(
                Grievance.department_id == dept_id,
                Grievance.created_at >= fourteen_days_ago,
                Grievance.created_at < seven_days_ago
            )
        )
        prev_vol = prev_vol_res.scalar_one_or_none() or 0
        
        if prev_vol >= 5 and recent_vol > prev_vol * 1.5:
            await _record_anomaly(
                db, dept_id, "VOLUME_SPIKE", "HIGH", "Weekly Volume", 
                float(recent_vol), float(prev_vol), 
                f"Volume spiked by over 50%. ({prev_vol} to {recent_vol})"
            )

        # 2. SLA Breach Rate
        active_res = await db.execute(
            select(func.count(Grievance.id)).where(Grievance.department_id == dept_id, Grievance.current_state != 'CLOSED')
        )
        active_cnt = active_res.scalar_one_or_none() or 0
        
        breach_res = await db.execute(
            select(func.count(Grievance.id)).where(
                Grievance.department_id == dept_id, Grievance.current_state != 'CLOSED', Grievance.escalation_level == 2
            )
        )
        breach_cnt = breach_res.scalar_one_or_none() or 0
        
        if active_cnt >= 10:
            breach_rate = breach_cnt / active_cnt
            if breach_rate > 0.3:
                await _record_anomaly(
                    db, dept_id, "SLA_BREACH_SPIKE", "CRITICAL", "Active SLA Breach Rate", 
                    round(breach_rate * 100, 2), 30.0, 
                    f"Over 30% of active grievances have breached SLA ({breach_cnt}/{active_cnt})."
                )

        # 3. Abnormal Reopening Rate
        resolved_res = await db.execute(
            select(func.count(Grievance.id)).where(
                Grievance.department_id == dept_id, 
                Grievance.resolved_at.is_not(None)
            )
        )
        resolved_cnt = resolved_res.scalar_one_or_none() or 0
        
        reopen_res = await db.execute(
            select(func.count(Grievance.id)).where(
                Grievance.department_id == dept_id, 
                Grievance.current_state == 'REOPENED'
            )
        )
        reopen_cnt = reopen_res.scalar_one_or_none() or 0
        
        if resolved_cnt >= 10:
            reopen_rate = reopen_cnt / resolved_cnt
            if reopen_rate > 0.2:
                await _record_anomaly(
                    db, dept_id, "REOPEN_SPIKE", "HIGH", "Reopen Rate", 
                    round(reopen_rate * 100, 2), 20.0, 
                    f"Over 20% of resolved grievances are being reopened ({reopen_cnt}/{resolved_cnt})."
                )

async def _record_anomaly(
    db: AsyncSession, 
    department_id: uuid.UUID, 
    anomaly_type: str, 
    severity: str, 
    metric: str, 
    observed: float, 
    expected: float, 
    explanation: str
):
    # Check if a recent unacknowledged anomaly of the same type exists for this department
    now = datetime.now(timezone.utc)
    one_day_ago = now - timedelta(days=1)
    
    existing_res = await db.execute(
        select(OperationalAnomaly).where(
            OperationalAnomaly.department_id == department_id,
            OperationalAnomaly.anomaly_type == anomaly_type,
            OperationalAnomaly.acknowledged_at.is_(None),
            OperationalAnomaly.detected_at >= one_day_ago
        )
    )
    existing = existing_res.scalars().first()
    
    if existing:
        existing.observed_value = observed
        existing.explanation = explanation
        existing.detected_at = now
    else:
        anomaly = OperationalAnomaly(
            department_id=department_id,
            anomaly_type=anomaly_type,
            severity=severity,
            metric_name=metric,
            observed_value=observed,
            expected_value=expected,
            explanation=explanation,
            detected_at=now
        )
        db.add(anomaly)

async def get_active_anomalies(db: AsyncSession, department_id: Optional[uuid.UUID] = None) -> List[OperationalAnomaly]:
    query = select(OperationalAnomaly).where(OperationalAnomaly.acknowledged_at.is_(None)).order_by(OperationalAnomaly.detected_at.desc())
    if department_id:
        query = query.where(OperationalAnomaly.department_id == department_id)
    res = await db.execute(query)
    return res.scalars().all()
