import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select

from app.main import app
from app.core.config import settings
from app.core.security import verify_password
from app.models.user import User, UserRole

@pytest.mark.asyncio
async def test_citizen_signup_success(db_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            f"{settings.API_V1_STR}/auth/signup",
            json={
                "email": "jane_doe@sara.com",
                "password": "securepassword123",
                "full_name": "Jane Doe"
            }
        )
    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "Account created successfully"
    assert "user" in body
    assert body["user"]["role"] == "CITIZEN"
    assert body["user"]["email"] == "jane_doe@sara.com"
    assert "password_hash" not in body["user"]

    # Verify user exists in database and password is hashed
    result = await db_session.execute(select(User).where(User.email == "jane_doe@sara.com"))
    db_user = result.scalars().first()
    assert db_user is not None
    assert db_user.full_name == "Jane Doe"
    assert verify_password("securepassword123", db_user.password_hash)

@pytest.mark.asyncio
async def test_signup_always_creates_citizen(db_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            f"{settings.API_V1_STR}/auth/signup",
            json={
                "email": "fake_admin_signup@sara.com",
                "password": "securepassword123",
                "full_name": "Fake Admin",
                "role": "ADMIN" # attempt role escalation
            }
        )
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["role"] == "CITIZEN"

@pytest.mark.asyncio
async def test_signup_duplicate_email(db_session):
    # First signup
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post(
            f"{settings.API_V1_STR}/auth/signup",
            json={
                "email": "duplicate_signup@sara.com",
                "password": "securepassword123",
                "full_name": "First User"
            }
        )
        
        # Duplicate signup
        response = await ac.post(
            f"{settings.API_V1_STR}/auth/signup",
            json={
                "email": "duplicate_signup@sara.com",
                "password": "anotherpassword123",
                "full_name": "Second User"
            }
        )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email address already registered"

@pytest.mark.asyncio
async def test_signup_email_normalization(db_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            f"{settings.API_V1_STR}/auth/signup",
            json={
                "email": "  NORMALIZED_signup@SARA.com  ",
                "password": "securepassword123",
                "full_name": "Normalized User"
            }
        )
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "normalized_signup@sara.com"

    # Try duplicate signup with same email but lowercase/no spaces
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        dup_res = await ac.post(
            f"{settings.API_V1_STR}/auth/signup",
            json={
                "email": "normalized_signup@sara.com",
                "password": "anotherpassword123",
                "full_name": "Normalized User Duplicate"
            }
        )
    assert dup_res.status_code == 400
