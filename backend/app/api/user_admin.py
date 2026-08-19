import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, update

from app.core.database import get_db
from app.core.dependencies import RoleChecker, get_current_user
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.staff_authorization import StaffAuthorization
from app.models.session import RefreshToken
from app.schemas.auth import UserProfile
from app.schemas.user import (
    UserCreateAdmin, UserUpdateAdmin, RoleUpdate, StatusUpdate,
    StaffAuthorizationCreate, StaffAuthorizationUpdate, StaffAuthorizationResponse
)
from app.services.audit_service import log_security_event

# Restrict all routes in this file to ADMIN role
router = APIRouter(
    prefix="/admin/users",
    tags=["admin_users"],
    dependencies=[Depends(RoleChecker([UserRole.ADMIN]))]
)

async def _verify_department(db: AsyncSession, department_id: Optional[uuid.UUID], role: UserRole):
    """Verify department requirements for officers and supervisors."""
    if role in [UserRole.OFFICER, UserRole.SUPERVISOR]:
        if not department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Department is required for role: {role.value}"
            )
        result = await db.execute(select(Department).where(Department.id == department_id))
        dept = result.scalars().first()
        if not dept or not dept.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or inactive department specified"
            )

async def _verify_not_last_admin_user(db: AsyncSession, user_id: uuid.UUID):
    """Safeguard: Cannot deactivate/modify the last active admin user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user and user.role == UserRole.ADMIN:
        count_res = await db.execute(
            select(func.count(User.id))
            .where(User.role == UserRole.ADMIN, User.is_active == True)
        )
        active_admins = count_res.scalar_one()
        if active_admins <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove or deactivate the last active administrator."
            )

async def _verify_not_last_admin_auth(db: AsyncSession, auth_id: uuid.UUID):
    """Safeguard: Cannot deactivate/revoke the last active admin authorization."""
    result = await db.execute(select(StaffAuthorization).where(StaffAuthorization.id == auth_id))
    auth = result.scalars().first()
    if auth and auth.role == UserRole.ADMIN:
        count_res = await db.execute(
            select(func.count(StaffAuthorization.id))
            .where(StaffAuthorization.role == UserRole.ADMIN, StaffAuthorization.is_active == True)
        )
        active_admins = count_res.scalar_one()
        if active_admins <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove or deactivate the last active administrator."
            )

@router.get("", response_model=List[UserProfile])
async def admin_list_users(
    role: Optional[UserRole] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(User)
    if role:
        query = query.where(User.role == role)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def admin_create_user(
    data: UserCreateAdmin,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user)
):
    email = data.email.lower().strip()
    result = await db.execute(select(User).where(User.email == email))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address already registered"
        )
        
    await _verify_department(db, data.department_id, data.role)
    
    new_user = User(
        email=email,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        role=data.role,
        department_id=data.department_id,
        is_active=True,
        email_verified=True,
        auth_provider="credentials"
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
    
    target_role = data.role if data.role else user.role
    target_dept = data.department_id if data.department_id is not None else user.department_id
    
    if data.role is not None or data.department_id is not None:
        await _verify_department(db, target_dept, target_role)
        
    if data.email:
        email = data.email.lower().strip()
        email_check = await db.execute(select(User).where(User.email == email, User.id != id))
        if email_check.scalars().first():
            raise HTTPException(status_code=409, detail="Email already in use")
        user.email = email
        
    if data.full_name:
        user.full_name = data.full_name
        
    if data.role:
        if data.role != user.role and user.role == UserRole.ADMIN:
            # Check last active admin safeguard
            await _verify_not_last_admin_user(db, id)
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
    
    if user.role == UserRole.ADMIN and data.role != UserRole.ADMIN:
        await _verify_not_last_admin_user(db, id)

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
        
    if user.role == UserRole.ADMIN and not data.is_active:
        await _verify_not_last_admin_user(db, id)

    previous_state = {"is_active": user.is_active}
    user.is_active = data.is_active
    
    action = "USER_REACTIVATED" if data.is_active else "USER_DEACTIVATED"
    
    # If deactivating, revoke all user sessions
    if not data.is_active:
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == id)
            .values(revoked_at=datetime.now(timezone.utc))
        )
    
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

# --- Staff Authorization Endpoints ---

@router.get("/staff-authorizations", response_model=List[StaffAuthorizationResponse])
async def admin_list_staff_authorizations(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(StaffAuthorization).order_by(StaffAuthorization.created_at.desc()))
    return result.scalars().all()

@router.post("/staff-authorizations", response_model=StaffAuthorizationResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_staff_authorization(
    data: StaffAuthorizationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user)
):
    email = data.email.lower().strip()
    
    # Check if duplicate authorization
    result = await db.execute(select(StaffAuthorization).where(StaffAuthorization.email == email))
    existing_auth = result.scalars().first()
    if existing_auth:
        if existing_auth.is_active:
            raise HTTPException(status_code=409, detail="Staff member is already authorized")
        else:
            # Reactivate authorization
            existing_auth.is_active = True
            existing_auth.role = data.role
            existing_auth.department_id = data.department_id
            existing_auth.revoked_at = None
            
            # Check department requirements
            await _verify_department(db, data.department_id, data.role)
            
            # Update user if exists
            user_res = await db.execute(select(User).where(User.email == email))
            user = user_res.scalars().first()
            if user:
                user.role = data.role
                user.department_id = data.department_id
                user.is_active = True
                
            await log_security_event(
                db,
                action="STAFF_AUTHORIZATION_REACTIVATED",
                actor_id=admin.id,
                actor_role=admin.role.value,
                resource_type="staff_authorization",
                resource_id=existing_auth.id,
                new_state={"email": email, "role": data.role.value}
            )
            await db.commit()
            await db.refresh(existing_auth)
            return existing_auth

    await _verify_department(db, data.department_id, data.role)
    
    new_auth = StaffAuthorization(
        email=email,
        role=data.role,
        department_id=data.department_id,
        is_active=True
    )
    db.add(new_auth)
    await db.flush()
    
    # If User already exists, update their role/department to match the authorization
    user_res = await db.execute(select(User).where(User.email == email))
    user = user_res.scalars().first()
    if user:
        user.role = data.role
        user.department_id = data.department_id
        user.is_active = True
        
    await log_security_event(
        db,
        action="STAFF_AUTHORIZATION_CREATED",
        actor_id=admin.id,
        actor_role=admin.role.value,
        resource_type="staff_authorization",
        resource_id=new_auth.id,
        new_state={"email": email, "role": data.role.value}
    )
    await db.commit()
    await db.refresh(new_auth)
    return new_auth

@router.patch("/staff-authorizations/{id}", response_model=StaffAuthorizationResponse)
async def admin_update_staff_authorization(
    id: uuid.UUID,
    data: StaffAuthorizationUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user)
):
    result = await db.execute(select(StaffAuthorization).where(StaffAuthorization.id == id))
    auth = result.scalars().first()
    if not auth:
        raise HTTPException(status_code=404, detail="Staff authorization record not found")
        
    previous_state = {"role": auth.role.value, "department_id": str(auth.department_id) if auth.department_id else None, "is_active": auth.is_active}
    
    # Safeguard check for deactivation
    if data.is_active is False and auth.is_active:
        await _verify_not_last_admin_auth(db, id)

    target_role = data.role if data.role is not None else auth.role
    target_dept = data.department_id if data.department_id is not None else auth.department_id
    
    if data.role is not None or data.department_id is not None:
        await _verify_department(db, target_dept, target_role)
        
    if data.role is not None:
        if auth.role == UserRole.ADMIN and data.role != UserRole.ADMIN:
            await _verify_not_last_admin_auth(db, id)
        auth.role = data.role
        
    if data.department_id is not None:
        auth.department_id = data.department_id
        
    if data.is_active is not None:
        auth.is_active = data.is_active
        if not data.is_active:
            auth.revoked_at = datetime.now(timezone.utc)
            # Find and deactivate the user account as well, revoking session tokens
            user_res = await db.execute(select(User).where(User.email == auth.email))
            user = user_res.scalars().first()
            if user:
                user.is_active = False
                await db.execute(
                    update(RefreshToken)
                    .where(RefreshToken.user_id == user.id)
                    .values(revoked_at=datetime.now(timezone.utc))
                )
        else:
            auth.revoked_at = None
            # Reactivate user account if it exists
            user_res = await db.execute(select(User).where(User.email == auth.email))
            user = user_res.scalars().first()
            if user:
                user.is_active = True
                
    await log_security_event(
        db,
        action="STAFF_AUTHORIZATION_UPDATED",
        actor_id=admin.id,
        actor_role=admin.role.value,
        resource_type="staff_authorization",
        resource_id=auth.id,
        previous_state=previous_state,
        new_state={"role": auth.role.value, "department_id": str(auth.department_id) if auth.department_id else None, "is_active": auth.is_active}
    )
    await db.commit()
    await db.refresh(auth)
    return auth
