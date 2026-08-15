import uuid
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, case
from app.models.grievance import Grievance
from app.models.department import Department
from app.models.assignment import Assignment
from app.models.user import User
from app.models.grievance_event import GrievanceEvent
from app.schemas.analytics import GlobalMetricsResponse, DepartmentMetricsResponse, OfficerMetricsResponse

async def _get_base_metrics(db: AsyncSession, department_id: Optional[uuid.UUID] = None) -> dict:
    query = select(
        func.count(Grievance.id).label("total"),
        func.sum(case((Grievance.current_state != 'CLOSED', 1), else_=0)).label("open"),
        func.sum(case((Grievance.current_state == 'CLOSED', 1), else_=0)).label("closed"),
        func.sum(case((Grievance.current_state == 'REOPENED', 1), else_=0)).label("reopened"),
        func.sum(case((Grievance.escalation_level == 1, 1), else_=0)).label("warnings"),
        func.sum(case((Grievance.escalation_level == 2, 1), else_=0)).label("breaches"),
        func.sum(case((Grievance.escalated == True, 1), else_=0)).label("escalated"),
        func.sum(case((Grievance.risk_score >= 70, 1), else_=0)).label("critical")
    )
    if department_id:
        query = query.where(Grievance.department_id == department_id)
        
    res = await db.execute(query)
    row = res.first()
    
    # Safely convert to ints
    def _int(val): return int(val) if val else 0
    
    return {
        "total": _int(row[0]),
        "open": _int(row[1]),
        "closed": _int(row[2]),
        "reopened": _int(row[3]),
        "warnings": _int(row[4]),
        "breaches": _int(row[5]),
        "escalated": _int(row[6]),
        "critical": _int(row[7])
    }

async def _get_average_times(db: AsyncSession, department_id: Optional[uuid.UUID] = None) -> dict:
    # Average Resolution Time (closed_at - submitted_at)
    res_query = select(
        func.avg(func.extract('epoch', Grievance.closed_at) - func.extract('epoch', Grievance.submitted_at))
    ).where(Grievance.closed_at.is_not(None))
    if department_id:
        res_query = res_query.where(Grievance.department_id == department_id)
    res_avg = await db.execute(res_query)
    res_seconds = res_avg.scalar_one_or_none() or 0.0

    # Average Assignment Time (assigned_at - submitted_at)
    ass_query = select(
        func.avg(func.extract('epoch', Grievance.assigned_at) - func.extract('epoch', Grievance.submitted_at))
    ).where(Grievance.assigned_at.is_not(None))
    if department_id:
        ass_query = ass_query.where(Grievance.department_id == department_id)
    ass_avg = await db.execute(ass_query)
    ass_seconds = ass_avg.scalar_one_or_none() or 0.0

    # Average Acknowledgement Time
    # Using the first OFFICER_ACKNOWLEDGED event minus the assigned_at
    ack_subq = (
        select(GrievanceEvent.grievance_id, func.min(GrievanceEvent.created_at).label("ack_at"))
        .where(GrievanceEvent.event_type == 'OFFICER_ACKNOWLEDGED')
        .group_by(GrievanceEvent.grievance_id)
        .subquery()
    )
    
    ack_query = select(
        func.avg(func.extract('epoch', ack_subq.c.ack_at) - func.extract('epoch', Grievance.assigned_at))
    ).select_from(ack_subq).join(Grievance, Grievance.id == ack_subq.c.grievance_id).where(Grievance.assigned_at.is_not(None))
    if department_id:
        ack_query = ack_query.where(Grievance.department_id == department_id)
        
    ack_avg = await db.execute(ack_query)
    ack_seconds = ack_avg.scalar_one_or_none() or 0.0

    return {
        "resolution_hours": round(float(res_seconds) / 3600.0, 2),
        "assignment_hours": round(float(ass_seconds) / 3600.0, 2),
        "acknowledgement_hours": round(float(ack_seconds) / 3600.0, 2)
    }

async def get_global_metrics(db: AsyncSession) -> GlobalMetricsResponse:
    base = await _get_base_metrics(db)
    times = await _get_average_times(db)
    
    sla_compliance = 100.0
    if base["total"] > 0:
        sla_compliance = round(((base["total"] - base["breaches"]) / base["total"]) * 100.0, 2)
        
    return GlobalMetricsResponse(
        total_grievances=base["total"],
        open_grievances=base["open"],
        closed_grievances=base["closed"],
        reopened_grievances=base["reopened"],
        sla_warnings=base["warnings"],
        sla_breaches=base["breaches"],
        escalated_grievances=base["escalated"],
        critical_high_risk=base["critical"],
        average_resolution_hours=times["resolution_hours"],
        average_assignment_hours=times["assignment_hours"],
        average_acknowledgement_hours=times["acknowledgement_hours"],
        sla_compliance_percent=max(0.0, sla_compliance)
    )

