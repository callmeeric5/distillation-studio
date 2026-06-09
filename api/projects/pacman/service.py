from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException

from api.projects.pacman.schemas import PacmanScoreCreate
from backend.pac_man.src.level import Level
from backend.pac_man.src.parser import Config, Parser
from api.projects.pacman.storage import insert_score, list_scores


CONFIG_PATH = Path(__file__).resolve().parents[3] / "backend" / "pac_man" / "config.json"


def _load_config() -> Config:
    return Parser(str(CONFIG_PATH)).load()


def get_config() -> dict:
    config = _load_config()
    return {
        "levels": [
            {"width": level.width, "height": level.height, "seed": level.seed}
            for level in config.levels
        ],
        "level_max_time": config.level_max_time,
        "lives": config.lives,
        "pacgum": config.pacgum,
        "points": {
            "pacgum": config.points_per_pacgum,
            "super_pacgum": config.points_per_super_pacgum,
            "ghost": config.points_per_ghost,
        },
        "window": {
            "width": config.window_width,
            "height": config.window_height,
            "fps": config.fps,
        },
    }


def get_level(level_index: int) -> dict:
    config = _load_config()
    if level_index < 0 or level_index >= len(config.levels):
        raise HTTPException(status_code=404, detail="Pac-Man level does not exist.")

    level = Level(level_index, config)
    return {
        "level_index": level_index,
        "width": level.maze.width,
        "height": level.maze.height,
        "seed": level.level_config.seed,
        "time_limit": config.level_max_time,
        "lives": config.lives,
        "pacgum_count": config.pacgum,
        "points": {
            "pacgum": config.points_per_pacgum,
            "super_pacgum": config.points_per_super_pacgum,
            "ghost": config.points_per_ghost,
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
        "player": {"row": level.player.pos.x, "col": level.player.pos.y},
        "ghosts": [
            {
                "row": ghost.pos.x,
                "col": ghost.pos.y,
                "home_row": ghost.home.x,
                "home_col": ghost.home.y,
                "state": ghost.state.value,
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


def _serialize_score(row) -> dict:
    return {
        "id": row.id,
        "player_name": row.player_name,
        "score": row.score,
        "elapsed_seconds": row.elapsed_seconds,
        "level_reached": row.level_reached,
        "completed": row.completed,
        "created_at": row.created_at,
    }


async def create_score(score: PacmanScoreCreate) -> dict:
    row = await insert_score(score)
    return _serialize_score(row)


async def get_scores(limit: int = 10) -> list[dict]:
    return [_serialize_score(row) for row in await list_scores(limit)]
