import random

from .utils import AlgorithmGen, is_blocked, is_in_bound


class SidewinderGen(AlgorithmGen):
    def generate(self) -> None:
        height, width = self.grid.shape
        for row in range(height):
            run: list[tuple[int, int]] = []
            for col in range(width):
                coord = (row, col)
                if is_blocked(self.grid, coord):
                    run = []
                    continue
                run.append(coord)
                at_east = not is_in_bound(self.grid, row, col + 1) or is_blocked(
                    self.grid, (row, col + 1)
                )
                at_north = not is_in_bound(self.grid, row - 1, col) or is_blocked(
                    self.grid, (row - 1, col)
                )
                close_run = at_east or (not at_north and random.choice([True, False]))
                if close_run:
                    candidates = [
                        cell
                        for cell in run
                        if is_in_bound(self.grid, cell[0] - 1, cell[1])
                        and not is_blocked(self.grid, (cell[0] - 1, cell[1]))
                    ]
                    if candidates:
                        current = random.choice(candidates)
                        target = (current[0] - 1, current[1])
                        self.open_between(current, target, 0, 2)
                    run = []
                else:
                    target = (row, col + 1)
                    self.open_between(coord, target, 1, 3)
