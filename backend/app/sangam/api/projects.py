import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.sangam.schemas import (
    GovernmentProjectCreate,
    GovernmentProjectUpdate,
    GovernmentProjectResponse
)
from app.sangam.services.investment_service import InvestmentService
from app.sangam.api.intelligence import verify_sangam_access

router = APIRouter(prefix="/sangam/projects", tags=["sangam_projects"])
investment_service = InvestmentService()


@router.get("", response_model=List[GovernmentProjectResponse])
async def list_government_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dept_id = verify_sangam_access(current_user)
    await investment_service.seed_demo_projects_if_empty(db)
    projects = await investment_service.list_projects(db, department_id=dept_id)
    return projects


@router.get("/{project_id}", response_model=GovernmentProjectResponse)
async def get_government_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dept_id = verify_sangam_access(current_user)
    project = await investment_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Government project not found")
    if dept_id and project.department_id and project.department_id != dept_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied for department")

    return project


@router.post("", response_model=GovernmentProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_government_project(
    data: GovernmentProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERVISOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin and Supervisor roles can add new government projects."
        )
    if current_user.role == UserRole.SUPERVISOR and current_user.department_id:
        data.department_id = current_user.department_id

    project = await investment_service.create_project(db, data)
    # Re-run project matching
    await investment_service.match_projects_to_clusters(db)
    return project


@router.patch("/{project_id}", response_model=GovernmentProjectResponse)
async def update_government_project(
    project_id: uuid.UUID,
    data: GovernmentProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERVISOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin and Supervisor roles can update government projects."
        )

    project = await investment_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Government project not found")
    if current_user.role == UserRole.SUPERVISOR and project.department_id != current_user.department_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied for department")

    updated = await investment_service.update_project(db, project_id, data)
    await investment_service.match_projects_to_clusters(db)
    return updated
