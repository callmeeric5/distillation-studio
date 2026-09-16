from fastapi import HTTPException
from pydantic import ValidationError

from api.projects.agent_smith.schemas import RunCreateRequest
from api.projects.agent_smith.service import AgentSmithRunManager


def request(**updates):
    values = {
        "benchmark": "mbpp",
        "provider": "openrouter",
        "model": "openai/gpt-4.1-nano",
        "api_key": "top-secret-key",
        "task_definition": "Add two numbers.",
        "function_definition": "def add(a, b)",
        "test_list": ["assert add(1, 2) == 3"],
    }
    values.update(updates)
    return RunCreateRequest(**values)


def test_mbpp_requires_tests():
    try:
        request(test_list=[])
    except ValidationError as error:
        assert "at least one test" in str(error)
    else:
        raise AssertionError("Expected request validation to fail")


def test_queue_limit_and_secret_redaction():
    manager = AgentSmithRunManager(max_pending=3)
    jobs = [manager.create(request()) for _ in range(3)]
    status = manager.status(jobs[0].run_id)
    assert status["queue_position"] == 1
    assert "top-secret-key" not in repr(jobs[0])
    assert "top-secret-key" not in str(status)

    try:
        manager.create(request())
    except HTTPException as error:
        assert error.status_code == 429
    else:
        raise AssertionError("Expected a full queue")


def test_provider_model_pair_and_swe_task_are_allowlisted():
    manager = AgentSmithRunManager()
    try:
        manager.create(request(model="qwen/qwen3.6-27b"))
    except HTTPException as error:
        assert error.status_code == 400
    else:
        raise AssertionError("Expected provider/model validation to fail")

    try:
        manager.create(
            request(
                benchmark="swebench",
                task_id="attacker/custom-task",
                task_definition=None,
                function_definition=None,
                test_list=[],
            )
        )
    except HTTPException as error:
        assert error.status_code == 400
    else:
        raise AssertionError("Expected SWE-bench allowlist validation to fail")


def test_cancel_removes_queued_job_and_erases_key():
    manager = AgentSmithRunManager()
    job = manager.create(request())
    result = manager.cancel(job.run_id)
    assert result["status"] == "cancelled"
    assert job.api_key == ""
    assert not manager.pending
