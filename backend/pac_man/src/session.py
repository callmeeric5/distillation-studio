from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from uuid import uuid4

from backend.pac_man.src.level import Level
from backend.pac_man.src.parser import Config
from backend.pac_man.src.utils import DIRECTION


RUN_TTL_SECONDS = 60 * 30
MAX_TICK_SECONDS = 0.08
PLAYER_SPEED = 7.0
GHOST_SPEED = 4.5


class PacmanSessionError(ValueError):
    """Raised when a Pac-Man run cannot be updated."""


@dataclass
class PacmanRun:
    player_name: str
    config: Config
    cheat_mode: bool = False
    run_id: str = field(default_factory=lambda: uuid4().hex)
    level_index: int = 0
    total_elapsed_seconds: float = 0.0
    status: str = "playing"
    cheat_used: bool = False
    score_saved: bool = False
    last_seen: float = field(default_factory=monotonic)
    _level: Level = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.player_name = self.player_name.strip()
        if not self.player_name:
            raise PacmanSessionError("Player name is required.")
        self.cheat_used = self.cheat_mode
        self._level = self._build_level(self.level_index)

    @property
    def level(self) -> Level:
        return self._level

    def request_direction(self, direction: str) -> None:
        parsed = _parse_direction(direction)
        self.last_seen = monotonic()
        self.level.player.set_direction(parsed)
        if self.status == "paused":
            self.status = "playing"

    def set_paused(self, paused: bool) -> None:
        self.last_seen = monotonic()
        if self.status in {"won", "lost"}:
            return
        self.status = "paused" if paused else "playing"

    def set_cheat_mode(self, cheat_mode: bool) -> None:
        self.last_seen = monotonic()
        self.cheat_mode = cheat_mode
        self.cheat_used = self.cheat_used or cheat_mode
        self.level.is_cheat_mode = cheat_mode

    def tick(self, delta_seconds: float) -> None:
        self.last_seen = monotonic()
        if self.status != "playing":
            return

        delta = min(max(delta_seconds, 0.0), MAX_TICK_SECONDS)
        self.total_elapsed_seconds += delta
        self.level.on_update(delta)

        if self.level.game_over:
            self.status = "lost"
            return

        if not self.level.win:
            return

        previous_level_index = self.level_index
        if self.level_index >= len(self.config.levels) - 1:
            self.status = "won"
            return

        previous_score = self.level.player.score
        previous_lives = self.level.player.lives
        self.level_index += 1
        self._level = self._build_level(
            self.level_index,
            initial_score=previous_score,
            initial_lives=previous_lives,
        )
        if self.level_index != previous_level_index:
            self.last_seen = monotonic()

    def restart(self, cheat_mode: bool | None = None) -> None:
        self.last_seen = monotonic()
        if not self.player_name.strip():
            raise PacmanSessionError("Player name is required.")
        self.player_name = self.player_name.strip()
        if cheat_mode is not None:
            self.cheat_mode = cheat_mode
        self.cheat_used = self.cheat_mode
        self.score_saved = False
        self.level_index = 0
        self.total_elapsed_seconds = 0.0
        self.status = "playing"
        self._level = self._build_level(0)

    def snapshot(self) -> dict:
        level = self.level
        status_text = {
            "playing": "Playing",
            "paused": "Paused",
            "won": "Run complete",
            "lost": "Game over",
        }.get(self.status, "Playing")
        return {
            "run_id": self.run_id,
            "player_name": self.player_name,
            "status": self.status,
            "status_text": status_text,
            "completed": self.status == "won",
            "score_eligible": (
                not self.cheat_used
                and not self.score_saved
                and self.status in {"won", "lost"}
            ),
            "cheat_mode": self.cheat_mode,
            "cheat_used": self.cheat_used,
            "level": self.level_index + 1,
            "level_index": self.level_index,
            "level_count": len(self.config.levels),
            "score": level.player.score,
            "lives": level.player.lives,
            "time_left": max(0, int(level.time_left + 0.999)),
            "elapsed_seconds": int(self.total_elapsed_seconds + 0.5),
            "width": level.maze.width,
            "height": level.maze.height,
            "seed": level.level_config.seed,
            "points": {
                "pacgum": self.config.points_per_pacgum,
                "super_pacgum": self.config.points_per_super_pacgum,
                "ghost": self.config.points_per_ghost,
            },
            "cells": [
                [
                    {
                        "row": row_index,
                        "col": col_index,
                        "walls": _cell_walls(cell),
                        "is_42_pattern": cell.is_42_pattern,
                    }
                    for col_index, cell in enumerate(row)
                ]
                for row_index, row in enumerate(level.maze.cells)
            ],
            "player": {
                "row": level.player.row,
                "col": level.player.col,
                "pos_row": level.player.pos.x,
                "pos_col": level.player.pos.y,
                "direction": level.player.direction.value,
            },
            "ghosts": [
                {
                    "row": ghost.row,
                    "col": ghost.col,
                    "pos_row": ghost.pos.x,
                    "pos_col": ghost.pos.y,
                    "home_row": ghost.home.x,
                    "home_col": ghost.home.y,
                    "state": ghost.state.value,
                    "direction": ghost.direction.value,
                }
                for ghost in level.ghosts
            ],
            "pacgums": [
                {"row": pacgum.pos.x, "col": pacgum.pos.y, "points": pacgum.points}
                for pacgum in level.pacgums
            ],
            "super_pacgums": [
                {"row": pacgum.pos.x, "col": pacgum.pos.y, "points": pacgum.points}
                for pacgum in level.super_pacgums
            ],
        }

    def frame_snapshot(self) -> dict:
        level = self.level
        status_text = {
            "playing": "Playing",
            "paused": "Paused",
            "won": "Run complete",
            "lost": "Game over",
        }.get(self.status, "Playing")
        return {
            "run_id": self.run_id,
            "player_name": self.player_name,
            "status": self.status,
            "status_text": status_text,
            "completed": self.status == "won",
            "score_eligible": (
                not self.cheat_used
                and not self.score_saved
                and self.status in {"won", "lost"}
            ),
            "cheat_mode": self.cheat_mode,
            "cheat_used": self.cheat_used,
            "level": self.level_index + 1,
            "level_index": self.level_index,
            "level_count": len(self.config.levels),
            "score": level.player.score,
            "lives": level.player.lives,
            "time_left": max(0, int(level.time_left + 0.999)),
            "elapsed_seconds": int(self.total_elapsed_seconds + 0.5),
            "player": {
                "row": level.player.row,
                "col": level.player.col,
                "pos_row": level.player.pos.x,
                "pos_col": level.player.pos.y,
                "direction": level.player.direction.value,
            },
            "ghosts": [
                {
                    "row": ghost.row,
                    "col": ghost.col,
                    "pos_row": ghost.pos.x,
                    "pos_col": ghost.pos.y,
                    "home_row": ghost.home.x,
                    "home_col": ghost.home.y,
                    "state": ghost.state.value,
                    "direction": ghost.direction.value,
                }
                for ghost in level.ghosts
            ],
            "pacgums": [
                {"row": pacgum.pos.x, "col": pacgum.pos.y, "points": pacgum.points}
                for pacgum in level.pacgums
            ],
            "super_pacgums": [
                {"row": pacgum.pos.x, "col": pacgum.pos.y, "points": pacgum.points}
                for pacgum in level.super_pacgums
            ],
        }

    def _build_level(
        self,
        level_index: int,
        initial_score: int = 0,
        initial_lives: int | None = None,
    ) -> Level:
        level = Level(
            level_index,
            self.config,
            player_speed=PLAYER_SPEED,
            ghost_speed=GHOST_SPEED + min(level_index, 5) * 0.25,
            is_cheat_mode=self.cheat_mode,
        )
        level.player.score = initial_score
        if initial_lives is not None:
            level.player.lives = initial_lives
            level.player.is_alive = initial_lives > 0
        return level


