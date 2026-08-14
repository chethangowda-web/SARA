import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from app.models.user import User, UserRole
from app.models.grievance import Grievance
from app.models.assignment import Assignment
from app.models.grievance_event import GrievanceEvent
from app.schemas.grievance import (
    GrievanceCreate,
    GrievanceResponse,
    GrievanceVerify,
    GrievanceAssign,
    GrievanceResolve,
    GrievanceEventResponse,
    VerificationAction
)
from app.services.grievance_service import create_grievance, transition_grievance
from app.core.rate_limiter import RateLimiter

router = APIRouter(prefix="/grievances", tags=["grievances"])

# Common auth validation helper for a grievance
async def _verify_access_auth(grievance: Grievance, user: User, db: AsyncSession) -> None:
    if user.role == UserRole.ADMIN:
        return
        
    if user.role == UserRole.CITIZEN:
        if grievance.citizen_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: citizen does not own this resource"
            )
        return
        
    if user.role == UserRole.OFFICER:
        # Check active assignment
        result = await db.execute(
            select(Assignment).where(
                Assignment.grievance_id == grievance.id,
                Assignment.officer_id == user.id,
                Assignment.is_active == True
            )
        )
        if not result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: officer is not currently assigned to this resource"
            )
        return
        
    if user.role == UserRole.SUPERVISOR:
        if grievance.department_id != user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: supervisor department mismatch"
            )
        return
        
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

# CITIZEN: Submit a grievance
@router.post("", response_model=GrievanceResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(20, 60, "user"))])
async def submit_new_grievance(
    data: GrievanceCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    citizen: User = Depends(get_current_user)
):
    if citizen.role != UserRole.CITIZEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizen role can submit a grievance"
        )
    grievance = await create_grievance(
        db=db,
        citizen=citizen,
        title=data.title,
        description=data.description,
        location=data.location,
        ip_address=request.client.host if request.client else None
    )
    # Trigger AI Pipeline (Classify, Priority, Summarize, Vector Embeddings, Duplicate Check)
    from app.ai.pipeline import process_grievance_ai_pipeline
    return await process_grievance_ai_pipeline(db, grievance.id)

# CITIZEN: List own grievances
@router.get("", response_model=List[GrievanceResponse])
async def list_my_grievances(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    citizen: User = Depends(get_current_user)
):
    if limit < 1:
        limit = 20
    if limit > 100:
        limit = 100
    if offset < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Offset cannot be negative")

    if citizen.role == UserRole.ADMIN:
        result = await db.execute(
            select(Grievance)
            .order_by(Grievance.created_at.desc())
            .limit(limit)
            .offset(offset)
            .options(selectinload(Grievance.citizen), selectinload(Grievance.department))
        )
    elif citizen.role == UserRole.CITIZEN:
        result = await db.execute(
            select(Grievance)
            .where(Grievance.citizen_id == citizen.id)
            .order_by(Grievance.created_at.desc())
            .limit(limit)
            .offset(offset)
            .options(selectinload(Grievance.citizen), selectinload(Grievance.department))
        )
    else:
        # Officers and supervisors list department or assignments separately
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Use role-specific endpoints to list resources"
        )
    return result.scalars().all()

# CITIZEN: Get detailed grievance
@router.get("/{id}", response_model=GrievanceResponse)
async def get_grievance_detail(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Grievance)
        .where(Grievance.id == id)
        .options(selectinload(Grievance.citizen), selectinload(Grievance.department))
    )
    grievance = result.scalars().first()
    if not grievance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grievance not found"
        )
    await _verify_access_auth(grievance, user, db)
    return grievance

# CITIZEN: Verify resolution (Accept/Reject)
@router.post("/{id}/verify", response_model=GrievanceResponse)
async def verify_grievance_resolution(
    id: uuid.UUID,
    data: GrievanceVerify,
    request: Request,
    db: AsyncSession = Depends(get_db),
    citizen: User = Depends(get_current_user)
):
    result = await db.execute(select(Grievance).where(Grievance.id == id))
    grievance = result.scalars().first()
    if not grievance:
        raise HTTPException(status_code=404, detail="Grievance not found")
        
    await _verify_access_auth(grievance, citizen, db)
    
    target_state = "CLOSED" if data.action == VerificationAction.ACCEPT else "REOPENED"
    payload = {"reason": data.reason} if data.reason else {}
    
    return await transition_grievance(
        db=db,
        grievance_id=id,
        target_state=target_state,
        actor=citizen,
        payload=payload,
        ip_address=request.client.host if request.client else None
    )

