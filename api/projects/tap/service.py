from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import suppress
from pathlib import Path
from typing import Any
import unicodedata


LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_WORLD_PATH = PROJECT_ROOT / "backend" / "tap" / "data" / "world.json"
PACKAGED_BINARY_PATH = PROJECT_ROOT / "backend" / "tap" / "server"
LOCAL_BINARY_PATH = PROJECT_ROOT / "backend" / "tap" / "target" / "release" / "server"
DEFAULT_BINARY_PATH = PACKAGED_BINARY_PATH if PACKAGED_BINARY_PATH.is_file() else LOCAL_BINARY_PATH
MAX_LINE_BYTES = 1024


class TapServerManager:
    def __init__(
        self,
        binary_path: Path | None = None,
        world_path: Path | None = None,
        host: str | None = None,
        port: int | None = None,
    ) -> None:
        configured_binary = os.getenv("TAP_SERVER_BINARY")
        configured_world = os.getenv("TAP_WORLD_FILE")
        self.binary_path = binary_path or (
            Path(configured_binary) if configured_binary else DEFAULT_BINARY_PATH
        )
        self.world_path = world_path or (Path(configured_world) if configured_world else DEFAULT_WORLD_PATH)
        self.host = host or os.getenv("TAP_SERVER_HOST", "127.0.0.1")
        self.port = port or int(os.getenv("TAP_SERVER_PORT", "4242"))
        self._process: asyncio.subprocess.Process | None = None
        self._lock = asyncio.Lock()
        self._log_tasks: list[asyncio.Task[None]] = []

    @property
    def address(self) -> tuple[str, int]:
        return self.host, self.port

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.returncode is None

    async def start(self) -> None:
        async with self._lock:
            if self.running:
                return
            await self._stop_unlocked()
            if not self.binary_path.is_file():
                raise RuntimeError(
                    f"TAP server binary was not found at {self.binary_path}. "
                    "Build backend/tap with `cargo build --release --bin server`."
                )
            if not self.world_path.is_file():
                raise RuntimeError(f"TAP world file was not found at {self.world_path}.")

            self._process = await asyncio.create_subprocess_exec(
                str(self.binary_path),
                str(self.world_path),
                f"{self.host}:{self.port}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            if self._process.stdout is not None:
                self._log_tasks.append(
                    asyncio.create_task(self._drain(self._process.stdout, logging.INFO))
                )
            if self._process.stderr is not None:
                self._log_tasks.append(
                    asyncio.create_task(self._drain(self._process.stderr, logging.WARNING))
                )
            await self._wait_until_ready()

    async def ensure_running(self) -> None:
        if not self.running:
            await self.start()

    async def stop(self) -> None:
        async with self._lock:
            await self._stop_unlocked()

    async def _stop_unlocked(self) -> None:
        process = self._process
        self._process = None
        if process is not None and process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
        for task in self._log_tasks:
            task.cancel()
        for task in self._log_tasks:
            with suppress(asyncio.CancelledError):
                await task
        self._log_tasks.clear()

    async def _wait_until_ready(self) -> None:
        for _ in range(50):
            if not self.running:
                code = self._process.returncode if self._process is not None else "unknown"
                await self._stop_unlocked()
                raise RuntimeError(f"TAP server stopped during startup with exit code {code}.")
            try:
                reader, writer = await asyncio.open_connection(self.host, self.port)
                greeting = await asyncio.wait_for(reader.readline(), timeout=0.5)
                writer.close()
                await writer.wait_closed()
                if greeting.rstrip(b"\r\n") == b"OK hello proto=1":
                    return
            except (ConnectionError, OSError, asyncio.TimeoutError):
                await asyncio.sleep(0.1)
        await self._stop_unlocked()
        raise RuntimeError("TAP server did not become ready in time.")

    async def _drain(self, stream: asyncio.StreamReader, level: int) -> None:
        while line := await stream.readline():
            LOGGER.log(level, "tap-server: %s", line.decode("utf-8", "replace").rstrip())


def validate_browser_command(payload: Any) -> str:
    if not isinstance(payload, dict) or payload.get("kind") != "command":
        raise ValueError("Expected a command message.")
    line = payload.get("line")
    if not isinstance(line, str):
        raise ValueError("Command line must be a string.")
    if len(line.encode("utf-8")) > MAX_LINE_BYTES:
        raise ValueError("Command exceeds the 1024-byte TAP limit.")
    if "\n" in line or "\r" in line or any(unicodedata.category(char) == "Cc" for char in line):
        raise ValueError("Command contains a control character.")
    return line


def get_world() -> dict[str, Any]:
    configured_world = os.getenv("TAP_WORLD_FILE")
    world_path = Path(configured_world) if configured_world else DEFAULT_WORLD_PATH
    with world_path.open(encoding="utf-8") as world_file:
        world = json.load(world_file)
    return {
        "start_room": world["start_room"],
        "rooms": {
            room_id: {
                "name": room["name"],
                "description": room["description"],
                "exits": room["exits"],
            }
            for room_id, room in world["rooms"].items()
        },
        "items": {
            item_id: {"name": item["name"], "description": item["description"]}
            for item_id, item in world["items"].items()
        },
        "npcs": {
            npc_id: {
                "name": npc["name"],
                "description": npc["description"],
                "hostile": npc.get("hostile", False),
                "quest": npc.get("quest"),
            }
            for npc_id, npc in world["npcs"].items()
        },
        "quests": {
            quest_id: {
                "description": quest["description"],
                "giver": quest["giver"],
                "reward": quest["reward"],
            }
            for quest_id, quest in world["quests"].items()
        },
    }


tap_server_manager = TapServerManager()
