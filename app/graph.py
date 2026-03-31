"""
app/graph.py
LangGraph 기반 RAG 챗봇 그래프
"""
from typing import TypedDict, Annotated
import operator

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.tools import rag_search
from app.config import OPENAI_API_KEY, OPENAI_MODEL


# ── State ─────────────────────────────────────────────────────────────────────

class RAGState(TypedDict):
    messages:   Annotated[list[BaseMessage], operator.add]
    tool_count: int


# ── LLM with tool binding ─────────────────────────────────────────────────────

llm = ChatOpenAI(
    model=OPENAI_MODEL,
    temperature=0,
    openai_api_key=OPENAI_API_KEY,
).bind_tools([rag_search])


# ── Nodes ─────────────────────────────────────────────────────────────────────

def call_llm(state: RAGState, config: RunnableConfig) -> dict:
    response = llm.invoke(state["messages"])
    return {"messages": [response], "tool_count": state["tool_count"]}


def call_tool(state: RAGState) -> dict:
    last = state["messages"][-1]
    results = []
    for call in last.tool_calls:
        if call["name"] == "rag_search":
            result = rag_search.invoke(call["args"]["query"])
            results.append(ToolMessage(content=result, tool_call_id=call["id"]))
    return {"messages": results, "tool_count": state["tool_count"] + 1}


def should_use_tool(state: RAGState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls and state["tool_count"] < 3:
        return "tool"
    return "end"


# ── Graph ─────────────────────────────────────────────────────────────────────

builder = StateGraph(RAGState)
builder.add_node("llm",  call_llm)
builder.add_node("tool", call_tool)

builder.set_entry_point("llm")
builder.add_conditional_edges("llm", should_use_tool, {"tool": "tool", "end": END})
builder.add_edge("tool", "llm")

memory = MemorySaver()
graph  = builder.compile(checkpointer=memory)
