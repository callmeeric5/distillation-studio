from __future__ import annotations

from pydantic import BaseModel


class TapRoom(BaseModel):
    name: str
    description: str
    exits: dict[str, str]


class TapItem(BaseModel):
    name: str
    description: str


class TapNpc(BaseModel):
    name: str
    description: str
    hostile: bool
    quest: str | None = None


class TapQuest(BaseModel):
    description: str
    giver: str
    reward: str


class TapWorldResponse(BaseModel):
    start_room: str
    rooms: dict[str, TapRoom]
    items: dict[str, TapItem]
    npcs: dict[str, TapNpc]
    quests: dict[str, TapQuest]
