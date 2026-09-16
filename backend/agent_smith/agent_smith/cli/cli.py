import argparse
import asyncio
import json
import os
import shlex
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from agent_smith.agent.agent import LIMITS, run_agent
from agent_smith.llm import UnifiedLLMClient
from agent_smith.mcp.mcp_client import connect_mcp
from agent_smith.models.agent import SolutionOutput
from agent_smith.models.benchmark import MBPPTaskInput, SWEBenchTaskInput
from agent_smith.models.llm import ProviderConfig
from agent_smith.models.sandbox import SandboxConfig
from agent_smith.sandbox import Sandbox


def parser_for(benchmark: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"Agent Smith: {benchmark}")
    parser.add_argument("--task-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model-name")
    parser.add_argument("--provider-url")
    parser.add_argument("--model-config", default="config/models.json")
    parser.add_argument(
        "--api-key-env",
        help="Name of an environment variable, never the key itself",
    )
    parser.add_argument(
        "--max-retries", type=int, help="Retries after a failed LLM request"
    )
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--sandbox-config", default="config/sandbox.json")
    parser.add_argument("--sandbox-image")
    parser.add_argument(
        "--max-iterations", type=int, default=LIMITS[benchmark].iterations
    )
    parser.add_argument(
        "--prompt-file",
        help="Additional instructions for a reproducible ablation",
    )
    return parser


async def execute(
    args: argparse.Namespace, benchmark: str, started: float
) -> SolutionOutput:
    """Load one task and run it with its MCP server and sandbox."""
    model = MBPPTaskInput if benchmark == "mbpp" else SWEBenchTaskInput
    task = model.model_validate_json(Path(args.task_file).read_text())
    settings = (
        json.loads(Path(args.model_config).read_text())
        if Path(args.model_config).exists()
        else {}
    )
    provider = ProviderConfig(
        model_name=args.model_name or settings.get("model_name", ""),
        provider_url=args.provider_url or settings.get("provider_url", ""),
        api_key_env=args.api_key_env or settings.get("api_key_env"),
        timeout_seconds=settings.get("timeout_seconds", 30),
        max_retries=args.max_retries
        if args.max_retries is not None
        else settings.get("max_retries", 1),
    )
    if not provider.model_name or not provider.provider_url:
        raise ValueError(
            "Provide --model-name and --provider-url, or config/models.json"
        )
    config = SandboxConfig.from_json_file(args.sandbox_config)
    sandbox_image = args.sandbox_image or os.getenv(
        "SANDBOX_IMAGE", "python:3.12-slim"
    )
    extra = Path(args.prompt_file).read_text() if args.prompt_file else ""
    if benchmark == "mbpp":
        server_module = "agent_smith.mcp.servers.mbpp"
    else:
        server_module = "agent_smith.mcp.servers.swebench"
    command = shlex.join(
        [
            sys.executable,
            "-m",
            server_module,
            "--task-file",
            str(Path(args.task_file).resolve()),
        ]
    )
    llm = UnifiedLLMClient(provider)
    try:
        mcp_options = (
            {
                "environment": {"TOOL_TIMEOUT": "600"},
                "read_timeout_seconds": 620,
            }
            if benchmark == "swebench"
            else {}
        )
        async with connect_mcp(stdio=command, **mcp_options) as mcp:
            if mcp is None:
                raise RuntimeError("MCP connection was not created")
            llm.set_tools(mcp.tools)
            async with Sandbox(sandbox_image, mcp, config) as sandbox:
                return await run_agent(
                    task,
                    benchmark,
                    llm,
                    sandbox,
                    args.max_iterations,
                    extra_prompt=extra,
                    started=started,
                )
    finally:
        await llm.close()


def main(benchmark: str) -> None:
    args = parser_for(benchmark).parse_args()
    load_dotenv(args.env_file, override=False)
    started = time.monotonic()
    try:
        if args.max_iterations < 1:
            raise ValueError("max_iterations must be positive")
        # asyncio.run is the single entry point from synchronous CLI code.
        output = asyncio.run(execute(args, benchmark, started))
    except (Exception, KeyboardInterrupt) as exc:
        task_id = "unknown"
        try:
            raw = json.loads(Path(args.task_file).read_text())
            task_id = str(
                raw.get("task_id", raw.get("instance_id", "unknown"))
            )
        except (OSError, ValueError):
            pass
        output = SolutionOutput(
            task_id=task_id,
            benchmark=benchmark,
            success=False,
            solution="",
            iterations=0,
            total_requests=0,
            total_input_tokens=0,
            total_output_tokens=0,
            total_time_seconds=time.monotonic() - started,
            error=f"{type(exc).__name__}: {exc}",
        )
    try:
        destination = Path(args.output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(output.model_dump_json(indent=2) + "\n")
    except OSError as exc:
        print(f"Cannot write output: {exc}", file=sys.stderr)
        raise SystemExit(2)
    print(
        f"{benchmark}: {'submitted' if output.success else output.error}; output={args.output}"
    )
    raise SystemExit(0 if output.success else 1)
