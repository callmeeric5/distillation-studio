from __future__ import annotations

import json
import re
from typing import Any

from backend.trace_ops_agent.models import DiagnosisResult


def parse_diagnosis(raw_text: str, reasoning_steps: list[str], tool_calls: list[str]) -> DiagnosisResult:
    payload = _extract_json(raw_text)
    if payload is None:
        return DiagnosisResult(
            summary=_fallback_summary(raw_text),
            root_cause="The model did not return a structured root cause.",
            evidence=[],
            recommended_actions=[],
            confidence="medium",
            reasoning_steps=reasoning_steps,
            tool_calls=tool_calls,
            raw_text=raw_text,
        )

    return DiagnosisResult(
        summary=_as_text(payload.get("summary"), "No summary returned."),
        root_cause=_as_text(payload.get("root_cause"), "No root cause returned."),
        evidence=_as_text_list(payload.get("evidence")),
        recommended_actions=_as_text_list(payload.get("recommended_actions")),
        confidence=_as_text(payload.get("confidence"), "medium"),
        reasoning_steps=reasoning_steps,
        tool_calls=tool_calls,
        raw_text=raw_text,
    )


def _extract_json(raw_text: str) -> dict[str, Any] | None:
    stripped = raw_text.strip()
    candidates = [stripped]

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL)
    if fenced:
        candidates.insert(0, fenced.group(1))

    object_match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
    if object_match:
        candidates.append(object_match.group(0))

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _as_text(value: object, fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _as_text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _fallback_summary(raw_text: str) -> str:
    text = " ".join(raw_text.split())
    if not text:
        return "No diagnosis returned."
    return text[:280]
