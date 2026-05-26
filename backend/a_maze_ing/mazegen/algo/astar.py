import heapq

from .utils import AlgorithmSolve


class AstarSolve(AlgorithmSolve):
    """
    Use priority_queue to get the current lowest cost cell
    Traverse the neighbor cells, find the lowest cost neighbor
    Then record the path chain, start from the neighbor

    f(total cost) = g(cost from entry to curr) + h(cost from curr to exit)
    """

    def solve(self) -> list[tuple[int, int]]:
        def h(a: tuple[int, int], b: tuple[int, int]):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        priority_queue: list[tuple[int, tuple[int, int]]] = []
        heapq.heappush(priority_queue, (0, self.entry))
        previous: dict[tuple[int, int], tuple[int, int]] = {}
        g_cost = {self.entry: 0}
        visited = set()
        while priority_queue:
            _, curr = heapq.heappop(priority_queue)
            if curr in visited:
                continue
            visited.add(curr)
            self.record_visit(curr)
            if curr == self.exit:
                return self._path(previous)
            for neighbor in self.get_neighbors(curr):
                neighbor_g = g_cost[curr] + 1
                if neighbor_g < g_cost.get(neighbor, float("inf")):
                    previous[neighbor] = curr
                    g_cost[neighbor] = neighbor_g
                    f_score = neighbor_g + h(neighbor, self.exit)
                    heapq.heappush(priority_queue, (f_score, neighbor))
        return [self.entry]

    def _path(self, previous) -> list[tuple[int, int]]:
        path = []
        current = self.exit
        while current != self.entry:
            path.append(current)
            current = previous[current]
        path.append(self.entry)
        return path[::-1]
