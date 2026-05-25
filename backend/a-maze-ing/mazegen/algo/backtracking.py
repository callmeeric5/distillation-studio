import random

from .utils import AlgorithmGen, is_blocked, is_in_bound


class BacktrackingGen(AlgorithmGen):
    def generate(self) -> None:
        self._backtracking(self.start)

    def _backtracking(self, coord: tuple[int, int]) -> None:
        '''
            The backtracking algorithm, which is using recursion

            Args:
                coord: The coord of the actual block

            Returns:
                The next coord as a tuple if it pass the checks
        '''
        if is_blocked(self.grid, coord):
            return
        directions = list(self.direction)
        random.shuffle(directions)
        self.visited[coord[0], coord[1]] = True
        for move_row, move_col, curr_wall, target_wall in directions:
            target_row = move_row + coord[0]
            target_col = move_col + coord[1]
            if not is_in_bound(self.grid, target_row, target_col):
                continue
            if is_blocked(self.grid, (target_row, target_col)):
                continue
            if self.visited[target_row, target_col]:
                continue
            self.open_between(
                coord,
                (target_row, target_col),
                curr_wall,
                target_wall,
            )
            self._backtracking((target_row, target_col))
