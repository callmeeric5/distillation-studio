from __future__ import annotations

from fastapi import APIRouter

from api.projects.a_maze_ing.schemas import MazeRequest, MazeSolveRequest
from api.projects.a_maze_ing.service import build_maze, generate_maze, solve_maze


router = APIRouter()


@router.post("/run")
def run_maze(request: MazeRequest) -> dict:
    return build_maze(request)


@router.post("/generate")
def generate_current_maze(request: MazeRequest) -> dict:
    return generate_maze(request)


@router.post("/solve")
def solve_current_maze(request: MazeSolveRequest) -> dict:
    return solve_maze(request)
