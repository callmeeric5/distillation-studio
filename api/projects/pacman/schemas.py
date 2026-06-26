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


class PacmanRunCreate(BaseModel):
    player_name: str = Field(..., min_length=1, max_length=32)
    cheat_mode: bool = False


class PacmanRunInput(BaseModel):
    direction: str | None = None
    paused: bool | None = None
    cheat_mode: bool | None = None


class PacmanRunTick(BaseModel):
    delta_seconds: float = Field(..., ge=0, le=1)


class PacmanActorPosition(BaseModel):
    row: float
    col: float
    pos_row: int
    pos_col: int
    direction: str


class PacmanGhostSnapshot(PacmanActorPosition):
    home_row: int
    home_col: int
    state: str


class PacmanRunSnapshot(BaseModel):
    run_id: str
    player_name: str
    status: str
    status_text: str
    completed: bool
    score_eligible: bool
    score_saved: bool
    score_save_error: str | None = None
    cheat_mode: bool
    cheat_used: bool
    level: int
    level_index: int
    level_count: int
    score: int
    lives: int
    time_left: int
    elapsed_seconds: int
    width: int
    height: int
    seed: int | None = None
    points: PacmanPointsConfig
    cells: list[list[PacmanCell]]
    player: PacmanActorPosition
    ghosts: list[PacmanGhostSnapshot]
    pacgums: list[PacmanCollectible]
    super_pacgums: list[PacmanCollectible]


class PacmanRunFrame(BaseModel):
    run_id: str
    player_name: str
    status: str
    status_text: str
    completed: bool
    score_eligible: bool
    score_saved: bool
    score_save_error: str | None = None
    cheat_mode: bool
    cheat_used: bool
    level: int
    level_index: int
    level_count: int
    score: int
    lives: int
    time_left: int
    elapsed_seconds: int
    player: PacmanActorPosition
    ghosts: list[PacmanGhostSnapshot]
    pacgums: list[PacmanCollectible]
    super_pacgums: list[PacmanCollectible]
