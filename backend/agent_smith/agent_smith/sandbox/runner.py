"""Persistent, restricted Python worker. Production runs this inside Docker.

Only standard-library modules are used here. AST checks prevent introspection;
import facades and the audit hook restrict what approved libraries can access.
Docker adds the network, process and memory boundary.
"""

import ast
import builtins
import contextlib
import json
import resource
import signal
import sys
import types
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from types import FrameType
from typing import Any, NoReturn

INPUT, OUTPUT = sys.stdin, sys.stdout
ACTIVE = False
CONFIG: dict[str, Any] = {}
EXEC_CODE: types.CodeType | None = None


class _FinalAnswer(BaseException):
    def __init__(self, answer: str) -> None:
        self.answer = answer


class _CodeTimeout(BaseException):
    pass


def _send(message: Mapping[str, Any]) -> None:
    print(
        json.dumps(message, default=lambda value: "<non-JSON value>"),
        file=OUTPUT,
        flush=True,
    )


def _path_allowed(filepath: str | Path, directories: Sequence[str]) -> Path:
    if not isinstance(filepath, (str, Path)):
        raise PermissionError("File descriptors are not allowed")
    path = Path(filepath).resolve()
    roots = [Path(directory).resolve() for directory in directories]
    if not any(path == root or root in path.parents for root in roots):
        raise PermissionError(f"Path is not allowed: {filepath}")
    return path


def _audit(event: str, args: tuple[Any, ...]) -> None:
    if not ACTIVE:
        return
    if event == "compile" or (event == "exec" and args[0] is not EXEC_CODE):
        raise PermissionError("Dynamic code execution through libraries is not allowed")
    if event == "open":
        _path_allowed(args[0], CONFIG["allowed_directories"])
    if event.startswith(("socket.", "subprocess.", "ctypes.", "os.", "shutil.")):
        raise PermissionError(f"Operation is not allowed: {event}")
    if event in {
        "sys.settrace",
        "sys.setprofile",
        "sys._getframe",
        "builtins.breakpoint",
    }:
        raise PermissionError(f"Operation is not allowed: {event}")


class _Module:
    """Do not leak other modules through e.g. typing.sys or random._os."""

    def __init__(self, module: types.ModuleType) -> None:
        self._module = module

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise PermissionError("Private module attributes are not allowed")
        value = getattr(self._module, name)
        if isinstance(value, types.ModuleType):
            if not _import_allowed(value.__name__):
                raise ImportError(f"Import is not allowed: {value.__name__}")
            return _Module(value)
        return value


def _import_allowed(name: str) -> bool:
    return any(
        name == rule.removesuffix(".*")
        or (rule.endswith(".*") and name.startswith(rule[:-1]))
        for rule in CONFIG["authorized_imports"]
    )


def _safe_import(
    name: str,
    globals: dict[str, Any] | None = None,
    locals: dict[str, Any] | None = None,
    fromlist: Sequence[str] = (),
    level: int = 0,
) -> _Module:
    global ACTIVE
    if level or not _import_allowed(name):
        raise ImportError(f"Import is not allowed: {name}")
    if any(part.startswith("_") for part in (fromlist or ())):
        raise ImportError("Private imports are not allowed")
    # Loading the configured stdlib module needs to read the interpreter's files.
    was_active = ACTIVE
    ACTIVE = False
    try:
        module = builtins.__import__(name, globals, locals, fromlist, level)
    finally:
        ACTIVE = was_active
    return _Module(module)


def _safe_open(filepath: str | Path, *args: Any, **kwargs: Any) -> Any:
    return builtins.open(
        _path_allowed(filepath, CONFIG["allowed_directories"]), *args, **kwargs
    )


def _restricted_builtins() -> dict[str, Any]:
    names = """abs all any bool bytes callable chr classmethod complex dict divmod
        enumerate filter float frozenset hash hex int isinstance issubclass iter len
        list map max min next object oct ord pow print property range repr reversed
        round set slice sorted staticmethod str sum super tuple type zip
        Exception ArithmeticError AssertionError IndexError KeyError RuntimeError
        TypeError ValueError ZeroDivisionError NameError ImportError PermissionError
        StopIteration KeyboardInterrupt SystemExit __build_class__""".split()
    safe = {name: getattr(builtins, name) for name in names}
    safe.update(open=_safe_open, __import__=_safe_import)
    return safe


