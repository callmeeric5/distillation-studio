import asyncio

import httpx

from agent_smith.agent.agent import run_agent
from agent_smith.llm.client import UnifiedLLMClient, completion_data
from agent_smith.models.agent import SolutionOutput
from agent_smith.models.benchmark import MBPPTaskInput, SWEBenchTaskInput
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


def test_provider_whitespace_is_not_a_valid_assistant_message():
    response = httpx.Response(
        200,
        json={
            "choices": [{"message": {"content": "  \n "}, "finish_reason": "stop"}],
            "usage": {},
        },
    )
    try:
        completion_data(response)
    except ValueError as error:
        assert "empty assistant message" in str(error)
    else:
        raise AssertionError("Whitespace-only provider output must be rejected")


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


def test_swebench_forces_test_after_edit_and_auto_submits_verified_patch():
    patch = "diff --git a/project.py b/project.py\n--- a/project.py\n+++ b/project.py\n"

    class FakeLLM:
        def __init__(self):
            self.config = ProviderConfig(
                model_name="test-model", provider_url="https://example.test/v1"
            )
            self.required_tool = None
            self.required_tools = []
            self.last_attempts = 1
            self.last_retry_errors = []
            self.total_requests = 0

        async def generate(self, *_args, **_kwargs):
            self.total_requests += 1
            self.required_tools.append(self.required_tool)
            responses = {
                "run_tests": "<tool_call>{\"name\":\"run_tests\",\"arguments\":{}}</tool_call>",
                "read_file": (
                    "<tool_call>{\"name\":\"read_file\",\"arguments\":"
                    "{\"filepath\":\"/testbed/project.py\",\"start_line\":1,"
                    "\"end_line\":22}}</tool_call>"
                ),
                "edit_file": (
                    "<tool_call>{\"name\":\"edit_file\",\"arguments\":"
                    "{\"filepath\":\"/testbed/project.py\",\"old_str\":\"old\","
                    "\"new_str\":\"new\"}}</tool_call>"
                ),
            }
            return LLMResponse(
                model_name="test-model",
                api_url="https://example.test/v1",
                llm_output=responses[self.required_tool],
                input_tokens=10,
                output_tokens=5,
                request_time_ms=1,
                retries=0,
            )

    class FakeSandbox:
        def __init__(self):
            self.test_runs = 0

        def manual(self):
            return "run_tests(); read_file(...); edit_file(...); get_patch()"

        async def execute(self, code, timeout=None):
            if "read_file" in code:
                return SandboxResult(success=True, result="1: old")
            if "edit_file" in code:
                return SandboxResult(success=True, result="Updated /testbed/project.py")
            if "run_tests" in code:
                self.test_runs += 1
                return SandboxResult(
                    success=True,
                    result={
                        "exit_code": 1 if self.test_runs == 1 else 0,
                        "stdout": "",
                        "stderr": "",
                    },
                )
            if "get_patch" in code:
                return SandboxResult(success=True, result=patch)
            raise AssertionError(f"Unexpected sandbox code: {code}")

    async def scenario():
        llm = FakeLLM()
        output = await run_agent(
            SWEBenchTaskInput(
                instance_id="project-1",
                problem_statement="Fix the bug.",
                docker_image="task-image",
                eval_script="true",
                hints_text=(
                    "https://github.com/example/repo/blob/abc/project.py#L2"
                ),
            ),
            "swebench",
            llm,
            FakeSandbox(),
        )
        assert output.success
        assert output.solution == patch
        assert output.iterations == 4
        assert llm.required_tools == [
            "run_tests",
            "read_file",
            "edit_file",
            "run_tests",
        ]

    asyncio.run(scenario())
