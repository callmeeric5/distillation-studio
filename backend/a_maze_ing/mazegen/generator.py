import random
from typing import Any

import numpy as np

from .algo.algo_factory import AlgorithmFactory
from .algo.utils import AlgorithmGen, GenerateMethod, open_wall, wall_direction
from .utils import PATTERN_42, MazeGrid


class MazeGenerator:
    """
    The class that handle all the lifespan of the maze

    This class centralize all the important information
    as the dimension, entry, exit handle the choosen algorithm
    the output, seed and initialize the maze grid

    Attributes:
        width:     The maze's width as an int
        height:    The maze's height as an int
        entry:     The entry coord as an int tuple
        exit:      The exit coord as an int tuple
        algorithm: The choosen algorithm
                   backtracking by default
        seed:      The maze's seed as an int 42 by default
        perfect:   Indicate if the maze must be perfect
                   with a bool True by default
        display_42: Indicate if the 42 symbol must be
                    displayed True by default
        output_file: Optional file name as an str for
                     the output None by default
    """

    def __init__(
        self,
        width: int,
        height: int,
        entry: tuple[int, int],
        exit: tuple[int, int],
        output_file: str,
        algorithm: GenerateMethod = GenerateMethod.BACKTRACKING,
        seed: int = 42,
        perfect: bool = True,
        display_42: bool = True,
        trace: list[dict[str, Any]] | None = None,
    ) -> None:
        self.width = width
        self.height = height
        self.entry = entry
        self.exit = exit
        self.algorithm = algorithm
        self.seed = seed
        self.perfect = perfect
        self.display_42 = display_42
        self.output_file = output_file
        self.trace = trace
        self._grid = MazeGrid(
            np.ones((self.height, self.width, 4), dtype=bool),
            np.zeros((self.height, self.width), dtype=bool),
        )
        self._visited = np.zeros((self.height, self.width), dtype=bool)
        random.seed(seed)

    def generate(self, method: GenerateMethod | None) -> MazeGrid:
        """
        The complet maze generation

        Make the 42 patern and instanciate the choosen algorithm class
        with the fatory and then generate the maze

        Args:
            method: The choosen algoritm to be initiate, if none it's the
                    default one

        Returns:
            The final MazeGrid created with the choosen algorithm
        """
        if method is None:
            method = self.algorithm
        if self.display_42:
            self._apply_42_pattern()
        algo = AlgorithmFactory.create(
            method,
            grid=self._grid,
            visited=self._visited,
            start=self.entry,
            trace=self.trace,
        )
        if isinstance(algo, AlgorithmGen):
            algo.generate()
        if not self.perfect:
            self._imperfect()
        return self._grid

    def _apply_42_pattern(self) -> None:
        """
        Compute the center of the grid to display the 42 pattern

        It but the cells of the pattern in the block so they
        can not be used

        Raises:
            ValueError: If the grid is too small to contain the pattern
                        or if the pattern erase the entry or exit
        """
        height_42, width_42 = len(PATTERN_42), len(PATTERN_42[0])
        if self.height < height_42 or self.width < width_42:
            raise ValueError(
                f"maze size {self.width}x{self.height} is too small for "
                f"42 pattern {width_42}x{height_42}"
            )
        h_start = (self.height - height_42) // 2
        w_start = (self.width - width_42) // 2
        cells = []
        for height in range(height_42):
            for width in range(width_42):
                if PATTERN_42[height][width] == 1:
                    coord = (h_start + height, w_start + width)
                    if coord == self.entry:
                        raise ValueError(
                            f"42 pattern is overlapped with entry: {coord}"
                        )
                    elif coord == self.exit:
                        raise ValueError(
                            f"42 pattern is overlapped with exit: {coord}"
                        )
                    cells.append(coord)
        for x, y in cells:
            self._grid.blocked[x][y] = True

    def print_maze(self) -> None:
        """
        Make an assci representation of the maze

        Go trough the numpy dimentional array and print:
            + and --- for the borders
            | for the vertical walls
            E for the entry
            X for the exit
            ### for the cells of the 42 pattern
        """
        grid = self._grid.walls
        h, w = grid.shape[0], grid.shape[1]
        print("+" + "---+" * w)
        for i in range(h):
            row = "|"
            for j in range(w):
                if (i, j) == self.entry:
                    cell = " E "
                elif (i, j) == self.exit:
                    cell = " X "
                elif self._grid.blocked[i][j]:
                    cell = "###"
                else:
                    cell = "   "
                if grid[i][j][1]:
                    row += cell + "|"
                else:
                    row += cell + " "
            print(row)
            bottom = "+"
            for j in range(w):
                if grid[i][j][2]:
                    bottom += "---+"
                else:
                    bottom += "   +"
            print(bottom)

    def _imperfect(self) -> None:
        """
        Turns a perfect maze to an imperfect one
        The idea is applying a 2*2 stamp on the grid board
        across 2 rows and 2 rols,
        it won't violate the "no open 3x3 rule"
        break the walls of the patter projection
        """
        stamps = max(1, (self.width * self.height) // 30)
        seen: list[tuple[int, int]] = []
        for _ in range(stamps):
            row = random.randint(0, self.height - 2)
            col = random.randint(0, self.width - 2)
            if any(abs(row - r) < 3 and abs(col - c) < 3 for r, c in seen):
                continue
            if self._grid.blocked[row, col]:
                continue
            if self._grid.blocked[row, col + 1]:
                continue
            if self._grid.blocked[row + 1, col]:
                continue
            if self._grid.blocked[row + 1, col + 1]:
                continue

            self._apply_stamp(row, col)
            seen.append((row, col))

    def _apply_stamp(self, row: int, col: int) -> None:
        self._open_between((row, col), (row, col + 1), 1, 3)
        self._open_between((row + 1, col), (row + 1, col + 1), 1, 3)
        self._open_between((row, col), (row + 1, col), 2, 0)
        self._open_between((row, col + 1), (row + 1, col + 1), 2, 0)

    def _open_between(
        self,
        current: tuple[int, int],
        target: tuple[int, int],
        curr_wall: int,
        target_wall: int,
    ) -> None:
        open_wall(self._grid, current[0], current[1], curr_wall)
        open_wall(self._grid, target[0], target[1], target_wall)
        if self.trace is not None:
            self.trace.append(
                {
                    "kind": "extra",
                    "from": {"row": current[0], "col": current[1]},
                    "to": {"row": target[0], "col": target[1]},
                    "direction": wall_direction(curr_wall),
                }
            )
