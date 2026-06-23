from src import Graph, Parser
from src.parser import Connection, Position, Zone, ZoneType


def test_graph() -> None:
    config = Parser("maps/easy/01_linear_path.txt").parse()
    graph = Graph(config)
    assert graph.get_neighbors("start") == ["waypoint1"]
    assert graph.get_zone("start") == Zone(
        name="start",
        pos=Position(x=0, y=0),
        zone_type=ZoneType.NORMAL,
        color="green",
    )
    assert graph.get_connection(("start", "waypoint1")) == Connection(
        source="start", target="waypoint1", max_link_capacity=1
    )
