"""
frontend/streamlit_app.py
────────────────────────────────────────────────
탭 1: 📚 RAG 문서 챗봇     → POST /chat
탭 2: 🍽️ 신메뉴 개발 Agent → POST /menu-chat
────────────────────────────────────────────────
"""
import os
import uuid

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Agent Hub",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@600;700&family=Noto+Sans+KR:wght@300;400;500&display=swap');

:root {
    --cream:    #FAF7F2;
    --espresso: #2C1810;
    --gold:     #D4A843;
    --border:   #E8E0D5;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--cream) !important;
    font-family: 'Noto Sans KR', sans-serif;
    color: var(--espresso);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%) !important;
}
[data-testid="stSidebar"] * { color: #e8eaf6 !important; }
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    color: #e8eaf6 !important;
    border-radius: 6px;
    transition: all 0.2s;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.15) !important;
}

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 8px;
    background: transparent;
    border-bottom: 2px solid var(--border);
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    font-family: 'Noto Sans KR', sans-serif;
    font-weight: 500;
    font-size: 0.95rem;
    padding: 0.6rem 1.4rem;
    border-radius: 8px 8px 0 0;
    border: 1px solid transparent;
    background: transparent;
    color: #8A7E75;
    transition: all 0.2s;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: white !important;
    border-color: var(--border) !important;
    border-bottom-color: white !important;
    color: var(--espresso) !important;
    font-weight: 600 !important;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    background: white !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    margin-bottom: 0.6rem !important;
    box-shadow: 0 1px 3px rgba(44,24,16,0.05) !important;
}

/* Chat input */
[data-testid="stChatInput"] textarea {
    background: white !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 10px !important;
    font-family: 'Noto Sans KR', sans-serif !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 3px rgba(212,168,67,0.12) !important;
}

