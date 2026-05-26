from typing import Any

from .algo.algo_factory import AlgorithmFactory, AlgorithmSolve
from .algo.utils import SolveMethod, is_blocked
from .utils import MazeGrid


class MazeSolver:
    def __init__(
        self,
        grid: MazeGrid,
        entry: tuple[int, int],
        exit: tuple[int, int],
        algorithm: SolveMethod = SolveMethod.ASTAR,
        trace: list[dict[str, Any]] | None = None,
    ) -> None:
        self._grid = grid
        self.entry = entry
        self.exit = exit
        self.algorithm = algorithm
        self.trace = trace

    def solve(self, method: SolveMethod | None) -> list[tuple[int, int]]:
        if not method:
            method = self.algorithm
        algo = AlgorithmFactory.create(
            method=method,
            grid=self._grid,
            entry=self.entry,
            exit=self.exit,
            trace=self.trace,
        )
        if isinstance(algo, AlgorithmSolve):
            path = algo.solve()
        return path

    def save(self, method: SolveMethod | None, output_file: str) -> None:
        """
        Conver the grid to hex
        Save the entry/exit
        Save the path
        """
        path = self.solve(method)
        with open(output_file, mode="w", encoding="utf-8") as f:
            height, width = self._grid.shape
            for row in range(height):
                line = []
                for col in range(width):
                    if is_blocked(self._grid, (row, col)):
                        line.append("F")
                    else:
                        line.append(format(self._to_bit(row, col), "X"))
                f.write("".join(line) + "\n")
            f.write("\n")
            f.write(f"{self.entry[1]},{self.entry[0]}\n")
            f.write(f"{self.exit[1]},{self.exit[0]}\n")
            f.write(self._convert_path(path) + "\n")

    def _to_bit(self, row: int, col: int) -> int:
        """
        Convert to binary bits
        """
        value = 0
        walls = self._grid.walls
        # NORTH
        if walls[row, col, 0]:
            value += 1
        # EAST
        if walls[row, col, 1]:
            value += 2
        # SOUTH
        if walls[row, col, 2]:
            value += 4
        # WEST
        if walls[row, col, 3]:
            value += 8
        return value

    def _convert_path(self, path: list[tuple[int, int]]) -> str:
        """
        Convert to NESW
        """
        res = ""
        for i in range(len(path) - 1):
            curr_row, curr_col = path[i]
            next_row, next_col = path[i + 1]
            row_diff = next_row - curr_row
            col_diff = next_col - curr_col
            if row_diff == 1:
                res += "S"
            elif row_diff == -1:
                res += "N"
            elif col_diff == 1:
                res += "E"
            elif col_diff == -1:
                res += "W"
        return res
