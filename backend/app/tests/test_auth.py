import pytest
import pytest_asyncio
import jwt
import uuid
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.future import select

from app.main import app
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token, decode_token
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.audit import AuditLog
from app.models.session import RefreshToken

@pytest_asyncio.fixture
async def sample_department(db_session):
    # Setup test department
    dept = Department(name="Test Dept", code="TEST_DEPT", is_active=True)
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)
    return dept

@pytest_asyncio.fixture
async def sample_admin(db_session):
    admin = User(
        email="test_admin@sara.com",
        full_name="Test Admin",
        password_hash=hash_password("admin_pass"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin

@pytest.mark.asyncio
async def test_citizen_registration_succeeds(db_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            f"{settings.API_V1_STR}/auth/register",
            json={
                "email": "new_citizen@sara.com",
                "password": "securepassword123",
                "full_name": "New Citizen"
            }
        )
    assert response.status_code == 201
    assert "password_hash" not in response.json()
    assert response.json()["role"] == "CITIZEN"

@pytest.mark.asyncio
async def test_public_registration_cannot_create_privileged_roles(db_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            f"{settings.API_V1_STR}/auth/register",
            json={
                "email": "fake_admin@sara.com",
                "password": "securepassword123",
                "full_name": "Fake Admin",
                "role": "ADMIN" # try to hijack role
            }
        )
    # The Pydantic UserRegister schema does not accept role, so it gets ignored or fails.
    # Our endpoint creates CITIZEN role explicitly.
    assert response.status_code == 201
    assert response.json()["role"] == "CITIZEN"

@pytest.mark.asyncio
async def test_duplicate_email_returns_409(db_session):
    # Register first
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post(
            f"{settings.API_V1_STR}/auth/register",
            json={
                "email": "dup@sara.com",
                "password": "securepassword123",
                "full_name": "Dup User"
            }
        )
        # Register second
        response = await ac.post(
            f"{settings.API_V1_STR}/auth/register",
            json={
                "email": "dup@sara.com",
                "password": "anotherpassword",
                "full_name": "Dup User Two"
            }
        )
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_password_is_hashed_and_never_returned(db_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            f"{settings.API_V1_STR}/auth/register",
            json={
                "email": "hash_check@sara.com",
                "password": "mypassword123",
                "full_name": "Hash Check"
            }
        )
    assert response.status_code == 201
    profile = response.json()
    assert "password" not in profile
    assert "password_hash" not in profile
    
    # Query database and verify hash is set and bcrypt formatted
    result = await db_session.execute(select(User).where(User.email == "hash_check@sara.com"))
    db_user = result.scalars().first()
    assert db_user.password_hash != "mypassword123"
    assert verify_password("mypassword123", db_user.password_hash)

@pytest.mark.asyncio
async def test_correct_login_returns_tokens(db_session):
    # Register user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post(
            f"{settings.API_V1_STR}/auth/register",
            json={
                "email": "login_test@sara.com",
                "password": "loginpassword",
                "full_name": "Login User"
            }
        )
        # Login
        response = await ac.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "login_test@sara.com", "password": "loginpassword"}
        )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "sara_refresh_token" in response.cookies
    assert response.json()["user"]["email"] == "login_test@sara.com"

@pytest.mark.asyncio
async def test_incorrect_credentials_return_401(db_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "nonexistent@sara.com", "password": "loginpassword"}
        )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

