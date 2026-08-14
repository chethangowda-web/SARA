import jwt
import uuid
from typing import List, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User

# Authentication oauth2 scheme extracting token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=True
)

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency that extracts, validates JWT access token and loads current active user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        user_id_str: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id_str is None or token_type != "access":
            raise credentials_exception
            
        user_id = uuid.UUID(user_id_str)
    except jwt.PyJWTError:
        raise credentials_exception
    except ValueError:
        raise credentials_exception

    # Fetch user from DB
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account"
        )
        
    return user

class RoleChecker:
    """
    Reusable role authorization checker.
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this resource"
            )
        return current_user

# Resource-ownership stubs for future milestones
async def verify_resource_ownership(
    user: User, 
    resource_owner_id: uuid.UUID
) -> bool:
    """
    Stub for verifying if current user owns or is assigned the resource.
    - Citizens own their resources (owner_id matches user.id).
    - Officers own resources assigned to them.
    - Supervisors own resources in their department.
    - Admins have system-wide bypass.
    """
    if user.role.value == "ADMIN":
        return True
    return user.id == resource_owner_id
