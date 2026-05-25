import random

from .utils import AlgorithmGen, is_blocked, is_in_bound


class PrimGen(AlgorithmGen):
    def generate(self) -> None:
        if is_blocked(self.grid, self.start):
            return

        visited = {self.start}
        frontier = self._frontier(self.start, visited)
        while frontier:
            index = random.randrange(len(frontier))
            current, target, curr_wall, target_wall = frontier.pop(index)
            if target in visited:
                continue
            self.open_between(current, target, curr_wall, target_wall)
            visited.add(target)
            frontier.extend(self._frontier(target, visited))

    def _frontier(
        self,
        coord: tuple[int, int],
        visited: set[tuple[int, int]],
    ) -> list[tuple[tuple[int, int], tuple[int, int], int, int]]:
        cells = []
        for move_row, move_col, curr_wall, target_wall in self.direction:
            target = (coord[0] + move_row, coord[1] + move_col)
            if not is_in_bound(self.grid, target[0], target[1]):
                continue
            if is_blocked(self.grid, target) or target in visited:
                continue
            cells.append((coord, target, curr_wall, target_wall))
        return cells
