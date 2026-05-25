from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

from ..utils import DIRECTIONS, MazeGrid


class GenerateMethod(Enum):
    """
    List of the generating algorithm
    """

    BACKTRACKING = "backtracking"
    PRIM = "prim"
    BINARY_TREE = "binary_tree"
    SIDEWINDER = "sidewinder"


class SolveMethod(Enum):
    """
    List of the solving algorithm
    """

    BFS = "bfs"
    DFS = "dfs"
    ASTAR = "astar"


@dataclass
class AlgorithmGen(ABC):
    """
    Is the blueprint for each Maze generator algorithm

    Attributes:
        grid: The starting grid of the maze
        visited: The boolean matrix of the visited block
        start: A tuple with the coord of the maze's start
        direction: A list of tuple which will give our direction:
                move_row: the row were we're going
                move_col: the col were we're going
                curr_wall: the wall that sould be broken to go
                           to the target
                target_wall: the wall of the target that have
                              been break
    """

    grid: MazeGrid
    visited: np.ndarray
    start: tuple[int, int]
    trace: list[dict[str, Any]] | None = None
    direction: list[tuple[int, int, int, int]] = field(
        default_factory=lambda: list(DIRECTIONS)
    )

    @abstractmethod
    def generate(self) -> None:
        """
        The generate methode that each inheriting class must have
        """
        pass

    def open_between(
        self,
        current: tuple[int, int],
        target: tuple[int, int],
        curr_wall: int,
        target_wall: int,
        kind: str = "carve",
    ) -> None:
        """
        Open both walls between two neighboring cells and optionally trace it.
        """
        open_wall(self.grid, current[0], current[1], curr_wall)
        open_wall(self.grid, target[0], target[1], target_wall)
        if self.trace is not None:
            self.trace.append(
                {
                    "kind": kind,
                    "from": {"row": current[0], "col": current[1]},
                    "to": {"row": target[0], "col": target[1]},
                    "direction": wall_direction(curr_wall),
                }
            )


@dataclass
class AlgorithmSolve(ABC):
    """
    Is the blueprint for each solving algorithm

    Attributes:
        grid: the already generated MazeGrid
        entry: The entry coord as a tuple
        exit: The exit coord as a tuple
    """

    grid: MazeGrid
    entry: tuple[int, int]
    exit: tuple[int, int]
    trace: list[dict[str, int]] | None = None

    @abstractmethod
    def solve(self) -> list[tuple[int, int]]:
        """
        Each algorithm must have a solver
        """
        pass

    def record_visit(self, coord: tuple[int, int]) -> None:
        if self.trace is not None:
            self.trace.append({"row": coord[0], "col": coord[1]})

    def get_neighbors(self, coord) -> list[tuple[int, int]]:
        """
        Neignbors are the adjasent cells having the open wall
        """
        row, col = coord
        neighbors = []
        for move_row, move_col, curr_wall, _ in DIRECTIONS:
            target_row = row + move_row
            target_col = col + move_col
            if not is_in_bound(self.grid, target_row, target_col):
                continue
            if self.grid.blocked[target_row][target_col]:
                continue
            if self.grid.walls[row][col][curr_wall]:
                continue
            neighbors.append((target_row, target_col))
        return neighbors


def is_blocked(grid: MazeGrid, coord: tuple[int, int]) -> bool:
    """
    Check if the given coord is in the blocked list

    Args:
        MazeGrid: The generating maze grid
        coord: The coord that being check

    Returns:
        True if it's in the blocked list
        False if it's not
    """
    return grid.blocked[coord[0], coord[1]]


def is_in_bound(grid: MazeGrid, row: int, col: int) -> bool:
    """
    Check if the algorithm isn't trying to go outside the maze wall

    Args:
        MazeGrid: The generating maze grid
        row: The row where the algorithm is trying to go
        col: The col where the algorithm is trying to go

    Returns:
        True if the row AND col are in the maze
        False if it's outside
    """
    return 0 <= row < grid.shape[0] and 0 <= col < grid.shape[1]


def open_wall(grid: MazeGrid, row: int, col: int, wall_index: int) -> None:
    """
    Break the given wall

    Args:
        MazeGrid: The generating maze grid
        row: The row of the block
        col: The col of the block
        wall_index: The wall of the block that we want to open
    """
    grid.walls[row, col, wall_index] = False


def wall_direction(wall_index: int) -> str:
    return {
        0: "north",
        1: "east",
        2: "south",
        3: "west",
    }[wall_index]
