from __future__ import annotations

from fastapi import APIRouter, Query

from api.projects.pacman.schemas import (
    PacmanConfigResponse,
    PacmanLevelResponse,
    PacmanRunCreate,
    PacmanRunInput,
    PacmanRunSnapshot,
    PacmanRunTick,
    PacmanScore,
    PacmanScoreCreate,
    PacmanScoresResponse,
)
from api.projects.pacman.service import (
    create_run,
    create_run_score,
    create_score,
    get_config,
    get_level,
    get_scores,
    restart_run,
    tick_run,
    update_run_input,
)


router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "project": "pacman"}


@router.get("/config", response_model=PacmanConfigResponse)
async def config() -> dict:
    return get_config()


@router.get("/levels/{level_index}", response_model=PacmanLevelResponse)
async def level(level_index: int) -> dict:
    return get_level(level_index)


@router.get("/scores", response_model=PacmanScoresResponse)
async def scores(limit: int = Query(10, ge=1, le=50)) -> dict:
    return {"scores": await get_scores(limit)}


@router.post("/scores", response_model=PacmanScore)
async def submit_score(score: PacmanScoreCreate) -> dict:
    return await create_score(score)


@router.post("/runs", response_model=PacmanRunSnapshot)
async def start_run(payload: PacmanRunCreate) -> dict:
    return create_run(payload)


@router.post("/runs/{run_id}/input", response_model=PacmanRunSnapshot)
async def run_input(run_id: str, payload: PacmanRunInput) -> dict:
    return update_run_input(run_id, payload)


@router.post("/runs/{run_id}/tick", response_model=PacmanRunSnapshot)
async def run_tick(run_id: str, payload: PacmanRunTick) -> dict:
    return tick_run(run_id, payload)


@router.post("/runs/{run_id}/restart", response_model=PacmanRunSnapshot)
async def run_restart(run_id: str, payload: PacmanRunCreate | None = None) -> dict:
    return restart_run(run_id, payload)


@router.post("/runs/{run_id}/scores", response_model=PacmanScore)
async def submit_run_score(run_id: str) -> dict:
    return await create_run_score(run_id)
