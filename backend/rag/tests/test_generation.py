from __future__ import annotations

from pathlib import Path

import pytest

from backend.rag.src.generation import NO_SOURCES_ANSWER, AnswerGenerator
from backend.rag.src.models import MinimalSource


class FakeTextGenerator:
    def __init__(self) -> None:
        self.prompt = ""

    def generate_text(self, prompt: str, max_new_tokens: int = 128) -> str:
        self.prompt = prompt
        assert max_new_tokens == 128
        return "Grounded answer"


def test_answer_generator_builds_grounded_prompt(tmp_path: Path) -> None:
    source_path = tmp_path / "module.py"
    source_path.write_text("prefix caching implementation", encoding="utf-8")
    source = MinimalSource(
        file_path="module.py",
        first_character_index=0,
        last_character_index=14,
    )
    model = FakeTextGenerator()

    answer = AnswerGenerator(model=model, project_root=tmp_path).generate(
        "How does caching work?",
        [source],
    )

    assert answer == "Grounded answer"
    assert "prefix caching" in model.prompt
    assert "How does caching work?" in model.prompt
    assert "Source: module.py" in model.prompt
    assert "at most three concise sentences" in model.prompt
    assert "Do not repeat" in model.prompt


def test_answer_generator_rejects_source_outside_project(tmp_path: Path) -> None:
    generator = AnswerGenerator(model=FakeTextGenerator(), project_root=tmp_path)
    source = MinimalSource(
        file_path="../outside.py",
        first_character_index=0,
        last_character_index=1,
    )

    with pytest.raises(ValueError, match="outside the RAG corpus"):
        generator.source_text(source)


def test_answer_generator_does_not_call_model_without_sources(tmp_path: Path) -> None:
    model = FakeTextGenerator()

    answer = AnswerGenerator(model=model, project_root=tmp_path).generate("unknown", [])

    assert answer == NO_SOURCES_ANSWER
    assert model.prompt == ""
