"""
대화 로직:
1. 파라미터를 순서대로 수집한다.
2. 모두 모이면 LangGraph 파이프라인을 실행한다.
3. 완료 후 follow-up Q&A는 LLM이 분석 결과를 컨텍스트로 답변한다.
"""
from __future__ import annotations
import os
import re

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from menu.session  import SessionState, session_store, next_missing_field, FIELD_LABELS
from menu.pipeline import run_pipeline


# ── LLM (follow-up Q&A용) ────────────────────────────────────────────────────

def _llm():
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.4,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )


# ── 파라미터 추출 ─────────────────────────────────────────────────────────────

_PATTERNS = {
    "brand_type": r"(?:브랜드|카테고리|업종)[:\s]+([^\n,]+)",
    "target":     r"(?:타겟|고객|대상)[:\s]+([^\n,]+)",
    "season":     r"(?:시즌|계절|시점)[:\s]+([^\n,]+)",
    "concept":    r"(?:콘셉트|컨셉|콘셉)[:\s]+([^\n,]+)",
    "menu_data":  r"(?:메뉴|레거시|현행\s*메뉴)[:\s]+([^\n]+)",
}


def _try_extract(text: str, state: SessionState):
    """첫 메시지에서 key:value 패턴으로 여러 필드를 한 번에 추출 시도."""
    for field, pattern in _PATTERNS.items():
        if getattr(state, field) is None:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                setattr(state, field, m.group(1).strip())


def _fill_next(text: str, state: SessionState):
    """순서대로 빈 필드에 사용자 입력을 채운다."""
    field = next_missing_field(state)
    if field:
        setattr(state, field, text.strip())


# ── 메인 핸들러 ───────────────────────────────────────────────────────────────

def handle_message(thread_id: str, user_input: str) -> str:
    state = session_store.get_or_create(thread_id)
    state.messages.append({"role": "user", "content": user_input})

    # ── 파라미터 수집 단계 ─────────────────────────────────────────────────────
    if state.stage == "collect":
        if len(state.messages) == 1:
            _try_extract(user_input, state)  # 구조화된 첫 메시지 시도

        _fill_next(user_input, state)

        missing = next_missing_field(state)
        if missing:
            reply = _ask_for_field(missing, state)
        else:
            state.stage = "running"
            reply = _run(state)
            state.stage = "done"

    # ── 완료 후 follow-up ──────────────────────────────────────────────────────
    elif state.stage == "done":
        reply = _followup(user_input, state)

    # ── 실행 중 (중복 요청 방어) ───────────────────────────────────────────────
    else:
        reply = "⏳ 분석이 진행 중입니다. 잠시 후 다시 시도해 주세요."

    state.messages.append({"role": "assistant", "content": reply})
    return reply


# ── 필드 안내 메시지 ──────────────────────────────────────────────────────────

def _ask_for_field(field: str, state: SessionState) -> str:
    filled = [(k, getattr(state, k)) for k in FIELD_LABELS if getattr(state, k) is not None]

    intro = ""
    if not filled:
        intro = (
            "안녕하세요! 🍽️ **신메뉴 개발 AI 에이전트**입니다.\n\n"
            "시장 조사 → 메뉴 기획 → 운영 검증 3단계를 자동으로 진행합니다. "
            "먼저 몇 가지 정보를 입력해 주세요.\n\n"
        )

    progress = ""
    for k, v in filled:
        label = FIELD_LABELS[k].split("(")[0].strip()
        preview = (v[:35] + "…") if len(v) > 35 else v
        progress += f"✅ **{label}**: {preview}\n"
    if progress:
        progress += "\n"

    label = FIELD_LABELS[field]
    return f"{intro}{progress}📝 **{label}** 을(를) 입력해 주세요."


# ── 파이프라인 실행 ───────────────────────────────────────────────────────────

def _run(state: SessionState) -> str:
    header = (
        "✅ **모든 정보가 수집되었습니다!**\n\n"
        f"- 브랜드/카테고리: {state.brand_type}\n"
        f"- 타겟: {state.target}\n"
        f"- 시즌: {state.season}\n"
        f"- 콘셉트: {state.concept}\n\n"
        "🔍 **3단계 AI 분석 시작:**\n"
        "1. 시장 트렌드 조사 (Market Research)\n"
        "2. 신메뉴 후보 기획 (Menu Ideation)\n"
        "3. 출시 가능성 검증 (Validation)\n\n"
        "⏳ 1~3분 소요됩니다…\n\n---\n\n"
    )

    try:
        result = run_pipeline(
            brand_type=state.brand_type,
            target=state.target,
            season=state.season,
            concept=state.concept,
            menu_data=state.menu_data,
        )

        combined = (
            "## 📊 Step 1 · 시장 트렌드 리포트\n\n"
            + result["trend_report"]
            + "\n\n---\n\n"
            "## 🍽️ Step 2 · 신메뉴 후보\n\n"
            + result["menu_candidates"]
            + "\n\n---\n\n"
            "## ✅ Step 3 · 출시 가능성 검토\n\n"
            + result["validation_report"]
        )
        state.result = combined
        return header + combined + "\n\n---\n\n💬 추가 질문이 있으시면 자유롭게 입력해 주세요!"

    except Exception as e:
        return header + f"❌ **분석 중 오류:**\n\n```\n{e}\n```\n\n다시 시작하려면 '다시 시작'을 입력하세요."


# ── Follow-up Q&A ─────────────────────────────────────────────────────────────

_RESTART_KW = ["다시", "새로", "처음", "재시작", "초기화", "reset", "restart"]


def _followup(user_input: str, state: SessionState) -> str:
    if any(k in user_input.lower() for k in _RESTART_KW):
        state.brand_type = None
        state.target     = None
        state.season     = None
        state.concept    = None
        state.menu_data  = None
        state.stage      = "collect"
        state.result     = None
        state.messages   = []
        return "🔄 **세션 초기화 완료.** 새 분석을 시작합니다.\n\n" + _ask_for_field("brand_type", state)

    if not state.result:
        return "분석 결과가 없습니다. '다시 시작'을 입력해 주세요."

    # LLM이 분석 결과를 컨텍스트로 답변
    llm = _llm()
    system = SystemMessage(content=(
        "당신은 신메뉴 개발 전문 컨설턴트다. "
        "아래 분석 결과를 참고해 사용자의 추가 질문에 간결하고 정확하게 한국어로 답변한다. "
        "분석 결과에 없는 내용은 추측하지 말고 '분석 결과에 해당 정보가 없습니다'라고 밝힌다.\n\n"
        f"=== 분석 결과 ===\n{state.result[:6000]}"  # 컨텍스트 길이 제한
    ))
    human = HumanMessage(content=user_input)
    response = llm.invoke([system, human])
    return response.content
