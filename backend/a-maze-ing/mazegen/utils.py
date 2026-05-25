from dataclasses import dataclass
from enum import Enum

import numpy as np

"""
    The matrix for the Forty Two icone
"""
PATTERN_42: list[list[int]] = [
    [1, 0, 0, 0, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 1, 1],
    [0, 0, 1, 0, 1, 0, 0],
    [0, 0, 1, 0, 1, 1, 1],
]


class Direction(Enum):
    """
    breakdown on NORTH:
    -1: go towards the north direction which means move up one row
    0: stay on the same column
    0: the index of Direction, north is 0, break current cell northern wall
    2: the index of Direction, south is 2, break target cell southern wall
    """

    NORTH = (-1, 0, 0, 2)
    EAST = (0, 1, 1, 3)
    SOUTH = (1, 0, 2, 0)
    WEST = (0, -1, 3, 1)


DIRECTIONS = [d.value for d in Direction]


@dataclass
class MazeGrid:
    """
    The maze grid with the data of the walls and blocked

    This class is used as a dataclass used by the Generator
    and Solver classes, it holdes our maze data that can be
    easly accessed by the shape and size property

    Attributes:
        walls: A numpy dimentional array which will be a 3D
        blocked: A numpy dimentional array which will be a 2D
    """

    walls: np.ndarray
    blocked: np.ndarray

    @property
    def shape(self) -> tuple[int, int]:
        """
        The shape property is the structure of the grid

        Returns:
            The shape of the walls dimentional array as a tuple

        Exemple:
            For a 10x10 maze the shape method will return
            a tuple like (10, 10)
        """
        return self.walls.shape[:2]

    @property
    def size(self) -> int:
        """
        The size proprety is used to acces the area of the grid

        Returns:
            The size of the grid as an int

        Exemple:
            For a 10x10 maze the size method return
            an int of 100 (the area of the grid)
        """
        height, width = self.shape
        return height * width
