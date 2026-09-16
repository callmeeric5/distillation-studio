import ast
import fnmatch
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, BinaryIO

ROOT = Path("/testbed")
LIMIT = 12000


def path_in_repo(path: str | Path) -> Path:
    root = ROOT.resolve()
    path = Path(path)
    if path.is_absolute():
        resolved = path.resolve()
        if resolved != root and root not in resolved.parents:
            path = (root / path.relative_to("/")).resolve()
        else:
            path = resolved
    else:
        path = (root / path).resolve()
    if path != root and root not in path.parents:
        raise PermissionError(f"Path outside repository: {path}")
    if ".git" in path.relative_to(root).parts:
        raise PermissionError("Git metadata is not a source file")
    return path


def truncate(text: str) -> str:
    return (
        text
        if len(text) <= LIMIT
        else text[:LIMIT] + "\n[Tool output truncated due to size limit]"
    )


def read_command_output(stream: BinaryIO) -> str:
    """Read command setup at the start and test summaries at the end."""
    stream.seek(0, 2)
    size = stream.tell()
    stream.seek(0)
    if size <= LIMIT:
        return stream.read().decode("utf-8", "replace")
    start = LIMIT // 3
    end = LIMIT - start
    first = stream.read(start).decode("utf-8", "replace")
    stream.seek(-end, 2)
    last = stream.read(end).decode("utf-8", "replace")
    return first + "\n[Middle of command output truncated]\n" + last


def files(
    directory: str | Path = "/testbed", pattern: str = "*"
) -> Iterator[Path]:
    root = path_in_repo(directory)
    if not root.is_dir():
        raise NotADirectoryError(str(root))
    if ".." in Path(pattern).parts or Path(pattern).is_absolute():
        raise ValueError("Use a relative file pattern")
    for path in sorted(root.rglob("*")):
        if any(
            p in {".git", ".venv", "__pycache__"} for p in path.relative_to(root).parts
        ):
            continue
        if path.is_file() and (
            fnmatch.fnmatch(path.name, pattern)
            or fnmatch.fnmatch(str(path.relative_to(root)), pattern)
        ):
            try:
                yield path_in_repo(path)
            except PermissionError:
                continue


def read_file(
    filepath: str | Path, start_line: int = 1, end_line: int | None = None
) -> str:
    """Read inclusive, 1-based line ranges, formatted as 'line: content'."""
    if start_line < 1 or (end_line is not None and end_line < start_line):
        raise ValueError("Invalid line range")
    lines = path_in_repo(filepath).read_text().splitlines()
    end_line = min(end_line or len(lines), len(lines))
    return truncate(
        "\n".join(f"{i + 1}: {lines[i]}" for i in range(start_line - 1, end_line))
    )


def without_display_line_numbers(text: str) -> str:
    """Remove read_file prefixes when every line clearly contains one."""
    lines = text.splitlines()
    matches = [re.match(r"^\d+: ?(.*)$", line) for line in lines]
    if lines and all(matches):
        return "\n".join(match.group(1) for match in matches if match is not None)
    return text


def match_ignoring_indentation(
    content: str, old_str: str, new_str: str
) -> tuple[str, str]:
    """Recover one copied source block while preserving its real indentation."""
    old_lines = old_str.splitlines()
    new_lines = new_str.splitlines()
    if not old_lines or len(old_lines) != len(new_lines):
        return "", ""
    wanted = [line.strip() for line in old_lines]
    source = content.splitlines()
    starts = [
        start
        for start in range(len(source) - len(old_lines) + 1)
        if [line.strip() for line in source[start : start + len(old_lines)]] == wanted
    ]
    if len(starts) != 1:
        return "", ""
    actual = source[starts[0] : starts[0] + len(old_lines)]
    replacement = []
    for actual_line, proposed_line in zip(actual, new_lines):
        indentation = actual_line[: len(actual_line) - len(actual_line.lstrip())]
        replacement.append(
            indentation + proposed_line.lstrip() if proposed_line.strip() else ""
        )
    return "\n".join(actual), "\n".join(replacement)


