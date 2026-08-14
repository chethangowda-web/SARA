import pytest
import uuid
from fastapi import status
from app.core.config import settings

@pytest.mark.asyncio
async def test_comments_flow(client_citizen, auth_headers_citizen, db_session):
    # Submit grievance
    payload = {
        "title": "Comment Test Grievance",
        "description": "Needs some comments.",
        "location": "Test Loc"
    }
    resp = await client_citizen.post(f"{settings.API_V1_STR}/grievances", json=payload, headers=auth_headers_citizen)
    g_id = resp.json()["id"]

    # Add comment
    c_payload = {"comment": "This is a test comment."}
    resp_c = await client_citizen.post(f"{settings.API_V1_STR}/grievances/{g_id}/comments", json=c_payload, headers=auth_headers_citizen)
    assert resp_c.status_code == status.HTTP_201_CREATED
    assert resp_c.json()["comment"] == "This is a test comment."

    # List comments
    resp_list = await client_citizen.get(f"{settings.API_V1_STR}/grievances/{g_id}/comments", headers=auth_headers_citizen)
    assert resp_list.status_code == status.HTTP_200_OK
    assert len(resp_list.json()) == 1
    assert resp_list.json()[0]["comment"] == "This is a test comment."

@pytest.mark.asyncio
async def test_comments_isolation(client_citizen, client_officer, auth_headers_citizen, auth_headers_officer, db_session):
    payload = {
        "title": "Comment Isolation Grievance",
        "description": "Needs some comments.",
        "location": "Test Loc"
    }
    resp = await client_citizen.post(f"{settings.API_V1_STR}/grievances", json=payload, headers=auth_headers_citizen)
    g_id = resp.json()["id"]

    # Officer without assignment -> 403
    c_payload = {"comment": "Unauthorized comment"}
    resp_c = await client_officer.post(f"{settings.API_V1_STR}/grievances/{g_id}/comments", json=c_payload, headers=auth_headers_officer)
    assert resp_c.status_code == status.HTTP_403_FORBIDDEN
