from __future__ import annotations

from fastapi import APIRouter

from api.projects.push_swap.schemas import GenerateRequest, RunRequest
from api.projects.push_swap.service import generate_unique_values, run_push_swap


router = APIRouter()


@router.post("/run")
def run_sort(request: RunRequest) -> dict:
    moves = run_push_swap(request.values, request.algorithm)
    return {
        "values": request.values,
        "algorithm": request.algorithm,
        "moves": moves,
        "move_count": len(moves),
    }


@router.post("/generate")
def generate_values(request: GenerateRequest) -> dict:
    values = generate_unique_values(request.size, request.minimum, request.maximum)
    return {"values": values}
