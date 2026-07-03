from __future__ import annotations

import os

import httpx
from fastapi import HTTPException

from api.projects.call_me_maybe.schemas import FunctionCallRequest
from backend.call_me_maybe.src.runner import parse_functions, run_function_call


MODEL_URL = os.getenv(
    "CALL_ME_MAYBE_MODEL_URL",
    "http://call-me-maybe-model:8001",
).rstrip("/")
MODEL_TIMEOUT_SECONDS = float(os.getenv("CALL_ME_MAYBE_MODEL_TIMEOUT", "120"))


class RemoteModelClient:
    def __init__(self, base_url: str = MODEL_URL) -> None:
        self.base_url = base_url
        self.timeout = httpx.Timeout(MODEL_TIMEOUT_SECONDS)

    def encode(self, text: str) -> list[int]:
        payload = self._post_json("/encode", {"text": text})
        token_ids = payload.get("token_ids")
        if not isinstance(token_ids, list):
            raise ModelServiceError("Model service returned invalid token ids.")
        return [int(token_id) for token_id in token_ids]

    def get_logits_from_input_ids(self, input_ids: list[int]) -> list[float]:
        payload = self._post_json("/logits", {"input_ids": input_ids})
        logits = payload.get("logits")
        if not isinstance(logits, list):
            raise ModelServiceError("Model service returned invalid logits.")
        return [float(logit) for logit in logits]

    def _post_json(self, path: str, body: dict) -> dict:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.base_url}{path}", json=body)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise ModelServiceError(str(error)) from error
        if not isinstance(payload, dict):
            raise ModelServiceError("Model service returned a non-object response.")
        return payload


class ModelServiceError(RuntimeError):
    pass


def run_call_me_maybe(request: FunctionCallRequest) -> dict:
    try:
        for function in request.functions_definition:
            missing = [
                arg_name
                for arg_name in function.args_names
                if arg_name not in function.args_types
            ]
            if missing:
                missing_args = ", ".join(missing)
                raise ValueError(
                    f"{function.fn_name} is missing args_types entries for: "
                    f"{missing_args}"
                )
        functions = parse_functions(
            [
                function.model_dump()
                for function in request.functions_definition
            ]
        )
        output = run_function_call(
            prompt=request.prompt,
            functions=functions,
            model=RemoteModelClient(),
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ModelServiceError as error:
        raise HTTPException(
            status_code=503,
            detail=f"Call_Me_Maybe model service is unavailable: {error}",
        ) from error
    return output.model_dump()
