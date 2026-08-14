import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class CommentCreate(BaseModel):
    comment: str = Field(..., min_length=1, max_length=2000)

class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    grievance_id: uuid.UUID
    author_id: Optional[uuid.UUID] = None
    author_role: Optional[str] = None
    comment: str
    created_at: datetime
