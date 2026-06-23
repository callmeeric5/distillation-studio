from typing import TypedDict

from .drone import Drone, DroneStatus
from .graph import Graph
from .parser import ZoneType


class MoveTrace(TypedDict):
    drone_id: int
    from_zone: str
    to_zone: str
    duration: int
    started_turn: int
    arrives_turn: int
    reason: str


class WaitingTrace(TypedDict):
    drone_id: int
    zone: str
    next_zone: str | None
    reason: str


class TurnTrace(TypedDict):
    turn: int
    moves: list[MoveTrace]
    waiting: list[WaitingTrace]


class Scheduler:
    """Run the turn-by-turn drone simulation."""

    def __init__(self, graph: Graph, paths: list[list[str]]) -> None:
        self.graph = graph
        self.drones = [
            Drone(path=path, id=index + 1)
            for index, path in enumerate(paths)
        ]
        self.turns: list[list[str]] = []
        self.trace: list[TurnTrace] = []

    def run(self) -> list[list[str]]:
        """Simulate until every drone reaches the end zone."""
        while not self._all_delivered():
            self._advance_transit()
            turn_number = len(self.turns) + 1
            moves, move_trace, waiting_trace = self._move_available_drones(
                turn_number
            )
            if moves or not self._all_delivered():
                self.turns.append(moves)
                self.trace.append(
                    {
                        "turn": turn_number,
                        "moves": move_trace,
                        "waiting": waiting_trace,
                    }
                )
        return self.turns

    def formatted_turns(self) -> list[str]:
        """Return simulation lines in subject-compatible format."""
        return [" ".join(turn) for turn in self.turns]

    def _advance_transit(self) -> None:
        for drone in self.drones:
            arrived = drone.advance_transit()
            if arrived == self.graph.end:
                drone.status = DroneStatus.DELIVERED

    def _move_available_drones(
        self,
        turn_number: int,
    ) -> tuple[list[str], list[MoveTrace], list[WaitingTrace]]:
        moves: list[str] = []
        move_trace: list[MoveTrace] = []
        waiting_by_drone: dict[int, WaitingTrace] = {}
        moved_drone_ids: set[int] = set()
        drones = sorted(self.drones, key=lambda drone: drone.pos, reverse=True)

        for drone in drones:
            if drone.status is DroneStatus.IN_TRANSIT:
                waiting_by_drone[drone.id] = self._waiting_trace(
                    drone, "in_transit"
                )
                continue
            if drone.status is DroneStatus.DELIVERED:
                waiting_by_drone[drone.id] = self._waiting_trace(
                    drone, "delivered"
                )
                continue
            destination = drone.next_zone
            if destination is None:
                drone.status = DroneStatus.DELIVERED
                waiting_by_drone[drone.id] = self._waiting_trace(
                    drone, "delivered"
                )
                continue
            if self.graph.get_zone(destination).zone_type == ZoneType.BLOCKED:
                waiting_by_drone[drone.id] = self._waiting_trace(
                    drone, "blocked_next_zone"
                )
                continue

            link_capacity = self.graph.get_connection(
                (drone.current_zone, destination)
            ).max_link_capacity
            link_load = self._link_load(drone.current_zone, destination)
            if link_load >= link_capacity:
                waiting_by_drone[drone.id] = self._waiting_trace(
                    drone, "link_capacity"
                )
                continue
            if self._zone_load(destination) >= self.graph.zone_capacity(
                destination
            ):
                waiting_by_drone[drone.id] = self._waiting_trace(
                    drone, "zone_capacity"
                )
                continue

            source = drone.current_zone
            duration = self.graph.movement_cost(destination)
            drone.start_move(duration)
            moved_drone_ids.add(drone.id)
            moves.append(f"D{drone.id}-{destination}")
            move_trace.append(
                {
                    "drone_id": drone.id,
                    "from_zone": source,
                    "to_zone": destination,
                    "duration": duration,
                    "started_turn": turn_number,
                    "arrives_turn": turn_number + duration,
                    "reason": "move",
                }
            )

        moves.sort(key=lambda move: int(move.split("-", 1)[0][1:]))
        move_trace.sort(key=lambda move: move["drone_id"])
        waiting_trace = [
            trace
            for drone_id, trace in sorted(waiting_by_drone.items())
            if drone_id not in moved_drone_ids
        ]
        return moves, move_trace, waiting_trace

    def _link_load(self, source: str, target: str) -> int:
        key = self._link_key(source, target)
        total = 0
        for drone in self.drones:
            if drone.status is not DroneStatus.IN_TRANSIT:
                continue
            if drone.destination_index is None:
                continue
            link_source = drone.path[drone.destination_index - 1]
            link_target = drone.path[drone.destination_index]
            if self._link_key(link_source, link_target) == key:
                total += 1
        return total

    def _zone_load(self, zone_name: str) -> int:
        if zone_name == self.graph.end:
            return 0
        total = 0
        for drone in self.drones:
            if drone.status is DroneStatus.ACTIVE:
                if drone.current_zone == zone_name:
                    total += 1
            elif drone.destination_index is not None:
                if drone.path[drone.destination_index] == zone_name:
                    total += 1
        return total

    def _all_delivered(self) -> bool:
        return all(
            drone.status is DroneStatus.DELIVERED
            for drone in self.drones
        )

    def _link_key(self, source: str, target: str) -> tuple[str, str]:
        return (min(source, target), max(source, target))

    def _waiting_trace(self, drone: Drone, reason: str) -> WaitingTrace:
        next_zone = drone.next_zone
        if drone.status is DroneStatus.IN_TRANSIT:
            next_zone = (
                drone.path[drone.destination_index]
                if drone.destination_index is not None
                else None
            )
        return {
            "drone_id": drone.id,
            "zone": drone.current_zone,
            "next_zone": next_zone,
            "reason": reason,
        }
