import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.grievance import Grievance
from app.schemas.evidence import EvidenceUploadResponse, EvidenceListResponse
from app.services.evidence_service import upload_evidence, get_evidence_list
from app.api.grievances import _verify_access_auth
from app.core.rate_limiter import RateLimiter
from app.core.config import settings
from fastapi.responses import FileResponse
from app.models.evidence import Evidence
from app.models.user import UserRole
import os

router = APIRouter(prefix="/grievances", tags=["evidence"])

@router.post("/{id}/evidence", response_model=EvidenceUploadResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(10, 60, "user"))])
async def upload_grievance_evidence(
    id: uuid.UUID,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Fetch grievance
    result = await db.execute(select(Grievance).where(Grievance.id == id))
    grievance = result.scalars().first()
    if not grievance:
        raise HTTPException(status_code=404, detail="Grievance not found")

    # Verify authorization
    await _verify_access_auth(grievance, user, db)

    return await upload_evidence(db, grievance, user, file, description)

@router.get("/{id}/evidence", response_model=List[EvidenceUploadResponse])
async def list_grievance_evidence(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Fetch grievance
    result = await db.execute(select(Grievance).where(Grievance.id == id))
    grievance = result.scalars().first()
    if not grievance:
        raise HTTPException(status_code=404, detail="Grievance not found")

    # Verify authorization
    await _verify_access_auth(grievance, user, db)

    return await get_evidence_list(db, id)


@router.get("/{id}/evidence/{evidence_id}/download")
async def download_evidence(
    id: uuid.UUID,
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(select(Grievance).where(Grievance.id == id))
    grievance = result.scalars().first()
    if not grievance:
        raise HTTPException(status_code=404, detail="Grievance not found")

    await _verify_access_auth(grievance, user, db)

    ev_result = await db.execute(select(Evidence).where(Evidence.id == evidence_id, Evidence.grievance_id == id))
    evidence = ev_result.scalars().first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    if evidence.is_deleted:
        raise HTTPException(status_code=404, detail="Evidence has been deleted")

    # Path traversal protection
    base_dir = os.path.abspath(settings.UPLOAD_DIR)
    resolved_path = os.path.abspath(evidence.storage_path)
    if not resolved_path.startswith(base_dir):
        raise HTTPException(status_code=400, detail="Invalid path traversal detected")

    if not os.path.exists(resolved_path):
        raise HTTPException(status_code=404, detail="Physical evidence file not found")

    return FileResponse(resolved_path, media_type=evidence.file_type, filename=evidence.file_name)


@router.delete("/{id}/evidence/{evidence_id}")
async def delete_evidence(
    id: uuid.UUID,
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(select(Grievance).where(Grievance.id == id))
    grievance = result.scalars().first()
    if not grievance:
        raise HTTPException(status_code=404, detail="Grievance not found")

    await _verify_access_auth(grievance, user, db)

    ev_result = await db.execute(select(Evidence).where(Evidence.id == evidence_id, Evidence.grievance_id == id))
    evidence = ev_result.scalars().first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    # Check permission to delete
    is_owner = evidence.uploaded_by == user.id
    is_supervisor = user.role == UserRole.SUPERVISOR and grievance.department_id == user.department_id
    is_admin = user.role == UserRole.ADMIN

    if not (is_owner or is_supervisor or is_admin):
        raise HTTPException(status_code=403, detail="Not authorized to delete this evidence")

    evidence.is_deleted = True
    
    from app.services.audit_service import log_security_event
    await log_security_event(
        db=db,
        action="EVIDENCE_DELETED",
        actor_id=user.id,
        actor_role=user.role.value,
        resource_type="evidence",
        resource_id=evidence.id
    )
    
    await db.commit()
    return {"status": "deleted"}
