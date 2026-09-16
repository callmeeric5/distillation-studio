from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.projects.rag import service
from api.projects.rag.router import router
from backend.rag.src.models import MinimalSource


class FakeRetriever:
    def search(self, question: str, k: int) -> list[MinimalSource]:
        assert question
        assert 1 <= k <= 10
        return [
            MinimalSource(
                file_path="README.md",
                first_character_index=0,
                last_character_index=5,
            )
        ]


class EmptyRetriever:
    def search(self, question: str, k: int) -> list[MinimalSource]:
        return []


class FakeModel:
    def __init__(self) -> None:
        self.closed = False

    def generate_text(self, prompt: str, max_new_tokens: int = 128) -> str:
        assert "README.md" in prompt
        return "Prefix caching reuses computed KV cache blocks."

    def close(self) -> None:
        self.closed = True


class UnavailableModel(FakeModel):
    def generate_text(self, prompt: str, max_new_tokens: int = 256) -> str:
        raise service.ModelServiceError("connection refused")


def test_health_endpoint() -> None:
    response = TestClient(build_app()).get("/api/projects/rag/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "project": "rag"}


def test_answer_endpoint_returns_answer_and_sources(monkeypatch) -> None:
    monkeypatch.setattr(service, "Retriever", FakeRetriever)
    monkeypatch.setattr(service, "RemoteTextGenerator", FakeModel)

    response = TestClient(build_app()).post(
        "/api/projects/rag/answer",
        json={"question": "How does prefix caching work?", "k": 3},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"].startswith("Prefix caching")
    assert payload["sources"] == [
        {
            "file_path": "README.md",
            "first_character_index": 0,
            "last_character_index": 5,
            "content": "*This",
        }
    ]


def test_answer_endpoint_validates_k() -> None:
    response = TestClient(build_app()).post(
        "/api/projects/rag/answer",
        json={"question": "Question", "k": 11},
    )

    assert response.status_code == 422


def test_answer_endpoint_rejects_whitespace_question() -> None:
    response = TestClient(build_app()).post(
        "/api/projects/rag/answer",
        json={"question": "   "},
    )

    assert response.status_code == 422


def test_answer_endpoint_handles_no_sources_without_calling_model(
    monkeypatch,
) -> None:
    class ModelThatMustNotGenerate(FakeModel):
        def generate_text(self, prompt: str, max_new_tokens: int = 128) -> str:
            raise AssertionError("The model should not run without sources")

    monkeypatch.setattr(service, "Retriever", EmptyRetriever)
    monkeypatch.setattr(service, "RemoteTextGenerator", ModelThatMustNotGenerate)

    response = TestClient(build_app()).post(
        "/api/projects/rag/answer",
        json={"question": "An unmatched question"},
    )

    assert response.status_code == 200
    assert response.json()["sources"] == []
    assert response.json()["answer"].startswith("No relevant sources")


def test_answer_endpoint_returns_503_when_model_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(service, "Retriever", FakeRetriever)
    monkeypatch.setattr(service, "RemoteTextGenerator", UnavailableModel)

    response = TestClient(build_app()).post(
        "/api/projects/rag/answer",
        json={"question": "How does prefix caching work?"},
    )

    assert response.status_code == 503
    assert "model service is unavailable" in response.json()["detail"]


def build_app() -> FastAPI:
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/projects/rag")
    return test_app
