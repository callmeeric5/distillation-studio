from __future__ import annotations

from dataclasses import dataclass

from backend.trace_ops_agent.models import ProviderName


@dataclass(frozen=True)
class ProviderConfig:
    name: ProviderName
    models: tuple[str, ...]


PROVIDERS: dict[ProviderName, ProviderConfig] = {
    "openai": ProviderConfig("openai", ("gpt-4o-mini", "gpt-4.1-mini")),
    "gemini": ProviderConfig(
        "gemini",
        ("gemini-2.5-flash-lite", "gemini-2.5-flash"),
    ),
    "anthropic": ProviderConfig(
        "anthropic",
        ("claude-3-5-haiku-latest", "claude-3-5-sonnet-latest"),
    ),
    "deepseek": ProviderConfig("deepseek", ("deepseek-chat", "deepseek-reasoner")),
}


def validate_provider_model(provider: str, model: str) -> ProviderName:
    if provider not in PROVIDERS:
        supported = ", ".join(PROVIDERS)
        raise ValueError(f"Unsupported provider '{provider}'. Supported providers: {supported}.")

    provider_name = provider
    config = PROVIDERS[provider_name]
    if model not in config.models:
        supported = ", ".join(config.models)
        raise ValueError(f"Unsupported model '{model}' for {provider}. Supported models: {supported}.")

    return provider_name


def build_chat_model(provider: ProviderName, model: str, api_key: str):
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=model, api_key=api_key, temperature=0)

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(model=model, google_api_key=api_key, temperature=0)

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=model, api_key=api_key, temperature=0)

    if provider == "deepseek":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url="https://api.deepseek.com",
            temperature=0,
        )

    raise ValueError(f"Unsupported provider '{provider}'.")
