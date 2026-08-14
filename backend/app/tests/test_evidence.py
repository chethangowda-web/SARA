import pytest
import uuid
import os
from fastapi import status
from app.models.evidence import Evidence
from app.core.config import settings
from sqlalchemy.future import select

@pytest.mark.asyncio
async def test_evidence_upload_valid(client_citizen, auth_headers_citizen, db_session):
    # Submit grievance
    payload = {
        "title": "Evidence Test Grievance",
        "description": "Needs some evidence.",
        "location": "Test Loc"
    }
    resp = await client_citizen.post(f"{settings.API_V1_STR}/grievances", json=payload, headers=auth_headers_citizen)
    g_id = resp.json()["id"]

    # Upload evidence
    files = {'file': ('test.txt', b'hello evidence', 'text/plain')}
    data = {'description': 'Text evidence'}
    
    resp_ev = await client_citizen.post(f"{settings.API_V1_STR}/grievances/{g_id}/evidence", files=files, data=data, headers=auth_headers_citizen)
    assert resp_ev.status_code == status.HTTP_201_CREATED
    data_ev = resp_ev.json()
    assert data_ev["file_name"] == "test.txt"
    assert data_ev["file_type"] == "text/plain"
    assert data_ev["file_size"] == 14
    assert data_ev["description"] == "Text evidence"
    assert "storage_path" not in data_ev

    # List evidence
    resp_list = await client_citizen.get(f"{settings.API_V1_STR}/grievances/{g_id}/evidence", headers=auth_headers_citizen)
    assert resp_list.status_code == status.HTTP_200_OK
    assert len(resp_list.json()) == 1
    assert resp_list.json()[0]["id"] == data_ev["id"]

@pytest.mark.asyncio
async def test_evidence_upload_invalid_mime(client_citizen, auth_headers_citizen, db_session):
    # Submit grievance
    payload = {
        "title": "Evidence Test Grievance Invalid",
        "description": "Needs some evidence.",
        "location": "Test Loc"
    }
    resp = await client_citizen.post(f"{settings.API_V1_STR}/grievances", json=payload, headers=auth_headers_citizen)
    g_id = resp.json()["id"]

    # Upload invalid evidence
    files = {'file': ('test.exe', b'bad', 'application/x-msdownload')}
    
    resp_ev = await client_citizen.post(f"{settings.API_V1_STR}/grievances/{g_id}/evidence", files=files, headers=auth_headers_citizen)
    assert resp_ev.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_evidence_isolation(client_citizen, client_officer, auth_headers_citizen, auth_headers_officer, db_session):
    payload = {
        "title": "Isolation Grievance",
        "description": "Needs some evidence.",
        "location": "Test Loc"
    }
    resp = await client_citizen.post(f"{settings.API_V1_STR}/grievances", json=payload, headers=auth_headers_citizen)
    g_id = resp.json()["id"]

    # Officer trying to get evidence without assignment -> 403
    resp_list = await client_officer.get(f"{settings.API_V1_STR}/grievances/{g_id}/evidence", headers=auth_headers_officer)
    assert resp_list.status_code == status.HTTP_403_FORBIDDEN
