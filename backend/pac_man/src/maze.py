from dataclasses import dataclass

from mazegenerator.mazegenerator import MazeGenerator

from backend.pac_man.src.logger import logger
from backend.pac_man.src.parser import LevelConfig
from backend.pac_man.src.utils import DIRECTION, Position


@dataclass(frozen=True)
class Cell:
    north_wall: bool
    east_wall: bool
    south_wall: bool
    west_wall: bool
    is_42_pattern: bool


@dataclass(frozen=True)
class Maze:
    width: int
    height: int
    cells: list[list[Cell]]

    def can_move(self, pos: Position, direction: DIRECTION) -> bool:
        """Can the entity move on the given direction and position"""
        x, y = pos.x, pos.y
        cell = self.cells[x][y]
        if direction == DIRECTION.UP:
            return not cell.north_wall and x > 0
        if direction == DIRECTION.DOWN:
            return not cell.south_wall and x < self.height - 1
        if direction == DIRECTION.LEFT:
            return not cell.west_wall and y > 0
        if direction == DIRECTION.RIGHT:
            return not cell.east_wall and y < self.width - 1
        return False


class MazeLoader:
    """
    load the level config and convert the maze
    """

    def __init__(self, level: LevelConfig) -> None:
        self.level = level

    def load(self) -> Maze:
        try:
            generator = MazeGenerator(
                (self.level.width, self.level.height),
                False,
                (0, 0),
                (self.level.width - 1, self.level.height - 1),
                self.level.seed if self.level.seed else 42,
            )
        except Exception as e:
            logger.error(f"failed to generate maze, {e}")
            raise
        _cells = []

        for row in generator.maze:
            cells = []
            for col in row:
                cells.append(
                    Cell(
                        north_wall=col & 1 != 0,
                        east_wall=col & 2 != 0,
                        south_wall=col & 4 != 0,
                        west_wall=col & 8 != 0,
                        is_42_pattern=col == 15,
                    )
                )
            _cells.append(cells)
        logger.info(
            f"maze generated, width: {self.level.width} "
            f"height: {self.level.height}"
        )
        return Maze(self.level.width, self.level.height, _cells)
