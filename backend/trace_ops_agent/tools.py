from __future__ import annotations

from langchain_core.tools import StructuredTool

from backend.trace_ops_agent.storage import TraceLogRepository


def build_log_tools(repository: TraceLogRepository) -> list[StructuredTool]:
    async def search_logs(
        keyword: str | None = None,
        service: str | None = None,
        level: str | None = None,
        limit: int = 8,
    ) -> list[dict[str, str | None]]:
        """Search diagnosis logs by keyword, service, level, and limit."""
        return await repository.search_logs(keyword=keyword, service=service, level=level, limit=limit)

    async def get_log_by_id(log_id: str) -> dict[str, str | None] | None:
        """Return one full log record by log id, such as log-0003."""
        return await repository.get_log_by_id(log_id)

    async def get_error_summary() -> dict[str, object]:
        """Summarize error levels, affected services, and notable error logs."""
        return await repository.error_summary()

    async def get_stack_traces(
        service: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, str | None]]:
        """Return stack-trace-like, exception, or timeout logs."""
        return await repository.stack_traces(service=service, limit=limit)

    async def get_clustered_logs(service: str | None = None) -> list[dict[str, object]]:
        """Group similar logs into compact clusters for broad incident triage."""
        return await repository.clustered_logs(service=service)

    return [
        StructuredTool.from_function(coroutine=search_logs),
        StructuredTool.from_function(coroutine=get_log_by_id),
        StructuredTool.from_function(coroutine=get_error_summary),
        StructuredTool.from_function(coroutine=get_stack_traces),
        StructuredTool.from_function(coroutine=get_clustered_logs),
    ]
