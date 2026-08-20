import pytest
import pytest_asyncio
import uuid
from datetime import date, datetime, timezone, timedelta
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.user import User, UserRole
from app.models.staff_authorization import StaffAuthorization
from app.models.audit import AuditLog
from app.core.security import hash_password, verify_password, create_access_token

@pytest.mark.asyncio
async def test_citizen_registration_validation(client_citizen, db_session):
    # 1. Invalid email
    response = await client_citizen.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "Password123!",
            "full_name": "Test Citizen",
            "phone": "9876543210",
            "date_of_birth": "2000-01-01"
        }
    )
    assert response.status_code == 422 # Pydantic validation error

    # 2. Too young (under 18)
    underage_dob = (date.today() - timedelta(days=17 * 365)).isoformat()
    response = await client_citizen.post(
        "/api/v1/auth/register",
        json={
            "email": "young@citizen.com",
            "password": "Password123!",
            "full_name": "Test Citizen",
            "phone": "9876543210",
            "date_of_birth": underage_dob
        }
    )
    assert response.status_code == 422
    assert "at least 18 years old" in response.json()["detail"][0]["msg"]

    # 3. Weak password (no uppercase, no special, under 12 chars)
    response = await client_citizen.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@citizen.com",
            "password": "password123",
            "full_name": "Test Citizen",
            "phone": "9876543210",
            "date_of_birth": "2000-01-01"
        }
    )
    assert response.status_code == 422
    assert "at least 12 characters" in response.json()["detail"][0]["msg"]

    # 4. Valid Citizen Registration
    valid_dob = (date.today() - timedelta(days=20 * 365)).isoformat()
    response = await client_citizen.post(
        "/api/v1/auth/register",
        json={
            "email": "valid@citizen.com",
            "password": "StrongPassword123!",
            "full_name": "Valid Citizen",
            "phone": "+919876543210",
            "date_of_birth": valid_dob
        }
    )
    assert response.status_code == 201
    user_data = response.json()
    assert user_data["email"] == "valid@citizen.com"
    assert user_data["role"] == "CITIZEN"
    assert user_data["email_verified"] is False

    # Check database record
    res = await db_session.execute(select(User).where(User.email == "valid@citizen.com"))
    user = res.scalars().first()
    assert user is not None
    assert user.verification_token is not None
    assert user.email_verified is False
    assert user.auth_provider == "credentials"


