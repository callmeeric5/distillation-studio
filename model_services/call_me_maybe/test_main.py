from __future__ import annotations

from fastapi.testclient import TestClient

from model_services.call_me_maybe.app import main


class FakeRuntime:
    def generate(self, prompt: str, max_new_tokens: int = 128) -> str:
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


def test_qwen_generation_uses_chat_template_and_repetition_controls() -> None:
    class FakeInputIds:
        shape = (1, 3)

    class FakeInputs(dict):
        def to(self, device: str):
            assert device == main.DEVICE
            return self

    class FakeTokenizer:
        eos_token_id = 42

        def __init__(self) -> None:
            self.messages = []
            self.formatted_prompt = ""

        def apply_chat_template(self, messages, **kwargs):
            self.messages = messages
            assert kwargs == {
                "tokenize": False,
                "add_generation_prompt": True,
                "enable_thinking": False,
            }
            return "chat-formatted prompt"

        def __call__(self, prompt: str, return_tensors: str):
            self.formatted_prompt = prompt
            assert return_tensors == "pt"
            return FakeInputs(input_ids=FakeInputIds())

        def decode(self, tokens, skip_special_tokens: bool):
            assert tokens == [7, 8]
            assert skip_special_tokens is True
            return "concise answer"

    class FakeInferenceMode:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc_value, traceback):
            return False

    class FakeTorch:
        @staticmethod
        def inference_mode():
            return FakeInferenceMode()

    class FakeModel:
        def __init__(self) -> None:
            self.kwargs = {}

        def generate(self, **kwargs):
            self.kwargs = kwargs
            return [[0, 1, 2, 7, 8]]

    runtime = main.QwenRuntime.__new__(main.QwenRuntime)
    runtime.tokenizer = FakeTokenizer()
    runtime.model = FakeModel()
    runtime.torch = FakeTorch()

    result = runtime.generate("raw prompt")

    assert result == "concise answer"
    assert runtime.tokenizer.formatted_prompt == "chat-formatted prompt"
    assert runtime.tokenizer.messages[1] == {"role": "user", "content": "raw prompt"}
    assert runtime.model.kwargs["max_new_tokens"] == 128
    assert runtime.model.kwargs["repetition_penalty"] == 1.15
    assert runtime.model.kwargs["no_repeat_ngram_size"] == 6
    assert runtime.model.kwargs["eos_token_id"] == 42


def test_existing_function_selection_endpoint_remains_available(monkeypatch) -> None:
    monkeypatch.setattr(main, "runtime", FakeRuntime())

    response = TestClient(main.app).post(
        "/select-function",
        json={"prompt": "choose", "function_names": ["first", "second"]},
    )

    assert response.status_code == 200
    assert response.json() == {"name": "first"}
