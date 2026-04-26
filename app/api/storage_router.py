from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import BaseModel

from app.services import r2_service
from app.core.config import settings

router = APIRouter()


class StorageUploadResponse(BaseModel):
    key: str
    url: str
    filename: str


@router.post("/upload", response_model=StorageUploadResponse, status_code=201)
async def upload_to_storage(file: UploadFile = File(...)):
    """Internal endpoint — upload any file to R2 and return its public URL.
    Used by the chat service to store generated thesis PDFs."""
    if not settings.R2_ENDPOINT:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="R2 storage not configured",
        )

    key = r2_service.make_key("generated", file.filename)
    content_type = file.content_type or "application/octet-stream"

    try:
        url = r2_service.upload_fileobj(file.file, key, content_type)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"R2 upload error: {exc}",
        )

    return StorageUploadResponse(key=key, url=url, filename=file.filename)
