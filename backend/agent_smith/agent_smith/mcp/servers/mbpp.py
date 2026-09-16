"""MCP server containing the tools used by the MBPP agent."""

import argparse
import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from agent_smith.models.benchmark import MBPPTaskInput
from agent_smith.models.sandbox import SandboxConfig
from agent_smith.sandbox import Sandbox

mcp = FastMCP(
    "Agent Smith MBPP", host="127.0.0.1", port=int(os.getenv("MCP_PORT", "8000"))
)
task: MBPPTaskInput | None = None


@mcp.tool()
async def run_tests(
    code: str, test_list: list[str] | None = None, test_imports: list[str] | None = None
) -> dict[str, object]:
    """Test code against the loaded task, or explicit tests in standalone mode."""
    tests = task.test_list if task else (test_list or [])
    imports = task.test_imports if task else (test_imports or [])
    if not tests:
        raise ValueError("No tests supplied; pass test_list or start with --task-file")
    # Each assertion catches its own failure so feedback includes partial progress.
    lines = imports + [code, "passed = 0", "failures = []"]
    for index, test in enumerate(tests, 1):
        lines += ["try:"] + ["    " + line for line in test.splitlines()]
        lines += [
            "    passed += 1",
            "except Exception as exc:",
            f"    failures.append('test {index}: ' + str(exc))",
        ]
    lines += [f"result = dict(passed=passed, total={len(tests)}, failures=failures)"]
    async with Sandbox(
        os.getenv("SANDBOX_IMAGE", "python:3.12-slim"),
        config=SandboxConfig(max_execution_time_seconds=10),
    ) as sandbox:
        result = await sandbox.execute("\n".join(lines))
    if not result.success:
        return {
            "passed": 0,
            "total": len(tests),
            "error": result.error,
            "stdout": result.stdout,
        }
    return result.result


@mcp.resource("task://current")
def current_task() -> str:
    return task.model_dump_json() if task else "No task loaded"


@mcp.prompt()
def solve_problem() -> str:
    return "Write a Python function, run_tests(code=code), repair failures, then final_answer(code)."


def main() -> None:
    global task
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-file")
    parser.add_argument(
        "--transport", choices=["stdio", "streamable-http"], default="stdio"
    )
    args = parser.parse_args()
    if args.task_file:
        task = MBPPTaskInput.model_validate_json(Path(args.task_file).read_text())
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
