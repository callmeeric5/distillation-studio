from __future__ import annotations

from fastapi import APIRouter

from api.projects.call_me_maybe.schemas import (
    FunctionCallRequest,
    FunctionCallResponse,
)
from api.projects.call_me_maybe.service import run_call_me_maybe


router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "project": "call-me-maybe"}


@router.post("/run", response_model=FunctionCallResponse)
def run(request: FunctionCallRequest) -> dict:
    return run_call_me_maybe(request)
