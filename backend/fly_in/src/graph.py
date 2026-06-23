from .parser import Config, Connection, Zone


class Graph:
    def __init__(self, config: Config) -> None:
        if not config.start or not config.end:
            raise ValueError("graph requires start and end zones")
        self.nb_drones = config.nb_drones
        self.start = config.start.name
        self.end = config.end.name
        self.zones = {self.start: config.start, self.end: config.end}
        self.connections = {}
        for zone in config.zones:
            self.zones[zone.name] = zone
        self.adjacency: dict[str, list[str]] = {
            name: [] for name in self.zones
        }
        for connection in config.connections:
            key = tuple(sorted((connection.source, connection.target)))
            self.connections[key] = connection
            self.adjacency[connection.source].append(connection.target)
            self.adjacency[connection.target].append(connection.source)

    def get_neighbors(self, name: str) -> list[str]:
        return self.adjacency.get(name, [])

    def get_zone(self, name: str) -> Zone:
        return self.zones[name]

    def get_connection(self, name: tuple[str, str]) -> Connection:
        return self.connections[tuple(sorted(name))]

    def movement_cost(self, zone_name: str) -> int:
        zone_type = self.get_zone(zone_name).zone_type
        if zone_type.value == "restricted":
            return 2
        return 1

    def zone_capacity(self, zone_name: str) -> int:
        if zone_name in {self.start, self.end}:
            return self.nb_drones
        return self.get_zone(zone_name).max_drones

    def path_cost(self, path: list[str]) -> int:
        return sum(self.movement_cost(zone) for zone in path[1:])

    def path_capacity(self, path: list[str]) -> int:
        capacities = []
        for zone in path[1:-1]:
            capacities.append(self.zone_capacity(zone))
        for source, target in zip(path, path[1:]):
            capacities.append(
                self.get_connection((source, target)).max_link_capacity
            )
        return max(1, min(capacities, default=self.nb_drones))
