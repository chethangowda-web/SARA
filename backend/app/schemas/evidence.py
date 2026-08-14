import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class EvidenceUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    grievance_id: uuid.UUID
    file_name: str
    file_type: str
    file_size: int
    description: Optional[str] = None
    uploaded_at: datetime
    is_deleted: bool

class EvidenceListResponse(BaseModel):
    items: List[EvidenceUploadResponse]
