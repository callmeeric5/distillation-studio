import random

from .utils import AlgorithmGen, is_blocked, is_in_bound


class BinaryTreeGen(AlgorithmGen):
    def generate(self) -> None:
        self._binary_tree()

    def _binary_tree(self) -> None:
        '''
            The binary tree algorithm

            It's a preaty straighforward algorithm
            it go trough the grid and randomly break
            either the North or the East wall
        '''
        height, width = self.grid.shape
        for row in range(height):
            for col in range(width):
                coord = (row, col)
                if is_blocked(self.grid, coord):
                    continue
                choice = []
                east_row = row
                east_col = col + 1
                if is_in_bound(self.grid, east_row, east_col)\
                   and not is_blocked(self.grid, (east_row, east_col)):
                    choice.append((east_row, east_col, 1, 3))
                north_row = row - 1
                north_col = col
                if is_in_bound(self.grid, north_row, north_col)\
                   and not is_blocked(self.grid, (north_row, north_col)):
                    choice.append((north_row, north_col, 0, 2))
                if choice:
                    target_row, target_col, curr_wall, \
                        target_wall = random.choice(choice)
                    self.open_between(
                        (row, col),
                        (target_row, target_col),
                        curr_wall,
                        target_wall,
                    )
