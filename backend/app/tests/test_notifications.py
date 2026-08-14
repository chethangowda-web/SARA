import pytest
import uuid
from fastapi import status
from app.core.config import settings
from app.models.governance import Notification
from sqlalchemy.future import select

@pytest.mark.asyncio
async def test_notifications_flow(client_citizen, auth_headers_citizen, db_session):
    # Retrieve notifications (should be empty initially)
    resp = await client_citizen.get(f"{settings.API_V1_STR}/notifications", headers=auth_headers_citizen)
    assert resp.status_code == status.HTTP_200_OK

    # We manually create a notification for test
    # Get user id from token
    user_resp = await client_citizen.get(f"{settings.API_V1_STR}/auth/me", headers=auth_headers_citizen)
    user_id = user_resp.json()["id"]

    notif = Notification(
        user_id=uuid.UUID(user_id),
        title="Test Notification",
        message="This is a test notification",
        type="TEST",
        is_read=False
    )
    db_session.add(notif)
    await db_session.commit()

    # List again
    resp_list = await client_citizen.get(f"{settings.API_V1_STR}/notifications", headers=auth_headers_citizen)
    assert len(resp_list.json()) >= 1
    notif_id = resp_list.json()[0]["id"]

    # Mark as read
    resp_patch = await client_citizen.patch(f"{settings.API_V1_STR}/notifications/{notif_id}/read", headers=auth_headers_citizen)
    assert resp_patch.status_code == status.HTTP_200_OK
    assert resp_patch.json()["is_read"] == True

    # Mark all read
    resp_post = await client_citizen.post(f"{settings.API_V1_STR}/notifications/read-all", headers=auth_headers_citizen)
    assert resp_post.status_code == status.HTTP_200_OK
