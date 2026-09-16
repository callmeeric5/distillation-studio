"""Communication between the host application and the sandbox worker.

The worker runs inside Docker and stays alive so Python variables persist between
agent steps. Messages are encoded as one JSON object per line.
"""

import asyncio
import builtins
import json
import keyword
import time
from collections.abc import Mapping
from pathlib import Path
from types import TracebackType
from typing import Any

from agent_smith.mcp.mcp_client import MCPConnection
from agent_smith.models.sandbox import SandboxConfig, SandboxResult


class Sandbox:
    def __init__(
        self,
        image: str = "python:3.12-slim",
        mcp: MCPConnection | None = None,
        config: SandboxConfig | None = None,
    ) -> None:
        self.image = image
        self.mcp = mcp
        self.config = config or SandboxConfig()
        self.tools = mcp.tools if mcp else []
        self.container_id = ""
        self.process: asyncio.subprocess.Process | None = None

    async def docker(self, *arguments: str) -> str:
        """Run one short Docker command and wait for it to finish."""
        process = await asyncio.create_subprocess_exec(
            "docker",
            *arguments,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            # Collect both output streams and enforce a host-side timeout.
            stdout, stderr = await asyncio.wait_for(process.communicate(), 60)
        except BaseException:
            if process.returncode is None:
                process.kill()
            await process.wait()
            raise
        if process.returncode:
            raise RuntimeError(stderr.decode(errors="replace").strip())
        return stdout.decode().strip()

    async def start(self) -> "Sandbox":
        names = [tool.python_name for tool in self.tools]
        if len(names) != len(set(names)):
            raise ValueError("MCP tool names conflict after Python name conversion")
        for name in names:
            if (
                name == "final_answer"
                or name.startswith("_")
                or keyword.iskeyword(name)
                or name in dir(builtins)
            ):
                raise ValueError(f"Reserved tool name: {name}")
        self.container_id = await self.docker(
            "run",
            "-d",
            "--rm",
            "--network",
            "none",
            "--memory",
            f"{self.config.max_memory_mb}m",
            "--memory-swap",
            f"{self.config.max_memory_mb}m",
            "--pids-limit",
            "128",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--entrypoint",
            "sleep",
            self.image,
            "infinity",
        )
        try:
            await self.docker(
                "exec",
                self.container_id,
                "mkdir",
                "-p",
                *self.config.allowed_directories,
            )
            runner = Path(__file__).with_name("runner.py").read_text()
            command = [
                "docker",
                "exec",
                "-i",
                "-w",
                self.config.allowed_directories[0],
                self.container_id,
                "python",
                "-I",
                "-c",
                runner,
            ]
            # Keep this process alive so variables persist between agent steps.
            self.process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=4 * 1024 * 1024,
            )
            return self
        except BaseException:
            await self.close()
            raise

    async def send(self, message: Mapping[str, Any]) -> None:
        """Send one JSON-line message to the sandbox worker."""
        process = self.process
        if process is None or process.stdin is None:
            raise RuntimeError(
                "Sandbox input is not available; start the sandbox first"
            )
        line = json.dumps(message) + "\n"
        process.stdin.write(line.encode())
        await process.stdin.drain()

    async def receive(self, seconds: float) -> dict[str, Any]:
        """Wait for one JSON-line message from the sandbox worker."""
        process = self.process
        if process is None or process.stdout is None:
            raise RuntimeError(
                "Sandbox output is not available; start the sandbox first"
            )
        line = await asyncio.wait_for(
            process.stdout.readline(), timeout=max(0, seconds)
        )
        if not line:
            raise ConnectionError("Sandbox worker stopped (possibly out of memory)")
        return json.loads(line)

    async def execute(
        self, code: str, timeout: float | None = None
    ) -> SandboxResult:
        """Execute one code block and handle any MCP calls it makes."""
        if timeout is not None and timeout <= 0:
            raise TimeoutError("Task time exhausted before execution")
        task_deadline = (
            time.monotonic() + timeout if timeout is not None else float("inf")
        )
        # The worker enforces code time; the host leaves one second for feedback.
        code_deadline = time.monotonic() + self.config.max_execution_time_seconds + 1
        await self.send(
            {
                "code": code,
                "persistent": True,
                "config": self.config.model_dump(),
                "tools": [
                    {**tool.model_dump(), "python_name": tool.python_name}
                    for tool in self.tools
                ],
            }
        )
        try:
            while True:
                seconds = min(task_deadline, code_deadline) - time.monotonic()
                message = await self.receive(seconds)
                if message["type"] == "result":
                    return SandboxResult.model_validate(message["data"])
                if message["type"] == "control":
                    if message["exception"] == "KeyboardInterrupt":
                        raise KeyboardInterrupt
                    raise SystemExit(message.get("code"))
                if message["type"] == "tool_call":
                    started = time.monotonic()
                    try:
                        if self.mcp is None:
                            raise RuntimeError("No MCP server connected")
                        # MCP calls pause code time but still consume total task time.
                        remaining = (
                            max(0, task_deadline - started)
                            if timeout is not None
                            else None
                        )
                        value = await asyncio.wait_for(
                            self.mcp.call(message["name"], message["arguments"]),
                            timeout=remaining,
                        )
                        if isinstance(value, str) and message["name"] != "get_patch":
                            limit = self.config.max_output_chars
                            if len(value) > limit:
                                value = (
                                    value[:limit]
                                    + "\n[Tool output truncated due to size limit]"
                                )
                        reply = {"success": True, "result": value}
                    except asyncio.TimeoutError:
                        raise
                    except Exception as exc:
                        reply = {"success": False, "error": str(exc)}
                    await self.send(reply)
                    code_deadline += time.monotonic() - started
        except asyncio.TimeoutError:
            await self.close()
            raise TimeoutError("Execution timed out") from None

    def manual(self) -> str:
        lines = [
            "Python variables persist between steps. Use keyword arguments for tools.",
            "final_answer(answer: str) submits source code (MBPP) or a patch (SWE-bench).",
        ]
        for tool in self.tools:
            properties = tool.input_schema.get("properties", {})
            required = set(tool.input_schema.get("required", []))
            parameters = []
            for name, schema in properties.items():
                types = schema.get("type")
                if not types:
                    types = (
                        " | ".join(
                            option.get("type", "any")
                            for option in schema.get("anyOf", [])
                        )
                        or "any"
                    )
                optional = "" if name in required else f" = {schema.get('default')!r}"
                parameters.append(f"{name}: {types}{optional}")
            lines.append(
                f"{tool.python_name}({', '.join(parameters)}): {tool.description}"
            )
        if self.mcp:
            lines.append(self.mcp.manual())
        return "\n".join(lines)

    async def close(self) -> None:
        try:
            if self.container_id:
                await self.docker("rm", "-f", self.container_id)
                self.container_id = ""
        finally:
            if self.process:
                if self.process.returncode is None:
                    self.process.kill()
                await self.process.wait()
                self.process = None

    async def restart(self) -> "Sandbox":
        """Replace a stopped worker while keeping the connected MCP server."""
        await self.close()
        return await self.start()

    async def __aenter__(self) -> "Sandbox":
        return await self.start()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()
