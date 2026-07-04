from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from transformers import AutoModelForCausalLM, AutoTokenizer, logging


logging.set_verbosity_error()

MODEL_NAME = os.getenv("CALL_ME_MAYBE_MODEL_NAME", "Qwen/Qwen3-0.6B")
DEVICE = os.getenv("CALL_ME_MAYBE_MODEL_DEVICE", "cpu")
MAX_INPUT_TOKENS = int(os.getenv("CALL_ME_MAYBE_MAX_INPUT_TOKENS", "8192"))


class EncodeRequest(BaseModel):
    text: str = Field(..., max_length=12000)


class EncodeResponse(BaseModel):
    token_ids: list[int]


class EncodeBatchRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, max_length=64)


class EncodeBatchResponse(BaseModel):
    token_ids_list: list[list[int]]


class LogitsRequest(BaseModel):
    input_ids: list[int] = Field(..., min_length=1, max_length=MAX_INPUT_TOKENS)


class LogitsResponse(BaseModel):
    logits: list[float]


class CandidateLogitsRequest(BaseModel):
    input_ids: list[int] = Field(..., min_length=1, max_length=MAX_INPUT_TOKENS)
    candidate_token_ids: list[int] = Field(..., min_length=1, max_length=256)


class CandidateLogitsResponse(BaseModel):
    logits: dict[str, float]


class SelectFunctionRequest(BaseModel):
    prompt: str = Field(..., max_length=12000)
    function_names: list[str] = Field(..., min_length=1, max_length=64)


class SelectFunctionResponse(BaseModel):
    name: str


class QwenRuntime:
    def __init__(self) -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME,
            trust_remote_code=True,
        )
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float32 if DEVICE == "cpu" else torch.float16,
            trust_remote_code=True,
        )
        self.model.to(DEVICE).eval()
        for parameter in self.model.parameters():
            parameter.requires_grad = False

    def encode(self, text: str) -> list[int]:
        return self.tokenizer.encode(text, add_special_tokens=False)

    def encode_many(self, texts: list[str]) -> list[list[int]]:
        return [
            self.tokenizer.encode(text, add_special_tokens=False)
            for text in texts
        ]

    def select_function_name(self, prompt: str, function_names: list[str]) -> str:
        prompt_tokens = self.encode(prompt)
        if len(prompt_tokens) > MAX_INPUT_TOKENS:
            raise HTTPException(
                status_code=400,
                detail=f"Input is too long: {len(prompt_tokens)} tokens.",
            )

        encoded_functions = self.encode_many(
            [prompt + name for name in function_names]
        )
        fn_tokens_by_name = {
            name: token_ids[len(prompt_tokens):]
            for name, token_ids in zip(
                function_names,
                encoded_functions,
                strict=True,
            )
        }

        selected_tokens: list[int] = []
        while True:
            for name, fn_tokens in fn_tokens_by_name.items():
                if selected_tokens == fn_tokens:
                    return name

            next_candidates = set()
            for fn_tokens in fn_tokens_by_name.values():
                if selected_tokens == fn_tokens[: len(selected_tokens)] and len(
                    fn_tokens
                ) > len(selected_tokens):
                    next_candidates.add(fn_tokens[len(selected_tokens)])

            if not next_candidates:
                raise HTTPException(
                    status_code=400,
                    detail="No valid function name token remains.",
                )

            input_ids = prompt_tokens + selected_tokens
            if len(input_ids) > MAX_INPUT_TOKENS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Input is too long: {len(input_ids)} tokens.",
                )
            candidate_logits = self.candidate_logits(
                input_ids,
                sorted(next_candidates),
            )
            next_token = max(
                next_candidates,
                key=lambda token_id: candidate_logits[str(token_id)],
            )
            selected_tokens.append(next_token)

    def logits(self, input_ids: list[int]) -> list[float]:
        last_logits = self._last_logits(input_ids)
        return [float(value) for value in last_logits.tolist()]

    def candidate_logits(
        self,
        input_ids: list[int],
        candidate_token_ids: list[int],
    ) -> dict[str, float]:
        last_logits = self._last_logits(input_ids)
        return {
            str(token_id): float(last_logits[token_id].item())
            for token_id in candidate_token_ids
        }

    def _last_logits(self, input_ids: list[int]) -> torch.Tensor:
        input_tensor = torch.tensor([input_ids], device=DEVICE, dtype=torch.long)
        with torch.inference_mode():
            output = self.model(input_ids=input_tensor)
        return output.logits[0, -1]


runtime: QwenRuntime | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    global runtime
    runtime = QwenRuntime()
    yield


app = FastAPI(title="Call Me Maybe Qwen Model Service", lifespan=lifespan)


def get_runtime() -> QwenRuntime:
    if runtime is None:
        raise HTTPException(status_code=503, detail="Model is not loaded yet.")
    return runtime


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "model": MODEL_NAME}


@app.post("/encode", response_model=EncodeResponse)
def encode(request: EncodeRequest) -> EncodeResponse:
    token_ids = get_runtime().encode(request.text)
    if len(token_ids) > MAX_INPUT_TOKENS:
        raise HTTPException(
            status_code=400,
            detail=f"Input is too long: {len(token_ids)} tokens.",
        )
    return EncodeResponse(token_ids=token_ids)


@app.post("/select-function", response_model=SelectFunctionResponse)
def select_function(request: SelectFunctionRequest) -> SelectFunctionResponse:
    return SelectFunctionResponse(
        name=get_runtime().select_function_name(
            request.prompt,
            request.function_names,
        )
    )


@app.post("/encode-batch", response_model=EncodeBatchResponse)
def encode_batch(request: EncodeBatchRequest) -> EncodeBatchResponse:
    token_ids_list = get_runtime().encode_many(request.texts)
    for token_ids in token_ids_list:
        if len(token_ids) > MAX_INPUT_TOKENS:
            raise HTTPException(
                status_code=400,
                detail=f"Input is too long: {len(token_ids)} tokens.",
            )
    return EncodeBatchResponse(token_ids_list=token_ids_list)


@app.post("/logits", response_model=LogitsResponse)
def logits(request: LogitsRequest) -> LogitsResponse:
    return LogitsResponse(logits=get_runtime().logits(request.input_ids))


@app.post("/candidate-logits", response_model=CandidateLogitsResponse)
def candidate_logits(request: CandidateLogitsRequest) -> CandidateLogitsResponse:
    return CandidateLogitsResponse(
        logits=get_runtime().candidate_logits(
            request.input_ids,
            request.candidate_token_ids,
        )
    )
