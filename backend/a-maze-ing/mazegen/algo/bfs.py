from collections import deque

from .utils import AlgorithmSolve


class BfsSolve(AlgorithmSolve):
    def solve(self) -> list[tuple[int, int]]:
        queue = deque([self.entry])
        previous: dict[tuple[int, int], tuple[int, int]] = {}
        visited = {self.entry}
        while queue:
            current = queue.popleft()
            self.record_visit(current)
            if current == self.exit:
                return self._path(previous)
            for neighbor in self.get_neighbors(current):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                previous[neighbor] = current
                queue.append(neighbor)
        return [self.entry]

    def _path(self, previous) -> list[tuple[int, int]]:
        if self.exit not in previous and self.exit != self.entry:
            return [self.entry]
        path = []
        current = self.exit
        while current != self.entry:
            path.append(current)
            current = previous[current]
        path.append(self.entry)
        return path[::-1]
