"""Turn an LLM response into Python code."""

import json
import re
import ast
import keyword


def _normalize_tags(text: str) -> str:
    """Convert DeepSeek's DSML tag names to ordinary XML-like tags."""
    return text.replace("｜DSML｜", "")


def visible_response(text: str) -> str:
    """Remove private reasoning while keeping the model's visible action."""
    return re.sub(
        r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE
    ).strip()


def _capture_expression(code: str) -> str:
    """Save a single expression so its value appears in the observation."""
    tree = ast.parse(code)
    if len(tree.body) == 1 and isinstance(tree.body[0], ast.Expr):
        value = tree.body[0].value
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "print"
            and len(value.args) == 1
            and not value.keywords
            and isinstance(value.args[0], ast.Call)
        ):
            value = value.args[0]
        expression = ast.get_source_segment(code, value)
        if expression:
            return "result = " + expression
    return code


def _normalize_final_answer(code: str) -> str:
    """Recover a few common ways models accidentally describe submission."""
    tree = ast.parse(code)
    if len(tree.body) != 1:
        return code

    statement = tree.body[0]

    def is_get_patch_call(value: ast.AST | None) -> bool:
        return (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "get_patch"
            and not value.args
            and not value.keywords
        )

    def is_get_patch_text(value: ast.AST | None) -> bool:
        return isinstance(value, ast.Constant) and value.value == "get_patch()"

    def is_final_answer_with_get_patch_text(value: ast.AST | None) -> bool:
        if not (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "final_answer"
        ):
            return False
        values = list(value.args) + [item.value for item in value.keywords]
        return len(values) == 1 and is_get_patch_text(values[0])

    # final_answer = get_patch()
    if (
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id == "final_answer"
        and is_get_patch_call(statement.value)
    ):
        return "result = final_answer(get_patch())"

    # final_answer: "get_patch()"
    if (
        isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
        and statement.target.id == "final_answer"
        and statement.value is None
        and is_get_patch_text(statement.annotation)
    ):
        return "result = final_answer(get_patch())"

    # {"final_answer": "get_patch()"}, with or without result =
    value = statement.value if isinstance(statement, (ast.Expr, ast.Assign)) else None
    if is_final_answer_with_get_patch_text(value):
        return "result = final_answer(get_patch())"
    if (
        isinstance(value, ast.Dict)
        and len(value.keys) == 1
        and isinstance(value.keys[0], ast.Constant)
        and value.keys[0].value == "final_answer"
        and is_get_patch_text(value.values[0])
    ):
        return "result = final_answer(get_patch())"

    return code


def _tool_repr(name: object, arguments: object) -> str:
    """Turn a tool name and argument dictionary into a Python function."""
    if not isinstance(name, str) or not isinstance(arguments, dict):
        raise ValueError("Tool call needs a name and argument object")
    name = re.sub(r"\W", "_", name)
    if name[:1].isdigit():
        name = "tool_" + name
    if (
        not name.isidentifier()
        or keyword.iskeyword(name)
        or not all(
            isinstance(key, str) and key.isidentifier() and not keyword.iskeyword(key)
            for key in arguments
        )
    ):
        raise ValueError("Invalid tool call")
    args = ", ".join(f"{key}={value!r}" for key, value in arguments.items())
    return f"result = {name}({args})"