# OFFICER: Acknowledge assigned grievance
@router.post("/{id}/acknowledge", response_model=GrievanceResponse)
async def acknowledge_grievance(
    id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    officer: User = Depends(get_current_user)
):
    return await transition_grievance(
        db=db,
        grievance_id=id,
        target_state="ACKNOWLEDGED",
        actor=officer,
        ip_address=request.client.host if request.client else None
    )

# OFFICER: Start work on assigned grievance
@router.post("/{id}/start", response_model=GrievanceResponse)
async def start_grievance_work(
    id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    officer: User = Depends(get_current_user)
):
    return await transition_grievance(
        db=db,
        grievance_id=id,
        target_state="IN_PROGRESS",
        actor=officer,
        ip_address=request.client.host if request.client else None
    )

# OFFICER: Submit resolution notes
@router.post("/{id}/resolve", response_model=GrievanceResponse)
async def resolve_grievance(
    id: uuid.UUID,
    data: GrievanceResolve,
    request: Request,
    db: AsyncSession = Depends(get_db),
    officer: User = Depends(get_current_user)
):
    # Transition to RESOLUTION_SUBMITTED first
    g = await transition_grievance(
        db=db,
        grievance_id=id,
        target_state="RESOLUTION_SUBMITTED",
        actor=officer,
        payload={"resolution_notes": data.resolution_notes},
        ip_address=request.client.host if request.client else None
    )
    
    # Enforce auto-transition immediately into VERIFICATION state via SYSTEM actor
    system_user = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000000"), # Zero-UUID system placeholder
        email="system@sara.gov",
        full_name="SARA Automation System",
        password_hash="",
        role=UserRole.ADMIN, # System runs with admin privileges
        is_active=True
    )
    
    return await transition_grievance(
        db=db,
        grievance_id=id,
        target_state="VERIFICATION",
        actor=system_user,
        ip_address=request.client.host if request.client else None
    )

# SUPERVISOR: List department grievances
@router.get("/department/list", response_model=List[GrievanceResponse])
async def list_department_grievances(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    supervisor: User = Depends(RoleChecker([UserRole.SUPERVISOR, UserRole.ADMIN]))
):
    if limit < 1:
        limit = 20
    if limit > 100:
        limit = 100
    if offset < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Offset cannot be negative")

    if supervisor.role == UserRole.ADMIN:
        result = await db.execute(
            select(Grievance)
            .order_by(Grievance.created_at.desc())
            .limit(limit)
            .offset(offset)
            .options(selectinload(Grievance.citizen), selectinload(Grievance.department))
        )
    else:
        if supervisor.department_id is None:
            raise HTTPException(status_code=400, detail="Supervisor has no department assigned")
        result = await db.execute(
            select(Grievance)
            .where(Grievance.department_id == supervisor.department_id)
            .order_by(Grievance.created_at.desc())
            .limit(limit)
            .offset(offset)
            .options(selectinload(Grievance.citizen), selectinload(Grievance.department))
        )
    return result.scalars().all()

# SUPERVISOR: Assign/reassign officer to grievance
@router.post("/{id}/assign", response_model=GrievanceResponse)
async def assign_grievance_officer(
    id: uuid.UUID,
    data: GrievanceAssign,
    request: Request,
    db: AsyncSession = Depends(get_db),
    supervisor: User = Depends(RoleChecker([UserRole.SUPERVISOR, UserRole.ADMIN]))
):
    return await transition_grievance(
        db=db,
        grievance_id=id,
        target_state="ASSIGNED",
        actor=supervisor,
        payload={"officer_id": str(data.officer_id)},
        ip_address=request.client.host if request.client else None
    )

# SHARED: Get chronological event timeline
@router.get("/{id}/timeline", response_model=List[GrievanceEventResponse])
async def get_grievance_timeline(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(select(Grievance).where(Grievance.id == id))
    grievance = result.scalars().first()
    if not grievance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grievance not found"
        )
    await _verify_access_auth(grievance, user, db)
    
    events_res = await db.execute(
        select(GrievanceEvent)
        .where(GrievanceEvent.grievance_id == id)
        .order_by(GrievanceEvent.created_at.asc())
    )
    return events_res.scalars().all()
