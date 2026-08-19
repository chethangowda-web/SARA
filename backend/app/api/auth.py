import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.session import RefreshToken
from app.schemas.auth import UserRegister, UserLogin, UserProfile, Token, RefreshTokenIn, UserSignupResponse
from app.services.audit_service import log_security_event
from app.core.rate_limiter import RateLimiter
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/auth", tags=["auth"])

def _hash_token(token: str) -> str:
    """Helper to sha256 hash refresh tokens for database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def _serialize_user(user: User) -> dict:
    """Serialize a User (with department relationship loaded) to a profile dict."""
    department_name = None
    department = getattr(user, "department", None)
    if department is not None:
        department_name = department.name
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "department_id": str(user.department_id) if user.department_id else None,
        "department_name": department_name,
        "is_active": user.is_active,
        "preferred_language": user.preferred_language,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }

def _set_refresh_cookie(response: Response, token: str):
    """Set the refresh token cookie with security flags."""
    response.set_cookie(
        key="sara_refresh_token",
        value=token,
        httponly=True,
        samesite="strict",
        secure=settings.COOKIE_SECURE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/"
    )

def _clear_refresh_cookie(response: Response):
    """Clear the refresh token cookie."""
    response.delete_cookie(
        key="sara_refresh_token",
        path="/"
    )

@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(5, 60, "ip"))])
async def register(
    data: UserRegister, 
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    email_norm = data.email.strip().lower()
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == email_norm))
    existing_user = result.scalars().first()
    if existing_user:
        await log_security_event(
            db,
            action="REGISTRATION_FAILED_DUPLICATE",
            ip_address=request.client.host if request.client else None
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address already registered"
        )
    
    # Hash password and create citizen user (enforced Citizen role for public registration)
    new_user = User(
        email=email_norm,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        role=UserRole.CITIZEN,
        is_active=True
    )
    db.add(new_user)
    await db.flush() # Populate ID
    
    await log_security_event(
        db,
        action="USER_CREATED",
        actor_id=new_user.id,
        actor_role="CITIZEN",
        resource_type="user",
        resource_id=new_user.id,
        ip_address=request.client.host if request.client else None
    )
    await db.commit()
    
    return _serialize_user(new_user)

@router.post("/signup", response_model=UserSignupResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(5, 60, "ip"))])
async def signup(
    data: UserRegister, 
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    email_norm = data.email.strip().lower()
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == email_norm))
    existing_user = result.scalars().first()
    if existing_user:
        await log_security_event(
            db,
            action="REGISTRATION_FAILED_DUPLICATE",
            ip_address=request.client.host if request.client else None
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address already registered"
        )
    
    # Hash password and create citizen user (enforced Citizen role for public registration)
    new_user = User(
        email=email_norm,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        role=UserRole.CITIZEN,
        is_active=True
    )
    db.add(new_user)
    await db.flush() # Populate ID
    
    await log_security_event(
        db,
        action="USER_CREATED",
        actor_id=new_user.id,
        actor_role="CITIZEN",
        resource_type="user",
        resource_id=new_user.id,
        ip_address=request.client.host if request.client else None
    )
    await db.commit()
    
    return {
        "message": "Account created successfully",
        "user": _serialize_user(new_user)
    }

@router.post("/login", response_model=Token, dependencies=[Depends(RateLimiter(5, 60, "ip"))])
async def login(
    response: Response,
    request: Request,
    data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    generic_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    email_norm = data.email.strip().lower()

    # Fetch user
    result = await db.execute(
        select(User).where(User.email == email_norm).options(selectinload(User.department))
    )
    user = result.scalars().first()
    
    if not user or not user.is_active:
        # Generic login fail log
        await log_security_event(
            db,
            action="LOGIN_FAILED",
            ip_address=request.client.host if request.client else None
        )
        raise generic_error

    # Verify password
    if not verify_password(data.password, user.password_hash):
        await log_security_event(
            db,
            action="LOGIN_FAILED",
            actor_id=user.id,
            actor_role=user.role.value,
            ip_address=request.client.host if request.client else None
        )
        raise generic_error

    # Successful login: Generate tokens
    jti = str(uuid.uuid4())
    access_token = create_access_token(subject=user.id, role=user.role.value, jti=jti)
    refresh_token = create_refresh_token(subject=user.id, role=user.role.value, jti=jti)

    # Create server-side session
    token_session = RefreshToken(
        user_id=user.id,
        token_jti=jti,
        token_hash=_hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    db.add(token_session)
    
    await log_security_event(
        db,
        action="LOGIN_SUCCESS",
        actor_id=user.id,
        actor_role=user.role.value,
        ip_address=request.client.host if request.client else None
    )
    await db.commit()

    # Set refresh cookie and return access details
    _set_refresh_cookie(response, refresh_token)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": _serialize_user(user)
    }

@router.post("/refresh", response_model=Token, dependencies=[Depends(RateLimiter(30, 60, "ip"))])
async def refresh_tokens(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    data: Optional[RefreshTokenIn] = None,
):
    # Accept the refresh token from the JSON body (primary) or the HTTP-only cookie (fallback).
    refresh_token = (data.refresh_token if data and data.refresh_token else None) or request.cookies.get("sara_refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token"
        )
        
    try:
        payload = decode_token(refresh_token)
        user_id_str = payload.get("sub")
        token_type = payload.get("type")
        jti = payload.get("jti")
        
        if token_type != "refresh" or not user_id_str or not jti:
            raise HTTPException(status_code=401, detail="Invalid refresh token payload")
            
        user_id = uuid.UUID(user_id_str)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # Fetch corresponding session and user
    res_session = await db.execute(select(RefreshToken).where(RefreshToken.token_jti == jti))
    session = res_session.scalars().first()
    
    if not session or session.revoked_at or session.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired or revoked")
        
    if session.token_hash != _hash_token(refresh_token):
        raise HTTPException(status_code=401, detail="Session verification failed")

    res_user = await db.execute(
        select(User).where(User.id == user_id).options(selectinload(User.department))
    )
    user = res_user.scalars().first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")

    # Session is valid: Rotate refresh session and generate new tokens
    new_jti = str(uuid.uuid4())
    new_access_token = create_access_token(subject=user.id, role=user.role.value, jti=new_jti)
    new_refresh_token = create_refresh_token(subject=user.id, role=user.role.value, jti=new_jti)

    # Update previous session to revoked
    session.revoked_at = datetime.now(timezone.utc)
    
    # Store new session
    new_session = RefreshToken(
        user_id=user.id,
        token_jti=new_jti,
        token_hash=_hash_token(new_refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    db.add(new_session)
    
    await log_security_event(
        db,
        action="TOKEN_REFRESH",
        actor_id=user.id,
        actor_role=user.role.value,
        ip_address=request.client.host if request.client else None
    )
    await db.commit()

    _set_refresh_cookie(response, new_refresh_token)
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": _serialize_user(user)
    }

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    data: Optional[RefreshTokenIn] = None,
):
    refresh_token = (data.refresh_token if data and data.refresh_token else None) or request.cookies.get("sara_refresh_token")
    if refresh_token:
        try:
            payload = decode_token(refresh_token)
            jti = payload.get("jti")
            if jti:
                # Revoke session in database
                res_session = await db.execute(select(RefreshToken).where(RefreshToken.token_jti == jti))
                session = res_session.scalars().first()
                if session and not session.revoked_at:
                    session.revoked_at = datetime.now(timezone.utc)
                    await log_security_event(
                        db,
                        action="LOGOUT",
                        actor_id=session.user_id,
                        ip_address=request.client.host if request.client else None
                    )
                    await db.commit()
        except Exception:
            # Ignore token decoding exceptions on logout
            pass
            
    _clear_refresh_cookie(response)
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserProfile)
async def get_me(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.id == current_user.id).options(selectinload(User.department))
    )
    user = result.scalars().first()
    return _serialize_user(user)
