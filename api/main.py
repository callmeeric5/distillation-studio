from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.projects.registry import PROJECT_ROUTERS
from api.projects.agent_smith.service import run_manager


@asynccontextmanager
async def lifespan(_: FastAPI):
    await run_manager.start()
    try:
        yield
    finally:
        await run_manager.stop()


app = FastAPI(title="Distillation Studio API", lifespan=lifespan)

for project_router in PROJECT_ROUTERS:
    app.include_router(project_router.router, prefix=project_router.prefix)
