from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List


class DocumentOut(BaseModel):
    id: UUID
    user_id: UUID
    original_name: str
    status: str
    chunk_count: int
    error_message: Optional[str] = None
    r2_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentList(BaseModel):
    documents: List[DocumentOut]
    total: int


class UploadResponse(BaseModel):
    document: DocumentOut
    message: str
