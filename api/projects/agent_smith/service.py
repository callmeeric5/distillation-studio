from __future__ import annotations

import asyncio
import json
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException

from api.projects.agent_smith.schemas import RunCreateRequest


PROVIDERS = {
    "openrouter": {
        "label": "OpenRouter",
        "url": "https://openrouter.ai/api/v1",
        "models": [
            {"id": "openai/gpt-4.1-nano", "label": "GPT-4.1 Nano"},
            {"id": "google/gemini-3.1-flash-lite", "label": "Gemini 3.1 Flash Lite"},
            {"id": "deepseek/deepseek-v4-flash-0731", "label": "DeepSeek V4 Flash"},
            {"id": "minimax/minimax-m2.7", "label": "MiniMax M2.7"},
        ],
    },
    "groq": {
        "label": "Groq",
        "url": "https://api.groq.com/openai/v1",
        "models": [{"id": "qwen/qwen3.6-27b", "label": "Qwen 3.6 27B"}],
    },
}

SWE_TASK_FILES = {
    "django__django-11066": "django-11066.json",
    "sympy__sympy-14711": "sympy-14711.json",
    "sympy__sympy-18189": "sympy-18189.json",
}
PROJECT_ROOT = Path(__file__).resolve().parents[3]
TASK_ROOT = PROJECT_ROOT / "backend" / "agent_smith" / "benchmark_tasks"
TERMINAL_STATUSES = {"succeeded", "failed", "cancelled"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RunJob:
    run_id: str
    benchmark: str
    provider: str
    model: str
    api_key: str = field(repr=False)
    payload: dict[str, Any]
    status: str = "queued"
    created_at: str = field(default_factory=utc_now)
    created_monotonic: float = field(default_factory=time.monotonic, repr=False)
    started_at: str | None = None
    started_monotonic: float | None = field(default=None, repr=False)
    finished_at: str | None = None
    finished_monotonic: float | None = field(default=None, repr=False)
    steps: list[dict[str, Any]] = field(default_factory=list)
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    execution_task: asyncio.Task[None] | None = field(default=None, repr=False)


class AgentSmithRunManager:
    def __init__(self, max_pending: int = 3, retention_seconds: int = 3600) -> None:
        self.max_pending = max_pending
        self.retention_seconds = retention_seconds
        self.jobs: dict[str, RunJob] = {}
        self.pending: deque[str] = deque()
        self.wake = asyncio.Event()
        self.consumer_task: asyncio.Task[None] | None = None
        self.active_id: str | None = None
        self.stopping = False

    async def start(self) -> None:
        if self.consumer_task is None or self.consumer_task.done():
            self.stopping = False
            self.consumer_task = asyncio.create_task(self._consume())

    async def stop(self) -> None:
        self.stopping = True
        for run_id in list(self.pending):
            job = self.jobs.get(run_id)
            if job:
                self._mark_cancelled(job)
        self.pending.clear()
        active = self.jobs.get(self.active_id or "")
        if active and active.execution_task:
            active.execution_task.cancel()
        if self.consumer_task:
            self.consumer_task.cancel()
            await asyncio.gather(self.consumer_task, return_exceptions=True)
            self.consumer_task = None

    def options(self) -> dict[str, Any]:
        tasks = []
        for task_id, filename in SWE_TASK_FILES.items():
            data = json.loads((TASK_ROOT / filename).read_text())
            tasks.append(
                {
                    "id": task_id,
                    "repository": data.get("repo", ""),
                    "title": data["problem_statement"].splitlines()[0],
                }
            )
        return {
            "providers": PROVIDERS,
            "swebench_tasks": tasks,
            "limits": {
                "max_pending": self.max_pending,
                "retention_seconds": self.retention_seconds,
                "mbpp": {"max_iterations": 10, "timeout_seconds": 120},
                "swebench": {"max_iterations": 30, "timeout_seconds": 900},
            },
        }

    def create(self, request: RunCreateRequest) -> RunJob:
        self._cleanup()
        self._validate_provider_model(request.provider, request.model)
        if request.benchmark == "swebench" and request.task_id not in SWE_TASK_FILES:
            raise HTTPException(status_code=400, detail="Unknown SWE-bench task.")
        queued = sum(
            1 for run_id in self.pending if self.jobs[run_id].status == "queued"
        )
        if queued >= self.max_pending:
            raise HTTPException(status_code=429, detail="Agent Smith queue is full.")

        run_id = str(uuid4())
        job = RunJob(
            run_id=run_id,
            benchmark=request.benchmark,
            provider=request.provider,
            model=request.model,
            api_key=request.api_key.get_secret_value(),
            payload=request.model_dump(exclude={"api_key"}),
        )
        self.jobs[run_id] = job
        self.pending.append(run_id)
        self.wake.set()
        return job

    def status(self, run_id: str, after_step: int = 0) -> dict[str, Any]:
        self._cleanup()
        job = self._get(run_id)
        now = time.monotonic()
        started = job.started_monotonic or job.created_monotonic
        stopped = job.finished_monotonic or now
        metrics = job.result or self._metrics_from_steps(job.steps)
        return {
            "run_id": job.run_id,
            "benchmark": job.benchmark,
            "provider": job.provider,
            "model": job.model,
            "status": job.status,
            "queue_position": self._queue_position(job),
            "created_at": job.created_at,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
            "elapsed_seconds": round(max(0.0, stopped - started), 2),
            "iterations": metrics.get("iterations", len(job.steps)),
            "total_requests": metrics.get("total_requests", len(job.steps)),
            "total_input_tokens": metrics.get("total_input_tokens", 0),
            "total_output_tokens": metrics.get("total_output_tokens", 0),
            "steps": [step for step in job.steps if step["step"] > after_step],
            "solution": metrics.get("solution", ""),
            "error": job.error or metrics.get("error"),
        }

    def cancel(self, run_id: str) -> dict[str, Any]:
        job = self._get(run_id)
        if job.status == "queued":
            try:
                self.pending.remove(run_id)
            except ValueError:
                pass
            self._mark_cancelled(job)
        elif job.status == "running" and job.execution_task:
            self._mark_cancelled(job)
            job.execution_task.cancel()
        return self.status(run_id)

    async def _consume(self) -> None:
        while not self.stopping:
            if not self.pending:
                self.wake.clear()
                await self.wake.wait()
                continue
            run_id = self.pending.popleft()
            job = self.jobs.get(run_id)
            if not job or job.status != "queued":
                continue
            self.active_id = run_id
            job.status = "running"
            job.started_at = utc_now()
            job.started_monotonic = time.monotonic()
            job.execution_task = asyncio.create_task(self._execute(job))
            try:
                await job.execution_task
            except asyncio.CancelledError:
                if job.status != "cancelled":
                    self._mark_cancelled(job)
                if self.stopping:
                    raise
            finally:
                job.execution_task = None
                self.active_id = None

    async def _execute(self, job: RunJob) -> None:
        api_key = job.api_key
        try:
            from agent_smith.models.benchmark import MBPPTaskInput, SWEBenchTaskInput
            from agent_smith.web import execute_web_task

            if job.benchmark == "mbpp":
                task = MBPPTaskInput(
                    task_id=uuid4().int % 2_000_000_000,
                    task_definition=job.payload["task_definition"].strip(),
                    function_definition=job.payload["function_definition"].strip(),
                    test_imports=[item.strip() for item in job.payload["test_imports"]],
                    test_list=[item.strip() for item in job.payload["test_list"]],
                )
            else:
                filename = SWE_TASK_FILES[job.payload["task_id"]]
                task = SWEBenchTaskInput.model_validate_json(
                    (TASK_ROOT / filename).read_text()
                )

            async def on_step(step: Any, output: Any) -> None:
                data = step.model_dump()
                data["total_input_tokens"] = output.total_input_tokens
                data["total_output_tokens"] = output.total_output_tokens
                job.steps.append(data)

            output = await execute_web_task(
                task=task,
                benchmark=job.benchmark,
                provider_url=PROVIDERS[job.provider]["url"],
                model_name=job.model,
                api_key=api_key,
                on_step=on_step,
            )
            job.result = {
                "iterations": output.iterations,
                "total_requests": output.total_requests,
                "total_input_tokens": output.total_input_tokens,
                "total_output_tokens": output.total_output_tokens,
                "solution": output.solution,
                "error": output.error,
            }
            job.status = "succeeded" if output.success else "failed"
            job.error = output.error
        except asyncio.CancelledError:
            raise
        except Exception as error:
            message = str(error).replace(api_key, "[redacted]")
            job.status = "failed"
            job.error = message or error.__class__.__name__
        finally:
            job.api_key = ""
            if job.finished_at is None:
                job.finished_at = utc_now()
                job.finished_monotonic = time.monotonic()

    def _validate_provider_model(self, provider: str, model: str) -> None:
        config = PROVIDERS.get(provider)
        valid_models = {item["id"] for item in config["models"]} if config else set()
        if model not in valid_models:
            raise HTTPException(status_code=400, detail="Unsupported provider/model combination.")

    def _get(self, run_id: str) -> RunJob:
        job = self.jobs.get(run_id)
        if not job:
            raise HTTPException(status_code=404, detail="Agent Smith run was not found.")
        return job

    def _queue_position(self, job: RunJob) -> int | None:
        if job.status != "queued":
            return None
        try:
            return list(self.pending).index(job.run_id) + 1
        except ValueError:
            return None

    def _mark_cancelled(self, job: RunJob) -> None:
        job.status = "cancelled"
        job.error = "Run cancelled."
        job.api_key = ""
        job.finished_at = utc_now()
        job.finished_monotonic = time.monotonic()

    def _cleanup(self) -> None:
        cutoff = time.monotonic() - self.retention_seconds
        expired = [
            run_id
            for run_id, job in self.jobs.items()
            if job.status in TERMINAL_STATUSES
            and job.finished_monotonic is not None
            and job.finished_monotonic < cutoff
        ]
        for run_id in expired:
            del self.jobs[run_id]

    @staticmethod
    def _metrics_from_steps(steps: list[dict[str, Any]]) -> dict[str, Any]:
        if not steps:
            return {}
        last = steps[-1]
        return {
            "iterations": len(steps),
            "total_requests": len(steps),
            "total_input_tokens": last.get("total_input_tokens", 0),
            "total_output_tokens": last.get("total_output_tokens", 0),
        }


run_manager = AgentSmithRunManager()