@pytest.mark.asyncio
async def test_inactive_user_cannot_login(db_session):
    # Create inactive user
    inactive_user = User(
        email="inactive@sara.com",
        full_name="Inactive User",
        password_hash=hash_password("inactivepass"),
        role=UserRole.CITIZEN,
        is_active=False
    )
    db_session.add(inactive_user)
    await db_session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "inactive@sara.com", "password": "inactivepass"}
        )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_auth_me_works_with_valid_access_token(db_session):
    user = User(
        email="me_test@sara.com",
        full_name="Me Test",
        password_hash=hash_password("mepassword"),
        role=UserRole.CITIZEN,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(subject=user.id, role=user.role.value)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(
            f"{settings.API_V1_STR}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 200
    assert response.json()["email"] == "me_test@sara.com"

@pytest.mark.asyncio
async def test_auth_me_rejects_invalid_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(
            f"{settings.API_V1_STR}/auth/me",
            headers={"Authorization": "Bearer invalid_token_value"}
        )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_auth_me_rejects_expired_token(db_session):
    user = User(
        email="expired_test@sara.com",
        full_name="Expired Test",
        password_hash=hash_password("pass"),
        role=UserRole.CITIZEN,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    
    # Create expired token
    now = datetime.now(timezone.utc)
    expire = now - timedelta(minutes=5)
    payload = {
        "sub": str(user.id),
        "role": user.role.value,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid.uuid4())
    }
    expired_token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(
            f"{settings.API_V1_STR}/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_access_token_cannot_be_used_as_refresh_token(db_session):
    user = User(
        email="access_as_refresh@sara.com",
        full_name="User",
        password_hash=hash_password("pass"),
        role=UserRole.CITIZEN,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()

    access_token = create_access_token(subject=user.id, role=user.role.value)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        ac.cookies.set("sara_refresh_token", access_token)
        response = await ac.post(f"{settings.API_V1_STR}/auth/refresh")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_refresh_token_rotation_works(db_session):
    # Register and Login
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post(
            f"{settings.API_V1_STR}/auth/register",
            json={
                "email": "rot@sara.com",
                "password": "rotpassword",
                "full_name": "Rotation"
            }
        )
        login_res = await ac.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "rot@sara.com", "password": "rotpassword"}
        )
        cookie = ac.cookies.get("sara_refresh_token")
        
        # Call refresh
        refresh_res = await ac.post(f"{settings.API_V1_STR}/auth/refresh")
        assert refresh_res.status_code == 200
        new_cookie = ac.cookies.get("sara_refresh_token")
        
        # Cookies must be rotated (different values)
        assert cookie != new_cookie

@pytest.mark.asyncio
async def test_revoked_refresh_token_cannot_be_used(db_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post(
            f"{settings.API_V1_STR}/auth/register",
            json={
                "email": "rev@sara.com",
                "password": "revpassword",
                "full_name": "Revocation"
            }
        )
        await ac.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "rev@sara.com", "password": "revpassword"}
        )
        cookie = ac.cookies.get("sara_refresh_token")
        
        # Logout to revoke it
        await ac.post(f"{settings.API_V1_STR}/auth/logout")
        
        # Try refresh again
        ac.cookies.set("sara_refresh_token", cookie)
        refresh_res = await ac.post(f"{settings.API_V1_STR}/auth/refresh")
    assert refresh_res.status_code == 401

@pytest.mark.asyncio
async def test_role_checker_blocks_unauthorized_roles(db_session, sample_department):
    # Create Citizen
    citizen = User(
        email="test_cit@sara.com",
        full_name="Citizen",
        password_hash=hash_password("pass"),
        role=UserRole.CITIZEN,
        is_active=True
    )
    db_session.add(citizen)
    await db_session.commit()
    await db_session.refresh(citizen)

    token = create_access_token(subject=citizen.id, role=citizen.role.value)
    
    # Try calling admin route with Citizen token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            f"{settings.API_V1_STR}/admin/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "email": "new_officer@sara.com",
                "password": "password123",
                "full_name": "New Officer",
                "role": "OFFICER",
                "department_id": str(sample_department.id)
            }
        )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_admin_routes_allow_admin(db_session, sample_admin, sample_department):
    token = create_access_token(subject=sample_admin.id, role=sample_admin.role.value)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            f"{settings.API_V1_STR}/admin/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "email": "admin_onboarded_officer@sara.com",
                "password": "password123",
                "full_name": "Onboarded Officer",
                "role": "OFFICER",
                "department_id": str(sample_department.id)
            }
        )
    assert response.status_code == 201
    assert response.json()["role"] == "OFFICER"

@pytest.mark.asyncio
async def test_audit_logs_are_immutable(db_session):
    # Write a log entry
    log = AuditLog(action="IMMUTABLE_TEST")
    db_session.add(log)
    await db_session.commit()
    await db_session.refresh(log)
    
    # Attempt to update
    try:
        await db_session.execute(
            text("UPDATE audit_logs SET action = 'MUTATED' WHERE id = :id"),
            {"id": log.id}
        )
        await db_session.commit()
    except Exception:
        # DB rule DO INSTEAD NOTHING might just ignore it, or SQLAlchemy might succeed but no row change.
        pass

    # Verify action remains "IMMUTABLE_TEST"
    await db_session.refresh(log)
    assert log.action == "IMMUTABLE_TEST"

    # Attempt to delete
    try:
        await db_session.execute(
            text("DELETE FROM audit_logs WHERE id = :id"),
            {"id": log.id}
        )
        await db_session.commit()
    except Exception:
        pass

    # Verify log still exists
    res = await db_session.execute(select(AuditLog).where(AuditLog.id == log.id))
    db_log = res.scalars().first()
    assert db_log is not None

@pytest.mark.asyncio
async def test_department_assignment_rules(db_session, sample_admin):
    token = create_access_token(subject=sample_admin.id, role=sample_admin.role.value)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Officer without department should fail (400)
        response = await ac.post(
            f"{settings.API_V1_STR}/admin/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "email": "nodep_officer@sara.com",
                "password": "password123",
                "full_name": "No Dept Officer",
                "role": "OFFICER"
            }
        )
    assert response.status_code == 400
    assert "Department is required" in response.json()["detail"]

def test_cookie_secure_settings_dev_and_prod(monkeypatch):
    from app.core.config import Settings
    
    # 1. Dev setting
    monkeypatch.setenv("ENVIRONMENT", "development")
    dev_settings = Settings()
    assert dev_settings.COOKIE_SECURE is False
    
    # 2. Prod setting
    monkeypatch.setenv("ENVIRONMENT", "production")
    prod_settings = Settings()
    assert prod_settings.COOKIE_SECURE is True
