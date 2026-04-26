import os
import uuid
import shutil
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.models.document import Document
from app.schemas.docs import DocumentOut, DocumentList, UploadResponse


def upload_document(db: Session, user_id: str, file: UploadFile) -> UploadResponse:
    _validate_file(file)

    doc_id = uuid.uuid4()
    safe_name = f"{doc_id}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_name)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    doc = Document(
        id=doc_id,
        user_id=uuid.UUID(user_id),
        original_name=file.filename,
        file_path=file_path,
        status="ready",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return UploadResponse(
        document=DocumentOut.model_validate(doc),
        message="Documento guardado correctamente",
    )


def list_documents(db: Session, user_id: str) -> DocumentList:
    docs = (
        db.query(Document)
        .filter(Document.user_id == uuid.UUID(user_id))
        .order_by(Document.created_at.desc())
        .all()
    )
    return DocumentList(
        documents=[DocumentOut.model_validate(d) for d in docs],
        total=len(docs),
    )


def get_document(db: Session, document_id: str, user_id: str) -> DocumentOut:
    doc = _get_owned_doc(db, document_id, user_id)
    return DocumentOut.model_validate(doc)


def delete_document(db: Session, document_id: str, user_id: str) -> None:
    doc = _get_owned_doc(db, document_id, user_id)

    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    db.delete(doc)
    db.commit()


# ── private helpers ──────────────────────────────────────────────────────────

def _validate_file(file: UploadFile) -> None:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are accepted")

    file.file.seek(0, 2)
    size_mb = file.file.tell() / (1024 * 1024)
    file.file.seek(0)

    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.MAX_FILE_SIZE_MB} MB limit",
        )


def _get_owned_doc(db: Session, document_id: str, user_id: str) -> Document:
    doc = db.query(Document).filter(
        Document.id == uuid.UUID(document_id),
        Document.user_id == uuid.UUID(user_id),
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc
