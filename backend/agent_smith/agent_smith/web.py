"""Library entry point used by the Distillation Studio API."""

from __future__ import annotations

import asyncio
import shlex
import sys
import tempfile
import time
from collections.abc import Awaitable, Callable
from pathlib import Path

from agent_smith.agent.agent import LIMITS, run_agent
from agent_smith.llm import UnifiedLLMClient
from agent_smith.mcp.mcp_client import connect_mcp
from agent_smith.models.agent import SolutionOutput, StepMetrics
from agent_smith.models.benchmark import MBPPTaskInput, SWEBenchTaskInput
from agent_smith.models.llm import ProviderConfig
from agent_smith.models.sandbox import SandboxConfig
from agent_smith.sandbox import Sandbox


StepCallback = Callable[[StepMetrics, SolutionOutput], Awaitable[None] | None]
TaskInput = MBPPTaskInput | SWEBenchTaskInput


def exception_details(error: BaseException) -> str:
    """Flatten TaskGroup exceptions so deployment errors remain actionable."""
    if isinstance(error, BaseExceptionGroup):
        messages = [exception_details(item) for item in error.exceptions]
        return " | ".join(dict.fromkeys(message for message in messages if message))
    message = str(error).strip()
    return f"{type(error).__name__}: {message or 'no details'}"


def contains_cancellation(error: BaseException) -> bool:
    if isinstance(error, asyncio.CancelledError):
        return True
    if isinstance(error, BaseExceptionGroup):
        return any(contains_cancellation(item) for item in error.exceptions)
    return False


async def execute_web_task(
    task: TaskInput,
    benchmark: str,
    provider_url: str,
    model_name: str,
    api_key: str,
    on_step: StepCallback | None = None,
) -> SolutionOutput:
    """Run one validated task without reading or mutating process environment keys."""
    if benchmark not in LIMITS:
        raise ValueError(f"Unsupported benchmark: {benchmark}")

    provider = ProviderConfig(
        model_name=model_name,
        provider_url=provider_url,
        timeout_seconds=30,
        max_retries=1,
    )
    config = SandboxConfig()
    llm = UnifiedLLMClient(provider, api_keys=[api_key])
    started = time.monotonic()

    with tempfile.TemporaryDirectory(prefix="agent-smith-") as directory:
        task_file = Path(directory) / "task.json"
        task_file.write_text(task.model_dump_json(indent=2))
        server_module = (
            "agent_smith.mcp.servers.mbpp"
            if benchmark == "mbpp"
            else "agent_smith.mcp.servers.swebench"
        )
        command = shlex.join(
            [sys.executable, "-m", server_module, "--task-file", str(task_file)]
        )
        try:
            async with connect_mcp(stdio=command) as mcp:
                if mcp is None:
                    raise RuntimeError("MCP connection was not created")
                llm.set_tools(mcp.tools)
                async with Sandbox("python:3.12-slim", mcp, config) as sandbox:
                    return await run_agent(
                        task,
                        benchmark,
                        llm,
                        sandbox,
                        max_iterations=LIMITS[benchmark].iterations,
                        started=started,
                        on_step=on_step,
                    )
        except BaseExceptionGroup as error:
            if contains_cancellation(error):
                raise asyncio.CancelledError from None
            raise RuntimeError(f"Agent runtime failed: {exception_details(error)}") from None
        finally:
            await llm.close()
