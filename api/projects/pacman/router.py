from __future__ import annotations

from fastapi import APIRouter, Query

from api.projects.pacman.schemas import (
    PacmanConfigResponse,
    PacmanLevelResponse,
    PacmanScore,
    PacmanScoreCreate,
    PacmanScoresResponse,
)
from api.projects.pacman.service import create_score, get_config, get_level, get_scores


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
