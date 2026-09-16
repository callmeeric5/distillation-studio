"""OpenAI-compatible LLM client with key rotation and usage tracking."""

import asyncio
import json
import os
import re
import time
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlparse

import httpx

from agent_smith.models.llm import LLMResponse
from agent_smith.models.llm import ProviderConfig
from agent_smith.models.sandbox import SandboxTool

PROVIDER_KEYS = {
    "openrouter.ai": "OPENROUTER_API_KEYS",
    "api.groq.com": "GROQ_API_KEYS",
    "api.together.ai": "TOGETHER_API_KEYS",
    "api.together.xyz": "TOGETHER_API_KEYS",
    "api.mistral.ai": "MISTRAL_API_KEYS",
    "api.fireworks.ai": "FIREWORKS_API_KEYS",
}


def response_error(response: httpx.Response) -> str:
    """Return the provider's short error message without headers or API keys."""
    try:
        data = response.json()
        if isinstance(data, dict):
            error = data.get("error", data)
            message = error.get("message") if isinstance(error, dict) else str(error)
        else:
            message = str(data)
    except (ValueError, TypeError, AttributeError):
        message = response.text
    message = " ".join(str(message or "Bad request").split())
    return message[:500]


def retry_delay(response: httpx.Response, retry: int) -> float:
    """Use a provider's rate-limit delay, or a short exponential delay."""
    if response.status_code == 429:
        value = response.headers.get("retry-after", "")
        if not value:
            match = re.search(
                r"try again in ([\d.]+)s", response_error(response), re.IGNORECASE
            )
            value = match.group(1) if match else ""
        try:
            return float(value) + 0.25
        except ValueError:
            pass
    return min(2**retry, 4)


