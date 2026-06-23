from src import Graph, Parser, Solver


def test_graph() -> None:
    config = Parser("maps/easy/01_linear_path.txt").parse()
    graph = Graph(config)
    solver = Solver(graph)
    path = solver.solve()
    print(path)
    assert path is not None
    assert path == ["start", "waypoint1", "waypoint2", "goal"]
