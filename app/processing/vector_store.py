import chromadb
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from app.core.config import settings
from typing import List


def _get_vectorstore() -> Chroma:
    embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
    chroma_client = chromadb.HttpClient(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
    )
    return Chroma(
        client=chroma_client,
        collection_name=settings.CHROMA_COLLECTION,
        embedding_function=embeddings,
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