def completion_data(
    response: httpx.Response,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Validate one successful HTTP response from an OpenAI-compatible API."""
    try:
        data = response.json()
    except ValueError as exc:
        raise ValueError("provider returned invalid JSON") from exc
    if not isinstance(data, dict):
        raise ValueError("provider response must be a JSON object")
    if data.get("error"):
        raise ValueError(response_error(response))

    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("provider response is missing choices")
    choice = choices[0]
    message = choice.get("message") if isinstance(choice, dict) else None
    if not isinstance(message, dict):
        raise ValueError("provider response is missing the assistant message")
    content = message.get("content")
    has_content = isinstance(content, str) and bool(content.strip())
    if not has_content and not message.get("tool_calls"):
        finish = (
            choice.get("native_finish_reason")
            or choice.get("finish_reason")
            or "unknown"
        )
        raise ValueError(
            f"provider response contains an empty assistant message ({finish})"
        )

    usage = data.get("usage")
    if not isinstance(usage, dict):
        usage = {}
    return data, message, usage


def estimated_tokens(text: str) -> int:
    """Estimate tokens when an OpenAI-compatible provider omits usage."""
    return (len(text) + 2) // 3


def token_usage(
    usage: Mapping[str, Any], messages: Sequence[Mapping[str, str]], answer: str
) -> tuple[int, int]:
    """Prefer provider counts and fill missing counts with conservative estimates."""
    input_tokens = usage.get("prompt_tokens")
    output_tokens = usage.get("completion_tokens")
    if not isinstance(input_tokens, int) or input_tokens <= 0:
        input_tokens = sum(
            estimated_tokens(message.get("content", "")) + 4 for message in messages
        )
    if (
        not isinstance(output_tokens, int)
        or output_tokens < 0
        or (output_tokens == 0 and answer)
    ):
        output_tokens = estimated_tokens(answer)
    return input_tokens, output_tokens


class UnifiedLLMClient:
    def __init__(
        self, config: ProviderConfig, api_keys: Sequence[str] | None = None
    ) -> None:
        self.config = config
        name = config.api_key_env or PROVIDER_KEYS.get(
            urlparse(config.provider_url).hostname, ""
        )
        if api_keys is None:
            raw = os.getenv(name, "")
            if not raw and name.endswith("_KEYS"):
                raw = os.getenv(name[:-1], "")
            self.keys = [key.strip() for key in raw.split(",") if key.strip()]
        else:
            self.keys = [key.strip() for key in api_keys if key.strip()]
        if not self.keys:
            raise ValueError("No API keys found; configure .env or --api-key-env")
        self.total_requests = 0
        self.last_attempts = 0
        self.last_retry_errors = []
        self.tools = []
        self.required_tool = None
        self.client = httpx.AsyncClient(timeout=config.timeout_seconds)

    def set_tools(self, tools: Sequence[SandboxTool]) -> None:
        """Provide MCP tools in the standard chat-completions format."""
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.python_name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                },
            }
            for tool in tools
        ]
        self.tools.append(
            {
                "type": "function",
                "function": {
                    "name": "final_answer",
                    "description": "Submit the final source code or git patch.",
                    "parameters": {
                        "type": "object",
                        "properties": {"answer": {"type": "string"}},
                        "required": ["answer"],
                    },
                },
            }
        )

    async def generate(
        self,
        messages: list[dict[str, str]],
        max_tokens: int,
        timeout: float = 120,
    ) -> LLMResponse:
        """Send one request. The timeout includes retries and backoff delays."""
        started = time.monotonic()
        deadline = started + timeout
        self.last_attempts = 0
        self.last_retry_errors = []
        url = self.config.provider_url.rstrip("/")
        if not url.endswith("/chat/completions"):
            url += "/chat/completions"
        body = {
            "model": self.config.model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0,
            "stop": ["<end_code>"],
        }
        if self.tools:
            body["tools"] = self.tools
        if self.required_tool:
            body["tool_choice"] = {
                "type": "function",
                "function": {"name": self.required_tool},
            }
        for retry in range(self.config.max_retries + 1):
            key = self.keys[self.total_requests % len(self.keys)]
            self.total_requests += 1
            self.last_attempts += 1
            try:
                # Limit the HTTP request to the task's remaining time.
                response = await asyncio.wait_for(
                    self.client.post(
                        url, headers={"Authorization": f"Bearer {key}"}, json=body
                    ),
                    timeout=max(0, deadline - time.monotonic()),
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                response = None
                another_key_available = False
                adjustable_output = False
                if isinstance(exc, httpx.HTTPStatusError):
                    response = exc.response
                    status = exc.response.status_code
                    error = f"HTTP {status}: {response_error(exc.response)}"
                    another_key_available = self.last_attempts < len(self.keys)
                    key_error = status in {401, 402, 403, 429}
                    unsettled_requests = status == 402 and "in-flight" in error.lower()
                    affordable = re.search(
                        r"can only afford (\d+)", error, re.IGNORECASE
                    )
                    adjustable_output = status == 402 and affordable is not None
                    if adjustable_output:
                        body["max_tokens"] = min(
                            body["max_tokens"], int(affordable.group(1))
                        )
                    retryable = (
                        (another_key_available and key_error)
                        or unsettled_requests
                        or adjustable_output
                        or status == 429
                        or status >= 500
                    )
                else:
                    error = type(exc).__name__
                    retryable = True
                if not retryable or retry == self.config.max_retries:
                    raise RuntimeError(f"LLM request failed: {error}") from None
                self.last_retry_errors.append(error)
                if another_key_available or adjustable_output:
                    delay = 0
                else:
                    delay = (
                        retry_delay(response, retry)
                        if response is not None
                        else min(2**retry, 4)
                    )
                if time.monotonic() + delay >= deadline:
                    raise TimeoutError(
                        "Task time exhausted during API retries"
                    ) from None
                await asyncio.sleep(delay)
                continue

            try:
                data, message, usage = completion_data(response)
            except ValueError as exc:
                error = f"Invalid provider response: {exc}"
                if retry == self.config.max_retries:
                    raise RuntimeError(f"LLM request failed: {error}") from None
                self.last_retry_errors.append(error)
                if "empty assistant message" in str(exc):
                    body["tool_choice"] = "none"
                    body["messages"] = messages + [
                        {
                            "role": "user",
                            "content": (
                                "Your previous response was empty. Do not use native function calling. "
                                "Reply with exactly one Python code block that calls one available tool."
                            ),
                        }
                    ]
                another_key_available = self.last_attempts < len(self.keys)
                delay = 0 if another_key_available else min(2**retry, 4)
                if time.monotonic() + delay >= deadline:
                    raise TimeoutError(
                        "Task time exhausted during API retries"
                    ) from None
                await asyncio.sleep(delay)
                continue

            text = message.get("content") or ""
            if message.get("tool_calls"):
                text = "\n".join(
                    "<tool_call>" + json.dumps(call["function"]) + "</tool_call>"
                    for call in message["tool_calls"]
                )
            input_tokens, output_tokens = token_usage(usage, messages, text)
            return LLMResponse(
                model_name=data.get("model", self.config.model_name),
                api_url=self.config.provider_url,
                llm_output=text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                request_time_ms=(time.monotonic() - started) * 1000,
                retries=retry,
            )

    async def close(self) -> None:
        await self.client.aclose()
