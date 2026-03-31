"""
app/rag.py
문서 ingestion 유틸리티
docs/ 폴더의 .txt / .pdf 파일을 ChromaDB에 임베딩합니다.

실행: python -m app.rag
"""
import os
import glob
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from app.config import OPENAI_API_KEY, CHROMA_PATH, DOCS_PATH, EMBED_MODEL


def load_documents(docs_path: str):
    docs = []
    for path in glob.glob(os.path.join(docs_path, "**/*"), recursive=True):
        if path.endswith(".txt"):
            docs.extend(TextLoader(path, encoding="utf-8").load())
        elif path.endswith(".pdf"):
            docs.extend(PyPDFLoader(path).load())
    return docs


def ingest():
    print(f"📂 문서 로드 중: {DOCS_PATH}")
    docs = load_documents(DOCS_PATH)
    if not docs:
        print("⚠️  docs/ 폴더에 .txt 또는 .pdf 파일이 없습니다.")
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    print(f"✂️  청크 수: {len(chunks)}")

    embeddings = OpenAIEmbeddings(model=EMBED_MODEL, openai_api_key=OPENAI_API_KEY)
    Chroma.from_documents(chunks, embeddings, persist_directory=CHROMA_PATH)
    print(f"✅ ChromaDB 저장 완료: {CHROMA_PATH}")


if __name__ == "__main__":
    ingest()
