from __future__ import annotations

from fastapi import FastAPI

from api.projects.a_maze_ing.router import router as a_maze_ing_router
from api.projects.push_swap.router import router as push_swap_router


app = FastAPI(title="Distillation Studio API")

app.include_router(a_maze_ing_router, prefix="/api/projects/a-maze-ing")
app.include_router(push_swap_router, prefix="/api/projects/push-swap")
