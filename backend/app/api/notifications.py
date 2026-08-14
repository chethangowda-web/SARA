import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.governance import Notification
from app.schemas.governance import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("", response_model=List[NotificationResponse])
async def list_my_notifications(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if limit < 1:
        limit = 20
    if limit > 100:
        limit = 100
    if offset < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Offset cannot be negative")

    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()

@router.patch("/{id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Notification)
        .where(Notification.id == id, Notification.user_id == user.id)
    )
    notification = result.scalars().first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    return notification

@router.post("/read-all")
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == user.id)
        .values(is_read=True)
    )
    await db.commit()
    return {"status": "success", "detail": "All notifications marked as read"}
