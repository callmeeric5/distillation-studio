import argparse
import sys

from llm_sdk import Small_LLM_Model

from .parser import Parser
from .runner import run_function_call

DEFAULT_PPROMTS_FILE = "data/input/function_calling_tests.json"
DEFAULT_FUNCTIONS_FILE = "data/input/functions_definition.json"
DEFAULT_OUTPUT_FILE = "data/output/function_calls.json"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--functions_definition", default=DEFAULT_FUNCTIONS_FILE, type=str
    )
    parser.add_argument("--input", default=DEFAULT_PPROMTS_FILE, type=str)
    parser.add_argument("--output", default=DEFAULT_OUTPUT_FILE, type=str)
    return parser.parse_args()


def main() -> None:
    """Run the function-calling generation pipeline."""
    args = _parse_args()

    try:
        prompts = Parser(args.input).load_prompts()
        functions = Parser(args.functions_definition).load_functions()
        if not functions:
            raise ValueError("no function definitions provided")
        model = Small_LLM_Model()
        results = []
        for item in prompts:
            output = run_function_call(item.prompt, functions, model)
            results.append(output.model_dump())
        Parser(args.output).save_result(results)
    except ValueError as err:
        print(f"error: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
