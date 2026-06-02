from __future__ import annotations

from backend.trace_ops_agent.graph import run_agent
from backend.trace_ops_agent.logs import new_diagnosis_id, normalize_logs
from backend.trace_ops_agent.models import DiagnosisRequest, DiagnosisResult
from backend.trace_ops_agent.providers import validate_provider_model
from backend.trace_ops_agent.storage import TraceLogRepository


async def diagnose(request: DiagnosisRequest) -> DiagnosisResult:
    provider = validate_provider_model(request.provider, request.model)
    normalized_request = DiagnosisRequest(
        provider=provider,
        model=request.model,
        api_key=request.api_key,
        incident=request.incident,
        logs=request.logs,
        max_iterations=request.max_iterations,
    )
    diagnosis_id = new_diagnosis_id()
    repository = TraceLogRepository(diagnosis_id)
    await repository.insert_logs(normalize_logs(diagnosis_id, request.logs))
    return await run_agent(normalized_request, diagnosis_id, repository)
