import json
from pathlib import Path
from typing import Any

from .models import Function, Prompt


class Parser:
    """Read project JSON inputs and write generated JSON results."""

    def __init__(self, path: str) -> None:
        self.file_path = Path(path)

    def _load_json(self) -> list[dict[str, Any]]:
        """Load and validate a JSON array of objects."""
        if not self.file_path.exists():
            raise ValueError(f"{self.file_path} is not found")

        if self.file_path.suffix != ".json":
            raise ValueError(f"{self.file_path} is not a .json file")

        try:
            with self.file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"can't decode {self.file_path}") from e

        if not isinstance(data, list):
            raise ValueError(f"{self.file_path} is not a valid Json array")

        if not all(isinstance(item, dict) for item in data):
            raise ValueError(
                f"{self.file_path} is not a valid Json array of dict"
            )

        return data

    def load_functions(self) -> list[Function]:
        """Load function definitions from the configured JSON file."""
        return [Function.model_validate(item) for item in self._load_json()]

    def load_prompts(self) -> list[Prompt]:
        """Load natural-language prompts from the configured JSON file."""
        return [Prompt.model_validate(item) for item in self._load_json()]

    def save_result(self, res: list[dict[str, Any]]) -> None:
        """Write generated function calls as valid JSON."""
        dir_path = self.file_path.parent
        dir_path.mkdir(parents=True, exist_ok=True)
        with self.file_path.open("w", encoding="utf-8") as f:
            json.dump(res, f, indent=4)
