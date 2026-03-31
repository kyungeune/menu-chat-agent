"""
backend/app/router_rag.py
기존 RAG 챗봇 엔드포인트 → POST /chat
"""
from fastapi import APIRouter
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from app.graph import graph

router = APIRouter(tags=["RAG Chatbot"])


class ChatRequest(BaseModel):
    thread_id: str
    user_input: str

class ChatResponse(BaseModel):
    reply: str


SYSTEM_PROMPT = """\
당신은 내부 문서 기반 RAG QA 어시스턴트입니다.

[규칙]
- 답변 전 반드시 rag_search를 사용해 근거를 찾으세요(가능한 경우).
- 답변에는 (출처=문서명, 페이지=번호) 형태의 근거를 2~4개 포함하세요.
- 근거가 없으면 '문서에 근거가 부족합니다'라고 말하세요.
"""


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    config = {"configurable": {"thread_id": req.thread_id}}

    result_state = graph.invoke(
        {
            "messages": [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=req.user_input),
            ],
            "tool_count": 0,
        },
        config=config,
    )

    ai_msg = None
    for msg in reversed(result_state["messages"]):
        if isinstance(msg, AIMessage):
            ai_msg = msg
            break

    reply = ai_msg.content if ai_msg else "(응답이 없습니다.)"
    return ChatResponse(reply=reply)
