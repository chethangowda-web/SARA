import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(settings.DATABASE_URL, future=True)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(
        bind=db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

@pytest_asyncio.fixture(autouse=True)
async def override_get_db(db_session):
    from app.main import app
    from app.core.database import get_db
    
    async def _get_db_override():
        yield db_session
        
    app.dependency_overrides[get_db] = _get_db_override
    yield
    app.dependency_overrides.clear()

@pytest_asyncio.fixture(autouse=True)
async def clean_db(db_session):
    from sqlalchemy import text
    await db_session.rollback()
    await db_session.execute(text("TRUNCATE TABLE refresh_tokens, audit_logs, users, departments, system_settings, sla_policies, accountability_dossiers, notifications, grievance_comments, evidence, analytics_snapshots, operational_anomalies CASCADE;"))
    await db_session.commit()
    yield
    
from app.models.user import User, UserRole
from app.core.security import hash_password, create_access_token
from httpx import AsyncClient, ASGITransport
import uuid

@pytest_asyncio.fixture
async def test_dept_a(db_session):
    from app.models.department import Department
    dept = Department(name="Dept A", code="DEPT_A", is_active=True)
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)
    return dept

@pytest_asyncio.fixture
async def test_citizen(db_session):
    user = User(
        email=f"citizen_{uuid.uuid4()}@sara.com",
        full_name="Citizen",
        password_hash=hash_password("password"),
        role=UserRole.CITIZEN,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def test_officer(db_session):
    user = User(
        email=f"officer_{uuid.uuid4()}@sara.com",
        full_name="Officer",
        password_hash=hash_password("password"),
        role=UserRole.OFFICER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def test_supervisor(db_session, test_dept_a):
    user = User(
        email=f"supervisor_{uuid.uuid4()}@sara.com",
        full_name="Supervisor",
        password_hash=hash_password("password"),
        role=UserRole.SUPERVISOR,
        department_id=test_dept_a.id,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def test_admin(db_session):
    user = User(
        email=f"admin_{uuid.uuid4()}@sara.com",
        full_name="Admin",
        password_hash=hash_password("password"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def client_citizen():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def client_officer():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def client_supervisor():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def client_admin():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
def auth_headers_citizen(test_citizen):
    token = create_access_token(str(test_citizen.id), test_citizen.role.value)
    return {"Authorization": f"Bearer {token}"}

@pytest_asyncio.fixture
def auth_headers_officer(test_officer):
    token = create_access_token(str(test_officer.id), test_officer.role.value)
    return {"Authorization": f"Bearer {token}"}

@pytest_asyncio.fixture
def auth_headers_supervisor(test_supervisor):
    token = create_access_token(str(test_supervisor.id), test_supervisor.role.value)
    return {"Authorization": f"Bearer {token}"}

@pytest_asyncio.fixture
def auth_headers_admin(test_admin):
    token = create_access_token(str(test_admin.id), test_admin.role.value)
    return {"Authorization": f"Bearer {token}"}

@pytest_asyncio.fixture(autouse=True)
async def clear_redis():
    import redis.asyncio as aioredis
    from app.core.config import settings
    r = aioredis.from_url(settings.REDIS_URL)
    try:
        keys = await r.keys("rate_limit:*")
        if keys:
            await r.delete(*keys)
    except Exception:
        pass
    yield
    try:
        keys = await r.keys("rate_limit:*")
        if keys:
            await r.delete(*keys)
    except Exception:
        pass
    await r.aclose()
