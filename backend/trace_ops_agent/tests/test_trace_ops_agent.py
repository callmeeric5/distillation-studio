from __future__ import annotations

import pytest

from backend.trace_ops_agent.logs import new_diagnosis_id, normalize_logs
from backend.trace_ops_agent.parser import parse_diagnosis
from backend.trace_ops_agent.providers import validate_provider_model


def test_validate_provider_model_rejects_unsupported_model() -> None:
    with pytest.raises(ValueError):
        validate_provider_model("openai", "not-a-real-model")


def test_normalize_logs_assigns_stable_ids() -> None:
    diagnosis_id = new_diagnosis_id()
    logs = normalize_logs(
        diagnosis_id,
        "[2026-06-02T08:10:12Z] ERROR payment-service connection timeout",
    )

    assert logs[0].diagnosis_id == diagnosis_id
    assert logs[0].log_id == "log-0001"
    assert logs[0].level == "ERROR"
    assert logs[0].service == "payment-service"


def test_parse_diagnosis_reads_structured_json() -> None:
    result = parse_diagnosis(
        raw_text='{"summary":"latency spike","root_cause":"pool exhausted","evidence":["log-0001"],"recommended_actions":["scale pool"],"confidence":"high"}',
        reasoning_steps=["checked error summary"],
        tool_calls=["get_error_summary({})"],
    )

    assert result.summary == "latency spike"
    assert result.root_cause == "pool exhausted"
    assert result.evidence == ["log-0001"]
    assert result.recommended_actions == ["scale pool"]
    assert result.reasoning_steps == ["checked error summary"]
    assert result.tool_calls == ["get_error_summary({})"]
