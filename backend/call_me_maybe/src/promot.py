import json

from .models import Function


def build_tools(functions: list[Function]) -> str:
    """Serialize function definitions for the LLM prompt."""
    return "\n".join(
        json.dumps(function.model_dump()) for function in functions
    )


def build_prompt(user_prompt: str, functions: list[Function]) -> str:
    """Build the function-selection prompt in the Hermes format."""
    fn_tools = build_tools(functions)
    return f"""
    <|im_start|>system
    You are a function calling AI model. You are provided with function \
    signatures within <tools></tools> XML tags.
    You need to choose the most suitable function \
    to assist with the user query.
    Don't make assumptions about what values to plug into functions \
    and don't use any functions out of the provided tools.
    <tool_call>
    {fn_tools}
    </tool_call>
    <|im_end|>
    <|im_start|>user
    {user_prompt}
    <|im_end|>
    <|im_start|>assistant
    <tool_call>
"""
