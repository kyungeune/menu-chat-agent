"""
backend/main.py
────────────────────────────────
POST /chat          ← RAG 문서 챗봇 (기존)
POST /menu-chat     ← 신메뉴 Agent  (신규)
GET  /health
────────────────────────────────
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.router_rag  import router as rag_router
from routers.router_menu import router as menu_router

app = FastAPI(
    title="AI Agent Hub",
    description="RAG 문서 챗봇 + 신메뉴 개발 Agent",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rag_router)   # /chat
app.include_router(menu_router)  # /menu-chat


@app.get("/health")
def health():
    return {"status": "ok"}
