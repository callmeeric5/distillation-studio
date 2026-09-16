from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, SecretStr, model_validator


Benchmark = Literal["mbpp", "swebench"]
Provider = Literal["openrouter", "groq"]


class RunCreateRequest(BaseModel):
    benchmark: Benchmark
    provider: Provider
    model: str = Field(..., min_length=1, max_length=160)
    api_key: SecretStr = Field(..., min_length=1, max_length=512)
    task_id: str | None = Field(default=None, max_length=100)
    task_definition: str | None = Field(default=None, max_length=6000)
    function_definition: str | None = Field(default=None, max_length=1000)
    test_imports: list[str] = Field(default_factory=list, max_length=20)
    test_list: list[str] = Field(default_factory=list, min_length=0, max_length=20)

    @model_validator(mode="after")
    def validate_task(self) -> "RunCreateRequest":
        if self.benchmark == "swebench":
            if not self.task_id:
                raise ValueError("A built-in SWE-bench task is required.")
            return self
        if not (self.task_definition or "").strip():
            raise ValueError("MBPP task definition is required.")
        if not (self.function_definition or "").strip():
            raise ValueError("MBPP function definition is required.")
        if not self.test_list:
            raise ValueError("MBPP requires at least one test.")
        for value in [*self.test_imports, *self.test_list]:
            if not value.strip() or len(value) > 1000:
                raise ValueError("Imports and tests must be non-empty and at most 1000 characters.")
        return self


class RunCreatedResponse(BaseModel):
    run_id: str
    status: Literal["queued"]


class RunStatusResponse(BaseModel):
    run_id: str
    benchmark: Benchmark
    provider: Provider
    model: str
    status: Literal["queued", "running", "succeeded", "failed", "cancelled"]
    queue_position: int | None = None
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
    elapsed_seconds: float
    iterations: int
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    steps: list[dict]
    solution: str = ""
    error: str | None = None
