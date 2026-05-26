from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from api.projects.a_maze_ing.grid_io import (
    deserialize_cells,
    serialize_cells,
    validate_coord,
)
from api.projects.a_maze_ing.schemas import MazeRequest, MazeSolveRequest
from backend.a_maze_ing.mazegen.algo.utils import GenerateMethod, SolveMethod
from backend.a_maze_ing.mazegen.generator import MazeGenerator
from backend.a_maze_ing.mazegen.solver import MazeSolver
from backend.a_maze_ing.mazegen.utils import MazeGrid


def build_maze(request: MazeRequest) -> dict:
    generated = generate_maze(request)
    grid = deserialize_cells(
        MazeSolveRequest(
            width=request.width,
            height=request.height,
            entry=request.entry,
            exit=request.exit,
            cells=generated["cells"],
            solve_algorithm=request.solve_algorithm,
        )
    )
    solved = solve_grid(
        grid=grid,
        entry=(request.entry.row, request.entry.col),
        exit_cell=(request.exit.row, request.exit.col),
        algorithm=SolveMethod(request.solve_algorithm),
    )
    generated["solve_steps"] = solved["solve_steps"]
    generated["path"] = solved["path"]
    generated["stats"]["visited_steps"] = solved["stats"]["visited_steps"]
    generated["stats"]["path_length"] = solved["stats"]["path_length"]
    return generated


def generate_maze(request: MazeRequest) -> dict:
    entry = (request.entry.row, request.entry.col)
    exit_cell = (request.exit.row, request.exit.col)
    validate_endpoints(entry, exit_cell, request.height, request.width)

    generation_steps: list[dict[str, Any]] = []
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
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {
        "config": request.model_dump(),
        "cells": serialize_cells(grid),
        "generation_steps": generation_steps,
        "solve_steps": [],
        "path": [],
        "stats": {
            "width": request.width,
            "height": request.height,
            "cells": request.width * request.height,
            "generation_steps": len(generation_steps),
            "visited_steps": 0,
            "path_length": 0,
        },
    }


def solve_maze(request: MazeSolveRequest) -> dict:
    entry = (request.entry.row, request.entry.col)
    exit_cell = (request.exit.row, request.exit.col)
    validate_endpoints(entry, exit_cell, request.height, request.width)
    return solve_grid(
        grid=deserialize_cells(request),
        entry=entry,
        exit_cell=exit_cell,
        algorithm=SolveMethod(request.solve_algorithm),
    )


def solve_grid(
    grid: MazeGrid,
    entry: tuple[int, int],
    exit_cell: tuple[int, int],
    algorithm: SolveMethod,
) -> dict:
    solve_steps: list[dict[str, int]] = []
    try:
        solver = MazeSolver(
            grid=grid,
            entry=entry,
            exit=exit_cell,
            algorithm=algorithm,
            trace=solve_steps,
        )
        path = solver.solve(None)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {
        "solve_steps": solve_steps,
        "path": [{"row": row, "col": col} for row, col in path],
        "stats": {
            "visited_steps": len(solve_steps),
            "path_length": len(path),
        },
    }


def validate_endpoints(
    entry: tuple[int, int],
    exit_cell: tuple[int, int],
    height: int,
    width: int,
) -> None:
    validate_coord(entry, height, width, "entry")
    validate_coord(exit_cell, height, width, "exit")
    if entry == exit_cell:
        raise HTTPException(status_code=400, detail="Entry and exit must be different cells.")