async def get_department_metrics(db: AsyncSession, department_id: uuid.UUID) -> DepartmentMetricsResponse:
    dept_res = await db.execute(select(Department).where(Department.id == department_id))
    dept = dept_res.scalars().first()
    if not dept:
        raise ValueError("Department not found")
        
    base = await _get_base_metrics(db, department_id)
    times = await _get_average_times(db, department_id)
    
    sla_compliance = 100.0
    if base["total"] > 0:
        sla_compliance = round(((base["total"] - base["breaches"]) / base["total"]) * 100.0, 2)
        
    # Risk Distribution
    res_risk = await db.execute(select(Grievance.risk_score).where(Grievance.department_id == department_id))
    risk_scores = [r[0] for r in res_risk.all()]
    risk_dist = {
        "Low (0-30)": sum(1 for s in risk_scores if s <= 30),
        "Medium (31-69)": sum(1 for s in risk_scores if 30 < s < 70),
        "High (70+)": sum(1 for s in risk_scores if s >= 70),
    }

    return DepartmentMetricsResponse(
        department_id=dept.id,
        department_name=dept.name,
        total_grievances=base["total"],
        open_grievances=base["open"],
        closed_grievances=base["closed"],
        sla_compliance_percent=max(0.0, sla_compliance),
        average_resolution_hours=times["resolution_hours"],
        average_assignment_hours=times["assignment_hours"],
        average_acknowledgement_hours=times["acknowledgement_hours"],
        escalation_count=base["escalated"],
        risk_distribution=risk_dist,
        reopened_grievances=base["reopened"]
    )

async def get_officer_metrics(db: AsyncSession, officer_id: uuid.UUID) -> OfficerMetricsResponse:
    officer_res = await db.execute(select(User).where(User.id == officer_id))
    officer = officer_res.scalars().first()
    if not officer:
        raise ValueError("Officer not found")
        
    # Assigned count
    asg_query = select(func.count(Assignment.id)).where(Assignment.officer_id == officer_id)
    asg_res = await db.execute(asg_query)
    assigned = asg_res.scalar_one_or_none() or 0
    
    # Active workload
    act_query = select(func.count(Assignment.id)).select_from(Assignment).join(Grievance).where(
        Assignment.officer_id == officer_id,
        Assignment.is_active == True,
        Grievance.current_state != 'CLOSED'
    )
    act_res = await db.execute(act_query)
    active = act_res.scalar_one_or_none() or 0
    
    # Completed (Assigned && Grievance is CLOSED)
    comp_query = select(func.count(Assignment.id)).select_from(Assignment).join(Grievance).where(
        Assignment.officer_id == officer_id,
        Grievance.current_state == 'CLOSED'
    )
    comp_res = await db.execute(comp_query)
    completed = comp_res.scalar_one_or_none() or 0
    
    # Breaches associated with assigned grievances
    br_query = select(func.count(Grievance.id)).select_from(Assignment).join(Grievance).where(
        Assignment.officer_id == officer_id,
        Grievance.escalation_level == 2
    )
    br_res = await db.execute(br_query)
    breaches = br_res.scalar_one_or_none() or 0
    
    # Reopened associated with assigned grievances
    ro_query = select(func.count(Grievance.id)).select_from(Assignment).join(Grievance).where(
        Assignment.officer_id == officer_id,
        Grievance.current_state == 'REOPENED'
    )
    ro_res = await db.execute(ro_query)
    reopened = ro_res.scalar_one_or_none() or 0

    # Average Resolution Time (for this officer's completed grievances)
    res_time_query = select(
        func.avg(func.extract('epoch', Grievance.closed_at) - func.extract('epoch', Grievance.submitted_at))
    ).select_from(Assignment).join(Grievance).where(
        Assignment.officer_id == officer_id,
        Grievance.closed_at.is_not(None)
    )
    res_time_avg = await db.execute(res_time_query)
    res_seconds = res_time_avg.scalar_one_or_none() or 0.0

    # Average Acknowledgement Time (for this officer)
    ack_subq = (
        select(GrievanceEvent.grievance_id, func.min(GrievanceEvent.created_at).label("ack_at"))
        .where(GrievanceEvent.event_type == 'OFFICER_ACKNOWLEDGED', GrievanceEvent.actor_id == officer_id)
        .group_by(GrievanceEvent.grievance_id)
        .subquery()
    )
    
    ack_query = select(
        func.avg(func.extract('epoch', ack_subq.c.ack_at) - func.extract('epoch', Grievance.assigned_at))
    ).select_from(ack_subq).join(Grievance, Grievance.id == ack_subq.c.grievance_id).join(Assignment, Assignment.grievance_id == Grievance.id).where(
        Assignment.officer_id == officer_id,
        Grievance.assigned_at.is_not(None)
    )
    ack_avg = await db.execute(ack_query)
    ack_seconds = ack_avg.scalar_one_or_none() or 0.0

    return OfficerMetricsResponse(
        officer_id=officer.id,
        officer_name=officer.full_name,
        assigned_grievances=assigned,
        active_workload=active,
        completed_grievances=completed,
        average_acknowledgement_hours=round(float(ack_seconds) / 3600.0, 2),
        average_resolution_hours=round(float(res_seconds) / 3600.0, 2),
        sla_breaches=breaches,
        reopened_grievances=reopened
    )
