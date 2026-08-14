import pytest
from httpx import AsyncClient
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import UserRole
from app.models.analytics import AnalyticsSnapshot, OperationalAnomaly

pytestmark = pytest.mark.asyncio

async def test_analytics_rbac(
    client_admin: AsyncClient,
    auth_headers_citizen: dict,
    auth_headers_officer: dict,
    auth_headers_supervisor: dict,
    auth_headers_admin: dict
):
    # Citizen: 403 on all
    resp = await client_admin.get("/api/v1/analytics/overview", headers=auth_headers_citizen)
    assert resp.status_code == 403
    
    resp = await client_admin.get("/api/v1/analytics/trends", headers=auth_headers_citizen)
    assert resp.status_code == 403

    # Officer: 403 on overview
    resp = await client_admin.get("/api/v1/analytics/overview", headers=auth_headers_officer)
    assert resp.status_code == 403
    
    # Officer: 403 on trends
    resp = await client_admin.get("/api/v1/analytics/trends", headers=auth_headers_officer)
    assert resp.status_code == 403
    
    # Supervisor: 403 on global overview (supervisor uses department overview or global restricts to dept)
    resp = await client_admin.get("/api/v1/analytics/overview", headers=auth_headers_supervisor)
    assert resp.status_code == 403 # Endpoint specifically enforces this
    
    # Admin: 200 on global overview
    resp = await client_admin.get("/api/v1/analytics/overview", headers=auth_headers_admin)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_grievances" in data

async def test_admin_global_metrics(
    client_admin: AsyncClient,
    auth_headers_admin: dict
):
    resp = await client_admin.get("/api/v1/analytics/overview", headers=auth_headers_admin)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_grievances" in data
    assert "average_resolution_hours" in data
    assert "average_assignment_hours" in data
    assert "average_acknowledgement_hours" in data
    assert "sla_compliance_percent" in data

async def test_supervisor_department_isolation(
    client_admin: AsyncClient,
    auth_headers_supervisor: dict,
    auth_headers_admin: dict,
    db_session: AsyncSession
):
    # Supervisor can view trends
    resp = await client_admin.get("/api/v1/analytics/trends", headers=auth_headers_supervisor)
    assert resp.status_code == 200
    
    # Supervisor can view anomalies
    resp = await client_admin.get("/api/v1/analytics/anomalies", headers=auth_headers_supervisor)
    assert resp.status_code == 200
    
    # Supervisor accessing a different department
    # Let's hit /departments/{uuid4} which should throw 403 because it's not their dept
    resp = await client_admin.get(f"/api/v1/analytics/departments/{uuid4()}", headers=auth_headers_supervisor)
    assert resp.status_code == 403

async def test_officer_self_only_access(
    client_admin: AsyncClient,
    auth_headers_officer: dict,
    test_officer
):
    # Valid access for their own metrics
    resp = await client_admin.get(f"/api/v1/analytics/officers/{test_officer.id}", headers=auth_headers_officer)
    assert resp.status_code == 200
    assert resp.json()["officer_id"] == str(test_officer.id)
    
    # Invalid access for someone else's metrics
    resp = await client_admin.get(f"/api/v1/analytics/officers/{uuid4()}", headers=auth_headers_officer)
    assert resp.status_code == 403

async def test_trend_calculations(
    client_admin: AsyncClient,
    auth_headers_admin: dict
):
    resp = await client_admin.get("/api/v1/analytics/trends", headers=auth_headers_admin)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 4
    metrics = [d["metric"] for d in data]
    assert "daily_volume" in metrics
    assert "daily_closures" in metrics
    assert "daily_sla_breaches" in metrics
    assert "daily_average_resolution_hours" in metrics

async def test_ai_insights_deterministic_fallback(
    client_admin: AsyncClient,
    auth_headers_admin: dict
):
    # Since we aren't mocking the API call, it might succeed or fail depending on settings.GEMINI_API_KEY
    resp = await client_admin.get("/api/v1/analytics/insights", headers=auth_headers_admin)
    assert resp.status_code == 200
    data = resp.json()
    assert "insights" in data
    assert isinstance(data["insights"], list)
    assert "provider" in data
