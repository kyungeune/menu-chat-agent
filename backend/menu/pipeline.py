"""
LangGraph 기반 3단계 신메뉴 개발 파이프라인
CrewAI 의존성 없이 LangChain + LangGraph + Tavily 웹검색으로 구현

Node 흐름:
  market_research  →  menu_ideation  →  validation  →  END
"""
from __future__ import annotations

import os
from typing import TypedDict, Annotated
import operator

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, END

# ── 모델 설정 ─────────────────────────────────────────────────────────────────

def _llm():
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.3,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

def _search_tool():
    return TavilySearchResults(
        max_results=6,
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
    )


# ── LangGraph State ──────────────────────────────────────────────────────────

class PipelineState(TypedDict):
    # inputs
    brand_type: str
    target: str
    season: str
    concept: str
    menu_data: str

    # inter-node outputs
    trend_report: str
    menu_candidates: str
    validation_report: str

    # accumulated log (optional — for debugging)
    logs: Annotated[list[str], operator.add]


# ── Node 1: Market Research ──────────────────────────────────────────────────

def market_research_node(state: PipelineState) -> dict:
    """
    웹 검색(Tavily)으로 시장 트렌드를 조사하고 리포트를 생성한다.
    메뉴 아이디어는 제안하지 않는다.
    """
    brand_type = state["brand_type"]
    target     = state["target"]
    season     = state["season"]
    concept    = state["concept"]

    # ── 웹 검색 ──────────────────────────────
    search = _search_tool()
    queries = [
        f"{brand_type} {season} 트렌드 메뉴 {concept}",
        f"{brand_type} {target} 소비 트렌드 {season}",
        f"{brand_type} 경쟁사 신메뉴 {season}",
    ]
    search_results = []
    for q in queries:
        try:
            results = search.invoke(q)
            for r in results:
                search_results.append(f"[{r.get('url','')}]\n{r.get('content','')}")
        except Exception as e:
            search_results.append(f"(검색 오류: {e})")

    raw_search = "\n\n---\n\n".join(search_results[:12])  # 최대 12개 단락

    # ── LLM 리포트 생성 ───────────────────────
    llm = _llm()
    system = SystemMessage(content=(
        "당신은 대기업 외식 프랜차이즈 본사 전략/상품기획 조직에서 근무하는 전문 시장조사 담당자이다. "
        "웹 검색 결과를 분석해 '무엇이 왜 유행하는지'를 설명하는 트렌드 리포트를 작성한다. "
        "메뉴 아이디어·신규 메뉴 제안·레시피 언급은 절대 금지한다. "
        "모든 주장은 아래 검색 결과에서 관찰된 근거를 기반으로 서술한다. "
        "결과는 반드시 한국어로 아래 섹션 구조를 지켜 작성한다.\n\n"
        "출력 형식:\n"
        "[요약]\n- 핵심 트렌드 3~4줄 압축 요약\n\n"
        "[키워드 TOP]\n- 트렌드 대표 키워드 5개\n\n"
        "[근거]\n- 검색 결과에서 관찰된 사실 기반 근거 (복수 출처 공통 흐름 중심)\n\n"
        "[경쟁사 사례]\n- 메뉴 유형·구성 특징·포지셔닝·가격대·주요 타겟\n\n"
        "[인사이트]\n- 시장 방향성 ('어떤 흐름이 관찰된다' 수준, '해야 한다' 금지)"
    ))
    human = HumanMessage(content=(
        f"브랜드/카테고리: {brand_type}\n"
        f"타겟 고객: {target}\n"
        f"시즌: {season}\n"
        f"콘셉트: {concept}\n\n"
        f"=== 웹 검색 결과 ===\n{raw_search}"
    ))
    response = llm.invoke([system, human])
    trend_report = response.content

    return {
        "trend_report": trend_report,
        "logs": [f"[1/3] 시장 조사 완료 ({len(trend_report)}자)"],
    }


# ── Node 2: Menu Ideation ────────────────────────────────────────────────────

