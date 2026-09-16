from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RagAnswerRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    question: str = Field(..., min_length=1, max_length=4000)
    k: int = Field(default=5, ge=1, le=10)


class RagSource(BaseModel):
    file_path: str
    first_character_index: int
    last_character_index: int
    content: str


class RagAnswerResponse(BaseModel):
    question: str
    answer: str
    sources: list[RagSource]