def _validate(code: str) -> types.CodeType:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        # Also blocks str.format's attribute traversal, which bypasses the AST.
        if isinstance(node, ast.Attribute) and (
            node.attr.startswith("_") or node.attr in {"format", "format_map", "mro"}
        ):
            raise PermissionError(f"Attribute is not allowed: {node.attr}")
        if (
            isinstance(node, ast.Name)
            and node.id.startswith("_")
            and node.id != "__import__"
        ):
            raise PermissionError(f"Name is not allowed: {node.id}")
        if isinstance(node, (ast.ImportFrom, ast.Import)):
            names = (
                [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else [a.name for a in node.names]
            )
            if any(not _import_allowed(name) for name in names):
                raise ImportError(f"Import is not allowed: {names}")
        if isinstance(node, ast.ImportFrom) and any(
            a.name.startswith("_") for a in node.names
        ):
            raise ImportError("Private imports are not allowed")
    return compile(tree, "<sandbox>", "exec")


def _tool_wrapper(tool: Mapping[str, Any]) -> Callable[..., Any]:
    def call_tool(*args: Any, **arguments: Any) -> Any:
        global ACTIVE
        properties = list(tool.get("input_schema", {}).get("properties", {}))
        if len(args) > len(properties):
            raise TypeError("Too many positional tool arguments")
        for key, value in zip(properties, args):
            if key in arguments:
                raise TypeError(f"Duplicate argument: {key}")
            arguments[key] = value
        # Normalize user objects while restrictions are still active. A custom
        # dict subclass must not execute callbacks in the trusted protocol layer.
        arguments = json.loads(
            json.dumps(arguments, default=lambda value: "<non-JSON value>")
        )
        remaining = signal.setitimer(signal.ITIMER_REAL, 0)[0]
        was_active = ACTIVE
        ACTIVE = False
        try:
            _send({"type": "tool_call", "name": tool["name"], "arguments": arguments})
            response = json.loads(INPUT.readline())
        finally:
            ACTIVE = was_active
            signal.setitimer(signal.ITIMER_REAL, remaining)
        if not response["success"]:
            raise RuntimeError(response["error"])
        return response.get("result")

    return call_tool


def _final_answer(answer: str) -> NoReturn:
    if not isinstance(answer, str):
        raise TypeError("final_answer expects a string")
    raise _FinalAnswer(answer)


class _Output:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.value = ""
        self.truncated = False

    def write(self, text: str) -> int:
        chunk = text[: max(0, self.limit - len(self.value))]
        self.value += chunk
        if len(chunk) < len(text) and not self.truncated:
            self.value += "\n[Output truncated due to size limit]"
            self.truncated = True
        return len(text)

    def flush(self) -> None:
        pass


def _timeout(signum: int, frame: FrameType | None) -> NoReturn:
    raise _CodeTimeout()


def _bounded_result(value: Any, limit: int) -> Any:
    """Keep JSON containers intact while shortening large string fields."""
    normalized = json.loads(json.dumps(value, default=lambda item: "<non-JSON value>"))

    def count_strings(item: Any) -> int:
        if isinstance(item, str):
            return 1
        if isinstance(item, dict):
            return sum(count_strings(child) for child in item.values())
        if isinstance(item, list):
            return sum(count_strings(child) for child in item)
        return 0

    marker = "\n[Result field truncated due to size limit]"
    share = max(64, limit // max(1, count_strings(normalized)) - len(marker))

    def shorten(item: Any, field: str = "") -> Any:
        if isinstance(item, str) and len(item) > share:
            if field in {"stdout", "stderr"}:
                start = share // 3
                return item[:start] + marker + "\n" + item[-(share - start) :]
            return item[:share] + marker
        if isinstance(item, dict):
            return {key: shorten(child, key) for key, child in item.items()}
        if isinstance(item, list):
            return [shorten(child, field) for child in item]
        return item

    return shorten(normalized)


def execute(
    request: Mapping[str, Any], environment: dict[str, Any]
) -> dict[str, Any]:
    global ACTIVE, CONFIG, EXEC_CODE
    CONFIG = request["config"]
    stdout = _Output(CONFIG.get("max_output_chars", 12000))
    stderr = _Output(CONFIG.get("max_output_chars", 12000))
    environment.update(
        __builtins__=_restricted_builtins(),
        __name__="__sandbox__",
        final_answer=_final_answer,
    )
    environment.pop("result", None)
    for tool in request["tools"]:
        environment[tool["python_name"]] = _tool_wrapper(tool)
    try:
        code = _validate(request["code"])
        EXEC_CODE = code
        signal.setitimer(signal.ITIMER_REAL, CONFIG["max_execution_time_seconds"])
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            ACTIVE = True
            exec(code, environment)
        result = {"success": True, "result": environment.get("result")}
    except _FinalAnswer as done:
        result = {"success": True, "completed": True, "final_answer": done.answer}
    except _CodeTimeout:
        result = {
            "success": False,
            "error": "Sandbox execution timed out; output is partial",
        }
    except (KeyboardInterrupt, SystemExit) as exc:
        return {
            "type": "control",
            "exception": type(exc).__name__,
            "code": getattr(exc, "code", None),
        }
    except Exception as exc:
        result = {"success": False, "error": f"{type(exc).__name__}: {exc}"}
    finally:
        ACTIVE = False
        signal.setitimer(signal.ITIMER_REAL, 0)
    result.update(stdout=stdout.value, stderr=stderr.value)
    ACTIVE = True
    signal.setitimer(signal.ITIMER_REAL, 1)
    try:
        if "result" in result:
            limit = CONFIG.get("max_output_chars", 12000)
            result["result"] = _bounded_result(result["result"], limit)
    except (Exception, _CodeTimeout) as exc:
        result = {
            "success": False,
            "error": f"Result serialization failed: {type(exc).__name__}",
            "stdout": stdout.value,
            "stderr": stderr.value,
        }
    finally:
        ACTIVE = False
        signal.setitimer(signal.ITIMER_REAL, 0)
    return {"type": "result", "data": result}


def main() -> None:
    sys.addaudithook(_audit)
    signal.signal(signal.SIGALRM, _timeout)
    environment: dict[str, Any] = {}
    for line in INPUT:
        request = json.loads(line)
        if not environment:
            limit = request["config"]["max_memory_mb"] * 1024 * 1024
            # RLIMIT_AS is supported on Linux; Docker independently caps RAM.
            if sys.platform == "linux":
                resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
        response = execute(request, environment)
        if (
            response["type"] == "control"
            and response["exception"] == "KeyboardInterrupt"
        ):
            response.pop("code", None)
        _send(response)
        if response["type"] == "control" or not request.get("persistent", False):
            break


if __name__ == "__main__":
    main()
