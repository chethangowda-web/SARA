import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.dependencies import RoleChecker, get_current_user
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.department import Department
from app.schemas.auth import UserProfile
from app.schemas.user import UserCreateAdmin, UserUpdateAdmin, RoleUpdate, StatusUpdate
from app.services.audit_service import log_security_event

# Restrict all routes in this file to ADMIN role
router = APIRouter(
    prefix="/admin/users",
    tags=["admin_users"],
    dependencies=[Depends(RoleChecker(["ADMIN"]))]
)

async def _verify_department(db: AsyncSession, department_id: Optional[uuid.UUID], role: UserRole):
    """Verify department requirements for officers and supervisors."""
    if role in [UserRole.OFFICER, UserRole.SUPERVISOR]:
        if not department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Department is required for role: {role.value}"
            )
        # Check if department exists
        result = await db.execute(select(Department).where(Department.id == department_id))
        dept = result.scalars().first()
        if not dept or not dept.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or inactive department specified"
            )

@router.post("", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def admin_create_user(
    data: UserCreateAdmin,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user)
):
    # Check if duplicate email
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address already registered"
        )
        
    await _verify_department(db, data.department_id, data.role)
    
    new_user = User(
        email=data.email,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        role=data.role,
        department_id=data.department_id,
        is_active=True
    )
    db.add(new_user)
    await db.flush()
    
    await log_security_event(
        db,
        action="USER_CREATED",
        actor_id=admin.id,
        actor_role=admin.role.value,
        resource_type="user",
        resource_id=new_user.id,
        new_state={"role": new_user.role.value, "email": new_user.email},
        ip_address=request.client.host if request.client else None
    )
    await db.commit()
    return new_user

@router.patch("/{id}", response_model=UserProfile)
async def admin_update_user(
    id: uuid.UUID,
    data: UserUpdateAdmin,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user)
):
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    previous_state = {"email": user.email, "full_name": user.full_name, "role": user.role.value, "department_id": str(user.department_id) if user.department_id else None}
    
    # Check department validation if role or department changes
    target_role = data.role if data.role else user.role
    target_dept = data.department_id if data.department_id is not None else user.department_id
    
    if data.role is not None or data.department_id is not None:
        await _verify_department(db, target_dept, target_role)
        
    if data.email:
        # Check if email duplicate
        email_check = await db.execute(select(User).where(User.email == data.email, User.id != id))
        if email_check.scalars().first():
            raise HTTPException(status_code=409, detail="Email already in use")
        user.email = data.email
        
    if data.full_name:
        user.full_name = data.full_name
        
    if data.role:
        user.role = data.role
        
    if data.department_id is not None:
        user.department_id = data.department_id
        
    new_state = {"email": user.email, "full_name": user.full_name, "role": user.role.value, "department_id": str(user.department_id) if user.department_id else None}
    
    await log_security_event(
        db,
        action="USER_UPDATED",
        actor_id=admin.id,
        actor_role=admin.role.value,
        resource_type="user",
        resource_id=user.id,
        previous_state=previous_state,
        new_state=new_state,
        ip_address=request.client.host if request.client else None
    )
    await db.commit()
    return user

@router.patch("/{id}/role", response_model=UserProfile)
async def admin_change_role(
    id: uuid.UUID,
    data: RoleUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user)
):
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    previous_state = {"role": user.role.value}
    
    # Verify department matches role requirements
    await _verify_department(db, user.department_id, data.role)
    
    user.role = data.role
    
    await log_security_event(
        db,
        action="ROLE_CHANGED",
        actor_id=admin.id,
        actor_role=admin.role.value,
        resource_type="user",
        resource_id=user.id,
        previous_state=previous_state,
        new_state={"role": user.role.value},
        ip_address=request.client.host if request.client else None
    )
    await db.commit()
    return user

@router.patch("/{id}/status", response_model=UserProfile)
async def admin_change_status(
    id: uuid.UUID,
    data: StatusUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user)
):
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    previous_state = {"is_active": user.is_active}
    user.is_active = data.is_active
    
    action = "USER_REACTIVATED" if data.is_active else "USER_DEACTIVATED"
    
    await log_security_event(
        db,
        action=action,
        actor_id=admin.id,
        actor_role=admin.role.value,
        resource_type="user",
        resource_id=user.id,
        previous_state=previous_state,
        new_state={"is_active": user.is_active},
        ip_address=request.client.host if request.client else None
    )
    await db.commit()
    return user
