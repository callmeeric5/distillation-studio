from __future__ import annotations

import asyncio
import socket
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.projects.tap.router as tap_router_module
from api.projects.tap.service import (
    DEFAULT_WORLD_PATH,
    LOCAL_BINARY_PATH,
    TapServerManager,
    get_world,
    validate_browser_command,
)


def test_world_metadata_is_safe_and_complete() -> None:
    world = get_world()
    assert world["start_room"] in world["rooms"]
    assert len(world["rooms"]) == 9
    assert world["npcs"]["npc.goblin"]["hostile"] is True
    assert "damage" not in world["npcs"]["npc.goblin"]


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"kind": "command", "line": "LOOK\nWHO"}, "control character"),
        ({"kind": "command", "line": "x" * 1025}, "1024-byte"),
        ({"kind": "unknown", "line": "LOOK"}, "command message"),
    ],
)
def test_browser_command_validation(payload: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        validate_browser_command(payload)
    assert validate_browser_command({"kind": "command", "line": "CHAT ROOM hello"}) == "CHAT ROOM hello"


def test_server_manager_starts_and_stops_release_binary() -> None:
    if not LOCAL_BINARY_PATH.is_file():
        pytest.skip("Build the TAP release server before running the manager integration test.")

    async def scenario() -> None:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        manager = TapServerManager(
            binary_path=Path(LOCAL_BINARY_PATH),
            world_path=Path(DEFAULT_WORLD_PATH),
            port=port,
        )
        await manager.start()
        assert manager.running
        reader, writer = await asyncio.open_connection(*manager.address)
        assert await reader.readline() == b"OK hello proto=1\n"
        writer.close()
        await writer.wait_closed()
        first_process = manager._process
        assert first_process is not None
        first_pid = first_process.pid
        first_process.kill()
        await first_process.wait()
        await manager.ensure_running()
        assert manager._process is not None
        assert manager._process.pid != first_pid
        await manager.stop()
        assert not manager.running

    asyncio.run(scenario())


def test_websocket_bridges_two_players_and_rejects_injected_lines(monkeypatch) -> None:
    if not LOCAL_BINARY_PATH.is_file():
        pytest.skip("Build the TAP release server before running the websocket integration test.")
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    manager = TapServerManager(
        binary_path=Path(LOCAL_BINARY_PATH),
        world_path=Path(DEFAULT_WORLD_PATH),
        port=port,
    )
    monkeypatch.setattr(tap_router_module, "tap_server_manager", manager)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        await manager.start()
        try:
            yield
        finally:
            await manager.stop()

    app = FastAPI(lifespan=lifespan)
    app.include_router(tap_router_module.router)

    def receive_line(socket, expected: str) -> dict:
        for _ in range(12):
            message = socket.receive_json()
            if message.get("line") == expected:
                return message
        raise AssertionError(f"Did not receive {expected!r}")

    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok", "project": "tap"}
        assert len(client.get("/world").json()["rooms"]) == 9
        with client.websocket_connect("/session") as alice:
            assert alice.receive_json() == {"kind": "protocol", "line": "OK hello proto=1"}
            alice.send_json({"kind": "command", "line": "CONNECT alice"})
            receive_line(alice, "OK connected")

            with client.websocket_connect("/session") as bob:
                assert bob.receive_json() == {"kind": "protocol", "line": "OK hello proto=1"}
                bob.send_json({"kind": "command", "line": "CONNECT bob"})
                receive_line(bob, "OK connected")

                alice.send_json({"kind": "command", "line": "CHAT GLOBAL hello bob"})
                receive_line(bob, "EVT GLOBAL CHAT alice hello bob")

                bob.send_json({"kind": "command", "line": "LOOK\nWHO"})
                error = bob.receive_json()
                assert error["kind"] == "gateway_error"
                assert "control character" in error["detail"]