/* Stage badge */
.stage-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 100px;
    font-size: 0.72rem;
    font-weight: 600;
}
.stage-collect { background:#FEF3C7; color:#92400E; }
.stage-running  { background:#DBEAFE; color:#1E40AF; }
.stage-done     { background:#D1FAE5; color:#065F46; }

/* Info card */
.info-card {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.13);
    border-radius: 7px;
    padding: 0.6rem 0.9rem;
    margin-bottom: 0.4rem;
    font-size: 0.79rem;
}
.info-card .lbl {
    font-size: 0.67rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: rgba(212,168,67,0.85);
    margin-bottom: 2px;
}
.info-card .val { color: rgba(232,234,246,0.9); font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────

defaults = {
    "rag_thread_id":  str(uuid.uuid4()),
    "rag_messages":   [],
    "menu_thread_id": str(uuid.uuid4()),
    "menu_messages":  [],
    "menu_stage":     "collect",
    "menu_session":   {},
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helpers ───────────────────────────────────────────────────────────────────

def call_rag(text: str) -> str:
    try:
        r = requests.post(
            f"{BACKEND_URL}/chat",
            json={"thread_id": st.session_state.rag_thread_id, "user_input": text},
            timeout=60,
        )
        r.raise_for_status()
        return r.json().get("reply", "(응답 없음)")
    except Exception as e:
        return f"⚠️ 오류: {e}"


def call_menu(text: str) -> tuple[str, str]:
    try:
        r = requests.post(
            f"{BACKEND_URL}/menu-chat",
            json={"thread_id": st.session_state.menu_thread_id, "user_input": text},
            timeout=300,
        )
        r.raise_for_status()
        d = r.json()
        return d.get("reply", "(응답 없음)"), d.get("stage", "collect")
    except Exception as e:
        return f"⚠️ 오류: {e}", "collect"


def fetch_menu_session() -> dict:
    try:
        r = requests.get(
            f"{BACKEND_URL}/menu-chat/session/{st.session_state.menu_thread_id}",
            timeout=5,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}


def reset_rag():
    st.session_state.rag_thread_id = str(uuid.uuid4())
    st.session_state.rag_messages  = []


def reset_menu():
    try:
        requests.post(
            f"{BACKEND_URL}/menu-chat/reset",
            json={"thread_id": st.session_state.menu_thread_id},
            timeout=5,
        )
    except Exception:
        pass
    st.session_state.menu_thread_id = str(uuid.uuid4())
    st.session_state.menu_messages  = []
    st.session_state.menu_stage     = "collect"
    st.session_state.menu_session   = {}


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="padding:0.3rem 0 1rem;">
        <div style="font-family:'Noto Serif KR',serif;font-size:1.2rem;font-weight:700;color:#e8eaf6;">
            🤖 AI Agent Hub
        </div>
        <div style="font-size:0.72rem;color:rgba(232,234,246,0.4);margin-top:4px;">
            RAG Chatbot  ·  신메뉴 Agent
        </div>
    </div>
    """, unsafe_allow_html=True)

    # RAG section
    st.markdown("##### 📚 RAG 문서 챗봇")
    st.caption(f"Thread: `{st.session_state.rag_thread_id[:8]}…`")
    if st.button("새 세션", key="b_rag_reset", use_container_width=True):
        reset_rag(); st.rerun()

    st.markdown("<hr style='border-color:rgba(255,255,255,0.1);margin:0.8rem 0'>",
                unsafe_allow_html=True)

    # Menu Agent section
    st.markdown("##### 🍽️ 신메뉴 Agent")
    stage = st.session_state.menu_stage
    labels = {"collect": "정보 수집 중", "running": "분석 실행 중", "done": "분석 완료"}
    st.markdown(
        f'<span class="stage-badge stage-{stage}">{labels.get(stage, stage)}</span>',
        unsafe_allow_html=True,
    )
    st.caption(f"Thread: `{st.session_state.menu_thread_id[:8]}…`")

    info = st.session_state.menu_session
    for k, lbl in [("brand_type","브랜드"),("target","타겟"),("season","시즌"),("concept","콘셉트")]:
        v = info.get(k)
        if v:
            st.markdown(
                f'<div class="info-card"><div class="lbl">{lbl}</div>'
                f'<div class="val">{v[:28]}{"…" if len(v)>28 else ""}</div></div>',
                unsafe_allow_html=True,
            )
    if info.get("has_menu_data"):
        st.markdown(
            '<div class="info-card"><div class="lbl">레거시 메뉴</div>'
            '<div class="val">✅ 등록됨</div></div>',
            unsafe_allow_html=True,
        )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("새 세션", key="b_menu_reset", use_container_width=True):
            reset_menu(); st.rerun()
    with c2:
        if st.button("새로고침", key="b_menu_info", use_container_width=True):
            st.session_state.menu_session = fetch_menu_session(); st.rerun()

    st.markdown("<hr style='border-color:rgba(255,255,255,0.1);margin:0.8rem 0'>",
                unsafe_allow_html=True)
    st.markdown(
        f"<div style='font-size:0.68rem;color:rgba(232,234,246,0.25);'>{BACKEND_URL}</div>",
        unsafe_allow_html=True,
    )

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_rag, tab_menu = st.tabs(["📚 RAG 문서 챗봇", "🍽️ 신메뉴 개발 Agent"])

# ── Tab 1: RAG ────────────────────────────────────────────────────────────────
with tab_rag:
    st.markdown("### 📚 RAG 문서 챗봇")
    st.caption("내부 문서 기반 QA · LangGraph + ChromaDB")

    if not st.session_state.rag_messages:
        st.markdown("""
        <div style="text-align:center;padding:2.5rem 1rem;color:#8A7E75;">
            <div style="font-size:2.8rem;margin-bottom:0.8rem;">📖</div>
            <div style="font-size:1rem;font-weight:600;color:#4A2820;">문서에 대해 질문해보세요</div>
            <div style="font-size:0.82rem;margin-top:0.4rem;">
                내부 문서를 검색해 출처와 함께 답변합니다
            </div>
        </div>
        """, unsafe_allow_html=True)

    for msg in st.session_state.rag_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if rag_input := st.chat_input("질문을 입력하세요…", key="rag_input"):
        st.session_state.rag_messages.append({"role": "user", "content": rag_input})
        with st.chat_message("user"):
            st.markdown(rag_input)
        with st.chat_message("assistant"):
            with st.spinner("문서 검색 중…"):
                reply = call_rag(rag_input)
            st.markdown(reply)
        st.session_state.rag_messages.append({"role": "assistant", "content": reply})
        st.rerun()

# ── Tab 2: Menu Agent ─────────────────────────────────────────────────────────
with tab_menu:
    st.markdown("### 🍽️ 신메뉴 개발 AI Agent")
    st.caption("시장 조사 → 메뉴 기획 → 운영 검증  ·  LangGraph 3-Node Pipeline · GPT-4o-mini")

    if not st.session_state.menu_messages:
        st.markdown("""
        <div style="text-align:center;padding:2.5rem 1rem;color:#8A7E75;">
            <div style="font-size:2.8rem;margin-bottom:0.8rem;">🥘</div>
            <div style="font-size:1rem;font-weight:600;color:#4A2820;">신메뉴 아이디어를 함께 만들어봐요</div>
            <div style="font-size:0.82rem;margin-top:0.4rem;line-height:1.7;">
                브랜드 · 타겟 고객 · 시즌 · 콘셉트 · 현행 메뉴를 입력하면<br>
                시장 조사부터 출시 가능성 검증까지 자동으로 진행합니다
            </div>
        </div>
        """, unsafe_allow_html=True)

    for msg in st.session_state.menu_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    is_running = (st.session_state.menu_stage == "running")
    placeholder = (
        "브랜드, 타겟, 시즌, 콘셉트, 현행 메뉴를 순서대로 입력해 주세요…"
        if not is_running else "⏳ 분석 진행 중… 잠시 기다려 주세요"
    )

    if menu_input := st.chat_input(placeholder, key="menu_input", disabled=is_running):
        st.session_state.menu_messages.append({"role": "user", "content": menu_input})
        with st.chat_message("user"):
            st.markdown(menu_input)
        with st.chat_message("assistant"):
            with st.spinner("분석 중… (최대 3분 소요)"):
                reply, new_stage = call_menu(menu_input)
            st.markdown(reply)
        st.session_state.menu_messages.append({"role": "assistant", "content": reply})
        st.session_state.menu_stage   = new_stage
        st.session_state.menu_session = fetch_menu_session()
        st.rerun()
