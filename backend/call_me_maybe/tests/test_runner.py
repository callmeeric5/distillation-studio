from __future__ import annotations

import pytest

from backend.call_me_maybe.src.runner import parse_functions, run_function_call


FUNCTIONS = [
    {
        "fn_name": "fn_add_numbers",
        "args_names": ["a", "b"],
        "args_types": {"a": "float", "b": "float"},
        "return_type": "float",
    },
    {
        "fn_name": "fn_reverse_string",
        "args_names": ["s"],
        "args_types": {"s": "str"},
        "return_type": "str",
    },
]


class FakeModel:
    def __init__(self, selected_name: str) -> None:
        self.selected_name = selected_name
        self.prompt_token_count: int | None = None

    def encode(self, text: str) -> list[int]:
        token_ids = [ord(char) for char in text]
        if self.prompt_token_count is None:
            self.prompt_token_count = len(token_ids)
        return token_ids

    def get_logits_from_input_ids(self, input_ids: list[int]) -> list[float]:
        assert self.prompt_token_count is not None
        selected_tokens = input_ids[self.prompt_token_count:]
        next_index = len(selected_tokens)
        next_token = ord(self.selected_name[next_index])
        logits = [0.0] * 256
        logits[next_token] = 100.0
        return logits


def test_run_function_call_selects_function_and_extracts_parameters() -> None:
    functions = parse_functions(FUNCTIONS)

    output = run_function_call(
        prompt="What is the sum of 2 and 3?",
        functions=functions,
        model=FakeModel("fn_add_numbers"),
    )

    assert output.model_dump() == {
        "prompt": "What is the sum of 2 and 3?",
        "name": "fn_add_numbers",
        "parameters": {"a": 2.0, "b": 3.0},
    }


def test_run_function_call_extracts_string_parameters() -> None:
    functions = parse_functions(FUNCTIONS)

    output = run_function_call(
        prompt="Reverse the string 'hello'",
        functions=functions,
        model=FakeModel("fn_reverse_string"),
    )

    assert output.name == "fn_reverse_string"
    assert output.parameters == {"s": "hello"}


def test_parse_functions_rejects_empty_config() -> None:
    with pytest.raises(ValueError, match="At least one function"):
        parse_functions([])
