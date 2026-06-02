from __future__ import annotations

from fastapi import APIRouter

from api.projects.trace_ops_agent.schemas import DiagnoseRequest, DiagnoseResponse
from api.projects.trace_ops_agent.service import diagnose_incident


router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "project": "trace-ops-agent"}


@router.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose(request: DiagnoseRequest) -> dict:
    return await diagnose_incident(request)
