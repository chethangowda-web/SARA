import pytest
from fastapi import status
from app.core.config import settings

@pytest.mark.asyncio
async def test_citizen_dashboard(client_citizen, auth_headers_citizen, db_session):
    resp = await client_citizen.get(f"{settings.API_V1_STR}/citizen/dashboard", headers=auth_headers_citizen)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "total_grievances" in data
    assert "recent_grievances" in data

@pytest.mark.asyncio
async def test_officer_dashboard(client_officer, auth_headers_officer, db_session):
    resp = await client_officer.get(f"{settings.API_V1_STR}/officer/dashboard", headers=auth_headers_officer)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "assigned_grievances" in data

@pytest.mark.asyncio
async def test_supervisor_dashboard(client_supervisor, auth_headers_supervisor, db_session):
    resp = await client_supervisor.get(f"{settings.API_V1_STR}/supervisor/dashboard", headers=auth_headers_supervisor)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "total_active_grievances" in data
    assert "officer_workload" in data

@pytest.mark.asyncio
async def test_admin_dashboard(client_admin, auth_headers_admin, db_session):
    resp = await client_admin.get(f"{settings.API_V1_STR}/admin/dashboard", headers=auth_headers_admin)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "total_grievances" in data
    assert "risk_distribution" in data

@pytest.mark.asyncio
async def test_dashboard_rbac(client_citizen, auth_headers_citizen, db_session):
    # Citizen trying to access admin dashboard
    resp = await client_citizen.get(f"{settings.API_V1_STR}/admin/dashboard", headers=auth_headers_citizen)
    assert resp.status_code == status.HTTP_403_FORBIDDEN
