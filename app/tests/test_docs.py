import os
# Entorno hermético antes de importar main (que crea UPLOAD_DIR y hace create_all):
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_docs.db")
os.environ.setdefault("UPLOAD_DIR", "./test_uploads")

import io
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.core.database import Base, get_db
from app.api import docs_router

SQLALCHEMY_TEST_URL = "sqlite:///./test_docs.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
AUTH_HEADER = {"authorization": "Bearer fake-token"}


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


def override_current_user():
    return TEST_USER_ID


app.dependency_overrides[get_db] = override_get_db
# La dependencia de auth real es `current_user` (envuelve get_user_id_from_token).
app.dependency_overrides[docs_router.current_user] = override_current_user
Base.metadata.drop_all(bind=engine)   # arranca limpio aunque queden archivos previos
Base.metadata.create_all(bind=engine)
client = TestClient(app)


def _fake_pdf_bytes() -> bytes:
    return b"%PDF-1.4 fake pdf content for testing"


def test_list_documents_empty():
    res = client.get("/docs/", headers=AUTH_HEADER)
    assert res.status_code == 200
    assert res.json()["total"] == 0


def test_upload_non_pdf_rejected():
    res = client.post(
        "/docs/upload",
        files={"file": ("report.txt", io.BytesIO(b"text content"), "text/plain")},
        headers=AUTH_HEADER,
    )
    assert res.status_code == 400


def test_upload_pdf_success():
    res = client.post(
        "/docs/upload",
        files={"file": ("thesis.pdf", io.BytesIO(_fake_pdf_bytes()), "application/pdf")},
        headers=AUTH_HEADER,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["document"]["status"] == "ready"
    assert data["document"]["original_name"] == "thesis.pdf"
    assert "id" in data["document"]


def test_get_document():
    upload_res = client.post(
        "/docs/upload",
        files={"file": ("doc.pdf", io.BytesIO(_fake_pdf_bytes()), "application/pdf")},
        headers=AUTH_HEADER,
    )
    doc_id = upload_res.json()["document"]["id"]
    res = client.get(f"/docs/{doc_id}", headers=AUTH_HEADER)
    assert res.status_code == 200
    assert res.json()["id"] == doc_id


def test_delete_document():
    upload_res = client.post(
        "/docs/upload",
        files={"file": ("del.pdf", io.BytesIO(_fake_pdf_bytes()), "application/pdf")},
        headers=AUTH_HEADER,
    )
    doc_id = upload_res.json()["document"]["id"]
    del_res = client.delete(f"/docs/{doc_id}", headers=AUTH_HEADER)
    assert del_res.status_code == 204


def test_get_nonexistent_document():
    res = client.get(f"/docs/{uuid.uuid4()}", headers=AUTH_HEADER)
    assert res.status_code == 404
