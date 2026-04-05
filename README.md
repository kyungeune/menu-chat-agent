# 🤖 AI Agent Hub

**RAG 문서 챗봇** + **신메뉴 개발 AI Agent** 통합 프로젝트
RAG 문서 챗봇과 신메뉴 개발 Agent를 하나의 서비스로 구성한 프로젝트입니다.  
Frontend는 Streamlit, Backend는 FastAPI로 구성되어 있으며, 기능은 크게 두 가지입니다.

- **RAG 문서 챗봇**: 내부 문서를 기반으로 질의응답
- **신메뉴 개발 Agent**: 사용자 입력을 순차 수집한 뒤 시장조사 → 메뉴기획 → 운영검증 수행
```
Streamlit Frontend  (port 8501)
  ├── 탭 1: 📚 RAG 문서 챗봇     → POST /chat
  └── 탭 2: 🍽️ 신메뉴 개발 Agent → POST /menu-chat

FastAPI Backend  (port 8000)
  ├── /chat          ← LangGraph RAG (ChromaDB)
  ├── /menu-chat     ← LangGraph 3-Node Pipeline
  │     ├── Node 1: market_research  (Tavily 웹검색 → 트렌드 리포트)
  │     ├── Node 2: menu_ideation    (신메뉴 3~5개 기획)
  │     └── Node 3: validation       (원가·수급·오퍼레이션 검증표)
  └── /health
```

---

## 📁 폴더 구조

```text
menu-agent-final/
├── app/                             # 공통 모듈 (RAG 관련 핵심 로직)
│   ├── config.py                    # 환경변수 / 모델 설정
│   ├── graph.py                     # LangGraph 기반 RAG 그래프
│   ├── rag.py                       # docs/ 문서를 임베딩하여 ChromaDB에 적재
│   └── tools.py                     # rag_search 등 RAG 도구 정의
│
├── backend/                         # FastAPI 백엔드
│   ├── main.py                      # FastAPI 앱 시작점, CORS, 라우터 등록, /health
│   ├── requirements.txt
│   ├── Dockerfile
│   └── app/
│       ├── router_rag.py            # POST /chat 엔드포인트
│       ├── router_menu.py           # /menu-chat 관련 엔드포인트
│       └── menu/
│           ├── chat.py              # 신메뉴 Agent 대화 흐름 제어
│           ├── session.py           # 세션 상태 저장 및 stage 관리
│           └── pipeline.py          # 시장조사 → 메뉴기획 → 검증 파이프라인 실행
│
├── frontend/                        # Streamlit 프론트엔드
│   ├── streamlit_app.py             # 사용자 UI
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
│
├── chroma_db/                       # ChromaDB 저장 폴더 (자동 생성)
├── docs/                            # RAG 검색 대상 문서 폴더
│   └── sample_knowledge.txt
├── docker-compose.yml               # frontend / backend 통합 실행
├── .env                             # OpenAI, Tavily 등 API 키 설정
└── README.md
```

---

## 🚀 시작하기

### 1. API 키 설정

`.env` 파일을 열어 키를 입력합니다.

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
TAVILY_API_KEY=tvly-...
```

| 키 | 발급처 | 비고 |
|----|--------|------|
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) | 필수 |
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com) | 신메뉴 Agent 웹검색용, 무료 플랜 가능 |

### 2. RAG 문서 추가 (선택)

`docs/` 폴더에 `.txt` 또는 `.pdf` 파일을 넣은 뒤:

```bash
# 컨테이너 실행 후 임베딩
docker compose exec backend python -m app.rag
```

### 3. 실행

```bash
docker compose up --build
```

브라우저에서 **http://localhost:8501** 접속

---

## 💬 사용 방법

### 📚 탭 1 — RAG 문서 챗봇
`docs/` 폴더에 넣은 문서 기반으로 질문·답변합니다.

### 🍽️ 탭 2 — 신메뉴 개발 Agent
아래 5가지 정보를 순서대로 입력하면 자동 분석합니다.

| 순서 | 항목 | 예시 |
|------|------|------|
| 1 | 브랜드/카테고리 | 카페, 피자, 햄버거 |
| 2 | 핵심 타겟 고객 | 30대 직장인 |
| 3 | 시즌/시점 | 여름, 겨울 |
| 4 | 콘셉트 | 건강하고 트렌디한 |
| 5 | 현행 메뉴 목록 | 아메리카노, 라떼, 크로플… |

---

## 🔌 API 엔드포인트

| Method | URL | 설명 |
|--------|-----|------|
| `GET`  | `/health` | 헬스체크 |
| `POST` | `/chat` | RAG 챗봇 메시지 |
| `POST` | `/menu-chat` | 신메뉴 Agent 메시지 |
| `POST` | `/menu-chat/reset` | 신메뉴 세션 초기화 |
| `GET`  | `/menu-chat/session/{id}` | 신메뉴 세션 정보 |