def _minimax_call(text: str) -> str | None:
    """Extract the native tool-call form sometimes returned by MiniMax."""
    match = re.search(
        r"<minimax:tool_call>\s*(.*?)(?:</minimax:tool_call>|```|<end_code>|\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if not match:
        return None

    call = match.group(1).strip()
    invoke = re.fullmatch(
        r"invoke\(([^()\s]+)\)\s+args\s+(\{.*\})",
        call,
        re.DOTALL,
    )
    if invoke:
        return _tool_repr(invoke.group(1), json.loads(invoke.group(2)))

    ast.parse(call)
    return call


def _fenced_tool_call(text: str) -> tuple[str, bool] | None:
    """Find a single function call in a Python or unlabelled code fence."""
    pattern = r"```([A-Za-z0-9_-]*)[ \t]*\n(.*?)(?:```|<end_code>|\Z)"
    for match in re.finditer(pattern, text, re.DOTALL | re.IGNORECASE):
        language = match.group(1).lower()
        if language not in {"", "python", "py"}:
            continue
        candidate = match.group(2).strip()
        try:
            tree = ast.parse(candidate)
        except SyntaxError:
            continue
        if len(tree.body) != 1:
            continue
        statement = tree.body[0]
        value = (
            statement.value if isinstance(statement, (ast.Expr, ast.Assign)) else None
        )
        if isinstance(value, ast.Call):
            return candidate, language == ""
    return None


def extract_code(text: str) -> str:
    """Extract one Python block or tool call from an LLM response."""
    text = _normalize_tags(text)

    fenced_call = _fenced_tool_call(text)
    if fenced_call:
        return fenced_call[0]

    """ ```python
    def add(a, b):
        return a + b
    ```
    """
    match = re.search(
        r"```python\s*(.*?)(?:```|<end_code>)", text, re.DOTALL | re.IGNORECASE
    )
    if match:
        return match.group(1).strip()

    minimax_call = _minimax_call(text)
    if minimax_call is not None:
        return minimax_call

    """
    <invoke name="read_file">
    <parameter name="filepath">/testbed/a.py</parameter>
    </invoke>
    """
    match = re.search(r'<invoke\s+name="(\w+)"[^>]*>(.*?)</invoke>', text, re.DOTALL)
    if match:
        arguments = {}
        parameters = re.findall(
            r'<parameter(?:\s+name="(\w+)")?[^>]*>(.*?)</parameter>',
            match.group(2),
            re.DOTALL,
        )
        for name, value in parameters:
            value = value.strip()
            if name:
                try:
                    arguments[name] = json.loads(value)
                except json.JSONDecodeError:
                    arguments[name] = value
            else:
                arguments.update(json.loads(value))
        return _tool_repr(match.group(1), arguments)

    # Hermes JSON
    matches = re.findall(r"<tool_call>(.*?)</tool_call>", text, re.DOTALL)
    if matches:
        call = json.loads(matches[0])
        arguments = call.get("arguments", {})
        if isinstance(arguments, str):
            arguments = json.loads(arguments)
        return _tool_repr(call["name"], arguments)

    # ReAct
    match = re.search(
        r"^Action:\s*(\w+).*?^Action Input:\s*({.*})",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if match:
        return _tool_repr(match.group(1), json.loads(match.group(2)))

    # Some models return the requested Python call without a Markdown fence.
    candidate = text.strip()
    try:
        ast.parse(candidate)
    except SyntaxError:
        pass
    else:
        return candidate

    raise ValueError("No supported code or tool call found")


def extract_with_feedback(text: str) -> tuple[str, str]:
    """Return normalized code plus an explicit note for any recovered formatting."""
    feedback = ""
    # Reasoning models may show example code inside <think> before their real
    # answer. Only code outside the private reasoning section should run.
    visible_text = _normalize_tags(visible_response(text))
    fenced_call = _fenced_tool_call(visible_text)
    if fenced_call:
        code, unlabelled = fenced_call
        if unlabelled:
            feedback = "Recovered a tool call from an unlabelled code fence."
    else:
        # Stop sequences are removed by providers, so an open fence is common.
        match = re.search(
            r"```(?:python|py)\s*\n(.*?)(?:```|<end_code>|\Z)",
            visible_text,
            re.DOTALL | re.IGNORECASE,
        )
    if not fenced_call and match:
        code = match.group(1).strip()
        if not visible_text[match.start() :].rstrip().endswith(("```", "<end_code>")):
            feedback = "Recovered an unclosed code fence by treating end of response as its end."
    elif not fenced_call:
        try:
            code = extract_code(visible_text)
        except (KeyError, TypeError, AttributeError, json.JSONDecodeError) as exc:
            raise ValueError(f"Malformed tool call: {exc}") from exc
        if "<minimax:tool_call>" in visible_text.lower():
            feedback = "Recovered MiniMax native tool-call format."
        if len(re.findall(r"<tool_call>.*?</tool_call>", visible_text, re.DOTALL)) > 1:
            note = "The model returned several native tool calls; only the first was executed."
            feedback = f"{feedback}\n{note}".strip()
    if not code:
        raise ValueError("No valid code block found: empty code")

    # Some models accidentally put a JSON closing brace after a Python call.
    # Remove it only when the original code is invalid and the shorter code is valid.
    try:
        ast.parse(code)
    except SyntaxError:
        repaired = code[:-1].rstrip() if code.endswith("}") else ""
        if repaired:
            try:
                ast.parse(repaired)
            except SyntaxError:
                pass
            else:
                code = repaired
                note = "Removed one extra closing brace from the Python call."
                feedback = f"{feedback}\n{note}".strip()

    normalized = _normalize_final_answer(code)
    if normalized != code:
        code = normalized
        note = "Converted the model's submission notation to final_answer(get_patch())."
        feedback = f"{feedback}\n{note}".strip()

    code = _capture_expression(code)
    ast.parse(code)
    return code, feedback
