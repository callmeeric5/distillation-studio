from __future__ import annotations

import os

import httpx
from fastapi import HTTPException

from api.projects.rag.schemas import RagAnswerRequest
from backend.rag.src.generation import AnswerGenerator
from backend.rag.src.retrieval import Retriever

MODEL_URL = os.getenv(
    "RAG_MODEL_URL",
    "http://call-me-maybe-model:8001",
).rstrip("/")
MODEL_TIMEOUT_SECONDS = float(os.getenv("RAG_MODEL_TIMEOUT", "180"))


class ModelServiceError(RuntimeError):
    pass


class RemoteTextGenerator:
    def __init__(self, base_url: str = MODEL_URL) -> None:
        self.base_url = base_url
        self.client = httpx.Client(timeout=httpx.Timeout(MODEL_TIMEOUT_SECONDS))

    def close(self) -> None:
        self.client.close()

    def generate_text(self, prompt: str, max_new_tokens: int = 256) -> str:
        try:
            response = self.client.post(
                f"{self.base_url}/generate",
                json={"prompt": prompt, "max_new_tokens": max_new_tokens},
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise ModelServiceError(str(error)) from error
        text = payload.get("text") if isinstance(payload, dict) else None
        if not isinstance(text, str):
            raise ModelServiceError("Model service returned invalid generated text.")
        return text


def answer_question(request: RagAnswerRequest) -> dict:
    model = RemoteTextGenerator()
    try:
        retriever = Retriever()
        sources = retriever.search(request.question, request.k)
        generator = AnswerGenerator(model=model)
        answer = generator.generate(request.question, sources)
        serialized_sources = [
            {
                **source.model_dump(),
                "content": generator.source_text(source),
            }
            for source in sources
        ]
    except ModelServiceError as error:
        raise HTTPException(
            status_code=503,
            detail=f"RAG model service is unavailable: {error}",
        ) from error
    except (FileNotFoundError, ValueError) as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    finally:
        model.close()

    return {
        "question": request.question,
        "answer": answer,
        "sources": serialized_sources,
    }
