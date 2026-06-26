import random
from collections.abc import Sequence

from backend.pac_man.src.ghost import Ghost, GhostState
from backend.pac_man.src.logger import logger
from backend.pac_man.src.maze import MazeLoader
from backend.pac_man.src.pacgum import Pacgum, SuperPacgum
from backend.pac_man.src.parser import Config
from backend.pac_man.src.player import Player
from backend.pac_man.src.utils import FRIGHTEN_DURATION, Position


ActorPoint = tuple[float, float]
ActorPath = tuple[ActorPoint, ActorPoint]
COLLISION_RADIUS = 0.42


class Level:
    """Every entity of the current level"""

    def __init__(
        self,
        lvl: int,
        config: Config,
        player_speed: int = 4,
        ghost_speed: int = 3,
        is_cheat_mode: bool = False,
    ) -> None:
        self.config = config
        self.is_cheat_mode = is_cheat_mode
        self.lvl = lvl
        self.level_config = config.levels[lvl]
        if self.level_config.seed is None:
            self.level_config.seed = random.randint(1, 999)
        random.seed(self.level_config.seed)
        self.maze = MazeLoader(self.level_config).load()
        self.player = Player(self.maze, config.lives, speed=player_speed)
        self.ghosts = self._create_ghosts(ghost_speed)
        self.super_pacgums = self._create_super_pacgums()
        self.pacgums = self._create_pacgums()
        self.time_left = float(config.level_max_time)
        self.win = False
        self.game_over = False

    def check_collisions(
        self,
        player_path: ActorPath | None = None,
        ghost_paths: Sequence[ActorPath] | None = None,
    ) -> None:
        """Check collision between player and entities"""
        self._check_pacgum_collision()
        self._check_super_pacgum_collision()
        self._check_ghost_collision(player_path, ghost_paths)

    def check_win(self) -> None:
        """Check level pass"""
        if not self.pacgums and not self.super_pacgums:
            self.win = True
            logger.info(
                f"Congradulations! You win level {self.lvl + 1}"
                f" with {self.player.score} points!"
            )

    def on_update(self, delta_time: float) -> None:
        """Run the level"""
        if self.win or self.game_over:
            return

        if not self.is_cheat_mode:
            self.time_left -= max(0.0, delta_time)
            if self.time_left <= 0:
                self.game_over = True
                logger.info("Time is up, you lose!")
                return

        player_start = self._actor_point(self.player)
        ghost_starts = [self._actor_point(ghost) for ghost in self.ghosts]

        self.player.on_update(delta_time)

        for ghost in self.ghosts:
            ghost.on_update(delta_time, self.player.pos)

        player_path = (player_start, self._actor_point(self.player))
        ghost_paths = [
            (ghost_start, self._actor_point(ghost))
            for ghost_start, ghost in zip(ghost_starts, self.ghosts)
        ]
        self.check_collisions(player_path, ghost_paths)
        self.check_win()

    def _check_pacgum_collision(self) -> None:
        """Check collision between player and pacgum"""
        for pacgum in self.pacgums:
            if self.player.pos == pacgum.pos:
                self.player.add_score(pacgum.points)
                self.pacgums.remove(pacgum)
                break

    def _check_super_pacgum_collision(self) -> None:
        """Check collision between player and superpacgum"""
        for super_pacgum in self.super_pacgums:
            if self.player.pos == super_pacgum.pos:
                self.player.add_score(super_pacgum.points)
                for ghost in self.ghosts:
                    ghost.get_frightened()
                self.super_pacgums.remove(super_pacgum)
                break

    def _check_ghost_collision(
        self,
        player_path: ActorPath | None = None,
        ghost_paths: Sequence[ActorPath] | None = None,
    ) -> None:
        """Check collision between player and ghost"""
        for index, ghost in enumerate(self.ghosts):
            ghost_path = ghost_paths[index] if ghost_paths is not None else None
            if not self._actors_collide(ghost, player_path, ghost_path):
                continue
            if ghost.state == GhostState.FRIGHTEN:
                self.player.add_score(self.config.points_per_ghost)
                ghost.get_eaten()
                logger.info(
                    "Eat a ghost adding "
                    f"{self.config.points_per_ghost} points!"
                )
            elif ghost.state == GhostState.CHASE:
                if self.is_cheat_mode:
                    continue
                self.player.lose_life()
                if self.player.lives <= 0:
                    self.game_over = True
                else:
                    self.player.respawn()
                    for ghost in self.ghosts:
                        ghost.respawn()
                break

    def _actors_collide(
        self,
        ghost: Ghost,
        player_path: ActorPath | None,
        ghost_path: ActorPath | None,
    ) -> bool:
        if self.player.pos == ghost.pos:
            return True
        if player_path is None or ghost_path is None:
            return False
        return _segment_distance(player_path, ghost_path) <= COLLISION_RADIUS

    def _actor_point(self, actor) -> ActorPoint:
        return (float(actor.row), float(actor.col))

    def _create_ghosts(self, ghost_speed: int) -> list[Ghost]:
        """Create ghosts on the 4 corners"""
        return [
            Ghost(self.maze, Position(0, 1), speed=ghost_speed),
            Ghost(
                self.maze,
                Position(1, self.maze.width - 1),
                speed=ghost_speed,
            ),
            Ghost(
                self.maze,
                Position(self.maze.height - 1, 1),
                speed=ghost_speed,
            ),
            Ghost(
                self.maze,
                Position(self.maze.height - 2, self.maze.width - 1),
                speed=ghost_speed,
            ),
        ]

    def _create_pacgums(self) -> list[Pacgum]:
        """Init pacgums"""
        used_positions = {
            (self.player.pos.x, self.player.pos.y),
            *[(ghost.pos.x, ghost.pos.y) for ghost in self.ghosts],
            *[(gum.pos.x, gum.pos.y) for gum in self.super_pacgums],
        }
        positions = self._random_empty_positions(
            count=self.config.pacgum,
            used_positions=used_positions,
        )
        return [
            Pacgum(pos, self.config.points_per_pacgum)
            for pos in positions
            if not self.maze.cells[pos.x][pos.y].is_42_pattern
        ]

    def _create_super_pacgums(self) -> list[SuperPacgum]:
        """Init superpacgums around corners"""
        positions = [
            Position(0, 0),
            Position(0, self.maze.width - 1),
            Position(self.maze.height - 1, 0),
            Position(self.maze.height - 1, self.maze.width - 1),
        ]
        return [
            SuperPacgum(
                pos,
                self.config.points_per_super_pacgum,
                FRIGHTEN_DURATION,
            )
            for pos in positions
            if not self.maze.cells[pos.x][pos.y].is_42_pattern
        ]

    def _random_empty_positions(
        self,
        count: int,
        used_positions: set[tuple[int, int]],
    ) -> list[Position]:
        """Possible location on the maze"""

        positions = []
        for row in range(self.maze.height):
            for col in range(self.maze.width):
                if (row, col) not in used_positions and not self.maze.cells[
                    row
                ][col].is_42_pattern:
                    positions.append(Position(row, col))

        random.shuffle(positions)
        return positions[:count]


