import asyncio

from agent_smith.agent.agent import run_agent
from agent_smith.llm.client import UnifiedLLMClient
from agent_smith.models.agent import SolutionOutput
from agent_smith.models.benchmark import MBPPTaskInput
from agent_smith.models.llm import LLMResponse, ProviderConfig
from agent_smith.models.sandbox import SandboxResult
from agent_smith.web import exception_details


def test_direct_api_key_does_not_require_environment(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEYS", raising=False)
    config = ProviderConfig(
        model_name="openai/gpt-4.1-nano",
        provider_url="https://openrouter.ai/api/v1",
    )
    client = UnifiedLLMClient(config, api_keys=[" request-key "])
    assert client.keys == ["request-key"]
    asyncio.run(client.close())


def test_task_group_errors_expose_the_leaf_cause():
    error = ExceptionGroup(
        "unhandled errors in a TaskGroup",
        [RuntimeError("Cannot connect to the Docker daemon")],
    )
    assert exception_details(error) == (
        "RuntimeError: Cannot connect to the Docker daemon"
    )


def test_run_agent_publishes_completed_steps():
    source = "def add(a, b):\n    return a + b"

    class FakeLLM:
        def __init__(self):
            self.config = ProviderConfig(
                model_name="test-model", provider_url="https://example.test/v1"
            )
            self.required_tool = None
            self.last_attempts = 1
            self.last_retry_errors = []
            self.total_requests = 0

        async def generate(self, *_args, **_kwargs):
            self.total_requests += 1
            if self.total_requests == 1:
                text = (
                    "Thought: test the implementation.\n```python\n"
                    f"code = {source!r}\nprint(run_tests(code=code))\n```<end_code>"
                )
            else:
                text = "Thought: submit it.\n```python\nfinal_answer(code)\n```<end_code>"
            return LLMResponse(
                model_name="test-model",
                api_url="https://example.test/v1",
                llm_output=text,
                input_tokens=10,
                output_tokens=5,
                request_time_ms=1,
                retries=0,
            )

    class FakeSandbox:
        def manual(self):
            return "run_tests(code: string); final_answer(answer: string)"

        async def execute(self, code, timeout=None):
            if "run_tests" in code:
                return SandboxResult(
                    success=True, result={"passed": 1, "total": 1, "failures": []}
                )
            return SandboxResult(success=True, completed=True, final_answer=source)

    published = []

    async def scenario():
        output = await run_agent(
            MBPPTaskInput(
                task_id=1,
                task_definition="Add two numbers.",
                function_definition="def add(a, b)",
                test_list=["assert add(1, 2) == 3"],
            ),
            "mbpp",
            FakeLLM(),
            FakeSandbox(),
            on_step=lambda step, state: published.append(
                (step.step, state.total_input_tokens)
            ),
        )
        assert isinstance(output, SolutionOutput)
        assert output.success
        assert output.solution == source

    asyncio.run(scenario())
    assert published == [(1, 10), (2, 20)]
