"""
app/tools.py
RAG 검색 도구 — ChromaDB 기반
"""
import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.tools import tool
from app.config import OPENAI_API_KEY, CHROMA_PATH, EMBED_MODEL


def get_vectorstore():
    embeddings = OpenAIEmbeddings(
        model=EMBED_MODEL,
        openai_api_key=OPENAI_API_KEY,
    )
    return Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings,
    )


@tool
def rag_search(query: str) -> str:
    """내부 문서에서 관련 내용을 검색합니다."""
    try:
        vs = get_vectorstore()
        docs = vs.similarity_search(query, k=4)
        if not docs:
            return "관련 문서를 찾을 수 없습니다."
        results = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "알 수 없음")
            page   = doc.metadata.get("page", "-")
            results.append(f"[{i}] 출처={source}, 페이지={page}\n{doc.page_content}")
        return "\n\n".join(results)
    except Exception as e:
        return f"검색 오류: {e}"
