import re
from pathlib import Path
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator


class SandboxConfig(BaseModel):
    """Security limits applied inside the sandbox container."""

    authorized_imports: List[str] = Field(
        default_factory=lambda: [
            "math",
            "math.*",
            "collections",
            "collections.*",
            "itertools",
            "re",
            "json",
            "typing",
            "typing.*",
            "functools",
            "operator",
            "heapq",
            "bisect",
            "copy",
            "string",
            "random",
            "datetime",
            "datetime.*",
            "array",
            "cmath",
        ]
    )
    allowed_directories: List[str] = Field(
        default_factory=lambda: ["/testbed", "/tmp/agent"]
    )
    max_execution_time_seconds: int = Field(default=30, gt=0)
    max_memory_mb: int = Field(default=512, ge=32)
    max_output_chars: int = Field(default=12000, ge=256)

    @field_validator("allowed_directories")
    @classmethod
    def validate_directories(cls, paths: List[str]) -> List[str]:
        if not paths or any(
            not Path(p).is_absolute() or Path(p) == Path("/") for p in paths
        ):
            raise ValueError("Use non-root absolute sandbox directories")
        return paths

    @classmethod
    def from_json_file(cls, path: str | Path) -> "SandboxConfig":
        return cls.model_validate_json(Path(path).read_text())


class SandboxTool(BaseModel):
    """Description of one tool discovered from the connected MCP server."""

    name: str
    description: str = ""
    input_schema: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, name: str) -> str:
        if not name.strip():
            raise ValueError("Tool name must not be empty")
        return name

    @property
    def python_name(self) -> str:
        name = re.sub(r"\W", "_", self.name)
        return name if not name[:1].isdigit() else f"tool_{name}"


class SandboxResult(BaseModel):
    """Observation returned to the agent loop after one execution."""

    success: bool
    completed: bool = False
    final_answer: Optional[str] = None
    result: Any = None
    stdout: str = ""
    stderr: str = ""
    changed_files: str = ""
    error: Optional[str] = None
