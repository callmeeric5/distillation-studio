from __future__ import annotations

from pydantic import BaseModel, Field


MAX_VALUES = 500


class RunRequest(BaseModel):
    values: list[int] = Field(..., min_length=1, max_length=MAX_VALUES)
    algorithm: str = "medium"


class GenerateRequest(BaseModel):
    size: int = Field(20, ge=2, le=MAX_VALUES)
    minimum: int = Field(-250, ge=-100000)
    maximum: int = Field(250, le=100000)
