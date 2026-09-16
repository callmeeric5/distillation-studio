from __future__ import annotations

from pathlib import Path
from typing import Protocol, cast

from .models import MinimalSource

PROJECT_ROOT = Path(__file__).resolve().parents[1]
NO_SOURCES_ANSWER = (
    "No relevant sources were found in the vLLM 0.10.1 corpus for this question."
)


class TextGenerator(Protocol):
    def generate_text(self, prompt: str, max_new_tokens: int = 128) -> str:
        """Generate text that continues ``prompt``."""


class TransformersTextGenerator:
    """Local Qwen runtime used by the standalone RAG CLI."""

    def __init__(self, model_name: str = "Qwen/Qwen3-0.6B") -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.torch = torch
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.model.to(self.device).eval()

    def generate_text(self, prompt: str, max_new_tokens: int = 128) -> str:
        formatted_prompt = self.tokenizer.apply_chat_template(
            [
                {
                    "role": "system",
                    "content": (
                        "Give one concise answer. Do not repeat sentences, and "
                        "stop when the answer is complete."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        inputs = self.tokenizer(
            formatted_prompt, return_tensors="pt"
        ).to(self.device)
        with self.torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                repetition_penalty=1.15,
                no_repeat_ngram_size=6,
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        generated_tokens = outputs[0][inputs["input_ids"].shape[1]:]
        return cast(
            str,
            self.tokenizer.decode(generated_tokens, skip_special_tokens=True),
        ).strip()


class AnswerGenerator:
    def __init__(
        self,
        model: TextGenerator | None = None,
        project_root: str | Path = PROJECT_ROOT,
    ) -> None:
        self.model = model or TransformersTextGenerator()
        self.project_root = Path(project_root).resolve()

    def source_text(self, source: MinimalSource) -> str:
        path = Path(source.file_path)
        resolved_path = (
            path.resolve()
            if path.is_absolute()
            else (self.project_root / path).resolve()
        )
        if not resolved_path.is_relative_to(self.project_root):
            raise ValueError(
                f"Source path is outside the RAG corpus: {source.file_path}"
            )
        text = resolved_path.read_text(encoding="utf-8")
        if not (
            0
            <= source.first_character_index
            <= source.last_character_index
            <= len(text)
        ):
            raise ValueError(f"Source range is invalid for: {source.file_path}")
        return text[source.first_character_index:source.last_character_index]

    def build_prompt(self, question: str, sources: list[MinimalSource]) -> str:
        context_parts = []
        for source in sources:
            context_parts.append(
                f"Source: {source.file_path}\n{self.source_text(source)}"
            )
        context = "\n\n".join(context_parts)
        return (
            "Answer the question once, in at most three concise sentences, using "
            "only the context below. Do not repeat any sentence or conclusion. "
            "If the context is insufficient, say so clearly.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n"
            "Answer:"
        )

    def generate(self, question: str, sources: list[MinimalSource]) -> str:
        if not sources:
            return NO_SOURCES_ANSWER
        return self.model.generate_text(self.build_prompt(question, sources))
