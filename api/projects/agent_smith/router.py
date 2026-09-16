from __future__ import annotations

from fastapi import APIRouter, Query, status

from api.projects.agent_smith.schemas import (
    RunCreateRequest,
    RunCreatedResponse,
    RunStatusResponse,
)
from api.projects.agent_smith.service import run_manager


router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "project": "agent-smith"}


@router.get("/options")
async def options() -> dict:
    return run_manager.options()


@router.post(
    "/runs",
    response_model=RunCreatedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_run(request: RunCreateRequest) -> dict[str, str]:
    job = run_manager.create(request)
    return {"run_id": job.run_id, "status": "queued"}


@router.get("/runs/{run_id}", response_model=RunStatusResponse)
async def get_run(
    run_id: str, after_step: int = Query(default=0, ge=0)
) -> dict:
    return run_manager.status(run_id, after_step=after_step)


@router.delete("/runs/{run_id}", response_model=RunStatusResponse)
async def cancel_run(run_id: str) -> dict:
    return run_manager.cancel(run_id)