def extend_definition(content: str, header: str, proposed: str) -> tuple[str, str]:
    """Insert a proposed leading body while keeping the current definition."""
    lines = content.splitlines()
    matches = [i for i, line in enumerate(lines) if line.strip() == header.strip()]
    if len(matches) != 1:
        return "", ""

    start = matches[0]
    header_indent = len(lines[start]) - len(lines[start].lstrip())
    end = start + 1
    while end < len(lines):
        line = lines[end]
        indentation = len(line) - len(line.lstrip())
        if line.strip() and indentation <= header_indent:
            break
        end += 1

    old_block = lines[start:end]
    added = proposed.splitlines()[1:]
    while added and not added[-1].strip():
        added.pop()
    smallest_indent = min(
        len(line) - len(line.lstrip()) for line in added if line.strip()
    )
    body_indent = " " * (header_indent + 4)
    added = [
        body_indent + line[smallest_indent:] if line.strip() else "" for line in added
    ]

    insert_at = 1
    first_body = old_block[1].strip() if len(old_block) > 1 else ""
    quote = (
        '"""'
        if first_body.startswith('"""')
        else "'''"
        if first_body.startswith("'''")
        else ""
    )
    if quote:
        insert_at = 2
        if first_body.count(quote) < 2:
            while insert_at < len(old_block) and quote not in old_block[insert_at]:
                insert_at += 1
            insert_at += 1

    new_block = old_block[:insert_at] + added + old_block[insert_at:]
    return "\n".join(old_block), "\n".join(new_block)


def edit_file(filepath: str | Path, old_str: str, new_str: str) -> str:
    """Replace exactly one match. Reject ambiguous or syntactically invalid edits."""
    path = path_in_repo(filepath)
    content = path.read_text()
    if content.count(old_str) == 0:
        cleaned_old = without_display_line_numbers(old_str)
        if cleaned_old != old_str:
            old_str = cleaned_old
            new_str = without_display_line_numbers(new_str)
    if content.count(old_str) == 0:
        matched_old, matched_new = match_ignoring_indentation(content, old_str, new_str)
        if matched_old:
            old_str, new_str = matched_old, matched_new
    if old_str == new_str:
        raise ValueError(
            "new_str must be different from old_str; the requested change already exists"
        )
    if old_str.rstrip("\n") == new_str.rstrip("\n"):
        raise ValueError("Changing only final newlines is not a source-code change")
    if not old_str or content.count(old_str) != 1:
        raise ValueError(
            "old_str must match exactly once; include more surrounding lines"
        )
    stripped = old_str.lstrip()
    replaces_definition = stripped.startswith(("def ", "class ", "async def "))
    if (
        path.suffix == ".py"
        and replaces_definition
        and "\n" not in old_str
        and "\n" in new_str
    ):
        if new_str.splitlines()[-1].strip():
            raise ValueError(
                "A definition header cannot replace the whole definition. Include the complete "
                "current function in old_str and preserve its docstring and unchanged behavior in "
                "new_str, or replace a smaller statement inside the function."
            )
        old_str, new_str = extend_definition(content, old_str, new_str)
        if not old_str:
            raise ValueError("Could not identify one complete definition for old_str")
    updated = content.replace(old_str, new_str, 1)
    if path.suffix == ".py":
        try:
            ast.parse(updated, filename=str(path))
        except SyntaxError as exc:
            raise ValueError(
                f"Edit rejected: syntax error at line {exc.lineno}: {exc.msg}"
            ) from exc
        for i, line in enumerate(updated.splitlines(), 1):
            if line.rstrip(" \t") != line and line not in content.splitlines():
                raise ValueError(
                    f"Edit rejected: trailing whitespace lint violation at line {i}"
                )
    path.write_text(updated)
    return f"Updated {path}"


def list_files(directory: str = "/testbed", pattern: str = "*") -> str:
    return truncate("\n".join(map(str, files(directory, pattern))))


def search_code(pattern: str, file_pattern: str = "*.py") -> str:
    regex = re.compile(pattern)
    matches = []
    size = 0
    for path in files(str(ROOT), file_pattern):
        try:
            for i, line in enumerate(path.read_text().splitlines(), 1):
                if regex.search(line):
                    match = f"{path}:{i} {line}"
                    matches.append(match)
                    size += len(match) + 1
                    if size > LIMIT:
                        return truncate("\n".join(matches))
        except (UnicodeError, OSError):
            continue
    return "\n".join(matches)


