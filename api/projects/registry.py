from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter

from api.projects.a_maze_ing.router import router as a_maze_ing_router
from api.projects.push_swap.router import router as push_swap_router


@dataclass(frozen=True)
class ProjectRouter:
    prefix: str
    router: APIRouter


PROJECT_ROUTERS = [
    ProjectRouter(prefix="/api/projects/a-maze-ing", router=a_maze_ing_router),
    ProjectRouter(prefix="/api/projects/push-swap", router=push_swap_router),
]
