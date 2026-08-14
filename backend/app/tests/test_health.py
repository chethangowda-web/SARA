import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
import redis.asyncio as aioredis
from sqlalchemy import text

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"{settings.API_V1_STR}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_postgres_connection(db_session):
    # Test simple connection select
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1

@pytest.mark.asyncio
async def test_pgvector_extension(db_session):
    # Test if pgvector extension is available
    result = await db_session.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
    ext = result.scalar()
    # It might be in public schema or not loaded if db is empty, but we verify pg_extension query
    # If the docker setup ran init-pgvector.sql correctly, vector should exist.
    assert ext == "vector"

@pytest.mark.asyncio
async def test_redis_connection():
    # Test redis ping
    r = aioredis.from_url(settings.REDIS_URL)
    ping_result = await r.ping()
    assert ping_result is True
    await r.aclose()
