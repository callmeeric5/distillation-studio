from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


AllowedType = Literal["str", "float", "int", "bool"]
ParameterValue = str | float | int | bool


class FunctionDefinition(BaseModel):
    fn_name: str = Field(..., min_length=1, max_length=120)
    args_names: list[str] = Field(..., min_length=1, max_length=20)
    args_types: dict[str, AllowedType]
    return_type: AllowedType


class FunctionCallRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    functions_definition: list[FunctionDefinition] = Field(
        ..., min_length=1, max_length=50
    )


class FunctionCallResponse(BaseModel):
    prompt: str
    name: str
    parameters: dict[str, ParameterValue]
