from typing import Literal

from pydantic import BaseModel, Field

AllowedType = Literal["str", "float", "int", "bool"]
ParameterValue = str | float | int | bool


class Prompt(BaseModel):
    """Input prompt loaded from the test JSON file."""

    prompt: str


class Function(BaseModel):
    """Function definition loaded from the tools JSON file."""

    name: str = Field(alias="fn_name")
    args: list[str] = Field(alias="args_names")
    args_types: dict[str, AllowedType]
    return_type: AllowedType


class Function_Calling_Output(BaseModel):
    """Schema of one generated function call."""

    prompt: str
    name: str
    parameters: dict[str, ParameterValue]
