"""MCP server containing the tools used by the SWE-bench agent."""

import argparse
import os
import re
from mcp.server.fastmcp import FastMCP
from agent_smith.models.benchmark import SWEBenchTaskInput
from agent_smith.tools.docker import DockerWorkspace
from pathlib import Path

mcp = FastMCP(
    "Agent Smith SWE-bench", host="127.0.0.1", port=int(os.getenv("MCP_PORT", "8000"))
)
workspace: DockerWorkspace | None = None
task: SWEBenchTaskInput | None = None
patch_before_tests: str | None = None
TEST_END_MARKER = ": '>>>>> End Test Output'"


def evaluation_script(script: str) -> str:
    """Make a SWE-bench script return the test command's exit status."""
    if TEST_END_MARKER not in script:
        return script
    capture = "agent_test_status=$?\n" + TEST_END_MARKER
    return script.replace(TEST_END_MARKER, capture, 1) + "\nexit $agent_test_status\n"


def production_patch(patch: str) -> str:
    """Remove test-file changes made by the evaluation script."""
    sections = re.split(r"(?=^diff --git )", patch, flags=re.MULTILINE)
    kept = []
    for section in sections:
        match = re.match(r"diff --git a/(\S+) b/\S+", section)
        if not match:
            kept.append(section)
            continue
        path = Path(match.group(1))
        if "tests" not in path.parts and not path.name.startswith("test_"):
            kept.append(section)
    return "".join(kept)


def repository() -> DockerWorkspace:
    global workspace
    if workspace is None:
        image = task.docker_image if task else os.getenv("SWE_DOCKER_IMAGE")
        if not image:
            raise ValueError("Supply --task-file or SWE_DOCKER_IMAGE")
        workspace = DockerWorkspace(
            image, timeout=int(os.getenv("TOOL_TIMEOUT", "120"))
        )
    return workspace


@mcp.tool()
def read_file(filepath: str, start_line: int = 1, end_line: int | None = None) -> str:
    """Read a 1-based range. Displayed '12: ' prefixes are not source text."""
    return repository().call(
        "read_file",
        {"filepath": filepath, "start_line": start_line, "end_line": end_line},
    )


@mcp.tool()
def edit_file(filepath: str, old_str: str, new_str: str) -> str:
    """Replace exactly one match; reject syntax errors and trailing whitespace."""
    global patch_before_tests
    path = Path(filepath)
    if "tests" in path.parts or path.name.startswith("test_"):
        raise ValueError(
            "Do not edit test files; fix the production source identified by the traceback"
        )
    result = repository().call(
        "edit_file", {"filepath": filepath, "old_str": old_str, "new_str": new_str}
    )
    patch_before_tests = None
    return result


@mcp.tool()
def list_files(directory: str = "/testbed", pattern: str = "*") -> str:
    """List matching repository files recursively."""
    return repository().call("list_files", {"directory": directory, "pattern": pattern})


@mcp.tool()
def search_code(pattern: str, file_pattern: str = "*.py") -> str:
    """Regex search: /absolute/path:line source text."""
    return repository().call(
        "search_code", {"pattern": pattern, "file_pattern": file_pattern}
    )


@mcp.tool()
def search_function_or_class_definition_in_code(name: str) -> str:
    """Find exact Python function/class definitions with AST."""
    return repository().call(
        "search_function_or_class_definition_in_code", {"name": name}
    )


@mcp.tool()
def find_references(name: str, filepath: str, line: int) -> str:
    """Find lexical references; filepath and line identify the source symbol."""
    return repository().call(
        "find_references", {"name": name, "filepath": filepath, "line": line}
    )


@mcp.tool()
def run_command(command: str, workdir: str = "/testbed") -> dict[str, object]:
    """Run Bash in the task container; return stdout, stderr and exit_code."""
    global patch_before_tests
    result = repository().run_command(command, workdir)
    patch_before_tests = None
    return result


@mcp.tool()
def run_python(code: str, workdir: str = "/testbed") -> dict[str, object]:
    """Run read-only diagnostic Python; use edit_file for repository changes."""
    global patch_before_tests
    result = repository().call("run_python", {"code": code, "workdir": workdir})
    patch_before_tests = None
    return result


@mcp.tool()
def run_tests() -> dict[str, object]:
    """Run the task's provided evaluation script inside its container."""
    global patch_before_tests
    if task is None:
        raise ValueError("run_tests requires --task-file")
    patch_before_tests = production_patch(repository().call("get_patch", {}))
    return repository().run_command(evaluation_script(task.eval_script))


@mcp.tool()
def get_patch() -> str:
    """Return the complete git diff, including newly created source files."""
    if patch_before_tests is not None:
        return patch_before_tests
    return production_patch(repository().call("get_patch", {}))


@mcp.resource("task://current")
def current_task() -> str:
    return task.model_dump_json() if task else "No task loaded"


@mcp.prompt()
def debug_issue() -> str:
    return "Reproduce, search, read, make a small edit, run tests, inspect get_patch(), then submit."


def main() -> None:
    global task
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-file")
    parser.add_argument(
        "--transport", choices=["stdio", "streamable-http"], default="stdio"
    )
    args = parser.parse_args()
    if args.task_file:
        task = SWEBenchTaskInput.model_validate_json(Path(args.task_file).read_text())
    try:
        mcp.run(transport=args.transport)
    finally:
        if workspace is not None:
            workspace.close()


if __name__ == "__main__":
    main()
