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
        self.client = httpx.Client(timeout=self.timeout)

    def close(self) -> None:
        self.client.close()

    def encode(self, text: str) -> list[int]:
        payload = self._post_json("/encode", {"text": text})
        token_ids = payload.get("token_ids")
        if not isinstance(token_ids, list):
            raise ModelServiceError("Model service returned invalid token ids.")
        return [int(token_id) for token_id in token_ids]

    def select_function_name(self, prompt: str, function_names: list[str]) -> str:
        payload = self._post_json(
            "/select-function",
            {"prompt": prompt, "function_names": function_names},
        )
        name = payload.get("name")
        if not isinstance(name, str):
            raise ModelServiceError("Model service returned an invalid function name.")
        return name

    def encode_many(self, texts: list[str]) -> list[list[int]]:
        payload = self._post_json("/encode-batch", {"texts": texts})
        token_ids_list = payload.get("token_ids_list")
        if not isinstance(token_ids_list, list):
            raise ModelServiceError("Model service returned invalid batch token ids.")
        if len(token_ids_list) != len(texts):
            raise ModelServiceError("Model service returned the wrong batch size.")
        encoded: list[list[int]] = []
        for token_ids in token_ids_list:
            if not isinstance(token_ids, list):
                raise ModelServiceError("Model service returned invalid batch token ids.")
            encoded.append([int(token_id) for token_id in token_ids])
        return encoded

    def get_logits_from_input_ids(self, input_ids: list[int]) -> list[float]:
        payload = self._post_json("/logits", {"input_ids": input_ids})
        logits = payload.get("logits")
        if not isinstance(logits, list):
            raise ModelServiceError("Model service returned invalid logits.")
        return [float(logit) for logit in logits]

    def get_candidate_logits_from_input_ids(
        self,
        input_ids: list[int],
        candidate_token_ids: list[int],
    ) -> dict[int, float]:
        payload = self._post_json(
            "/candidate-logits",
            {
                "input_ids": input_ids,
                "candidate_token_ids": candidate_token_ids,
            },
        )
        logits = payload.get("logits")
        if not isinstance(logits, dict):
            raise ModelServiceError("Model service returned invalid candidate logits.")
        return {int(token_id): float(value) for token_id, value in logits.items()}

    def _post_json(self, path: str, body: dict) -> dict:
        try:
            response = self.client.post(f"{self.base_url}{path}", json=body)
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
        model = RemoteModelClient()
        try:
            output = run_function_call(
                prompt=request.prompt,
                functions=functions,
                model=model,
            )
        finally:
            close = getattr(model, "close", None)
            if callable(close):
                close()
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ModelServiceError as error:
        raise HTTPException(
            status_code=503,
            detail=f"Call_Me_Maybe model service is unavailable: {error}",
        ) from error
    return output.model_dump()
