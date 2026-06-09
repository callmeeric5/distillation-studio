import random

from backend.pac_man.src.ghost import Ghost, GhostState
from backend.pac_man.src.logger import logger
from backend.pac_man.src.maze import MazeLoader
from backend.pac_man.src.pacgum import Pacgum, SuperPacgum
from backend.pac_man.src.parser import Config
from backend.pac_man.src.player import Player
from backend.pac_man.src.utils import FRIGHTEN_DURATION, Position


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

    def check_collisions(self) -> None:
        """Check collision between player and entities"""
        self._check_pacgum_collision()
        self._check_super_pacgum_collision()
        self._check_ghost_collision()

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

        self.time_left -= max(0.0, delta_time)
        if self.time_left <= 0:
            self.game_over = True
            logger.info("Time is up, you lose!")
            return

        self.player.on_update(delta_time)

        for ghost in self.ghosts:
            ghost.on_update(delta_time, self.player.pos)

        self.check_collisions()
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

    def _check_ghost_collision(self) -> None:
        """Check collision between player and ghost"""
        for ghost in self.ghosts:
            if self.player.pos != ghost.pos:
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
