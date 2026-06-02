from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


ProviderName = Literal["openai", "gemini", "anthropic", "deepseek"]


@dataclass(frozen=True)
class DiagnosisRequest:
    provider: ProviderName
    model: str
    api_key: str
    incident: str
    logs: str = ""
    max_iterations: int = 6


@dataclass(frozen=True)
class LogEntry:
    diagnosis_id: str
    log_id: str
    timestamp: str | None
    level: str
    service: str
    message: str
    raw: str


@dataclass
class DiagnosisResult:
    summary: str
    root_cause: str
    evidence: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
    confidence: str = "medium"
    reasoning_steps: list[str] = field(default_factory=list)
    tool_calls: list[str] = field(default_factory=list)
    raw_text: str = ""
