import re

from .models import AllowedType, Function, ParameterValue


def extract_parameters(
    prompt: str,
    function: Function,
) -> dict[str, ParameterValue]:
    """Extract and cast parameters according to a function prototype."""
    values: dict[str, ParameterValue] = {}
    quoted = _quoted_strings(prompt)
    numbers = _numbers(prompt)
    number_index = 0

    for arg_name in function.args:
        arg_type = function.args_types[arg_name]
        if arg_type in {"float", "int"}:
            values[arg_name] = _number_argument(
                arg_type, numbers, number_index
            )
            number_index += 1
        elif arg_type == "bool":
            values[arg_name] = _bool_argument(prompt)
        else:
            values[arg_name] = _string_argument(
                prompt,
                function.name,
                arg_name,
                quoted,
            )

    return values


def _number_argument(
    arg_type: AllowedType,
    numbers: list[str],
    index: int,
) -> ParameterValue:
    raw = numbers[index] if index < len(numbers) else "0"
    if arg_type == "int":
        return int(float(raw))
    return float(raw)


def _bool_argument(prompt: str) -> bool:
    prompt_l = prompt.lower()
    if any(word in prompt_l for word in ("true", "yes", "enabled")):
        return True
    if any(word in prompt_l for word in ("false", "no", "disabled")):
        return False
    numbers = _numbers(prompt)
    return bool(numbers and int(float(numbers[0])) % 2 == 0)


def _string_argument(
    prompt: str,
    function_name: str,
    arg_name: str,
    quoted: list[str],
) -> str:
    if "substitute" in function_name:
        return _substitute_string_argument(prompt, arg_name, quoted)
    if "reverse" in function_name:
        return quoted[0] if quoted else _last_word(prompt)
    if "greet" in function_name:
        return quoted[0] if quoted else _after_keyword(prompt, "greet")
    if quoted:
        arg_index = _argument_index(arg_name)
        return quoted[min(arg_index, len(quoted) - 1)]
    return _last_word(prompt)


def _substitute_string_argument(
    prompt: str,
    arg_name: str,
    quoted: list[str],
) -> str:
    prompt_l = prompt.lower()
    if arg_name == "source_string":
        source = _source_after_in(prompt)
        if source is not None:
            return source
        return quoted[0] if quoted else ""
    if arg_name == "regex":
        if "digit" in prompt_l or "number" in prompt_l:
            return r"\d+"
        if "vowel" in prompt_l:
            return r"[aeiouAEIOU]"
        if quoted:
            return re.escape(quoted[0])
        return ""
    if arg_name == "replacement":
        replacement = _replacement_after_with(prompt)
        if replacement is not None:
            return replacement
        return quoted[1] if len(quoted) > 1 else ""
    return quoted[0] if quoted else ""


def _quoted_strings(prompt: str) -> list[str]:
    matches = re.findall(r"'([^']*)'|\"([^\"]*)\"", prompt)
    return [single or double for single, double in matches]


def _numbers(prompt: str) -> list[str]:
    return re.findall(r"[-+]?\d+(?:\.\d+)?", prompt)


def _source_after_in(prompt: str) -> str | None:
    before_with = re.search(
        r"\bin(?:\s+the\s+string)?\s+['\"](.+)['\"]\s+\bwith\b",
        prompt,
        flags=re.IGNORECASE,
    )
    if before_with:
        return before_with.group(1)
    match = re.search(
        r"\bin(?:\s+the\s+string)?\s+['\"]([^'\"]*)['\"]",
        prompt,
        flags=re.IGNORECASE,
    )
    return match.group(1) if match else None


def _replacement_after_with(prompt: str) -> str | None:
    quoted_match = re.search(
        r"\bwith\s+['\"]([^'\"]*)['\"]",
        prompt,
        flags=re.IGNORECASE,
    )
    if quoted_match:
        return quoted_match.group(1)
    if re.search(r"\bwith\s+asterisks?\b", prompt, flags=re.IGNORECASE):
        return "*"
    word_match = re.search(r"\bwith\s+([A-Za-z0-9_+-]+)", prompt)
    return word_match.group(1) if word_match else None


def _after_keyword(prompt: str, keyword: str) -> str:
    match = re.search(
        rf"\b{re.escape(keyword)}\s+([A-Za-z0-9_+-]+)",
        prompt,
        flags=re.IGNORECASE,
    )
    return match.group(1) if match else _last_word(prompt)


def _last_word(prompt: str) -> str:
    words = re.findall(r"[A-Za-z0-9_+-]+", prompt)
    return words[-1] if words else ""


def _argument_index(arg_name: str) -> int:
    if len(arg_name) == 1 and "a" <= arg_name <= "z":
        return ord(arg_name) - ord("a")
    return 0