def search_function_or_class_definition_in_code(name: str) -> str:
    matches = []
    for path in files(str(ROOT), "*.py"):
        try:
            source = path.read_text()
            tree = ast.parse(source)
        except (SyntaxError, UnicodeError, OSError):
            continue
        for node in ast.walk(tree):
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and node.name == name
            ):
                matches.append(
                    f"{path}:{node.lineno} {source.splitlines()[node.lineno - 1]}"
                )
    return truncate("\n".join(matches))


def find_references(name: str, filepath: str | Path, line: int) -> str:
    path = path_in_repo(filepath)
    source = path.read_text().splitlines()
    if line < 1 or line > len(source):
        raise ValueError("Invalid source line")
    if not re.search(r"\b" + re.escape(name) + r"\b", source[line - 1]):
        raise ValueError("The requested symbol is absent from the source line")
    return search_code(r"\b" + re.escape(name) + r"\b")


def run_command(
    command: str, workdir: str | Path = "/testbed", timeout: int = 120
) -> dict[str, object]:
    """Run a command in the repository with bounded output and a timeout."""
    workdir = path_in_repo(workdir)
    stdout = tempfile.TemporaryFile()
    stderr = tempfile.TemporaryFile()
    try:
        process = subprocess.Popen(
            ["bash", "-o", "pipefail", "-lc", command],
            cwd=workdir,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
        )
        timed_out = False
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            # Kill the complete process group so no background process remains.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        return {
            "exit_code": process.returncode,
            "timed_out": timed_out,
            "stdout": read_command_output(stdout),
            "stderr": read_command_output(stderr),
            "feedback": "Command timed out; output is partial" if timed_out else "",
        }
    finally:
        stdout.close()
        stderr.close()


def validate_diagnostic_python(code: str) -> None:
    """Reject common file and process operations in diagnostic Python snippets."""
    tree = ast.parse(code)
    blocked_names = {"open", "__import__"}
    blocked_attributes = {
        "open",
        "write_text",
        "write_bytes",
        "unlink",
        "remove",
        "rename",
        "mkdir",
        "makedirs",
        "touch",
        "rmdir",
        "removedirs",
        "system",
        "popen",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports_subprocess = any(
                name.name.split(".")[0] == "subprocess" for name in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            imports_subprocess = (node.module or "").split(".")[0] == "subprocess"
        else:
            imports_subprocess = False
        if imports_subprocess:
            raise ValueError(
                "run_python is for diagnostics; use run_command for processes"
            )
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id in blocked_names:
            raise ValueError(
                "run_python cannot open or modify repository files; use repository tools"
            )
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in blocked_attributes
        ):
            raise ValueError(
                "run_python cannot open or modify repository files; use repository tools"
            )


def run_python(
    code: str,
    workdir: str | Path = "/testbed",
    timeout: int = 120,
    interpreter: str | None = None,
) -> dict[str, object]:
    """Run a read-only diagnostic snippet without shell quote escaping."""
    validate_diagnostic_python(code)
    script = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    try:
        script.write(code)
        script.close()
        command = (
            f"{shlex.quote(interpreter or sys.executable)} "
            f"{shlex.quote(script.name)}"
        )
        return run_command(command, workdir, timeout)
    finally:
        Path(script.name).unlink()


def get_patch() -> str:
    # Intent-to-add includes newly created source files without staging content.
    added = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout
    for name in added.decode().split("\0"):
        if name:
            subprocess.run(
                ["git", "add", "-N", "--", name],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
    return subprocess.run(
        ["git", "-c", "core.fileMode=false", "diff", "HEAD", "--"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=True,
    ).stdout


OPERATIONS: dict[str, Callable[..., Any]] = {
    "read_file": read_file,
    "edit_file": edit_file,
    "list_files": list_files,
    "search_code": search_code,
    "search_function_or_class_definition_in_code": (
        search_function_or_class_definition_in_code
    ),
    "find_references": find_references,
    "run_command": run_command,
    "run_python": run_python,
    "get_patch": get_patch,
}

if __name__ == "__main__":
    request = json.load(sys.stdin)
    try:
        result = {
            "ok": True,
            "value": OPERATIONS[request["name"]](**request["arguments"]),
        }
    except Exception as exc:
        result = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(result))
