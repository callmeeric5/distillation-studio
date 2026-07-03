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
    encoded_functions = _encode_many(
        model,
        [prompt + name for name in functions],
    )
    fn_tokens_dict = {
        name: token_ids[len(prompt_tokens):]
        for name, token_ids in zip(functions, encoded_functions, strict=True)
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

        candidate_logits = _candidate_logits(
            model,
            prompt_tokens + selected_tokens,
            next_fn_candidate,
        )
        next_token = max(next_fn_candidate, key=lambda i: candidate_logits[i])
        selected_tokens.append(next_token)


def _function_by_name(name: str, functions: list[Function]) -> Function:
    for function in functions:
        if function.name == name:
            return function
    raise ValueError(f"unknown function selected: {name}")


def _encode_many(model: SelectionModel, texts: list[str]) -> list[list[int]]:
    encode_many = getattr(model, "encode_many", None)
    if callable(encode_many):
        return encode_many(texts)
    return [model.encode(text) for text in texts]


def _candidate_logits(
    model: SelectionModel,
    input_ids: list[int],
    candidates: set[int],
) -> dict[int, float]:
    candidate_logits = getattr(
        model,
        "get_candidate_logits_from_input_ids",
        None,
    )
    if callable(candidate_logits):
        return candidate_logits(input_ids, sorted(candidates))

    logits = model.get_logits_from_input_ids(input_ids)
    return {candidate: logits[candidate] for candidate in candidates}
