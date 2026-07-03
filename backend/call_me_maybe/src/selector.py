from typing import Protocol

from .models import Function
from .promot import build_prompt


class SelectionModel(Protocol):
    def encode(self, text: str) -> list[int]:
        """Return tokenizer ids for text."""

    def get_logits_from_input_ids(self, input_ids: list[int]) -> list[float]:
        """Return next-token logits for a token id prefix."""


def select_function(
    prompt: str,
    functions: list[Function],
    model: SelectionModel,
) -> Function:
    """Select a function, using the LLM when it is available."""

    fn_names = [function.name for function in functions]
    llm_prompt = build_prompt(prompt, functions)
    selected_fn = _constrained_select(llm_prompt, fn_names, model)
    return _function_by_name(selected_fn, functions)


def _constrained_select(
    prompt: str,
    functions: list[str],
    model: SelectionModel,
) -> str:
    """Greedily decode one function while allowing only valid prefixes."""
    prompt_tokens = model.encode(prompt)
    fn_tokens_dict = {
        name: model.encode(prompt + name)[len(prompt_tokens):]
        for name in functions
    }
    selected_tokens: list[int] = []
    while True:
        # if found the matched function name, return function name
        for name, fn_tokens in fn_tokens_dict.items():
            if selected_tokens == fn_tokens:
                return name
        # append one next token to the matched prefix function tokens,
        # a dict trie implementation
        next_fn_candidate = set()
        for fn_tokens in fn_tokens_dict.values():
            if selected_tokens == fn_tokens[: len(selected_tokens)] and len(
                fn_tokens
            ) > len(selected_tokens):
                next_fn_candidate.add(fn_tokens[len(selected_tokens)])

        if not next_fn_candidate:
            raise ValueError("no valid function name token remains")

        logits = model.get_logits_from_input_ids(
            prompt_tokens + selected_tokens
        )
        next_token = max(next_fn_candidate, key=lambda i: logits[i])
        selected_tokens.append(next_token)


def _function_by_name(name: str, functions: list[Function]) -> Function:
    for function in functions:
        if function.name == name:
            return function
    raise ValueError(f"unknown function selected: {name}")
