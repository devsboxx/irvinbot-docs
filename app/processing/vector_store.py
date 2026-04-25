import logging
from typing import List

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.core.config import settings
from app.llm.providers import get_embeddings

logger = logging.getLogger(__name__)


def _get_vectorstore() -> Chroma:
    chroma_client = chromadb.HttpClient(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
    )
    return Chroma(
        client=chroma_client,
        collection_name=settings.CHROMA_COLLECTION,
        embedding_function=get_embeddings(),
    )


def add_documents(docs: List[Document]) -> int:
    vs = _get_vectorstore()
    ids = vs.add_documents(docs)
    return len(ids)


def delete_by_document_id(document_id: str) -> None:
    vs = _get_vectorstore()
    results = vs.get(where={"document_id": document_id})
    if results["ids"]:
        vs.delete(ids=results["ids"])


def count_by_document_id(document_id: str) -> int:
    vs = _get_vectorstore()
    results = vs.get(where={"document_id": document_id})
    return len(results["ids"])
