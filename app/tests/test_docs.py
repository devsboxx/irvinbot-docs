import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from main import app
from app.core.database import Base, get_db
from app.core.security import get_user_id_from_token

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
app.dependency_overrides[get_user_id_from_token] = override_current_user
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
    mock_chunks = [MagicMock(page_content="chunk 1", metadata={})]

    with patch("app.processing.pdf_parser.parse_and_chunk", return_value=mock_chunks):
        with patch("app.processing.vector_store.add_documents", return_value=1):
            res = client.post(
                "/docs/upload",
                files={"file": ("thesis.pdf", io.BytesIO(_fake_pdf_bytes()), "application/pdf")},
                headers=AUTH_HEADER,
            )

    assert res.status_code == 201
    data = res.json()
    assert data["document"]["status"] == "ready"
    assert data["document"]["chunk_count"] == 1


def test_get_document():
    mock_chunks = [MagicMock(page_content="x", metadata={})]
    with patch("app.processing.pdf_parser.parse_and_chunk", return_value=mock_chunks):
        with patch("app.processing.vector_store.add_documents", return_value=1):
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
    mock_chunks = [MagicMock(page_content="x", metadata={})]
    with patch("app.processing.pdf_parser.parse_and_chunk", return_value=mock_chunks):
        with patch("app.processing.vector_store.add_documents", return_value=1):
            upload_res = client.post(
                "/docs/upload",
                files={"file": ("del.pdf", io.BytesIO(_fake_pdf_bytes()), "application/pdf")},
                headers=AUTH_HEADER,
            )

    doc_id = upload_res.json()["document"]["id"]

    with patch("app.processing.vector_store.delete_by_document_id"):
        with patch("os.path.exists", return_value=False):
            del_res = client.delete(f"/docs/{doc_id}", headers=AUTH_HEADER)

    assert del_res.status_code == 204


def test_get_nonexistent_document():
    res = client.get("/docs/00000000-0000-0000-0000-000000000099", headers=AUTH_HEADER)
    assert res.status_code == 404
