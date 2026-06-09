from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PacmanScoreCreate(BaseModel):
    player_name: str = Field(..., min_length=1, max_length=32)
    score: int = Field(..., ge=0, le=10_000_000)
    elapsed_seconds: int = Field(..., ge=0, le=86_400)
    level_reached: int = Field(..., ge=1, le=100)
    completed: bool = False


class PacmanScore(PacmanScoreCreate):
    id: int
    created_at: datetime


class PacmanScoresResponse(BaseModel):
    scores: list[PacmanScore]


class PacmanLevelConfig(BaseModel):
    width: int
    height: int
    seed: int | None = None


class PacmanPointsConfig(BaseModel):
    pacgum: int
    super_pacgum: int
    ghost: int


class PacmanWindowConfig(BaseModel):
    width: int
    height: int
    fps: int


class PacmanConfigResponse(BaseModel):
    levels: list[PacmanLevelConfig]
    level_max_time: int
    lives: int
    pacgum: int
    points: PacmanPointsConfig
    window: PacmanWindowConfig


class PacmanCell(BaseModel):
    row: int
    col: int
    walls: int
    is_42_pattern: bool


class PacmanPosition(BaseModel):
    row: int
    col: int


class PacmanGhostInit(BaseModel):
    row: int
    col: int
    home_row: int
    home_col: int
    state: str


class PacmanCollectible(BaseModel):
    row: int
    col: int
    points: int


class PacmanLevelResponse(BaseModel):
    level_index: int
    width: int
    height: int
    seed: int | None = None
    time_limit: int
    lives: int
    pacgum_count: int
    points: PacmanPointsConfig
    cells: list[list[PacmanCell]]
    player: PacmanPosition
    ghosts: list[PacmanGhostInit]
    pacgums: list[PacmanCollectible]
    super_pacgums: list[PacmanCollectible]
