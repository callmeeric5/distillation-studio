from __future__ import annotations

from fastapi.testclient import TestClient

from model_services.call_me_maybe.app import main


class FakeRuntime:
    def generate(self, prompt: str, max_new_tokens: int = 256) -> str:
        return f"answer:{prompt}:{max_new_tokens}"

    def select_function_name(self, prompt: str, function_names: list[str]) -> str:
        return function_names[0]


def test_generate_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(main, "runtime", FakeRuntime())

    response = TestClient(main.app).post(
        "/generate",
        json={"prompt": "Use this context", "max_new_tokens": 128},
    )

    assert response.status_code == 200
    assert response.json() == {"text": "answer:Use this context:128"}


def test_generate_endpoint_validates_request(monkeypatch) -> None:
    monkeypatch.setattr(main, "runtime", FakeRuntime())
    client = TestClient(main.app)

    assert client.post("/generate", json={"prompt": ""}).status_code == 422
    assert client.post(
        "/generate",
        json={"prompt": "context", "max_new_tokens": 513},
    ).status_code == 422


def test_existing_function_selection_endpoint_remains_available(monkeypatch) -> None:
    monkeypatch.setattr(main, "runtime", FakeRuntime())

    response = TestClient(main.app).post(
        "/select-function",
        json={"prompt": "choose", "function_names": ["first", "second"]},
    )

    assert response.status_code == 200
    assert response.json() == {"name": "first"}
