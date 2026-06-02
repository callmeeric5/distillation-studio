from __future__ import annotations

import logging

from fastapi import HTTPException

from api.projects.trace_ops_agent.schemas import DiagnoseRequest
from backend.trace_ops_agent.models import DiagnosisRequest
from backend.trace_ops_agent.providers import validate_provider_model
from backend.trace_ops_agent.service import diagnose


logger = logging.getLogger(__name__)


async def diagnose_incident(request: DiagnoseRequest) -> dict:
    incident = request.incident.strip()
    api_key = request.api_key.strip()
    if not incident:
        raise HTTPException(status_code=400, detail="Incident description is required.")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required.")

    try:
        provider = validate_provider_model(request.provider, request.model)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    try:
        result = await diagnose(
            DiagnosisRequest(
                provider=provider,
                model=request.model,
                api_key=api_key,
                incident=incident,
                logs=request.logs,
                max_iterations=request.max_iterations,
            )
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        logger.exception(
            "Trace-Ops agent run failed for provider=%s model=%s",
            request.provider,
            request.model,
        )
        detail = str(error).strip() or error.__class__.__name__
        raise HTTPException(status_code=500, detail=f"Trace-Ops agent run failed: {detail}") from error

    return {
        "summary": result.summary,
        "root_cause": result.root_cause,
        "evidence": result.evidence,
        "recommended_actions": result.recommended_actions,
        "confidence": result.confidence,
        "reasoning_steps": result.reasoning_steps,
        "tool_calls": result.tool_calls,
        "raw_text": result.raw_text,
    }
