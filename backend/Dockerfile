FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 루트 app/ 패키지 (graph, tools, config 등)
COPY app/ ./app/

# RAG 데이터
COPY chroma_db/ ./chroma_db/
COPY docs/ ./docs/

# backend 소스 (routers/, menu/ 포함)
COPY backend/main.py ./backend/main.py
COPY backend/routers/ ./backend/routers/
COPY backend/menu/ ./backend/menu/

ENV PYTHONPATH=/app:/app/backend

WORKDIR /app/backend

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]