class PacmanRunStore:
    def __init__(self) -> None:
        self._runs: dict[str, PacmanRun] = {}

    def create(self, player_name: str, config: Config, cheat_mode: bool) -> PacmanRun:
        self.prune()
        run = PacmanRun(player_name=player_name, config=config, cheat_mode=cheat_mode)
        self._runs[run.run_id] = run
        return run

    def get(self, run_id: str) -> PacmanRun:
        self.prune()
        run = self._runs.get(run_id)
        if run is None:
            raise PacmanSessionError("Pac-Man run was not found or has expired.")
        run.last_seen = monotonic()
        return run

    def prune(self) -> None:
        cutoff = monotonic() - RUN_TTL_SECONDS
        expired = [run_id for run_id, run in self._runs.items() if run.last_seen < cutoff]
        for run_id in expired:
            self._runs.pop(run_id, None)


def _parse_direction(direction: str) -> DIRECTION:
    try:
        return DIRECTION(direction)
    except ValueError as exc:
        raise PacmanSessionError("Unsupported direction.") from exc


def _cell_walls(cell) -> int:
    walls = 0
    if cell.north_wall:
        walls |= 1
    if cell.east_wall:
        walls |= 2
    if cell.south_wall:
        walls |= 4
    if cell.west_wall:
        walls |= 8
    return walls
