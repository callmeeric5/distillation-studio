from __future__ import annotations

from fastapi import APIRouter

from api.projects.fly_in.schemas import MapListResponse, SimulationResponse
from api.projects.fly_in.service import list_maps, run_simulation


router = APIRouter()


@router.get("/maps", response_model=MapListResponse)
def get_maps() -> dict:
    return {"maps": list_maps()}


@router.get(
    "/maps/{difficulty}/{filename}/simulation",
    response_model=SimulationResponse,
)
def get_simulation(difficulty: str, filename: str) -> dict:
    return run_simulation(difficulty, filename)
