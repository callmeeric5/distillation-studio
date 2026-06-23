from dataclasses import dataclass
from enum import Enum


class DroneStatus(Enum):
    ACTIVE = "active"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"


@dataclass
class Drone:
    path: list[str]
    id: int
    pos: int = 0
    status: DroneStatus = DroneStatus.ACTIVE
    remaining_turns: int = 0
    destination_index: int | None = None

    @property
    def current_zone(self) -> str:
        return self.path[self.pos]

    @property
    def next_zone(self) -> str | None:
        next_pos = self.pos + 1
        if next_pos >= len(self.path):
            return None
        return self.path[next_pos]

    def start_move(self, duration: int) -> str:
        """Put the drone in transit toward the next zone."""
        next_zone = self.next_zone
        if next_zone is None:
            raise ValueError("delivered drone cannot move")
        self.status = DroneStatus.IN_TRANSIT
        self.remaining_turns = duration
        self.destination_index = self.pos + 1
        return next_zone

    def advance_transit(self) -> str | None:
        """Advance one turn and return the arrived zone, if any."""
        if self.status is not DroneStatus.IN_TRANSIT:
            return None
        self.remaining_turns -= 1
        if self.remaining_turns > 0:
            return None
        if self.destination_index is None:
            raise ValueError("in-transit drone has no destination")
        self.pos = self.destination_index
        self.destination_index = None
        self.status = DroneStatus.ACTIVE
        return self.current_zone
