import uuid
import hashlib
import os
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

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
from app.schemas.auth import (
    UserRegister, UserLogin, UserProfile, Token,
    GoogleLoginRequest, EmailVerificationRequest,
    ForgotPasswordRequest, ResetPasswordRequest
)
from app.services.audit_service import log_security_event
from app.core.rate_limiter import RateLimiter

router = APIRouter(prefix="/auth", tags=["auth"])

def _hash_token(token: str) -> str:
    """Helper to sha256 hash refresh tokens for database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

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
    email = data.email.lower().strip()
    
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == email))
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
    
    # Generate verification token
    verification_token = str(uuid.uuid4())[:8].upper() # 8-character code
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    
    # Hash password and create citizen user (enforced Citizen role for public registration)
    new_user = User(
        email=email,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        phone=data.phone,
        date_of_birth=data.date_of_birth,
        role=UserRole.CITIZEN,
        is_active=True,
        email_verified=False,
        verification_token=verification_token,
        verification_token_expires_at=expires_at,
        auth_provider="credentials"
    )
    db.add(new_user)
    await db.flush() # Populate ID
    
    # Log verification details to stdout/console for testing & integration
    print(f"[Verification Token] Email: {new_user.email}, Token: {verification_token}")
    
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
    
    return new_user

@router.post("/verify-email")
async def verify_email(
    data: EmailVerificationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    email = data.email.lower().strip()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or token")
    
    if user.verification_token != data.token:
        raise HTTPException(status_code=400, detail="Invalid email or token")
        
    if user.verification_token_expires_at and user.verification_token_expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Verification token has expired")
        
    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires_at = None
    
    await log_security_event(
        db,
        action="EMAIL_VERIFIED",
        actor_id=user.id,
        actor_role=user.role.value,
        resource_type="user",
        resource_id=user.id,
        ip_address=request.client.host if request.client else None
    )
    await db.commit()
    return {"status": "success", "detail": "Email verified successfully"}

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

    email = data.email.lower().strip()

    # Fetch user
    result = await db.execute(select(User).where(User.email == email))
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

    # Require verified email
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address not verified. Please verify your email first."
        )

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
    user.last_login_at = datetime.now(timezone.utc)
    
    await log_security_event(
        db,
        action="LOGIN_SUCCESS",
        actor_id=user.id,
        actor_role=user.role.value,
        ip_address=request.client.host if request.client else None
    )
    await db.commit()
    await db.refresh(user)

    # Set refresh cookie and return access details
    _set_refresh_cookie(response, refresh_token)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/google", response_model=Token, dependencies=[Depends(RateLimiter(5, 60, "ip"))])
async def google_login(
    response: Response,
    request: Request,
    data: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    import httpx
    # 1. Verify Google token with Google's API (or mock in test)
    id_token = data.id_token
    claims = None
    
    # Check if we are running unit tests and want to mock it
    if settings.ENVIRONMENT == "test" and id_token.startswith("mock_token_"):
        parts = id_token.split("_")
        role_part = parts[2].upper()
        email_part = "_".join(parts[3:])
        claims = {
            "email": email_part,
            "email_verified": "true",
            "sub": f"google_{email_part}",
            "name": f"Mock {role_part.capitalize()}",
            "aud": os.getenv("GOOGLE_CLIENT_ID", "mock_client_id")
        }
    else:
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}",
                    timeout=5.0
                )
                if res.status_code == 200:
                    claims = res.json()
                else:
                    raise HTTPException(status_code=401, detail="Invalid Google ID token")
        except Exception:
            raise HTTPException(status_code=401, detail="Failed to verify Google ID token")
            
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid Google token claims")
        
    email = claims.get("email", "").lower().strip()
    sub = claims.get("sub")
    email_verified = claims.get("email_verified") == "true" or claims.get("email_verified") is True
    
    if not email or not sub or not email_verified:
        raise HTTPException(status_code=400, detail="Google account email is not verified or available")
        
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    if google_client_id and claims.get("aud") != google_client_id:
        if settings.ENVIRONMENT != "test":
            raise HTTPException(status_code=401, detail="Google token audience mismatch")

    # 2. Match StaffAuthorization table
    from app.models.staff_authorization import StaffAuthorization
    res_auth = await db.execute(select(StaffAuthorization).where(StaffAuthorization.email == email, StaffAuthorization.is_active == True))
    auth_rec = res_auth.scalars().first()
    
    target_role = UserRole.CITIZEN
    target_dept_id = None
    
    if auth_rec:
        target_role = auth_rec.role
        target_dept_id = auth_rec.department_id

    # 3. Look up existing User
    res_user = await db.execute(select(User).where(User.email == email))
    user = res_user.scalars().first()
    
    if user:
        if not user.is_active:
            raise HTTPException(status_code=401, detail="User account is deactivated")
            
        user.auth_provider = "google"
        user.google_subject = sub
        user.email_verified = True
        
        # If staff record exists, enforce its role and department
        if auth_rec:
            user.role = target_role
            user.department_id = target_dept_id
        else:
            if user.role != UserRole.CITIZEN:
                raise HTTPException(status_code=403, detail="Government staff access denied: not authorized")
    else:
        user = User(
            email=email,
            full_name=claims.get("name", email.split("@")[0]),
            role=target_role,
            department_id=target_dept_id,
            is_active=True,
            email_verified=True,
            auth_provider="google",
            google_subject=sub,
            password_hash=""
        )
        db.add(user)
        await db.flush()

    # Generate tokens
    jti = str(uuid.uuid4())
    access_token = create_access_token(subject=user.id, role=user.role.value, jti=jti)
    refresh_token = create_refresh_token(subject=user.id, role=user.role.value, jti=jti)

    # Save session
    token_session = RefreshToken(
        user_id=user.id,
        token_jti=jti,
        token_hash=_hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    db.add(token_session)
    user.last_login_at = datetime.now(timezone.utc)
    
    await log_security_event(
        db,
        action="GOOGLE_LOGIN",
        actor_id=user.id,
        actor_role=user.role.value,
        ip_address=request.client.host if request.client else None
    )
    await db.commit()
    await db.refresh(user)

    _set_refresh_cookie(response, refresh_token)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    email = data.email.lower().strip()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if user:
        token = str(uuid.uuid4())
        user.password_reset_token = token
        user.password_reset_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        await db.commit()
        print(f"[PASSWORD RESET] Email: {email}, Token: {token}")
        
    return {"status": "success", "detail": "If the email is registered, a password reset link has been generated"}

@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    email = data.email.lower().strip()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if not user or user.password_reset_token != data.token:
        raise HTTPException(status_code=400, detail="Invalid email or token")
        
    if user.password_reset_expires_at and user.password_reset_expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Password reset token has expired")
        
    user.password_hash = hash_password(data.new_password)
    user.password_reset_token = None
    user.password_reset_expires_at = None
    
    # Revoke all active sessions (refresh tokens) for security
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id)
        .values(revoked_at=datetime.now(timezone.utc))
    )
    
    await log_security_event(
        db,
        action="PASSWORD_RESET",
        actor_id=user.id,
        actor_role=user.role.value
    )
    await db.commit()
    return {"status": "success", "detail": "Password has been reset successfully"}

@router.post("/refresh", response_model=Token, dependencies=[Depends(RateLimiter(30, 60, "ip"))])
async def refresh_tokens(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    refresh_token = request.cookies.get("sara_refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token cookie"
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

    res_session = await db.execute(select(RefreshToken).where(RefreshToken.token_jti == jti))
    session = res_session.scalars().first()
    
    if not session or session.revoked_at or session.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired or revoked")
        
    if session.token_hash != _hash_token(refresh_token):
        raise HTTPException(status_code=401, detail="Session verification failed")

    res_user = await db.execute(select(User).where(User.id == user_id))
    user = res_user.scalars().first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")

    new_jti = str(uuid.uuid4())
    new_access_token = create_access_token(subject=user.id, role=user.role.value, jti=new_jti)
    new_refresh_token = create_refresh_token(subject=user.id, role=user.role.value, jti=new_jti)

    session.revoked_at = datetime.now(timezone.utc)
    
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
    await db.refresh(user)

    _set_refresh_cookie(response, new_refresh_token)
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    refresh_token = request.cookies.get("sara_refresh_token")
    if refresh_token:
        try:
            payload = decode_token(refresh_token)
            jti = payload.get("jti")
            if jti:
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
            pass
            
    _clear_refresh_cookie(response)
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserProfile)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
