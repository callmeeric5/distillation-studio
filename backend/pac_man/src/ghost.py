import random
from enum import Enum

from backend.pac_man.src.logger import logger
from backend.pac_man.src.maze import Maze
from backend.pac_man.src.utils import (
    DIRECTION,
    FRIGHTEN_DURATION,
    OPPOSITE_DIRECTIONS,
    Position,
    next_position,
)


class GhostState(Enum):
    CHASE = "chase"
    FRIGHTEN = "frighten"
    EATEN = "eaten"


class Ghost:
    """Ghost state, movement, and direction choice."""

    def __init__(self, maze: Maze, pos: Position, speed: int) -> None:
        self.maze = maze
        self.home = Position(pos.x, pos.y)
        self.pos = Position(pos.x, pos.y)
        self.speed = speed
        self.state = GhostState.CHASE
        self.state_time = 0.0
        self.direction = DIRECTION.RIGHT
        self.target: Position | None = None
        self.is_alive = True
        self.row = float(self.pos.x)
        self.col = float(self.pos.y)

    def move(self, direction: DIRECTION) -> None:
        """Move one full cell immediately if the path is open."""
        if not self.maze.can_move(self.pos, direction):
            return

        self.direction = direction
        self._set_position(next_position(self.pos, direction))

    def get_eaten(self) -> None:
        """Switch to the eaten state so the ghost returns home."""
        if self.state == GhostState.EATEN:
            return
        self._set_state(GhostState.EATEN)
        self.is_alive = False
        logger.info("Ghost turns to eaten state")

    def get_frightened(self) -> None:
        """Switch to frightened unless the ghost is already eaten."""
        if self.state == GhostState.EATEN:
            return
        self._set_state(GhostState.FRIGHTEN)
        logger.info("Ghost turns to frighten state")

    def respawn(self) -> None:
        """Reset the ghost at home in chase state."""
        self._set_position(Position(self.home.x, self.home.y))
        self.direction = DIRECTION.RIGHT
        self._set_state(GhostState.CHASE)
        self.is_alive = True
        logger.info(f"Ghost is respawned at {self.pos} and start chasing")

    def on_update(self, delta_time: float, player_pos: Position) -> None:
        """Move according to elapsed time and current state."""
        self._update_state_time(delta_time)

        distance = max(0.0, delta_time) * max(1, self.speed)
        while distance > 0:
            if self.target is None:
                direction = self._choose_direction(player_pos)
                if direction is None:
                    break
                self.direction = direction
                self.target = next_position(self.pos, direction)
            distance = self._move_to_target(distance)

    def _update_state_time(self, delta_time: float) -> None:
        """Change state when reach to the limit of the state time"""
        if self.state != GhostState.FRIGHTEN:
            return

        self.state_time += max(0.0, delta_time)
        if self.state_time >= FRIGHTEN_DURATION:
            self._set_state(GhostState.CHASE)

    def _set_position(self, pos: Position) -> None:
        self.pos = pos
        self.row = float(pos.x)
        self.col = float(pos.y)

    def _set_state(self, state: GhostState) -> None:
        self.state = state
        self.state_time = 0.0
        self.target = None

    def _move_to_target(self, distance: float) -> float:
        if self.target is None:
            return 0.0

        distance_x = self.target.x - self.row
        distance_y = self.target.y - self.col
        target_distance = abs(distance_x) + abs(distance_y)

        if target_distance <= distance:
            distance -= target_distance
            self._set_position(self.target)
            self.target = None
            if self.state == GhostState.EATEN and self.pos == self.home:
                self.respawn()
            return distance

        ratio = distance / target_distance
        self.row += distance_x * ratio
        self.col += distance_y * ratio
        return 0.0

    def _choose_direction(self, player_pos: Position) -> DIRECTION | None:
        """According to the ghost state choose the proper direction"""
        directions = self._available_directions()
        if not directions:
            return None

        if self.state == GhostState.EATEN:
            return min(
                directions,
                key=lambda d: (
                    self._distance_to_target(d, self.home),
                    self._direction_order(d),
                ),
            )
        if self.state == GhostState.CHASE:
            return min(
                directions,
                key=lambda d: (
                    self._distance_to_target(d, player_pos),
                    self._direction_order(d),
                ),
            )
        if self.state == GhostState.FRIGHTEN:
            return max(
                directions,
                key=lambda d: (
                    self._distance_to_target(d, player_pos),
                    -self._direction_order(d),
                ),
            )
        return random.choice(directions)

    def _available_directions(self) -> list[DIRECTION]:
        """Return the available directions opposite
        direction is not prefered"""
        directions = [
            direction
            for direction in DIRECTION
            if self.maze.can_move(self.pos, direction)
        ]
        if len(directions) <= 1:
            return directions

        opposite = OPPOSITE_DIRECTIONS[self.direction]
        next_directions = [
            direction for direction in directions if direction != opposite
        ]
        return next_directions or directions

    def _distance_to_target(
        self,
        direction: DIRECTION,
        target: Position,
    ) -> int:
        """Mahathon distance between current pos and target pos"""
        next_pos = next_position(self.pos, direction)
        return abs(next_pos.x - target.x) + abs(next_pos.y - target.y)

    def _direction_order(self, direction: DIRECTION) -> int:
        if direction == self.direction:
            return -1
        return list(DIRECTION).index(direction)
