from __future__ import annotations

import asyncio
from contextlib import suppress

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from api.projects.tap.schemas import TapWorldResponse
from api.projects.tap.service import get_world, tap_server_manager, validate_browser_command


router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    try:
        await tap_server_manager.ensure_running()
    except RuntimeError as exc:
        return {"status": "unavailable", "project": "tap", "detail": str(exc)}
    return {"status": "ok", "project": "tap"}


@router.get("/world", response_model=TapWorldResponse)
async def world() -> dict:
    return get_world()


@router.websocket("/session")
async def session(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        await tap_server_manager.ensure_running()
        reader, writer = await asyncio.open_connection(*tap_server_manager.address)
    except (ConnectionError, OSError, RuntimeError) as exc:
        await websocket.send_json({"kind": "gateway_error", "detail": str(exc)})
        await websocket.close(code=1011)
        return

    async def browser_to_tap() -> None:
        while True:
            try:
                payload = await websocket.receive_json()
            except WebSocketDisconnect:
                return
            except Exception:
                await websocket.send_json(
                    {"kind": "gateway_error", "detail": "Expected a JSON command message."}
                )
                continue
            try:
                line = validate_browser_command(payload)
            except ValueError as exc:
                await websocket.send_json({"kind": "gateway_error", "detail": str(exc)})
                continue
            writer.write(line.encode("utf-8") + b"\n")
            await writer.drain()

    async def tap_to_browser() -> None:
        while line := await reader.readline():
            await websocket.send_json(
                {"kind": "protocol", "line": line.decode("utf-8", "replace").rstrip("\r\n")}
            )

    tasks = [asyncio.create_task(browser_to_tap()), asyncio.create_task(tap_to_browser())]
    try:
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            with suppress(WebSocketDisconnect, ConnectionError):
                task.result()
        for task in pending:
            task.cancel()
        for task in pending:
            with suppress(asyncio.CancelledError):
                await task
    finally:
        writer.close()
        with suppress(ConnectionError):
            await writer.wait_closed()
        if websocket.client_state == WebSocketState.CONNECTED:
            with suppress(WebSocketDisconnect, RuntimeError):
                await websocket.send_json({"kind": "disconnected", "detail": "TAP session closed."})
                await websocket.close()
