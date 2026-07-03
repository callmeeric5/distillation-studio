from __future__ import annotations

from typing import Protocol

from .extractor import extract_parameters
from .models import Function, Function_Calling_Output
from .selector import select_function


class ModelClient(Protocol):
    def encode(self, text: str) -> list[int]:
        """Return tokenizer ids for text."""

    def get_logits_from_input_ids(self, input_ids: list[int]) -> list[float]:
        """Return next-token logits for a token id prefix."""


def parse_functions(functions_definition: list[dict]) -> list[Function]:
    functions = [Function.model_validate(item) for item in functions_definition]
    if not functions:
        raise ValueError("At least one function definition is required.")
    return functions


def run_function_call(
    prompt: str,
    functions: list[Function],
    model: ModelClient,
) -> Function_Calling_Output:
    if not prompt.strip():
        raise ValueError("Prompt is required.")
    if not functions:
        raise ValueError("At least one function definition is required.")

    function = select_function(prompt, functions, model)
    return Function_Calling_Output(
        prompt=prompt,
        name=function.name,
        parameters=extract_parameters(prompt, function),
    )
