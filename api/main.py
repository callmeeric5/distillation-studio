from __future__ import annotations

from fastapi import FastAPI

from api.projects.registry import PROJECT_ROUTERS


app = FastAPI(title="Distillation Studio API")

for project_router in PROJECT_ROUTERS:
    app.include_router(project_router.router, prefix=project_router.prefix)