@pytest.mark.asyncio
async def test_citizen_email_verification_and_login(client_citizen, db_session):
    # Register first
    valid_dob = (date.today() - timedelta(days=20 * 365)).isoformat()
    await client_citizen.post(
        "/api/v1/auth/register",
        json={
            "email": "verify@citizen.com",
            "password": "StrongPassword123!",
            "full_name": "Verify Citizen",
            "phone": "+919876543210",
            "date_of_birth": valid_dob
        }
    )
    
    # Retrieve code from DB
    res = await db_session.execute(select(User).where(User.email == "verify@citizen.com"))
    user = res.scalars().first()
    token = user.verification_token
    
    # 1. Attempt login before verification (should fail)
    login_res = await client_citizen.post(
        "/api/v1/auth/login",
        json={"email": "verify@citizen.com", "password": "StrongPassword123!"}
    )
    assert login_res.status_code == 403
    assert "not verified" in login_res.json()["detail"]

    # 2. Verify with wrong token
    verify_res = await client_citizen.post(
        "/api/v1/auth/verify-email",
        json={"email": "verify@citizen.com", "token": "WRONG_TOKEN"}
    )
    assert verify_res.status_code == 400

    # 3. Verify with correct token
    verify_res = await client_citizen.post(
        "/api/v1/auth/verify-email",
        json={"email": "verify@citizen.com", "token": token}
    )
    assert verify_res.status_code == 200
    
    # 4. Login after verification (should succeed)
    login_res = await client_citizen.post(
        "/api/v1/auth/login",
        json={"email": "verify@citizen.com", "password": "StrongPassword123!"}
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()
    assert login_res.json()["user"]["email_verified"] is True


@pytest.mark.asyncio
async def test_privileged_staff_google_login(client_admin, db_session, test_dept_a):
    # Ensure staff authorizations are seeded
    admin_auth = StaffAuthorization(
        email="iamchethen2813@gmail.com",
        role=UserRole.ADMIN,
        is_active=True
    )
    officer_auth = StaffAuthorization(
        email="priyankah.4767@gmail.com",
        role=UserRole.OFFICER,
        department_id=test_dept_a.id,
        is_active=True
    )
    db_session.add_all([admin_auth, officer_auth])
    await db_session.commit()

    # 1. Admin login with Google (authorized email)
    res = await client_admin.post(
        "/api/v1/auth/google",
        json={"id_token": "mock_token_admin_iamchethen2813@gmail.com"}
    )
    assert res.status_code == 200
    assert res.json()["user"]["role"] == "ADMIN"
    assert res.json()["user"]["auth_provider"] == "google"

    # 2. Officer login with Google (authorized email)
    res = await client_admin.post(
        "/api/v1/auth/google",
        json={"id_token": "mock_token_officer_priyankah.4767@gmail.com"}
    )
    assert res.status_code == 200
    assert res.json()["user"]["role"] == "OFFICER"
    assert res.json()["user"]["department_id"] == str(test_dept_a.id)

    # 3. Unauthorized staff google login (should fallback to citizen or fail if they have a non-citizen role in DB)
    res = await client_admin.post(
        "/api/v1/auth/google",
        json={"id_token": "mock_token_officer_random@gmail.com"}
    )
    assert res.status_code == 200
    assert res.json()["user"]["role"] == "CITIZEN" # Unlisted google account registers as citizen


@pytest.mark.asyncio
async def test_admin_staff_management_and_safeguards(client_admin, db_session, test_dept_a, test_admin):
    # Setup Admin authentication
    token = create_access_token(str(test_admin.id), test_admin.role.value)
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Admin list authorizations (should include seeded ones plus test_admin)
    res = await client_admin.get("/api/v1/admin/users/staff-authorizations", headers=headers)
    assert res.status_code == 200
    
    # 2. Admin authorize new staff member
    res = await client_admin.post(
        "/api/v1/admin/users/staff-authorizations",
        headers=headers,
        json={
            "email": "new_officer@sara.gov",
            "role": "OFFICER",
            "department_id": str(test_dept_a.id)
        }
    )
    assert res.status_code == 201
    auth_id = res.json()["id"]

    # 3. Safeguard test: Try to deactivate/revoke the last administrator
    # Currently test_admin is the only admin in users, let's create admin authorization to test
    admin_auth = StaffAuthorization(
        email=test_admin.email,
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin_auth)
    await db_session.commit()

    # Try to deactivate the admin authorization
    res = await client_admin.patch(
        f"/api/v1/admin/users/staff-authorizations/{admin_auth.id}",
        headers=headers,
        json={"is_active": False}
    )
    assert res.status_code == 400
    assert "last active administrator" in res.json()["detail"]

    # Try to deactivate the admin user account status
    res = await client_admin.patch(
        f"/api/v1/admin/users/{test_admin.id}/status",
        headers=headers,
        json={"is_active": False}
    )
    assert res.status_code == 400
    assert "last active administrator" in res.json()["detail"]


@pytest.mark.asyncio
async def test_audit_logging_and_security_events(client_citizen, db_session):
    # Register to trigger audit event
    valid_dob = (date.today() - timedelta(days=20 * 365)).isoformat()
    await client_citizen.post(
        "/api/v1/auth/register",
        json={
            "email": "audit@citizen.com",
            "password": "StrongPassword123!",
            "full_name": "Audit Citizen",
            "phone": "+919876543210",
            "date_of_birth": valid_dob
        }
    )
    
    # Check audit log is created
    res = await db_session.execute(select(AuditLog).where(AuditLog.action == "USER_CREATED"))
    log = res.scalars().first()
    assert log is not None
    assert log.actor_role == "CITIZEN"
