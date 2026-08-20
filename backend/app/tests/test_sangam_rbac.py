import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import UserRole

@pytest.mark.asyncio
async def test_citizen_cannot_access_sangam_intelligence(client_citizen, auth_headers_citizen):
    response = await client_citizen.get(
        f"{settings.API_V1_STR}/sangam/overview",
        headers=auth_headers_citizen
    )
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]

@pytest.mark.asyncio
async def test_admin_can_access_sangam_intelligence(db_session, test_admin):
    token = create_access_token(test_admin.id, test_admin.role.value)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(
            f"{settings.API_V1_STR}/sangam/overview",
            headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 200
    assert "total_active_needs" in response.json()
    assert "unserved_gaps_count" in response.json()
