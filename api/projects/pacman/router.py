from __future__ import annotations

import asyncio
from time import monotonic

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from api.projects.pacman.schemas import (
    PacmanConfigResponse,
    PacmanLevelResponse,
    PacmanRunCreate,
    PacmanRunInput,
    PacmanRunSnapshot,
    PacmanRunTick,
    PacmanScore,
    PacmanScoreCreate,
    PacmanScoresResponse,
)
from api.projects.pacman.service import (
    create_run,
    create_run_score,
    create_score,
    get_config,
    get_level,
    get_run_or_raise,
    get_scores,
    restart_run,
    tick_run,
    update_run_input,
)


router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "project": "pacman"}


@router.get("/config", response_model=PacmanConfigResponse)
async def config() -> dict:
    return get_config()


@router.get("/levels/{level_index}", response_model=PacmanLevelResponse)
async def level(level_index: int) -> dict:
    return get_level(level_index)


@router.get("/scores", response_model=PacmanScoresResponse)
async def scores(limit: int = Query(10, ge=1, le=50)) -> dict:
    return {"scores": await get_scores(limit)}


@router.post("/scores", response_model=PacmanScore)
async def submit_score(score: PacmanScoreCreate) -> dict:
    return await create_score(score)


@router.post("/runs", response_model=PacmanRunSnapshot)
async def start_run(payload: PacmanRunCreate) -> dict:
    return create_run(payload)


@router.post("/runs/{run_id}/input", response_model=PacmanRunSnapshot)
async def run_input(run_id: str, payload: PacmanRunInput) -> dict:
    return update_run_input(run_id, payload)


@router.post("/runs/{run_id}/tick", response_model=PacmanRunSnapshot)
async def run_tick(run_id: str, payload: PacmanRunTick) -> dict:
    return tick_run(run_id, payload)


@router.post("/runs/{run_id}/restart", response_model=PacmanRunSnapshot)
async def run_restart(run_id: str, payload: PacmanRunCreate | None = None) -> dict:
    return restart_run(run_id, payload)


@router.post("/runs/{run_id}/scores", response_model=PacmanScore)
async def submit_run_score(run_id: str) -> dict:
    return await create_run_score(run_id)


@router.websocket("/runs/{run_id}/stream")
async def run_stream(websocket: WebSocket, run_id: str) -> None:
    await websocket.accept()
    try:
        run = get_run_or_raise(run_id)
    except Exception as exc:
        await websocket.send_json({"kind": "error", "detail": str(exc)})
        await websocket.close(code=1008)
        return

    tick_seconds = 1 / 30
    last_tick_at = monotonic()
    last_level_index = run.level_index
    await websocket.send_json({"kind": "snapshot", "data": run.snapshot()})

    try:
        while True:
            timeout = max(0.0, tick_seconds - (monotonic() - last_tick_at))
            try:
                message = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=timeout,
                )
                _apply_stream_message(run, message)
                continue
            except asyncio.TimeoutError:
                now = monotonic()
                delta = min(now - last_tick_at, tick_seconds * 2)
                last_tick_at = now

            previous_level_index = run.level_index
            run.tick(delta)
            if run.level_index != last_level_index or run.level_index != previous_level_index:
                last_level_index = run.level_index
                await websocket.send_json({"kind": "snapshot", "data": run.snapshot()})
            else:
                await websocket.send_json({"kind": "frame", "data": run.frame_snapshot()})

            if run.status in {"won", "lost"}:
                break
    except WebSocketDisconnect:
        return


def _apply_stream_message(run, message: dict) -> None:
    direction = message.get("direction")
    if isinstance(direction, str):
        run.request_direction(direction)

    paused = message.get("paused")
    if isinstance(paused, bool):
        run.set_paused(paused)

    cheat_mode = message.get("cheat_mode")
    if isinstance(cheat_mode, bool):
        run.set_cheat_mode(cheat_mode)
