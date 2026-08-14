import uuid
import os
import aiofiles
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.config import settings
from app.models.evidence import Evidence
from app.models.grievance import Grievance
from app.models.user import User
from app.models.grievance_event import GrievanceEvent
from app.services.audit_service import log_security_event

async def upload_evidence(
    db: AsyncSession, 
    grievance: Grievance, 
    uploader: User, 
    file: UploadFile, 
    description: Optional[str] = None
) -> Evidence:
    
    # 1. Validate file size
    # We must read the file to know its exact size, but UploadFile has a size property if spooled
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    
    max_bytes = settings.MAX_EVIDENCE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_EVIDENCE_SIZE_MB}MB"
        )
        
    # 2. Validate MIME type
    if file.content_type not in settings.ALLOWED_EVIDENCE_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} is not allowed"
        )
        
    # 3. Sanitize filename and path traversal
    original_filename = file.filename or "unknown_file"
    
    # Null byte detection
    if '\x00' in original_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename contains invalid characters"
        )
        
    # Check for path traversal in original name
    if '..' in original_filename or '/' in original_filename or '\\' in original_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Directory traversal characters are forbidden in filename"
        )
        
    # Verify extension against allowed mapping
    _, ext = os.path.splitext(original_filename.lower())
    ALLOWED_EXTENSIONS = {
        ".jpg": ["image/jpeg"],
        ".jpeg": ["image/jpeg"],
        ".png": ["image/png"],
        ".gif": ["image/gif"],
        ".webp": ["image/webp"],
        ".pdf": ["application/pdf"],
        ".mp4": ["video/mp4"],
        ".txt": ["text/plain"],
        ".doc": ["application/msword"],
        ".docx": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    }
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extension {ext} is not allowed"
        )
        
    if file.content_type not in ALLOWED_EXTENSIONS[ext]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content type mismatch with extension"
        )
        
    safe_filename = os.path.basename(original_filename)
    if len(safe_filename) > 200:
        safe_filename = safe_filename[-200:]
        
    # Read content to check magic bytes / signatures
    content = await file.read()
    
    # Reject executable headers (MZ / PE)
    if content.startswith(b'MZ'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Executable files are forbidden"
        )
        
    # Script tag detection in text files or simple block signatures
    if file.content_type == "text/plain":
        content_str = content.decode("utf-8", errors="ignore").lower()
        if "<?php" in content_str or "<script" in content_str or "javascript:" in content_str or "#!/bin" in content_str or "#!/usr/bin" in content_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Script execution content is forbidden"
            )

    # 4. Generate UUID-based storage name
    storage_uuid = uuid.uuid4()
    storage_filename = f"{storage_uuid}{ext}"
    
    # 5. Write to ./uploads/{grievance_id}/{uuid}.{ext}
    base_dir = os.path.abspath(settings.UPLOAD_DIR)
    grievance_dir = os.path.join(base_dir, str(grievance.id))
    
    # Path traversal protection - ensuring it's within base_dir
    if not os.path.abspath(grievance_dir).startswith(base_dir):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid path")
        
    os.makedirs(grievance_dir, exist_ok=True)
    file_path = os.path.join(grievance_dir, storage_filename)
    
    async with aiofiles.open(file_path, 'wb') as out_file:
        await out_file.write(content)
        
    # 6. Persist Evidence record
    async with db.begin_nested():
        evidence = Evidence(
            id=storage_uuid,
            grievance_id=grievance.id,
            uploaded_by=uploader.id,
            file_name=safe_filename,
            file_type=file.content_type,
            file_size=file_size,
            storage_path=file_path,
            description=description
        )
        db.add(evidence)
        
        # 7. Append GrievanceEvent
        event = GrievanceEvent(
            grievance_id=grievance.id,
            actor_id=uploader.id,
            actor_role=uploader.role.value,
            event_type="EVIDENCE_UPLOADED",
            from_state=grievance.current_state,
            to_state=grievance.current_state,
            metadata_json={
                "file_name": safe_filename,
                "file_type": file.content_type,
                "file_size": file_size
            }
        )
        db.add(event)
        
        # 8. log_security_event()
        await log_security_event(
            db=db,
            action="EVIDENCE_UPLOADED",
            actor_id=uploader.id,
            actor_role=uploader.role.value,
            resource_type="evidence",
            resource_id=evidence.id,
            new_state={"file_name": safe_filename, "file_type": file.content_type, "file_size": file_size}
        )
        await db.flush()
        
    await db.commit()
    return evidence

async def get_evidence_list(db: AsyncSession, grievance_id: uuid.UUID) -> List[Evidence]:
    result = await db.execute(
        select(Evidence)
        .where(Evidence.grievance_id == grievance_id, Evidence.is_deleted == False)
        .order_by(Evidence.uploaded_at.desc())
    )
    return result.scalars().all()
