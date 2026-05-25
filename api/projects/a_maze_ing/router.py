from __future__ import annotations

from fastapi import APIRouter

from api.projects.a_maze_ing.schemas import MazeRequest
from api.projects.a_maze_ing.service import build_maze


router = APIRouter()


@router.post("/run")
def run_maze(request: MazeRequest) -> dict:
    return build_maze(request)
