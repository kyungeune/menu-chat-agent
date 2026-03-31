"""
backend/app/router_menu.py
신메뉴 Agent 엔드포인트

POST /menu-chat
POST /menu-chat/reset
GET  /menu-chat/session/{thread_id}
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from menu.chat    import handle_message
from menu.session import session_store

router = APIRouter(prefix="/menu-chat", tags=["신메뉴 Agent"])


class MenuChatRequest(BaseModel):
    thread_id: str
    user_input: str

class MenuChatResponse(BaseModel):
    reply: str
    stage: str

class ResetRequest(BaseModel):
    thread_id: str

class SessionInfoResponse(BaseModel):
    thread_id: str
    stage: str
    brand_type:    Optional[str] = None
    target:        Optional[str] = None
    season:        Optional[str] = None
    concept:       Optional[str] = None
    has_menu_data: bool
    message_count: int


@router.post("", response_model=MenuChatResponse)
def menu_chat(req: MenuChatRequest):
    if not req.user_input.strip():
        raise HTTPException(status_code=400, detail="user_input is empty")
    reply = handle_message(req.thread_id, req.user_input)
    state = session_store.get(req.thread_id)
    stage = state.stage if state else "collect"
    return MenuChatResponse(reply=reply, stage=stage)


@router.post("/reset")
def reset(req: ResetRequest):
    session_store.delete(req.thread_id)
    return {"message": "Menu session reset", "thread_id": req.thread_id}


@router.get("/session/{thread_id}", response_model=SessionInfoResponse)
def session_info(thread_id: str):
    state = session_store.get(thread_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionInfoResponse(
        thread_id=state.thread_id,
        stage=state.stage,
        brand_type=state.brand_type,
        target=state.target,
        season=state.season,
        concept=state.concept,
        has_menu_data=state.menu_data is not None,
        message_count=len(state.messages),
    )
