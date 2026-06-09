from __future__ import annotations

import os
import re
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, MetaData, String, desc, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from api.projects.pacman.schemas import PacmanScoreCreate


DEFAULT_DATABASE_URL = "postgresql+asyncpg://traceops:traceops@postgres:5432/pacman"
_DATABASE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class Base(DeclarativeBase):
    metadata = MetaData()


class PacmanScoreRow(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    player_name: Mapped[str] = mapped_column(String(32), index=True)
    score: Mapped[int] = mapped_column(Integer, index=True)
    elapsed_seconds: Mapped[int] = mapped_column(Integer)
    level_reached: Mapped[int] = mapped_column(Integer, index=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker | None = None
_schema_ready = False
_database_ready = False


def _database_url() -> str:
    return os.getenv("PACMAN_DATABASE_URL") or DEFAULT_DATABASE_URL


def get_engine() -> AsyncEngine:
    global _engine, _session_factory
    if _engine is None:
        _engine = create_async_engine(_database_url(), pool_pre_ping=True)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_session_factory() -> async_sessionmaker:
    get_engine()
    if _session_factory is None:
        raise RuntimeError("Pac-Man database session factory is not initialized.")
    return _session_factory


async def ensure_database() -> None:
    global _database_ready
    if _database_ready:
        return

    url = make_url(_database_url())
    database_name = url.database
    if not database_name:
        raise RuntimeError("Pac-Man database URL must include a database name.")
    if not _DATABASE_NAME_RE.match(database_name):
        raise RuntimeError("Pac-Man database name must be a simple PostgreSQL identifier.")

    maintenance_engine = create_async_engine(
        url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True,
    )
    try:
        async with maintenance_engine.connect() as conn:
            exists = await conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
                {"database_name": database_name},
            )
            if not exists:
                await conn.execute(text(f'CREATE DATABASE "{database_name}"'))
    finally:
        await maintenance_engine.dispose()
    _database_ready = True


async def ensure_schema() -> None:
    global _schema_ready
    if _schema_ready:
        return
    await ensure_database()
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    _schema_ready = True


async def insert_score(score: PacmanScoreCreate) -> PacmanScoreRow:
    await ensure_schema()
    payload = score.model_dump()
    payload["player_name"] = " ".join(payload["player_name"].strip().split())
    async with get_session_factory()() as session:
        row = PacmanScoreRow(**payload)
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row


async def list_scores(limit: int = 10) -> list[PacmanScoreRow]:
    await ensure_schema()
    statement = (
        select(PacmanScoreRow)
        .order_by(
            desc(PacmanScoreRow.score),
            PacmanScoreRow.elapsed_seconds.asc(),
            desc(PacmanScoreRow.level_reached),
            PacmanScoreRow.created_at.asc(),
        )
        .limit(max(1, min(limit, 50)))
    )
    async with get_session_factory()() as session:
        return list((await session.execute(statement)).scalars().all())
