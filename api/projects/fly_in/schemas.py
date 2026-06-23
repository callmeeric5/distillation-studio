from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


Difficulty = Literal["easy", "medium", "hard", "challenger"]


class MapSummary(BaseModel):
    difficulty: Difficulty
    filename: str
    name: str
    path: str


class MapListResponse(BaseModel):
    maps: dict[Difficulty, list[MapSummary]]


class PositionResponse(BaseModel):
    x: int
    y: int


class ZoneResponse(BaseModel):
    name: str
    position: PositionResponse
    zone_type: str
    color: str | None
    max_drones: int
    role: Literal["start", "end", "normal"]


class ConnectionResponse(BaseModel):
    source: str
    target: str
    max_link_capacity: int


class DroneAssignmentResponse(BaseModel):
    drone_id: int
    path: list[str]
    path_index: int


class MoveTraceResponse(BaseModel):
    drone_id: int
    from_zone: str
    to_zone: str
    duration: int
    started_turn: int
    arrives_turn: int
    reason: str


class WaitingTraceResponse(BaseModel):
    drone_id: int
    zone: str
    next_zone: str | None
    reason: str


class TurnTraceResponse(BaseModel):
    turn: int
    moves: list[MoveTraceResponse]
    waiting: list[WaitingTraceResponse]
    formatted: str


class SimulationStatsResponse(BaseModel):
    drones: int
    zones: int
    connections: int
    turns: int
    paths: int
    start: str
    end: str


class SimulationResponse(BaseModel):
    map: MapSummary
    zones: list[ZoneResponse]
    connections: list[ConnectionResponse]
    assignments: list[DroneAssignmentResponse]
    turns: list[TurnTraceResponse]
    stats: SimulationStatsResponse
