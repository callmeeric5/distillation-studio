import heapq

from .graph import Graph
from .parser import ZoneType


class Solver:
    """Find useful routes and assign drones to them."""

    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def solve(self) -> list[str] | None:
        paths = self.find_paths()
        if not paths:
            return None
        return paths[0]

    def find_paths(self) -> list[list[str]]:
        """Return low-cost simple paths from start to end."""
        paths: list[list[str]] = []
        queue: list[tuple[float, int, list[str]]] = [
            (0, 0, [self.graph.start])
        ]

        while queue and len(paths) < self.graph.nb_drones:
            cost, _, path = heapq.heappop(queue)
            current = path[-1]
            if current == self.graph.end:
                paths.append(path)
                continue
            for neighbor in self._ordered_neighbors(current):
                if neighbor in path:
                    continue
                if self.graph.get_zone(neighbor).zone_type == ZoneType.BLOCKED:
                    continue
                next_path = [*path, neighbor]
                next_cost = cost + self._cost(neighbor)
                heapq.heappush(
                    queue,
                    (next_cost, len(next_path), next_path),
                )
        return paths

    def solve_all(self) -> list[list[str]]:
        """Assign one route to each drone using the best available paths."""
        paths = self.find_paths()
        if not paths:
            return []
        loads = [0 for _ in paths]
        assignments: list[list[str]] = []
        for _ in range(self.graph.nb_drones):
            index = min(
                range(len(paths)),
                key=lambda i: self._estimated_finish(paths[i], loads[i]),
            )
            assignments.append(paths[index])
            loads[index] += 1
        return assignments

    def _cost(self, node: str) -> float:
        zone_type = self.graph.get_zone(node).zone_type
        if zone_type == ZoneType.RESTRICTED:
            return 2
        if zone_type == ZoneType.PRIORITY:
            return 0.5
        return 1

    def _ordered_neighbors(self, node: str) -> list[str]:
        return sorted(
            self.graph.get_neighbors(node),
            key=lambda name: (
                self._cost(name),
                abs(
                    self.graph.get_zone(name).pos.x
                    - self.graph.get_zone(self.graph.end).pos.x
                )
                + abs(
                    self.graph.get_zone(name).pos.y
                    - self.graph.get_zone(self.graph.end).pos.y
                ),
                name,
            ),
        )

    def _estimated_finish(self, path: list[str], assigned: int) -> float:
        capacity = self.graph.path_capacity(path)
        return self.graph.path_cost(path) + (assigned / capacity)
