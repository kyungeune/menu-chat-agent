"""
app/config.py
공통 설정 — LLM, Embeddings, ChromaDB 경로
"""
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

CHROMA_PATH    = os.getenv("CHROMA_PATH", "./chroma_db")
DOCS_PATH      = os.getenv("DOCS_PATH",   "./docs")

EMBED_MODEL    = "text-embedding-3-small"
