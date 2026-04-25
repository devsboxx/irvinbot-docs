from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List


CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def parse_and_chunk(file_path: str, extra_metadata: dict = {}) -> List[Document]:
    loader = PyPDFLoader(file_path)
    pages = loader.load()

    chunks = _splitter.split_documents(pages)

    for i, chunk in enumerate(chunks):
        chunk.metadata.update({**extra_metadata, "chunk_index": i})

    return chunks
