from __future__ import annotations

import numpy as np
from fastapi import HTTPException

from api.projects.a_maze_ing.schemas import MazeSolveRequest
from backend.a_maze_ing.mazegen.utils import MazeGrid


WALL_NAMES = ["north", "east", "south", "west"]
WALL_INDEX = {"north": 0, "east": 1, "south": 2, "west": 3}


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


def deserialize_cells(request: MazeSolveRequest) -> MazeGrid:
    expected = request.width * request.height
    if len(request.cells) != expected:
        raise HTTPException(status_code=400, detail="Maze cell payload does not match dimensions.")

    walls = np.ones((request.height, request.width, 4), dtype=bool)
    blocked = np.zeros((request.height, request.width), dtype=bool)
    seen: set[tuple[int, int]] = set()

    for cell in request.cells:
        coord = (cell.row, cell.col)
        validate_coord(coord, request.height, request.width, "cell")
        if coord in seen:
            raise HTTPException(status_code=400, detail="Maze cell payload contains duplicate cells.")
        seen.add(coord)
        blocked[cell.row, cell.col] = cell.blocked
        wall_values = cell.walls.model_dump()
        for name, index in WALL_INDEX.items():
            walls[cell.row, cell.col, index] = wall_values[name]

    return MazeGrid(walls=walls, blocked=blocked)


def validate_coord(coord: tuple[int, int], height: int, width: int, name: str) -> None:
    row, col = coord
    if not (0 <= row < height and 0 <= col < width):
        raise HTTPException(status_code=400, detail=f"{name} must be inside the maze.")
