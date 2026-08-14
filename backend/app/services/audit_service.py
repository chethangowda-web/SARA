import uuid
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog

async def log_security_event(
    db: AsyncSession,
    action: str,
    actor_id: Optional[uuid.UUID] = None,
    actor_role: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[uuid.UUID] = None,
    previous_state: Optional[dict] = None,
    new_state: Optional[dict] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    """
    Asynchronously write security event logs to the database.
    """
    # Create the log entry
    audit_log = AuditLog(
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        previous_state=previous_state,
        new_state=new_state,
        ip_address=ip_address
    )
    
    db.add(audit_log)
    await db.flush()
    return audit_log
