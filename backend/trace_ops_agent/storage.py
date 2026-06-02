from __future__ import annotations

import os
from collections import Counter, defaultdict

from sqlalchemy import MetaData, String, Text, and_, insert, select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from backend.trace_ops_agent.models import LogEntry


DEFAULT_DATABASE_URL = "postgresql+asyncpg://traceops:traceops@postgres:5432/traceops"


class Base(DeclarativeBase):
    metadata = MetaData()


class TraceLog(Base):
    __tablename__ = "trace_ops_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    diagnosis_id: Mapped[str] = mapped_column(String(64), index=True)
    log_id: Mapped[str] = mapped_column(String(32), index=True)
    timestamp: Mapped[str | None] = mapped_column(String(64), nullable=True)
    level: Mapped[str] = mapped_column(String(16), index=True)
    service: Mapped[str] = mapped_column(String(128), index=True)
    message: Mapped[str] = mapped_column(Text)
    raw: Mapped[str] = mapped_column(Text)


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker | None = None
_schema_ready = False


def get_engine() -> AsyncEngine:
    global _engine, _session_factory
    if _engine is None:
        database_url = os.getenv("TRACEOPS_DATABASE_URL") or os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL
        _engine = create_async_engine(database_url, pool_pre_ping=True)
        _session_factory = async_sessionmaker(_engine)
    return _engine


def get_session_factory() -> async_sessionmaker:
    get_engine()
    if _session_factory is None:
        raise RuntimeError("Trace-Ops database session factory is not initialized.")
    return _session_factory


async def ensure_schema() -> None:
    global _schema_ready
    if _schema_ready:
        return
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    _schema_ready = True


class TraceLogRepository:
    def __init__(self, diagnosis_id: str):
        self.diagnosis_id = diagnosis_id

    async def insert_logs(self, logs: list[LogEntry]) -> None:
        await ensure_schema()
        if not logs:
            return
        rows = [
            {
                "diagnosis_id": log.diagnosis_id,
                "log_id": log.log_id,
                "timestamp": log.timestamp,
                "level": log.level,
                "service": log.service,
                "message": log.message,
                "raw": log.raw,
            }
            for log in logs
        ]
        async with get_engine().begin() as conn:
            await conn.execute(insert(TraceLog), rows)

    async def search_logs(
        self,
        keyword: str | None = None,
        service: str | None = None,
        level: str | None = None,
        limit: int = 8,
    ) -> list[dict[str, str | None]]:
        await ensure_schema()
        conditions = [TraceLog.diagnosis_id == self.diagnosis_id]
        if service:
            conditions.append(TraceLog.service.ilike(f"%{service}%"))
        if level:
            conditions.append(TraceLog.level == level.upper())
        if keyword:
            conditions.append(TraceLog.raw.ilike(f"%{keyword}%"))

        statement = (
            select(TraceLog)
            .where(and_(*conditions))
            .order_by(TraceLog.id.asc())
            .limit(max(1, min(limit, 200)))
        )
        async with get_session_factory()() as session:
            rows = (await session.execute(statement)).scalars().all()
        return [_serialize_log(row) for row in rows]

    async def get_log_by_id(self, log_id: str) -> dict[str, str | None] | None:
        await ensure_schema()
        statement = select(TraceLog).where(
            TraceLog.diagnosis_id == self.diagnosis_id,
            TraceLog.log_id == log_id,
        )
        async with get_session_factory()() as session:
            row = (await session.execute(statement)).scalar_one_or_none()
        return _serialize_log(row) if row else None

    async def error_summary(self) -> dict[str, object]:
        logs = await self.search_logs(limit=200)
        by_level = Counter(str(log["level"]) for log in logs)
        by_service = Counter(str(log["service"]) for log in logs)
        errors = [log for log in logs if str(log["level"]) in {"ERROR", "CRITICAL", "WARN"}]
        return {
            "total_logs": len(logs),
            "levels": dict(by_level),
            "services": dict(by_service),
            "notable_errors": errors[:10],
        }

    async def stack_traces(self, service: str | None = None, limit: int = 5) -> list[dict[str, str | None]]:
        logs = await self.search_logs(keyword="trace", service=service, limit=50)
        stack_like = [
            log
            for log in logs
            if "trace" in str(log["raw"]).lower()
            or "exception" in str(log["raw"]).lower()
            or "timeout" in str(log["raw"]).lower()
        ]
        return stack_like[: max(1, min(limit, 10))]

    async def clustered_logs(self, service: str | None = None) -> list[dict[str, object]]:
        logs = await self.search_logs(service=service, limit=200)
        clusters: dict[str, list[dict[str, str | None]]] = defaultdict(list)
        for log in logs:
            key = _cluster_key(str(log["message"]))
            clusters[key].append(log)
        return [
            {"pattern": key, "count": len(items), "examples": items[:3]}
            for key, items in sorted(clusters.items(), key=lambda item: len(item[1]), reverse=True)[:8]
        ]


def _serialize_log(log: TraceLog) -> dict[str, str | None]:
    return {
        "log_id": log.log_id,
        "timestamp": log.timestamp,
        "level": log.level,
        "service": log.service,
        "message": log.message,
        "raw": log.raw,
    }


def _cluster_key(message: str) -> str:
    words = [
        word.lower()
        for word in message.split()
        if not any(character.isdigit() for character in word) and len(word) > 2
    ]
    return " ".join(words[:6]) or message[:80]
