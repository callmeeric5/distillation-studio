from backend.pac_man.src.logger import logger
from backend.pac_man.src.maze import Maze
from backend.pac_man.src.utils import DIRECTION, Position, next_position


class Player:
    """
    Player state and one-cell movement rules.
    Args:
    pos: the current position of the player
    direction: the current position of the player
    request_direction: change the direction to a new one
    target: target cell for the current direction
    row: for calculating the animation
    col: for calculating the animation
    """

    def __init__(self, maze: Maze, lives: int, speed: int) -> None:
        self.maze = maze
        self.lives = lives
        self.speed = speed
        self.score = 0
        self.is_alive = True
        self.spawn_pos = self._find_spawn_position()
        self.pos = Position(self.spawn_pos.x, self.spawn_pos.y)
        self.direction = DIRECTION.RIGHT
        self.request_direction = DIRECTION.RIGHT
        self.target: Position | None = None
        self.row = float(self.pos.x)
        self.col = float(self.pos.y)

    def move(self, direction: DIRECTION) -> None:
        """Move one cell in the given direction if the path is open."""
        if not self.maze.can_move(self.pos, direction):
            return

        self.direction = direction
        self._set_position(next_position(self.pos, direction))

    def lose_life(self) -> None:
        """Decrease player lives by one."""
        self.lives = max(0, self.lives - 1)
        self.is_alive = self.lives > 0
        logger.info(f"Ah oh, you died... {self.lives} remaining")

    def respawn(self) -> None:
        """Respawn the player at the center of the maze."""
        self._set_position(Position(self.spawn_pos.x, self.spawn_pos.y))
        self.direction = DIRECTION.RIGHT
        self.request_direction = DIRECTION.RIGHT
        self.target = None
        self.is_alive = True
        logger.info(f"Player is respawned at {self.pos}")

    def add_score(self, point: int) -> None:
        """Add score points."""
        self.score += point
        logger.info(f"Player gains {point} points, total score: {self.score}")

    def set_direction(self, direction: DIRECTION) -> None:
        """Set direction."""
        self.request_direction = direction

    def on_update(self, delta_time: float) -> None:
        """
        Move the player according to elapsed time.
        """
        if not self.is_alive:
            return
        distance = max(0, delta_time) * max(1, self.speed)
        while distance > 0:
            if self.target is None:
                # If detect user change the direction
                if self.maze.can_move(self.pos, self.request_direction):
                    self.direction = self.request_direction
                # Move on the same direction
                if self.maze.can_move(self.pos, self.direction):
                    self.target = next_position(self.pos, self.direction)
                else:
                    break
            distance = self._move_to_target(distance)

    def _set_position(self, pos: Position) -> None:
        self.pos = pos
        self.row = float(pos.x)
        self.col = float(pos.y)

    def _find_spawn_position(self) -> Position:
        """Respawn at the center of the maze if possible"""
        center = Position(self.maze.height // 2, self.maze.width // 2)
        candidates = [
            center,
            Position(center.x - 1, center.y),
            Position(center.x + 1, center.y),
            Position(center.x, center.y - 1),
            Position(center.x, center.y + 1),
        ]

        for pos in candidates:
            if not self.maze.cells[pos.x][pos.y].is_42_pattern:
                return pos

        return center

    def _move_to_target(self, distance: float) -> float:
        """Move toward target and return leftover distance."""
        if not self.target:
            return 0.0
        distance_x = self.target.x - self.row
        distance_y = self.target.y - self.col
        target_distance = abs(distance_x) + abs(distance_y)
        if target_distance <= distance:
            distance -= target_distance
            self._set_position(self.target)
            self.target = None
            return distance
        ratio = distance / target_distance
        self.row += distance_x * ratio
        self.col += distance_y * ratio
        return 0.0
