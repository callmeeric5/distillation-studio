from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from api.projects.a_maze_ing.schemas import MazeRequest


A_MAZE_ING_DIR = Path(__file__).resolve().parents[3] / "backend" / "a-maze-ing"
if str(A_MAZE_ING_DIR) not in sys.path:
    sys.path.insert(0, str(A_MAZE_ING_DIR))

from mazegen.algo.utils import GenerateMethod, SolveMethod  # noqa: E402
from mazegen.generator import MazeGenerator  # noqa: E402
from mazegen.solver import MazeSolver  # noqa: E402
from mazegen.utils import MazeGrid  # noqa: E402


WALL_NAMES = ["north", "east", "south", "west"]


def build_maze(request: MazeRequest) -> dict:
    entry = (request.entry.row, request.entry.col)
    exit_cell = (request.exit.row, request.exit.col)
    validate_coord(entry, request.height, request.width, "entry")
    validate_coord(exit_cell, request.height, request.width, "exit")
    if entry == exit_cell:
        raise HTTPException(status_code=400, detail="Entry and exit must be different cells.")

    generation_steps: list[dict[str, Any]] = []
    solve_steps: list[dict[str, int]] = []

    try:
        generator = MazeGenerator(
            width=request.width,
            height=request.height,
            entry=entry,
            exit=exit_cell,
            output_file="",
            algorithm=GenerateMethod(request.generate_algorithm),
            seed=request.seed,
            perfect=request.perfect,
            display_42=request.display_42,
            trace=generation_steps,
        )
        grid = generator.generate(None)
        solver = MazeSolver(
            grid=grid,
            entry=entry,
            exit=exit_cell,
            algorithm=SolveMethod(request.solve_algorithm),
            trace=solve_steps,
        )
        path = solver.solve(None)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {
        "config": request.model_dump(),
        "cells": serialize_cells(grid),
        "generation_steps": generation_steps,
        "solve_steps": solve_steps,
        "path": [{"row": row, "col": col} for row, col in path],
        "stats": {
            "width": request.width,
            "height": request.height,
            "cells": request.width * request.height,
            "generation_steps": len(generation_steps),
            "visited_steps": len(solve_steps),
            "path_length": len(path),
        },
    }


def validate_coord(coord: tuple[int, int], height: int, width: int, name: str) -> None:
    row, col = coord
    if not (0 <= row < height and 0 <= col < width):
        raise HTTPException(status_code=400, detail=f"{name} must be inside the maze.")


def serialize_cells(grid: MazeGrid) -> list[dict]:
    height, width = grid.shape
    return [
        {
            "row": row,
            "col": col,
            "blocked": bool(grid.blocked[row, col]),
            "walls": {
                name: bool(grid.walls[row, col, index])
                for index, name in enumerate(WALL_NAMES)
            },
        }
        for row in range(height)
        for col in range(width)
    ]