def _segment_distance(first: ActorPath, second: ActorPath) -> float:
    first_start, first_end = first
    second_start, second_end = second
    if _segments_intersect(first_start, first_end, second_start, second_end):
        return 0.0
    return min(
        _point_segment_distance(first_start, second_start, second_end),
        _point_segment_distance(first_end, second_start, second_end),
        _point_segment_distance(second_start, first_start, first_end),
        _point_segment_distance(second_end, first_start, first_end),
    )


def _segments_intersect(
    first_start: ActorPoint,
    first_end: ActorPoint,
    second_start: ActorPoint,
    second_end: ActorPoint,
) -> bool:
    def orientation(a: ActorPoint, b: ActorPoint, c: ActorPoint) -> float:
        return (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])

    def on_segment(a: ActorPoint, b: ActorPoint, c: ActorPoint) -> bool:
        return (
            min(a[0], c[0]) <= b[0] <= max(a[0], c[0])
            and min(a[1], c[1]) <= b[1] <= max(a[1], c[1])
        )

    o1 = orientation(first_start, first_end, second_start)
    o2 = orientation(first_start, first_end, second_end)
    o3 = orientation(second_start, second_end, first_start)
    o4 = orientation(second_start, second_end, first_end)

    if o1 * o2 < 0 and o3 * o4 < 0:
        return True

    epsilon = 1e-9
    return (
        abs(o1) <= epsilon
        and on_segment(first_start, second_start, first_end)
        or abs(o2) <= epsilon
        and on_segment(first_start, second_end, first_end)
        or abs(o3) <= epsilon
        and on_segment(second_start, first_start, second_end)
        or abs(o4) <= epsilon
        and on_segment(second_start, first_end, second_end)
    )


def _point_segment_distance(
    point: ActorPoint,
    segment_start: ActorPoint,
    segment_end: ActorPoint,
) -> float:
    delta_row = segment_end[0] - segment_start[0]
    delta_col = segment_end[1] - segment_start[1]
    length_squared = delta_row * delta_row + delta_col * delta_col
    if length_squared == 0:
        return _point_distance(point, segment_start)

    progress = (
        (point[0] - segment_start[0]) * delta_row
        + (point[1] - segment_start[1]) * delta_col
    ) / length_squared
    progress = max(0.0, min(1.0, progress))
    closest = (
        segment_start[0] + progress * delta_row,
        segment_start[1] + progress * delta_col,
    )
    return _point_distance(point, closest)


def _point_distance(first: ActorPoint, second: ActorPoint) -> float:
    delta_row = first[0] - second[0]
    delta_col = first[1] - second[1]
    return (delta_row * delta_row + delta_col * delta_col) ** 0.5
