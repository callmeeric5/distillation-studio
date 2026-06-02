from __future__ import annotations

import re
from uuid import uuid4

from backend.trace_ops_agent.models import LogEntry


SAMPLE_LOGS = """[2026-06-02T08:10:12Z] ERROR order-service trace_id=trc-91 payment request timed out after 3000ms
[2026-06-02T08:10:13Z] WARN payment-service trace_id=trc-91 connection pool exhausted active=100 idle=0
[2026-06-02T08:10:14Z] ERROR order-service trace_id=trc-92 failed to reserve inventory after payment timeout
[2026-06-02T08:11:02Z] INFO api-gateway p95 latency=1840ms route=/checkout
[2026-06-02T08:11:33Z] ERROR payment-service trace_id=trc-94 database connection acquisition timeout"""

LOG_PATTERN = re.compile(
    r"^\s*(?:\[(?P<timestamp>[^\]]+)\]\s*)?"
    r"(?P<level>ERROR|WARN|WARNING|INFO|DEBUG|TRACE|CRITICAL)?\s*"
    r"(?P<service>[A-Za-z0-9_.:-]+)?\s*"
    r"(?P<message>.*)$",
    re.IGNORECASE,
)


def normalize_logs(diagnosis_id: str, raw_logs: str) -> list[LogEntry]:
    source = raw_logs.strip() or SAMPLE_LOGS
    entries: list[LogEntry] = []
    for index, line in enumerate(source.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        entries.append(_parse_line(diagnosis_id, index, line))
    return entries


def new_diagnosis_id() -> str:
    return f"diag-{uuid4().hex[:12]}"


def _parse_line(diagnosis_id: str, index: int, line: str) -> LogEntry:
    match = LOG_PATTERN.match(line)
    if not match:
        return LogEntry(
            diagnosis_id=diagnosis_id,
            log_id=f"log-{index:04d}",
            timestamp=None,
            level="INFO",
            service="unknown",
            message=line,
            raw=line,
        )

    level = (match.group("level") or "INFO").upper()
    if level == "WARNING":
        level = "WARN"

    service = match.group("service") or "unknown"
    message = match.group("message").strip() or line

    return LogEntry(
        diagnosis_id=diagnosis_id,
        log_id=f"log-{index:04d}",
        timestamp=match.group("timestamp"),
        level=level,
        service=service,
        message=message,
        raw=line,
    )
