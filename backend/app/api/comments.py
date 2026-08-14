import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.grievance import Grievance
from app.models.grievance_comment import GrievanceComment
from app.models.grievance_event import GrievanceEvent
from app.schemas.comment import CommentCreate, CommentResponse
from app.services.audit_service import log_security_event
from app.api.grievances import _verify_access_auth
from app.core.rate_limiter import RateLimiter

router = APIRouter(prefix="/grievances", tags=["comments"])

@router.post("/{id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(30, 60, "user"))])
async def add_grievance_comment(
    id: uuid.UUID,
    data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Fetch grievance
    result = await db.execute(select(Grievance).where(Grievance.id == id))
    grievance = result.scalars().first()
    if not grievance:
        raise HTTPException(status_code=404, detail="Grievance not found")

    # Verify authorization
    await _verify_access_auth(grievance, user, db)

    async with db.begin_nested():
        comment = GrievanceComment(
            grievance_id=grievance.id,
            author_id=user.id,
            author_role=user.role.value,
            comment=data.comment
        )
        db.add(comment)
        
        # Append GrievanceEvent (no state transition)
        event = GrievanceEvent(
            grievance_id=grievance.id,
            actor_id=user.id,
            actor_role=user.role.value,
            event_type="COMMENT_ADDED",
            from_state=grievance.current_state,
            to_state=grievance.current_state,
            reason=data.comment[:100] + "..." if len(data.comment) > 100 else data.comment
        )
        db.add(event)
        
        await log_security_event(
            db=db,
            action="COMMENT_ADDED",
            actor_id=user.id,
            actor_role=user.role.value,
            resource_type="grievance_comment",
            resource_id=comment.id
        )
        await db.flush()

    await db.commit()
    return comment

@router.get("/{id}/comments", response_model=List[CommentResponse])
async def list_grievance_comments(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Fetch grievance
    result = await db.execute(select(Grievance).where(Grievance.id == id))
    grievance = result.scalars().first()
    if not grievance:
        raise HTTPException(status_code=404, detail="Grievance not found")

    # Verify authorization
    await _verify_access_auth(grievance, user, db)

    result = await db.execute(
        select(GrievanceComment)
        .where(GrievanceComment.grievance_id == id)
        .order_by(GrievanceComment.created_at.asc())
    )
    return result.scalars().all()
