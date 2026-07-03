from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.projects.call_me_maybe.router import router
from api.projects.call_me_maybe import service


FUNCTIONS = [
    {
        "fn_name": "fn_add_numbers",
        "args_names": ["a", "b"],
        "args_types": {"a": "float", "b": "float"},
        "return_type": "float",
    }
]


class FakeModel:
    def __init__(self, selected_name: str = "fn_add_numbers") -> None:
        self.selected_name = selected_name
        self.prompt_token_count: int | None = None

    def encode(self, text: str) -> list[int]:
        token_ids = [ord(char) for char in text]
        if self.prompt_token_count is None:
            self.prompt_token_count = len(token_ids)
        return token_ids

    def get_logits_from_input_ids(self, input_ids: list[int]) -> list[float]:
        assert self.prompt_token_count is not None
        selected_tokens = input_ids[self.prompt_token_count:]
        next_token = ord(self.selected_name[len(selected_tokens)])
        logits = [0.0] * 256
        logits[next_token] = 100.0
        return logits


class UnavailableModel:
    def encode(self, text: str) -> list[int]:
        raise service.ModelServiceError("connection refused")

    def get_logits_from_input_ids(self, input_ids: list[int]) -> list[float]:
        return []


def test_run_endpoint_returns_function_call(monkeypatch) -> None:
    monkeypatch.setattr(service, "RemoteModelClient", FakeModel)
    client = TestClient(build_app())

    response = client.post(
        "/api/projects/call-me-maybe/run",
        json={
            "prompt": "What is the sum of 2 and 3?",
            "functions_definition": FUNCTIONS,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "prompt": "What is the sum of 2 and 3?",
        "name": "fn_add_numbers",
        "parameters": {"a": 2.0, "b": 3.0},
    }


def test_run_endpoint_rejects_bad_function_config() -> None:
    client = TestClient(build_app())

    response = client.post(
        "/api/projects/call-me-maybe/run",
        json={
            "prompt": "What is the sum of 2 and 3?",
            "functions_definition": [
                {
                    "fn_name": "fn_add_numbers",
                    "args_names": ["a", "b"],
                    "args_types": {"a": "float"},
                    "return_type": "float",
                }
            ],
        },
    )

    assert response.status_code == 400
    assert "missing args_types entries" in response.text


def test_run_endpoint_returns_503_when_model_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(service, "RemoteModelClient", UnavailableModel)
    client = TestClient(build_app())

    response = client.post(
        "/api/projects/call-me-maybe/run",
        json={
            "prompt": "What is the sum of 2 and 3?",
            "functions_definition": FUNCTIONS,
        },
    )

    assert response.status_code == 503
    assert "model service is unavailable" in response.json()["detail"]


def build_app() -> FastAPI:
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/projects/call-me-maybe")
    return test_app
