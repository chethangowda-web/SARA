import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, cast, Date
from app.models.grievance import Grievance
from app.models.assignment import Assignment
from app.schemas.analytics import TrendResponse, TrendPoint

async def get_volume_trend(
    db: AsyncSession, 
    department_id: Optional[uuid.UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> TrendResponse:
    query = select(
        cast(Grievance.created_at, Date).label("date"),
        func.count(Grievance.id).label("count")
    )
    
    if department_id:
        query = query.where(Grievance.department_id == department_id)
    if start_date:
        query = query.where(Grievance.created_at >= start_date)
    if end_date:
        query = query.where(Grievance.created_at <= end_date)
        
    query = query.group_by(cast(Grievance.created_at, Date)).order_by(cast(Grievance.created_at, Date))
    
    res = await db.execute(query)
    points = []
    for row in res.all():
        points.append(TrendPoint(timestamp=row[0].isoformat(), value=row[1]))
        
    return TrendResponse(metric="daily_volume", points=points)

async def get_closure_trend(
    db: AsyncSession, 
    department_id: Optional[uuid.UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> TrendResponse:
    query = select(
        cast(Grievance.closed_at, Date).label("date"),
        func.count(Grievance.id).label("count")
    ).where(Grievance.closed_at.is_not(None))
    
    if department_id:
        query = query.where(Grievance.department_id == department_id)
    if start_date:
        query = query.where(Grievance.closed_at >= start_date)
    if end_date:
        query = query.where(Grievance.closed_at <= end_date)
        
    query = query.group_by(cast(Grievance.closed_at, Date)).order_by(cast(Grievance.closed_at, Date))
    
    res = await db.execute(query)
    points = []
    for row in res.all():
        points.append(TrendPoint(timestamp=row[0].isoformat(), value=row[1]))
        
    return TrendResponse(metric="daily_closures", points=points)

async def get_sla_breach_trend(
    db: AsyncSession, 
    department_id: Optional[uuid.UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> TrendResponse:
    query = select(
        cast(Grievance.created_at, Date).label("date"),
        func.count(Grievance.id).label("count")
    ).where(Grievance.escalation_level == 2)
    
    if department_id:
        query = query.where(Grievance.department_id == department_id)
    if start_date:
        query = query.where(Grievance.created_at >= start_date)
    if end_date:
        query = query.where(Grievance.created_at <= end_date)
        
    query = query.group_by(cast(Grievance.created_at, Date)).order_by(cast(Grievance.created_at, Date))
    
    res = await db.execute(query)
    points = []
    for row in res.all():
        points.append(TrendPoint(timestamp=row[0].isoformat(), value=row[1]))
        
    return TrendResponse(metric="daily_sla_breaches", points=points)

async def get_resolution_time_trend(
    db: AsyncSession, 
    department_id: Optional[uuid.UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> TrendResponse:
    query = select(
        cast(Grievance.closed_at, Date).label("date"),
        func.avg(func.extract('epoch', Grievance.closed_at) - func.extract('epoch', Grievance.submitted_at)).label("avg_seconds")
    ).where(Grievance.closed_at.is_not(None))
    
    if department_id:
        query = query.where(Grievance.department_id == department_id)
    if start_date:
        query = query.where(Grievance.closed_at >= start_date)
    if end_date:
        query = query.where(Grievance.closed_at <= end_date)
        
    query = query.group_by(cast(Grievance.closed_at, Date)).order_by(cast(Grievance.closed_at, Date))
    
    res = await db.execute(query)
    points = []
    for row in res.all():
        points.append(TrendPoint(timestamp=row[0].isoformat(), value=round(float(row[1]) / 3600.0, 2)))
        
    return TrendResponse(metric="daily_average_resolution_hours", points=points)
