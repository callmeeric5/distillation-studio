from __future__ import annotations

from fastapi import APIRouter

from api.projects.codexion.schemas import RunRequest, RunResponse
from api.projects.codexion.service import run_codexion


router = APIRouter()


@router.post("/run", response_model=RunResponse)
def run_simulation(request: RunRequest) -> dict:
    return run_codexion(request)
