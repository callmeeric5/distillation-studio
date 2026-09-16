from __future__ import annotations

from fastapi import APIRouter

from api.projects.rag.schemas import RagAnswerRequest, RagAnswerResponse
from api.projects.rag.service import answer_question

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "project": "rag"}


@router.post("/answer", response_model=RagAnswerResponse)
def answer(request: RagAnswerRequest) -> dict:
    return answer_question(request)
