import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from app.models.user import User, UserRole
from app.models.department import Department
from app.schemas.analytics import (
    GlobalMetricsResponse, DepartmentMetricsResponse, OfficerMetricsResponse, 
    TrendResponse, AnomalyResponse, AIInsightResponse
)
from app.analytics.metrics import get_global_metrics, get_department_metrics, get_officer_metrics
from app.analytics.trends import (
    get_volume_trend, get_closure_trend, get_sla_breach_trend, get_resolution_time_trend
)
from app.analytics.anomalies import get_active_anomalies
from app.analytics.insights import InsightsGenerator

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

def enforce_department_boundary(user: User, department_id: Optional[uuid.UUID]):
    if user.role == UserRole.SUPERVISOR:
        if not user.department_id:
            raise HTTPException(status_code=403, detail="Supervisor has no assigned department")
        if department_id and str(user.department_id) != str(department_id):
            raise HTTPException(status_code=403, detail="Supervisors can only access their own department's analytics")

@router.get("/overview", response_model=GlobalMetricsResponse)
async def get_overview(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RoleChecker([UserRole.ADMIN, UserRole.SUPERVISOR]))
):
    if user.role == UserRole.SUPERVISOR:
        raise HTTPException(status_code=403, detail="Supervisors must use department endpoints for overview")
    return await get_global_metrics(db)

@router.get("/departments", response_model=List[DepartmentMetricsResponse])
async def list_departments(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RoleChecker([UserRole.ADMIN, UserRole.SUPERVISOR]))
):
    dept_res = await db.execute(select(Department.id).where(Department.is_active == True))
    all_depts = dept_res.scalars().all()
    
    results = []
    for dept_id in all_depts:
        if user.role == UserRole.SUPERVISOR and user.department_id != dept_id:
            continue
        results.append(await get_department_metrics(db, dept_id))
        
    return results

@router.get("/departments/{id}", response_model=DepartmentMetricsResponse)
async def get_department(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RoleChecker([UserRole.ADMIN, UserRole.SUPERVISOR]))
):
    enforce_department_boundary(user, id)
    return await get_department_metrics(db, id)

@router.get("/officers", response_model=List[OfficerMetricsResponse])
async def list_officers(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RoleChecker([UserRole.ADMIN, UserRole.SUPERVISOR]))
):
    query = select(User.id).where(User.role == UserRole.OFFICER, User.is_active == True)
    if user.role == UserRole.SUPERVISOR:
        query = query.where(User.department_id == user.department_id)
        
    officer_ids = (await db.execute(query)).scalars().all()
    
    results = []
    for oid in officer_ids:
        results.append(await get_officer_metrics(db, oid))
    return results

@router.get("/officers/{id}", response_model=OfficerMetricsResponse)
async def get_officer(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.role == UserRole.CITIZEN:
        raise HTTPException(status_code=403, detail="Forbidden")
        
    if user.role == UserRole.OFFICER:
        if str(user.id) != str(id):
            raise HTTPException(status_code=403, detail="Officers can only view their own metrics")
            
    if user.role == UserRole.SUPERVISOR:
        off_res = await db.execute(select(User).where(User.id == id))
        officer = off_res.scalars().first()
        if not officer or officer.department_id != user.department_id:
            raise HTTPException(status_code=403, detail="Supervisor can only view officers in their department")
            
    return await get_officer_metrics(db, id)

@router.get("/trends", response_model=List[TrendResponse])
async def get_trends(
    department_id: Optional[uuid.UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RoleChecker([UserRole.ADMIN, UserRole.SUPERVISOR]))
):
    enforce_department_boundary(user, department_id)
    if user.role == UserRole.SUPERVISOR:
        department_id = user.department_id
        
    res = []
    res.append(await get_volume_trend(db, department_id, start_date, end_date))
    res.append(await get_closure_trend(db, department_id, start_date, end_date))
    res.append(await get_sla_breach_trend(db, department_id, start_date, end_date))
    res.append(await get_resolution_time_trend(db, department_id, start_date, end_date))
    return res

@router.get("/anomalies", response_model=List[AnomalyResponse])
async def list_anomalies(
    department_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RoleChecker([UserRole.ADMIN, UserRole.SUPERVISOR]))
):
    enforce_department_boundary(user, department_id)
    if user.role == UserRole.SUPERVISOR:
        department_id = user.department_id
        
    return await get_active_anomalies(db, department_id)

@router.get("/insights", response_model=AIInsightResponse)
async def get_insights(
    department_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RoleChecker([UserRole.ADMIN, UserRole.SUPERVISOR]))
):
    enforce_department_boundary(user, department_id)
    
    global_metrics = await get_global_metrics(db)
    
    dept_metrics_list = []
    if user.role == UserRole.SUPERVISOR or department_id:
        target_dept = department_id or user.department_id
        dept_metrics_list.append(await get_department_metrics(db, target_dept))
    else:
        dept_res = await db.execute(select(Department.id).where(Department.is_active == True))
        for did in dept_res.scalars().all():
            dept_metrics_list.append(await get_department_metrics(db, did))
            
    generator = InsightsGenerator()
    return generator.generate_insights(global_metrics, dept_metrics_list)
