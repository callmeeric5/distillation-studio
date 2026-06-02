from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


TraceProvider = Literal["openai", "gemini", "anthropic", "deepseek"]


class DiagnoseRequest(BaseModel):
    provider: TraceProvider
    model: str = Field(..., min_length=1)
    api_key: str = Field(..., min_length=1)
    incident: str = Field(..., min_length=1, max_length=6000)
    logs: str = Field("", max_length=20000)
    max_iterations: int = Field(6, ge=1, le=12)


class DiagnoseResponse(BaseModel):
    summary: str
    root_cause: str
    evidence: list[str]
    recommended_actions: list[str]
    confidence: str
    reasoning_steps: list[str]
    tool_calls: list[str]
    raw_text: str
