from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from backend.trace_ops_agent.models import DiagnosisRequest, DiagnosisResult
from backend.trace_ops_agent.parser import parse_diagnosis
from backend.trace_ops_agent.prompts import SYSTEM_PROMPT, build_user_prompt
from backend.trace_ops_agent.providers import build_chat_model
from backend.trace_ops_agent.storage import TraceLogRepository
from backend.trace_ops_agent.tools import build_log_tools


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    iterations: int


async def run_agent(
    request: DiagnosisRequest,
    diagnosis_id: str,
    repository: TraceLogRepository,
) -> DiagnosisResult:
    tools = build_log_tools(repository)
    chat_model = build_chat_model(request.provider, request.model, request.api_key)
    model_with_tools = chat_model.bind_tools(tools)

    async def reason(state: AgentState) -> dict[str, object]:
        response = await model_with_tools.ainvoke(state["messages"])
        return {
            "messages": [response],
            "iterations": state.get("iterations", 0) + 1,
        }

    def route(state: AgentState) -> str:
        if state.get("iterations", 0) >= request.max_iterations:
            return END
        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"
        return END

    graph = StateGraph(AgentState)
    graph.add_node("reason", reason)
    graph.add_node("tools", ToolNode(tools))
    graph.set_entry_point("reason")
    graph.add_conditional_edges("reason", route, {"tools": "tools", END: END})
    graph.add_edge("tools", "reason")

    app = graph.compile()
    final_state = await app.ainvoke(
        {
            "messages": [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=build_user_prompt(request.incident)),
            ],
            "iterations": 0,
        }
    )
    messages = final_state["messages"]
    raw_text = _last_ai_text(messages)
    return parse_diagnosis(
        raw_text=raw_text,
        reasoning_steps=_reasoning_steps(messages),
        tool_calls=_tool_calls(messages),
    )


def _last_ai_text(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            return _content_to_text(message.content)
    return ""


def _reasoning_steps(messages: list[BaseMessage]) -> list[str]:
    steps: list[str] = []
    for message in messages:
        if isinstance(message, AIMessage):
            text = _content_to_text(message.content)
            if text:
                steps.append(text)
    return steps


def _tool_calls(messages: list[BaseMessage]) -> list[str]:
    calls: list[str] = []
    for message in messages:
        if isinstance(message, AIMessage) and message.tool_calls:
            for call in message.tool_calls:
                name = str(call.get("name", "tool"))
                args = call.get("args", {})
                calls.append(f"{name}({args})")
        elif isinstance(message, ToolMessage):
            content = _content_to_text(message.content)
            calls.append(f"{message.name or 'tool'} -> {content[:500]}")
    return calls


def _content_to_text(content: object) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts).strip()
    return str(content).strip()
