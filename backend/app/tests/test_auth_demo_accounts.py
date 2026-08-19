"""
Authentication tests for the four demo accounts (citizen/officer/supervisor/admin)
and core auth failure + RBAC scenarios.

These mirror the seeded accounts exactly (email + password) so the tests validate
the same path the browser uses.
"""
import pytest
import pytest_asyncio
import jwt
import uuid
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings
from app.core.security import hash_password, create_access_token
from app.models.user import User, UserRole
from app.models.department import Department

DEMO_PASSWORD = "SARA_demo_pass_2026"
DEMO_ACCOUNTS = [
    ("citizen@sara.gov", UserRole.CITIZEN),
    ("officer@sara.gov", UserRole.OFFICER),
    ("supervisor@sara.gov", UserRole.SUPERVISOR),
    ("admin@sara.gov", UserRole.ADMIN),
]


@pytest_asyncio.fixture
async def demo_department(db_session):
    dept = Department(name="Electrical Department", code="ELEC", is_active=True)
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)
    return dept


@pytest_asyncio.fixture
async def demo_users(db_session, demo_department):
    users = []
    for email, role in DEMO_ACCOUNTS:
        u = User(
            email=email,
            full_name=f"Demo {role.value.title()}",
            password_hash=hash_password(DEMO_PASSWORD),
            role=role,
            department_id=demo_department.id if role in (UserRole.OFFICER, UserRole.SUPERVISOR) else None,
            is_active=True,
        )
        db_session.add(u)
        users.append(u)
    await db_session.commit()
    for u in users:
        await db_session.refresh(u)
    return users


@pytest.mark.asyncio
async def test_citizen_login(demo_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "citizen@sara.gov", "password": DEMO_PASSWORD},
        )
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["user"]["role"] == "CITIZEN"
    assert body["user"]["email"] == "citizen@sara.gov"


@pytest.mark.asyncio
async def test_officer_login(demo_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "officer@sara.gov", "password": DEMO_PASSWORD},
        )
    assert res.status_code == 200
    body = res.json()
    assert body["user"]["role"] == "OFFICER"
    assert body["user"]["department_id"] is not None


@pytest.mark.asyncio
async def test_supervisor_login(demo_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "supervisor@sara.gov", "password": DEMO_PASSWORD},
        )
    assert res.status_code == 200
    body = res.json()
    assert body["user"]["role"] == "SUPERVISOR"


@pytest.mark.asyncio
async def test_admin_login(demo_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "admin@sara.gov", "password": DEMO_PASSWORD},
        )
    assert res.status_code == 200
    body = res.json()
    assert body["user"]["role"] == "ADMIN"


@pytest.mark.asyncio
async def test_invalid_password(demo_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "citizen@sara.gov", "password": "definitely_wrong_password"},
        )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_unknown_user():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "does-not-exist@sara.gov", "password": DEMO_PASSWORD},
        )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_inactive_user_cannot_login(db_session):
    inactive = User(
        email="inactive_demo@sara.gov",
        full_name="Inactive",
        password_hash=hash_password(DEMO_PASSWORD),
        role=UserRole.CITIZEN,
        is_active=False,
    )
    db_session.add(inactive)
    await db_session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "inactive_demo@sara.gov", "password": DEMO_PASSWORD},
        )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_requires_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get(f"{settings.API_V1_STR}/citizen/dashboard")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_role_based_access_demo_accounts(demo_users):
    # citizen can reach citizen dashboard, is denied admin dashboard
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login = await ac.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "citizen@sara.gov", "password": DEMO_PASSWORD},
        )
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        ok = await ac.get(f"{settings.API_V1_STR}/citizen/dashboard", headers=headers)
        denied = await ac.get(f"{settings.API_V1_STR}/admin/dashboard", headers=headers)
    assert ok.status_code == 200
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_role_based_access_admin_allowed(demo_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login = await ac.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "admin@sara.gov", "password": DEMO_PASSWORD},
        )
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        ok = await ac.get(f"{settings.API_V1_STR}/admin/dashboard", headers=headers)
        officer_denied = await ac.get(f"{settings.API_V1_STR}/officer/dashboard", headers=headers)
    assert ok.status_code == 200
    assert officer_denied.status_code == 403


@pytest.mark.asyncio
async def test_officer_and_supervisor_role_access(demo_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        for email, path in [
            ("officer@sara.gov", "officer/dashboard"),
            ("supervisor@sara.gov", "supervisor/dashboard"),
        ]:
            login = await ac.post(
                f"{settings.API_V1_STR}/auth/login",
                json={"email": email, "password": DEMO_PASSWORD},
            )
            assert login.status_code == 200
            token = login.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            ok = await ac.get(f"{settings.API_V1_STR}/{path}", headers=headers)
            admin_denied = await ac.get(f"{settings.API_V1_STR}/admin/dashboard", headers=headers)
            assert ok.status_code == 200, f"{email} should reach {path}"
            assert admin_denied.status_code == 403, f"{email} must be denied /admin/dashboard"


@pytest.mark.asyncio
async def test_expired_token_returns_401(db_session, demo_users):
    demo = next(u for u in demo_users if u.email == "citizen@sara.gov")
    now = datetime.now(timezone.utc)
    expire = now - timedelta(minutes=5)
    payload = {
        "sub": str(demo.id),
        "role": demo.role.value,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid.uuid4()),
    }
    expired = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get(
            f"{settings.API_V1_STR}/citizen/dashboard",
            headers={"Authorization": f"Bearer {expired}"},
        )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_refresh_via_body_token(demo_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login = await ac.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "citizen@sara.gov", "password": DEMO_PASSWORD},
        )
        assert login.status_code == 200
        refresh = login.json()["refresh_token"]

        refreshed = await ac.post(
            f"{settings.API_V1_STR}/auth/refresh",
            json={"refresh_token": refresh},
        )
    assert refreshed.status_code == 200
    body = refreshed.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["user"]["email"] == "citizen@sara.gov"


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(demo_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login = await ac.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "admin@sara.gov", "password": DEMO_PASSWORD},
        )
        refresh = login.json()["refresh_token"]

        logout = await ac.post(
            f"{settings.API_V1_STR}/auth/logout",
            json={"refresh_token": refresh},
        )
        assert logout.status_code == 200

        # The revoked refresh token must no longer be usable
        denied = await ac.post(
            f"{settings.API_V1_STR}/auth/refresh",
            json={"refresh_token": refresh},
        )
    assert denied.status_code == 401