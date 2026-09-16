"""The evaluation JSON schema from the subject; one record per real step."""

from datetime import datetime
from pydantic import BaseModel, Field


def timestamp() -> str:
    return datetime.now().isoformat()


class StepMetrics(BaseModel):
    step: int
    input_tokens: int = 0
    output_tokens: int = 0
    request_time_ms: float = 0
    api_url: str = ""
    model_name: str = ""
    llm_output: str = ""
    sandbox_input: str = ""
    sandbox_output: str = ""
    retries: int = 0
    timestamp: str = Field(default_factory=timestamp)


class SolutionOutput(BaseModel):
    task_id: str
    benchmark: str
    success: bool = False
    solution: str = ""  # Python source for MBPP; unified diff for SWE-bench.
    system_prompt: str = ""
    iterations: int = 0
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_time_seconds: float = 0
    steps: list[StepMetrics] = Field(default_factory=list)
    error: str | None = None
    timestamp: str = Field(default_factory=timestamp)
