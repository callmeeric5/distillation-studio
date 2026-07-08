from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Scheduler = Literal["FIFO", "EDF"]
CoderState = Literal["idle", "compiling", "debugging", "refactoring", "burned_out", "complete"]
DongleState = Literal["available", "in_use", "cooldown"]
EventKind = Literal[
    "dongle_taken",
    "compiling",
    "debugging",
    "refactoring",
    "burned_out",
    "completed",
    "log",
]
Outcome = Literal["completed", "burned_out"]


class RunRequest(BaseModel):
    number_of_coders: int = Field(4, ge=1, le=12)
    time_to_burnout: int = Field(1200, ge=1, le=10000)
    time_to_compile: int = Field(120, ge=0, le=5000)
    time_to_debug: int = Field(120, ge=0, le=5000)
    time_to_refactor: int = Field(120, ge=0, le=5000)
    number_of_compiles_required: int = Field(3, ge=1, le=20)
    dongle_cooldown: int = Field(20, ge=0, le=5000)
    scheduler: Scheduler = "FIFO"


class LogEventResponse(BaseModel):
    index: int
    time: int
    coder_id: int | None
    kind: EventKind
    message: str
    raw: str


class CoderFrameResponse(BaseModel):
    id: int
    state: CoderState
    compiles_done: int
    dongles: list[int]
    deadline: int


class DongleFrameResponse(BaseModel):
    id: int
    state: DongleState
    holder: int | None
    cooldown_until: int


class ReplayFrameResponse(BaseModel):
    index: int
    time: int
    event: LogEventResponse | None
    coders: list[CoderFrameResponse]
    dongles: list[DongleFrameResponse]


class SimulationStatsResponse(BaseModel):
    outcome: Outcome
    total_events: int
    total_time: int
    coders_completed: int
    compiles_completed: int
    scheduler: Scheduler


class RunResponse(BaseModel):
    config: RunRequest
    events: list[LogEventResponse]
    frames: list[ReplayFrameResponse]
    raw_log: list[str]
    stats: SimulationStatsResponse
