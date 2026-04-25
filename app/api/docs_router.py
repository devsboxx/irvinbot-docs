from fastapi import APIRouter, Depends, Header, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_user_id_from_token
from app.schemas.docs import DocumentOut, DocumentList, UploadResponse
from app.services import docs_service

router = APIRouter()


def current_user(authorization: str = Header(...)) -> str:
    return get_user_id_from_token(authorization)


@router.post("/upload", response_model=UploadResponse, status_code=201)
def upload(
    file: UploadFile = File(...),
    user_id: str = Depends(current_user),
    db: Session = Depends(get_db),
):
    return docs_service.upload_document(db, user_id, file)


@router.get("/", response_model=DocumentList)
def list_docs(
    user_id: str = Depends(current_user),
    db: Session = Depends(get_db),
):
    return docs_service.list_documents(db, user_id)


@router.get("/{document_id}", response_model=DocumentOut)
def get_doc(
    document_id: str,
    user_id: str = Depends(current_user),
    db: Session = Depends(get_db),
):
    return docs_service.get_document(db, document_id, user_id)


@router.delete("/{document_id}", status_code=204)
def delete_doc(
    document_id: str,
    user_id: str = Depends(current_user),
    db: Session = Depends(get_db),
):
    docs_service.delete_document(db, document_id, user_id)