def menu_ideation_node(state: PipelineState) -> dict:
    """
    트렌드 리포트를 기반으로 신메뉴 후보 3~5개를 설계한다.
    레거시 메뉴와 실질 중복을 강하게 방지한다.
    """
    llm = _llm()
    system = SystemMessage(content=(
        "당신은 대기업 외식 프랜차이즈 본사 R&D의 메뉴 기획 담당자다.\n\n"
        "[핵심 규칙: 레거시 메뉴 실질 중복 금지]\n"
        "- 아래 menu_data에 존재하는 메뉴와 이름만 다르고 실질이 유사한 메뉴를 제안하면 실패다.\n"
        "- 유사성 판단 4축 중 2축 이상 일치 시 중복:\n"
        "  1) 핵심 재료  2) 핵심 소스/시즈닝  3) 조리방식  4) 소비 맥락\n\n"
        "[차별화 최소 조건]\n"
        "- 각 후보는 레거시 대비 최소 2개 이상의 차별 요소 필수\n"
        "- 차별 요소: (A)메인재료 카테고리 변경 (B)소스 풍미 축 변경 "
        "(C)조리공정/식감 구조 변경 (D)포맷 변경 (E)타겟/소비상황 변경\n\n"
        "[현실 구현 가능성]\n"
        "- 희귀 수입 식재, 특수 전용 장비, 과도한 수작업 금지\n"
        "- 매장 표준 장비(프라이어/그릴/오븐/레인지) 기준\n"
        "- 조리 플로우 3~6단계로 표준화 가능해야 함\n\n"
        "[출력 규칙]\n"
        "- 반드시 한국어\n"
        "- 후보 정확히 3~5개\n"
        "- 각 후보마다 아래 7개 항목을 순서대로 포함:\n"
        "  1) 메뉴명(가칭)\n"
        "  2) 콘셉트(1줄)\n"
        "  3) 타겟/소비상황\n"
        "  4) 차별포인트(트렌드 키워드 연결)\n"
        "  5) 레시피 초안(구성요소/핵심 소스/토핑)\n"
        "  6) 조리 플로우(3~6단계)\n"
        "  7) 운영 난이도(낮/중/높)\n"
        "- 출력에 레거시 메뉴명 나열이나 비교표는 포함하지 말 것"
    ))
    human = HumanMessage(content=(
        f"=== 트렌드 리포트 ===\n{state['trend_report']}\n\n"
        f"=== 레거시/현행 메뉴 데이터 ===\n{state['menu_data']}\n\n"
        "위 트렌드 리포트를 근거로, 레거시 메뉴와 실질 중복 없는 신메뉴 후보 3~5개를 설계하라."
    ))
    response = llm.invoke([system, human])
    candidates = response.content

    return {
        "menu_candidates": candidates,
        "logs": [f"[2/3] 메뉴 기획 완료 ({len(candidates)}자)"],
    }


# ── Node 3: Validation ───────────────────────────────────────────────────────

def validation_node(state: PipelineState) -> dict:
    """
    메뉴 후보를 원가·수급·오퍼레이션·품질 일관성 기준으로 검증한다.
    마크다운 표 포함 출시 가능성 검토 문서를 생성한다.
    """
    llm = _llm()
    system = SystemMessage(content=(
        "당신은 대기업 프랜차이즈 본사 상품/운영 검증 담당자다.\n"
        "주관적 맛평가를 배제하고 원가·수급·오퍼레이션·품질 일관성·수익성 가정에 근거해 "
        "출시/보류 의사결정이 가능한 문서를 작성한다.\n\n"
        "[필수 요구사항]\n"
        "1. 출력은 반드시 한국어\n"
        "2. 출력 구조(순서 고정): [후보별 평가표] → [Top Pick 1~2개] → [리스크/개선안] → [가정 요약]\n"
        "3. [후보별 평가표]는 반드시 마크다운 표로 작성 (표 없으면 실패)\n"
        "4. 각 후보 평가: '추천/조건부 추천/보류/탈락' 중 하나만 사용\n"
        "5. 표 필수 컬럼:\n"
        "   후보명 | 평가 | 원가(원재료) | 원가(패키징) | 원가(토핑/부재료) | "
        "목표 판매가 가정 | 마진(보수적) | 마진(중립) | "
        "수급 리스크(계절/수입/대체재) | 오퍼레이션 리스크(시간/장비/동선/교육) | "
        "품질 일관성 리스크 | 필수 전제/체크포인트\n"
        "6. 개선안은 콘셉트 유지 전제에서만 제안 (새 메뉴 창작 금지)\n"
        "   허용: 공정 단순화, 규격화, 옵션화, 대체 원재료 범주, 패키징 변경\n"
        "7. Top Pick 1~2개 선정, 왜 살아남는지 3~5줄로 근거 제시\n"
        "8. 수치(원가/마진/시간)는 추정 범위로 표기, 가정 요약에 근거 명시\n"
        "9. 미사여구 금지, 결론·근거 중심"
    ))
    human = HumanMessage(content=(
        f"=== 신메뉴 후보 ===\n{state['menu_candidates']}\n\n"
        f"[브랜드 컨텍스트]\n"
        f"브랜드/카테고리: {state['brand_type']}, 타겟: {state['target']}, "
        f"시즌: {state['season']}, 콘셉트: {state['concept']}\n\n"
        "위 신메뉴 후보들에 대해 출시 가능성 검토 문서를 작성하라."
    ))
    response = llm.invoke([system, human])
    validation = response.content

    return {
        "validation_report": validation,
        "logs": [f"[3/3] 검증 완료 ({len(validation)}자)"],
    }


# ── Graph 조립 ────────────────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("market_research", market_research_node)
    graph.add_node("menu_ideation",   menu_ideation_node)
    graph.add_node("validation",      validation_node)

    graph.set_entry_point("market_research")
    graph.add_edge("market_research", "menu_ideation")
    graph.add_edge("menu_ideation",   "validation")
    graph.add_edge("validation",      END)

    return graph.compile()


# 싱글턴 그래프 (모듈 임포트 시 1회 컴파일)
pipeline = build_graph()


# ── 외부 진입점 ───────────────────────────────────────────────────────────────

def run_pipeline(
    brand_type: str,
    target: str,
    season: str,
    concept: str,
    menu_data: str,
) -> dict:
    """
    파이프라인을 실행하고 최종 state를 반환한다.
    반환 키: trend_report, menu_candidates, validation_report, logs
    """
    initial_state: PipelineState = {
        "brand_type":        brand_type,
        "target":            target,
        "season":            season,
        "concept":           concept,
        "menu_data":         menu_data,
        "trend_report":      "",
        "menu_candidates":   "",
        "validation_report": "",
        "logs":              [],
    }
    result = pipeline.invoke(initial_state)
    return result
