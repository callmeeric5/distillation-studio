from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    model_name: str
    provider_url: str
    api_key_env: str | None = None
    timeout_seconds: float = Field(default=60, gt=0)
    max_retries: int = Field(default=2, ge=0, le=10)


class LLMResponse(BaseModel):
    model_name: str
    api_url: str
    llm_output: str
    input_tokens: int
    output_tokens: int
    request_time_ms: float
    retries: int
