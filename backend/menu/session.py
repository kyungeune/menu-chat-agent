"""
Session / conversation state management.
"""
from dataclasses import dataclass, field
from typing import Optional
import threading


@dataclass
class SessionState:
    thread_id: str
    messages: list = field(default_factory=list)  # {"role": "user"|"assistant", "content": str}

    # collected parameters
    brand_type: Optional[str] = None
    target:     Optional[str] = None
    season:     Optional[str] = None
    concept:    Optional[str] = None
    menu_data:  Optional[str] = None

    # stage: collect → running → done
    stage:  str = "collect"
    result: Optional[str] = None  # final combined markdown


class SessionStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._sessions: dict[str, SessionState] = {}

    def get_or_create(self, thread_id: str) -> SessionState:
        with self._lock:
            if thread_id not in self._sessions:
                self._sessions[thread_id] = SessionState(thread_id=thread_id)
            return self._sessions[thread_id]

    def get(self, thread_id: str) -> Optional[SessionState]:
        return self._sessions.get(thread_id)

    def delete(self, thread_id: str):
        with self._lock:
            self._sessions.pop(thread_id, None)


session_store = SessionStore()

REQUIRED_FIELDS = ["brand_type", "target", "season", "concept", "menu_data"]

FIELD_LABELS = {
    "brand_type": "브랜드/카테고리 (예: 카페, 피자, 햄버거 전문점 등)",
    "target":     "핵심 타겟 고객 (예: 20대 대학생, 40대 직장인 등)",
    "season":     "시즌/시점 (예: 여름, 겨울, 2024 Q4 등)",
    "concept":    "메뉴 콘셉트 (예: 맛있지만 건강한, 프리미엄 로컬 식재료 등)",
    "menu_data":  "현행(레거시) 메뉴 목록 (메뉴명과 간단한 설명을 입력해 주세요)",
}


def next_missing_field(state: SessionState) -> Optional[str]:
    for f in REQUIRED_FIELDS:
        if getattr(state, f) is None:
            return f
    return None
